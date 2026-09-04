# -*- coding: utf-8 -*-
"""Il ragionamento d'asta: come spendere i crediti che restano.

Non e' un elenco ordinato per prezzo, e' una strategia. Tiene insieme quattro cose
che all'asta vanno decise contemporaneamente:

- **i top di reparto**, che valgono la spesa solo dove il divario dal sostituto e'
  davvero ampio;
- **gli slot**, perche' una rosa e' fatta di fasce e riempirle tutte con giocatori
  della stessa fascia e' il modo classico di sprecare crediti;
- **il modificatore di difesa**, che nelle leghe che lo usano cambia le priorita':
  un reparto arretrato con media voto alta vale piu' di un attaccante in piu';
- **le scommesse**, cioe' i pochi crediti da tenere per chi costa niente e puo'
  valere molto.

Tutto si ricalcola a ogni acquisto segnato, quindi il piano di adesso non e' quello
di dieci minuti fa.
"""
import itertools

import fanta_modello as M

RUOLI = ['P', 'D', 'C', 'A']
RUOLO_NOME = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti',
              'A': 'Attaccanti'}
TITOLARI = {'P': 1, 'D': 4, 'C': 4, 'A': 2}
GIORNATE = 38


def situazione(d, asta, cfg, mia):
    per_id = {p['id']: p for p in d['giocatori']}
    ho = {r: sum(1 for pid in mia if per_id.get(pid, {}).get('R') == r) for r in RUOLI}
    manca = {r: max(0, cfg['slot'][r] - ho[r]) for r in RUOLI}
    residuo = cfg['crediti'] - sum(mia.values())
    return {'ho': ho, 'manca': manca, 'residuo': residuo,
            'slot_mancanti': sum(manca.values()),
            'rosa': [per_id[pid] for pid in mia if pid in per_id]}


def budget_per_reparto(cfg, sit):
    """Divido i crediti che restano fra i reparti ancora da completare, in
    proporzione alla quota di ruolo e a quanti slot mancano davvero."""
    pesi = {r: cfg['quote'][r] * sit['manca'][r] / float(max(1, cfg['slot'][r]))
            for r in RUOLI}
    tot = sum(pesi.values()) or 1.0
    return {r: sit['residuo'] * pesi[r] / tot for r in RUOLI}


def piano(d, asta, cfg, massimi):
    """La rosa che ti consiglio di costruire con quello che resta sul mercato.

    Dentro ogni reparto prendo i migliori che il budget di reparto regge, lasciando
    sempre un credito per ogni slot ancora da riempire: e' cosi' che si evita di
    arrivare in fondo all'asta con tre buchi e due crediti.
    """
    mia = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
           if v['squadra'] == asta['mia']}
    sit = situazione(d, asta, cfg, mia)
    quote = budget_per_reparto(cfg, sit)
    presi = set(asta['acquisti'])

    scelti, riempitivi, spesa = {}, {}, 0
    for ru in RUOLI:
        liberi = sorted([p for p in d['giocatori']
                         if p['R'] == ru and p['id'] not in presi],
                        key=lambda x: -x['valore'])
        cassa = quote[ru]
        gruppo = []
        for p in liberi:
            if len(gruppo) >= sit['manca'][ru]:
                break
            costo = massimi.get(p['id'], 1)
            restano = sit['manca'][ru] - len(gruppo) - 1
            if costo > cassa - restano:
                continue
            gruppo.append((p, costo))
            cassa -= costo
        # gli ultimi slot si riempiono con chi capita a uno o due crediti: non ha
        # senso fare nomi, conta solo sapere quanti sono e quanto costano
        conta = [(q, c) for q, c in gruppo if c >= 4]
        coda = [(q, c) for q, c in gruppo if c < 4]
        scelti[ru] = conta
        riempitivi[ru] = (len(coda), sum(c for _, c in coda))
        spesa += sum(c for _, c in gruppo)
    return {'sit': sit, 'quote': quote, 'scelti': scelti, 'spesa': spesa,
            'riempitivi': riempitivi, 'avanzo': sit['residuo'] - spesa}


def blocchi_difesa(d, asta, cfg, massimi, quante=4):
    """Quattro modi di costruire il blocco del modificatore, a quattro prezzi.

    La versione di prima metteva in fila le squadre: portiere e tre difensori
    dell'Inter, dell'Atalanta, del Napoli. Era una bella tabella e un consiglio
    inutile, perche' all'asta quattro giocatori della stessa squadra non li
    prendi quasi mai — te li soffiano, o costano il doppio proprio perche' tutti
    hanno avuto la stessa idea.

    Qui invece il blocco si costruisce come si costruisce davvero: pescando in
    tutto il mercato rimasto, cercando la media voto piu' alta che quel budget
    consente. Quattro fasce, dalla piu' magra alla piu' ricca, cosi' si vede
    quanto costa ogni decimo di media — che e' l'unica domanda vera, visto che
    da 6,00 in su ogni 0,25 di media vale un punto a giornata.

    Il blocco e' portiere piu' TRE difensori perche' nel modificatore contano
    solo i tre voti migliori. Il quarto difensore va schierato lo stesso, ma in
    quella media non entra: per quel posto conviene chi porta bonus.
    """
    presi = set(asta['acquisti'])
    miei = set(mercato_miei(asta))

    def liberi(ru):
        return [p for p in d['giocatori']
                if p['R'] == ru and (p['id'] not in presi or p['id'] in miei)
                and p['pv_proiettate'] >= 18 and p['mv_att']]

    portieri = sorted(liberi('P'), key=lambda x: -x['mv_att'])
    difensori = sorted(liberi('D'), key=lambda x: -x['mv_att'])
    if not portieri or len(difensori) < 3:
        return []

    def costo(p):
        return 0 if p['id'] in miei else max(1, massimi.get(p['id'], 1))

    def costruisci(tetto):
        """Il miglior blocco entro un tetto di spesa.

        Prima riempio col miglior rapporto fra media voto e prezzo — cosi' il
        blocco sta in piedi comunque — poi spendo quel che avanza migliorando
        un pezzo alla volta. Lo stesso metodo delle rose, e per lo stesso
        motivo: partire dai piu' cari lascia buchi che poi non si turano.
        """
        def resa(p):
            return (p['mv_att'] - 5.7) / max(1.0, costo(p))

        scelti = {'P': None, 'D': []}
        for p in sorted(portieri, key=lambda x: -resa(x)):
            if costo(p) <= tetto - 3:      # tre crediti per i difensori
                scelti['P'] = p
                break
        if not scelti['P']:
            scelti['P'] = min(portieri, key=costo)
        speso = costo(scelti['P'])
        for p in sorted(difensori, key=lambda x: -resa(x)):
            if len(scelti['D']) >= 3:
                break
            restano = 3 - len(scelti['D']) - 1
            if costo(p) <= tetto - speso - restano:
                scelti['D'].append(p)
                speso += costo(p)
        if len(scelti['D']) < 3:
            return None

        # migliorie: sostituisco il piu' debole con il meglio che il resto paga
        for _ in range(30):
            fatto = False
            for ru, gruppo in (('P', [scelti['P']]), ('D', scelti['D'])):
                debole = min(gruppo, key=lambda x: x['mv_att'])
                disponibile = tetto - speso + costo(debole)
                pool = portieri if ru == 'P' else difensori
                meglio = None
                for q in pool:
                    if q['id'] in {x['id'] for x in [scelti['P']] + scelti['D']}:
                        continue
                    if q['mv_att'] <= debole['mv_att']:
                        break
                    if costo(q) <= disponibile:
                        meglio = q
                        break
                if meglio is None:
                    continue
                speso += costo(meglio) - costo(debole)
                if ru == 'P':
                    scelti['P'] = meglio
                else:
                    scelti['D'] = [x for x in scelti['D']
                                   if x['id'] != debole['id']] + [meglio]
                fatto = True
            if not fatto:
                break

        blocco = [scelti['P']] + sorted(scelti['D'], key=lambda x: -x['mv_att'])
        mv = M.media_blocco(scelti['P']['mv_att'],
                            [x['mv_att'] for x in scelti['D']])
        return {'blocco': blocco, 'costo': speso, 'mv': mv,
                'punti': M.punti_modificatore(mv) if mv else 0.0,
                'pv': sum(x['pv_proiettate'] for x in blocco) / 4.0,
                'squadre': len({x['squadra'] for x in blocco}),
                'gia_miei': [x['nome'] for x in blocco if x['id'] in miei]}

    # le fasce si adattano a quanto ti resta: proporre un blocco da 160 crediti
    # a chi ne ha 90 in cassa e' un dispetto, non un consiglio
    residuo = cfg['crediti'] - sum(v['prezzo'] for v in asta['acquisti'].values()
                                   if v['squadra'] == asta['mia'])
    massimo_spendibile = max(20, int(residuo * 0.55))
    tetti = [t for t in (35, 70, 115, 170) if t <= massimo_spendibile]
    if not tetti:
        tetti = [max(12, massimo_spendibile)]
    if massimo_spendibile > tetti[-1] * 1.35:
        tetti.append(massimo_spendibile)

    nomi = {35: 'Con poco', 70: 'Spesa media', 115: 'Investimento',
            170: 'Senza badare a spese'}
    fuori, visti = [], set()
    for t in tetti[:quante]:
        r = costruisci(t)
        if not r:
            continue
        firma = tuple(sorted(x['id'] for x in r['blocco']))
        if firma in visti:
            continue
        visti.add(firma)
        r['tetto'] = t
        r['titolo'] = nomi.get(t, 'Fino a %d crediti' % t)
        fuori.append(r)
    return fuori


def mercato_miei(asta):
    """Gli id dei giocatori che ho gia' comprato: nel blocco valgono zero
    crediti, perche' li ho gia' pagati."""
    return [pid for pid, v in asta['acquisti'].items()
            if v['squadra'] == asta['mia']]


def scommesse(d, asta, massimi, quante=12):
    """Chi costa poco e puo' valere molto.

    Una scommessa non e' semplicemente un giocatore economico: il portiere titolare
    del Lecce costa poco perche' vale poco, non perche' il mercato si sia distratto.
    Cerco altro: chi rende molto rispetto a quello che chiede, e ha una ragione
    concreta per farlo — l'eta', i rigori, un posto da titolare appena conquistato.
    I portieri restano fuori: li' non ci sono sorprese, o giochi o no.
    """
    presi = set(asta['acquisti'])

    # Quanto e' "poco" dipende dal reparto. Diciotto crediti sono tanti per un
    # difensore e pochi per un attaccante, dove il listino parte piu' in alto:
    # con un tetto unico gli attaccanti da scommessa erano sempre uno o due.
    # Il tetto lo prendo dai prezzi veri: la meta' del prezzo mediano dei
    # titolari di quel ruolo, mai sotto i dodici crediti.
    tetti = {}
    for ru in ('D', 'C', 'A'):
        prezzi = sorted(massimi.get(p['id'], 1) for p in d['giocatori']
                        if p['R'] == ru and p['id'] not in presi
                        and p['pv_proiettate'] >= 22)
        mediana = prezzi[len(prezzi) // 2] if prezzi else 20
        tetti[ru] = max(12, min(34, int(mediana * 0.62)))

    liberi = [p for p in d['giocatori']
              if p['id'] not in presi and p['R'] != 'P'
              and massimi.get(p['id'], 1) <= tetti.get(p['R'], 18)
              and p['valore'] > 0]

    # il metro e' il rendimento per credito, misurato dentro il proprio ruolo
    soglie = {}
    for ru in ('D', 'C', 'A'):
        resa = sorted((p['valore'] / max(1.0, massimi.get(p['id'], 1))
                       for p in liberi if p['R'] == ru), reverse=True)
        # se in un reparto ci sono pochi candidati, alzare l'asticella al primo
        # quarto non lascia nessuno: li' scendo alla meta'
        taglio = len(resa) // 4 if len(resa) >= 16 else len(resa) // 2
        soglie[ru] = resa[max(0, taglio)] if resa else 0

    out = []
    for p in liberi:
        costo = massimi.get(p['id'], 1)
        resa = p['valore'] / max(1.0, costo)
        if resa < soglie.get(p['R'], 0):
            continue
        r25 = p['storico'].get('2025-26') or {}
        forti, contorno = [], []
        if p.get('eta') and p['eta'] <= 23 and p['fm_att'] >= 6.25:
            forti.append("%d anni e fantamedia già da titolare" % p['eta'])
        if (r25.get('rig_tir') or 0) >= 3:
            forti.append('tira i rigori (%g su %g lo scorso anno)'
                         % (r25.get('rig_seg') or 0, r25['rig_tir']))
        if ((p.get('perc_titolarita') or 0) >= 70
                and p.get('dove_probabili') == 'titolari'
                and (p.get('slot') or 9) >= 4):
            forti.append('titolare annunciato pur essendo di bassa fascia')
        if p['stima']:
            forti.append('arriva da fuori: il mercato non sa ancora quanto vale')
        red = p.get('redazioni')
        if red and red['pro'] >= 1:
            forti.append('lo indica come occasione %s'
                         % ('un articolo di consigli' if red['pro'] == 1
                            else '%d articoli di consigli' % red['pro']))
        if not forti:
            continue
        if p['pv_proiettate'] >= 28:
            contorno.append('gioca praticamente sempre')
        if (r25.get('gol') or 0) >= 6:
            contorno.append('%d gol lo scorso anno' % int(r25['gol']))
        if (r25.get('ass') or 0) >= 4:
            contorno.append('%d assist' % int(r25['ass']))
        spinta = 1.15 if p['rischio'] == 'Basso' else 1.0
        if red and red['pro']:
            spinta *= 1.0 + min(0.25, 0.08 * red['pro'])
        if red and red['contro']:
            spinta *= max(0.75, 1.0 - 0.10 * red['contro'])
        out.append({'p': p, 'costo': costo, 'motivi': forti + contorno,
                    'punteggio': resa * spinta})
    out.sort(key=lambda x: -x['punteggio'])
    return out[:quante]


def piano_scommesse(d, asta, cfg, massimi, per_ruolo=4):
    """Le scommesse divise per reparto, con quante te ne servono davvero.

    In una rosa da venticinque, i giocatori che decidono il campionato sono
    cinque o sei; gli altri diciannove sono il problema che tutti sottovalutano.
    Le ultime caselle di ogni reparto si riempiono quasi sempre a fine asta, di
    fretta, con quello che avanza — ed e' li' che si perdono i punti, non sul
    top che hai pagato dieci crediti di troppo.

    Questa funzione risponde a tre domande in una volta: **quante** caselle di
    basso costo ti restano da riempire in ogni reparto, **chi** ci metterei, e
    **quanti crediti** tenere da parte perche' non ti tocchi prendere il primo
    che passa.
    """
    tutte = scommesse(d, asta, massimi, quante=60)
    mia = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
           if v['squadra'] == asta['mia']}
    sit = situazione(d, asta, cfg, mia)

    fuori = {}
    for ru in ('D', 'C', 'A'):
        quelle = [x for x in tutte if x['p']['R'] == ru][:per_ruolo]
        if not quelle:
            continue
        # le caselle che finiranno a scommesse: quelle oltre i titolari veri
        titolari = MINIMI.get(ru, 0)
        caselle = max(0, min(sit['manca'][ru], cfg['slot'][ru] - titolari))
        tenere = sum(x['costo'] for x in quelle[:max(1, caselle)])
        fuori[ru] = {'quali': quelle, 'caselle': caselle, 'tenere': tenere}
    return {'per_ruolo': fuori, 'sit': sit,
            'da_tenere': sum(v['tenere'] for v in fuori.values())}


def avvisi(d, asta, cfg, piano_, scar, cal):
    """Le cose che, se non te le dice nessuno, all'asta te ne accorgi troppo tardi."""
    sit = piano_['sit']
    fuori = []

    if sit['slot_mancanti'] and sit['residuo'] < sit['slot_mancanti']:
        fuori.append(('allarme', 'Ti restano <b>%d</b> crediti per <b>%d</b> slot: '
                                'non bastano nemmeno a un credito a testa.'
                      % (sit['residuo'], sit['slot_mancanti'])))
    elif sit['slot_mancanti']:
        medio = sit['residuo'] / float(sit['slot_mancanti'])
        if medio < 3 and sit['slot_mancanti'] > 4:
            fuori.append(('allarme', 'Ti restano <b>%.1f</b> crediti per slot: da qui '
                                     'in avanti puoi solo riempire.' % medio))

    for ru in RUOLI:
        if not sit['manca'][ru]:
            continue
        s = max([scar[k] for k in scar if k[0] == ru] or [1.0])
        if s >= 1.5:
            fuori.append(('allarme', '<b>%s</b>: ti mancano %d slot e le scorte '
                                     'stanno finendo. Se ti servono, muoviti adesso.'
                          % (RUOLO_NOME[ru], sit['manca'][ru])))
        if cal['ruoli'][ru] >= 1.25 and cal['per_ruolo_n'][ru] >= 3:
            fuori.append(('nota', '<b>%s</b>: la lega li sta pagando il %+d%% sopra il '
                                  'loro valore. Lascia correre e recupera altrove.'
                          % (RUOLO_NOME[ru], round((cal['ruoli'][ru] - 1) * 100))))
        elif cal['ruoli'][ru] <= 0.85 and cal['per_ruolo_n'][ru] >= 3:
            fuori.append(('ok', '<b>%s</b>: si comprano il %d%% sotto il loro valore. '
                                'È il reparto dove conviene spingere.'
                          % (RUOLO_NOME[ru], round((1 - cal['ruoli'][ru]) * 100))))

    portieri = sorted([p for p in sit['rosa'] if p['R'] == 'P'],
                      key=lambda x: -x['pv_proiettate'])
    if cfg['modificatore_difesa'] and portieri and len(portieri) >= 2:
        if portieri[1]['pv_proiettate'] < 12 and portieri[0]['pv_proiettate'] >= 24:
            fuori.append(('nota', 'Il tuo secondo portiere non gioca mai. Col '
                                  'modificatore, se <b>%s</b> salta due giornate il '
                                  'blocco difensivo crolla: un vice che scenda in '
                                  'campo costa pochi crediti e vale la pena.'
                          % portieri[0]['nome']))

    alti = [p for p in sit['rosa'] if p['rischio'] == 'Alto']
    if len(alti) >= 3:
        fuori.append(('allarme', 'Hai gia\' <b>%d</b> giocatori a rischio alto '
                                 '(%s): un altro e la rosa diventa fragile.'
                      % (len(alti), ', '.join(p['nome'] for p in alti[:4]))))

    fuori_ora = [p for p in sit['rosa'] if p['stato_attuale']]
    if fuori_ora:
        fuori.append(('nota', 'In rosa hai <b>%d</b> giocatori fuori adesso: %s. '
                              'Serve un ricambio pronto.'
                      % (len(fuori_ora), ', '.join(p['nome'] for p in fuori_ora[:4]))))

    if piano_['avanzo'] > 0.25 * max(1, sit['residuo']) and sit['slot_mancanti'] > 2:
        fuori.append(('nota', 'Il piano qui sotto lascia <b>%d</b> crediti non spesi: '
                              'puoi alzare il tiro su un top invece di spalmarli.'
                      % piano_['avanzo']))
    return fuori


# ============================================================ la rosa ideale
MINIMI = {'P': 1, 'D': 5, 'C': 5, 'A': 3}


def costruisci_rosa(d, asta, cfg, massimi, ancore=(), preferenze=None,
                    tetto_singolo=None):
    """La rosa che costruirei con i crediti e i giocatori ancora disponibili.

    Prima assicuro i titolari veri di ogni reparto — chi gioca almeno ventidue
    partite — scegliendoli in un'unica classifica per resa sul credito, non reparto
    per reparto: altrimenti il primo della lista si mangia il budget degli altri.
    Poi completo, e chiudo gli ultimi buchi col meno caro.
    """
    # la preferenza inclina la scelta verso un reparto senza imporre quote:
    # a parita' di resa sul credito, un difensore vale una volta e mezzo se sto
    # costruendo una corazzata dietro. Non e' un vincolo, e' un'inclinazione,
    # cosi' la rosa resta comunque sensata invece di diventare una caricatura.
    preferenze = preferenze or {}
    mia = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
           if v['squadra'] == asta['mia']}
    presi = set(asta['acquisti'])
    per_id = {p['id']: p for p in d['giocatori']}
    rosa = [per_id[pid] for pid in mia if pid in per_id]
    gia_miei = set(mia)
    budget = cfg['crediti'] - sum(mia.values())
    costo = {p['id']: max(1, massimi.get(p['id'], 1)) for p in d['giocatori']}

    for nome in ancore:
        p = next((q for q in d['giocatori'] if q['nome'] == nome
                  and q['id'] not in presi), None)
        if p and budget - costo[p['id']] >= 0:
            rosa.append(p)
            budget -= costo[p['id']]

    def quanti(ru, soglia=0):
        return sum(1 for q in rosa if q['R'] == ru and q['pv_proiettate'] >= soglia)

    def liberi(ruoli, soglia=0):
        return [p for p in d['giocatori']
                if p['R'] in ruoli and p['id'] not in presi and p not in rosa
                and p['pv_proiettate'] >= soglia and p['valore'] > 0]

    for fase in (True, False):
        while True:
            if fase:
                serve = [ru for ru in RUOLI if quanti(ru, 22) < MINIMI[ru]
                         and quanti(ru) < cfg['slot'][ru]]
            else:
                serve = [ru for ru in RUOLI if quanti(ru) < cfg['slot'][ru]]
            if not serve:
                break
            resta = sum(cfg['slot'][r] - quanti(r) for r in RUOLI) - 1
            pool = [p for p in liberi(serve, 22 if fase else 0)
                    if costo[p['id']] <= budget - resta
                    and (tetto_singolo is None or costo[p['id']] <= tetto_singolo
                         or p['id'] in gia_miei)]
            if not pool:
                break
            p = max(pool, key=lambda x: x['valore'] / costo[x['id']]
                    * preferenze.get(x['R'], 1.0))
            rosa.append(p)
            budget -= costo[p['id']]

    # il secondo portiere non e' un riempitivo: col modificatore, se il titolare
    # salta due giornate e schieri un portiere qualunque il blocco crolla. Meglio
    # il vice della stessa squadra (entra lui quando l'altro non c'e') o un altro
    # titolare vero, spendendo i pochi crediti che servono
    if cfg['modificatore_difesa'] and quanti('P') == 1 and cfg['slot']['P'] > 1:
        mio_por = next(q for q in rosa if q['R'] == 'P')
        candidati = [q for q in d['giocatori']
                     if q['R'] == 'P' and q['id'] not in presi and q not in rosa
                     and costo[q['id']] <= min(12, budget - (sum(cfg['slot'][r]
                                                                 for r in RUOLI)
                                                             - len(rosa) - 1))]
        stessa = [q for q in candidati if q['squadra'] == mio_por['squadra']]
        titolari = [q for q in candidati if q['pv_proiettate'] >= 24]
        scelta = None
        if stessa:
            scelta = max(stessa, key=lambda x: x['mv_att'])
        elif titolari:
            scelta = max(titolari, key=lambda x: x['mv_att'])
        if scelta is not None:
            rosa.append(scelta)
            budget -= costo[scelta['id']]

    # gli ultimi buchi: il meno caro che resta
    while len(rosa) < sum(cfg['slot'].values()):
        serve = [ru for ru in RUOLI if quanti(ru) < cfg['slot'][ru]]
        avanzi = [p for p in d['giocatori'] if p['R'] in serve
                  and p['id'] not in presi and p not in rosa]
        if not avanzi:
            break
        p = min(avanzi, key=lambda x: (costo[x['id']], -x['valore']))
        rosa.append(p)
        budget -= costo[p['id']]

    blocco = blocco_scelto(rosa)
    return {'rosa': rosa, 'gia_miei': gia_miei, 'avanzo': budget,
            'costo': costo, 'blocco': blocco,
            'spesa': {ru: sum(costo[p['id']] for p in rosa
                              if p['R'] == ru and p['id'] not in gia_miei)
                      for ru in RUOLI}}


def blocco_scelto(rosa):
    """Portiere che gioca piu' i tre difensori con la media voto migliore fra
    quelli che scendono in campo: e' il quartetto che determina il modificatore."""
    por = sorted([p for p in rosa if p['R'] == 'P'],
                 key=lambda x: -x['pv_proiettate'])[:1]
    dif = sorted([p for p in rosa if p['R'] == 'D' and p['pv_proiettate'] >= 22],
                 key=lambda x: -x['mv_att'])[:3]
    if not por or len(dif) < 3:
        return None
    q = por + dif
    return {'giocatori': q, 'mv': sum(x['mv_att'] for x in q) / len(q)}


def per_fascia(d, asta, massimi, ru, quanti=8):
    """Il reparto diviso in tre fasce di prezzo, cosi' si vede l'alternativa a
    ogni livello invece di un elenco unico dominato dai piu' cari."""
    presi = set(asta['acquisti'])
    liberi = [p for p in d['giocatori']
              if p['R'] == ru and p['id'] not in presi and p['valore'] > 0]
    liberi.sort(key=lambda x: -x['valore'])
    alto = [p for p in liberi if massimi.get(p['id'], 1) >= 40][:quanti]
    medio = [p for p in liberi if 12 <= massimi.get(p['id'], 1) < 40][:quanti]
    basso = [p for p in liberi if massimi.get(p['id'], 1) < 12][:quanti]
    return {'alto': alto, 'medio': medio, 'basso': basso}


def rigoristi(d, asta, massimi, quanti=12):
    """Chi tira i rigori: e' il bonus piu' prevedibile che esista al fanta."""
    presi = set(asta['acquisti'])
    out = []
    for p in d['giocatori']:
        if p['id'] in presi:
            continue
        r = p['storico'].get('2025-26') or {}
        tirati = r.get('rig_tir') or 0
        if tirati < 3:
            continue
        out.append({'p': p, 'tirati': tirati, 'segnati': r.get('rig_seg') or 0,
                    'costo': massimi.get(p['id'], 1),
                    'dubbio': p.get('cambio_squadra')})
    out.sort(key=lambda x: (-x['tirati'], -x['p']['valore']))
    return out[:quanti]


def occasioni(d, asta, massimi, quante=14):
    """Chi vale piu' di quanto costera': il divario fra il mio valore e il prezzo
    di mercato, misurato in fantapunti per credito."""
    presi = set(asta['acquisti'])
    out = []
    for p in d['giocatori']:
        if p['id'] in presi or p['valore'] <= 0 or p['pv_proiettate'] < 20:
            continue
        mercato = max(1, p['prezzo_mercato'])
        mio = max(1, massimi.get(p['id'], 1))
        if mercato >= mio:
            continue
        out.append({'p': p, 'costo': mio, 'mercato': mercato,
                    'divario': mio - mercato,
                    'resa': p['valore'] / mercato})
    out.sort(key=lambda x: -x['resa'])
    return out[:quante]


def sempre_presenti(d, asta, massimi, quanti=12):
    """Chi non salta mai: in una lega da trentotto giornate la presenza e' il
    bonus piu' sottovalutato di tutti."""
    presi = set(asta['acquisti'])
    out = [p for p in d['giocatori']
           if p['id'] not in presi and p['pv_proiettate'] >= 30 and p['valore'] > 0]
    out.sort(key=lambda p: -(p['valore'] / max(1, massimi.get(p['id'], 1))))
    return out[:quanti]


def punteggio_rosa(rosa, cfg):
    """Quanto rende una rosa in una stagione intera.

    Non e' la somma di tutti e venticinque: ogni giornata ne schieri undici, quindi
    contano soprattutto i titolari. La panchina pesa un quarto, e chi non gioca mai
    quasi niente. Sotto, la penalita' per i reparti che non hanno abbastanza
    giocatori veri: una rosa di nomi che non scendono in campo non regge trentotto
    giornate.
    """
    tot = 0.0
    for ru in RUOLI:
        g = sorted([p for p in rosa if p['R'] == ru], key=lambda x: -x['valore'])
        tot += sum(p['valore'] for p in g[:TITOLARI[ru]])
        tot += sum(0.25 * p['valore'] if p['pv_proiettate'] >= 15
                   else 0.05 * p['valore'] for p in g[TITOLARI[ru]:])
    for ru in ('D', 'C', 'A'):
        veri = sum(1 for p in rosa if p['R'] == ru and p['pv_proiettate'] >= 20)
        tot -= max(0, MINIMI[ru] - veri) * 12
    b = blocco_scelto(rosa)
    if cfg['modificatore_difesa']:
        tot += (max(0.0, b['mv'] - 6.0) * 4.0 * 38 / 3.0) if b else -25
    return tot


def rosa_ideale(d, asta, cfg, massimi):
    """Confronto piu' idee di squadra, non una sola.

    Un algoritmo che sceglie sempre il miglior rapporto valore/prezzo finisce per
    non comprare mai un top: ogni singolo acquisto costoso peggiora il rapporto,
    anche quando quel giocatore e' esattamente cio' che fa la differenza. Allora
    provo diverse ancore — i migliori per valore assoluto, da soli e a coppie — e
    tengo la rosa che rende di piu' su tutta la stagione.
    """
    presi = set(asta['acquisti'])
    liberi = sorted([p for p in d['giocatori']
                     if p['id'] not in presi and p['pv_proiettate'] >= 20],
                    key=lambda x: -x['valore'])
    big = [p['nome'] for p in liberi[:6]]

    tentativi = [()]
    tentativi += [(n,) for n in big]
    tentativi += [(big[i], big[j]) for i in range(min(4, len(big)))
                  for j in range(i + 1, min(5, len(big)))]

    migliore, punti = None, None
    for anc in tentativi:
        r = costruisci_rosa(d, asta, cfg, massimi, anc)
        if r['avanzo'] < 0:
            continue
        s = punteggio_rosa(r['rosa'], cfg)
        if punti is None or s > punti:
            migliore, punti = r, s
            migliore['ancore'] = anc
    if migliore is None:
        migliore = costruisci_rosa(d, asta, cfg, massimi)
        migliore['ancore'] = ()
        punti = punteggio_rosa(migliore['rosa'], cfg)
    migliore['punteggio'] = punti
    return migliore


# ====================================================== le tre proposte
MODULI = {'3-4-3': (3, 4, 3), '3-5-2': (3, 5, 2), '4-3-3': (4, 3, 3),
          '4-4-2': (4, 4, 2), '4-5-1': (4, 5, 1), '5-3-2': (5, 3, 2),
          '5-4-1': (5, 4, 1)}


def punti_mod_undici(undici, modificatore=True):
    """Il modificatore che darebbe questo undici.

    Regola della lega: bisogna schierare almeno quattro difensori, ma nella media
    entrano il portiere e i tre col voto migliore. Un modulo a tre dietro quindi
    non prende il modificatore per niente — ed e' una rinuncia che a fine stagione
    pesa parecchio.
    """
    if not modificatore or len(undici.get('D', [])) < 4 or not undici.get('P'):
        return 0.0
    return M.punti_modificatore(
        M.media_blocco(undici['P'][0]['mv_att'], [q['mv_att'] for q in undici['D']]))


def formazione(rosa, costo, gia_miei=(), modificatore=True):
    """Sceglie il modulo che valorizza di piu' i giocatori di questa rosa e
    dispone gli undici. Non ha senso imporre un 3-4-3 a chi ha cinque difensori
    buoni e due attaccanti: il modulo lo detta la rosa, non il contrario. E dove
    c'e' il modificatore, il conto include anche quello: tre dietro vuol dire
    rinunciarci."""
    per_ruolo = {ru: sorted([p for p in rosa if p['R'] == ru],
                            key=lambda x: -x['valore']) for ru in RUOLI}
    migliore, punti = None, None
    for nome, (nd, nc, na) in MODULI.items():
        if (len(per_ruolo['P']) < 1 or len(per_ruolo['D']) < nd
                or len(per_ruolo['C']) < nc or len(per_ruolo['A']) < na):
            continue
        undici = {'P': per_ruolo['P'][:1], 'D': per_ruolo['D'][:nd],
                  'C': per_ruolo['C'][:nc], 'A': per_ruolo['A'][:na]}
        s = sum(p['valore'] for g in undici.values() for p in g)
        s += punti_mod_undici(undici, modificatore) * GIORNATE
        if punti is None or s > punti:
            punti, migliore = s, (nome, undici)
    if migliore is None:
        return None
    nome, undici = migliore

    def etichetta(p):
        return 'tuo' if p['id'] in gia_miei else costo.get(p['id'], 1)

    schema = {ru: [(p, etichetta(p)) for p in undici[ru]] for ru in RUOLI}
    mod = punti_mod_undici(undici, modificatore)
    scelti = {p['id'] for g in undici.values() for p in g}
    panca = [(p, etichetta(p)) for p in
             sorted([q for q in rosa if q['id'] not in scelti],
                    key=lambda x: (RUOLI.index(x['R']), -x['valore']))]
    return {'modulo': nome, 'undici': schema, 'panchina': panca, 'modificatore': mod,
            'P': schema['P'], 'D': schema['D'], 'C': schema['C'], 'A': schema['A']}


def costruisci_a_quote(d, asta, cfg, massimi, quote, ancore=(), tetto=None):
    """Una rosa costruita dividendo il budget fra i reparti secondo una quota.

    L'altra costruzione — prendi sempre il miglior rapporto valore/prezzo finche'
    la rosa e' piena — e' quella giusta per rispondere "cosa comprerei". Ma non
    serve a proporre idee diverse: cambiando l'ordine cambia chi entra prima, e
    alla fine entrano comunque gli stessi undici, perche' il criterio non cambia.

    Qui invece decido prima quanti crediti vanno in ogni reparto, e ogni reparto
    compra i migliori che la sua borsa regge. Cosi' "corazzata dietro" compra
    davvero difensori da quaranta crediti e attaccanti da dieci — che e' la cosa
    che la rende un'idea invece di una sfumatura.
    """
    mia = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
           if v['squadra'] == asta['mia']}
    presi = set(asta['acquisti'])
    per_id = {p['id']: p for p in d['giocatori']}
    rosa = [per_id[pid] for pid in mia if pid in per_id]
    gia_miei = set(mia)
    budget = cfg['crediti'] - sum(mia.values())
    costo = {p['id']: max(1, massimi.get(p['id'], 1)) for p in d['giocatori']}

    for nome in ancore:
        q = next((x for x in d['giocatori'] if x['nome'] == nome
                  and x['id'] not in presi), None)
        if q and budget - costo[q['id']] >= 0:
            rosa.append(q)
            budget -= costo[q['id']]

    def quanti(ru):
        return sum(1 for q in rosa if q['R'] == ru)

    def mancano(ru):
        return max(0, cfg['slot'][ru] - quanti(ru))

    def disponibili(ru):
        return sorted([q for q in d['giocatori']
                       if q['R'] == ru and q['id'] not in presi and q not in rosa
                       and q['valore'] > 0
                       and (tetto is None or costo[q['id']] <= tetto)],
                      key=lambda x: -x['valore'] / costo[x['id']])

    # la borsa di ogni reparto
    somma = sum(quote.get(ru, 0) for ru in RUOLI) or 1.0
    borse = {ru: budget * quote.get(ru, 0) / somma for ru in RUOLI}

    # PRIMO GIRO: copertura. Ogni reparto si riempie coi giocatori che rendono di
    # piu' per credito speso, che e' il modo di non restare mai senza. Comprare
    # subito i piu' cari — il primo errore che ho fatto qui — svuota la borsa e
    # lascia il reparto pieno di gente che non gioca.
    for ru in RUOLI:
        for q in disponibili(ru):
            if not mancano(ru):
                break
            resta_qui = mancano(ru) - 1
            altrove = sum(mancano(r) for r in RUOLI if r != ru)
            tetto_ora = min(borse[ru] - resta_qui, budget - resta_qui - altrove)
            if costo[q['id']] > tetto_ora:
                continue
            rosa.append(q)
            budget -= costo[q['id']]
            borse[ru] -= costo[q['id']]

    # SECONDO GIRO: migliorie. Adesso che la rosa e' in piedi, ogni reparto spende
    # quello che gli e' avanzato per sostituire i suoi giocatori piu' deboli con
    # i migliori che puo' permettersi. E' qui che una quota alta in difesa diventa
    # davvero una corazzata: non comprando prima, ma comprando meglio.
    for _ in range(40):
        migliorata = False
        for ru in RUOLI:
            dentro = sorted([q for q in rosa if q['R'] == ru
                             and q['id'] not in gia_miei],
                            key=lambda x: x['valore'])
            if not dentro:
                continue
            debole = dentro[0]
            # un credito va tenuto da parte per ogni casella ancora vuota,
            # anche mentre miglioro: senza questa riserva la rosa finiva
            # completa e fuori budget di pochi crediti, e veniva scartata
            buchi = sum(mancano(r) for r in RUOLI)
            spendibile = borse[ru] + costo[debole['id']]
            meglio = None
            for q in sorted(disponibili(ru), key=lambda x: -x['valore']):
                if q['valore'] <= debole['valore']:
                    break
                if costo[q['id']] <= min(spendibile,
                                         budget + costo[debole['id']] - buchi):
                    meglio = q
                    break
            if meglio is None:
                continue
            rosa.remove(debole)
            rosa.append(meglio)
            differenza = costo[meglio['id']] - costo[debole['id']]
            budget -= differenza
            borse[ru] -= differenza
            migliorata = True
        if not migliorata:
            break

    # quello che avanza da un reparto torna in circolo per tutti gli altri
    for _ in range(20):
        avanzo_totale = budget
        candidati = []
        for ru in RUOLI:
            dentro = sorted([q for q in rosa if q['R'] == ru
                             and q['id'] not in gia_miei],
                            key=lambda x: x['valore'])
            if not dentro:
                continue
            debole = dentro[0]
            for q in sorted(disponibili(ru), key=lambda x: -x['valore']):
                if q['valore'] <= debole['valore']:
                    break
                extra = costo[q['id']] - costo[debole['id']]
                if extra <= avanzo_totale - sum(mancano(r) for r in RUOLI):
                    candidati.append((q['valore'] - debole['valore'], ru, debole, q))
                    break
        if not candidati:
            break
        _, ru, debole, meglio = max(candidati, key=lambda x: x[0])
        rosa.remove(debole)
        rosa.append(meglio)
        budget -= costo[meglio['id']] - costo[debole['id']]

    # gli ultimi buchi con quello che costa meno
    while len(rosa) < sum(cfg['slot'].values()):
        serve = [ru for ru in RUOLI if mancano(ru)]
        avanzi = [q for q in d['giocatori'] if q['R'] in serve
                  and q['id'] not in presi and q not in rosa]
        if not avanzi:
            break
        q = min(avanzi, key=lambda x: (costo[x['id']], -x['valore']))
        if costo[q['id']] > budget - (len(serve) - 1):
            break
        rosa.append(q)
        budget -= costo[q['id']]

    return {'rosa': rosa, 'gia_miei': gia_miei, 'avanzo': budget, 'costo': costo,
            'blocco': blocco_scelto(rosa),
            'spesa': {ru: sum(costo[q['id']] for q in rosa
                              if q['R'] == ru and q['id'] not in gia_miei)
                      for ru in RUOLI}}


STRATEGIE = [
    {
        'chiave': 'ottima',
        'quote': None,      # nessun vincolo: compra dove rende di piu'
        'titolo': 'La migliore che riesco a fare',
        'idea': ('Nessuna idea preconcetta: a ogni acquisto prendo il giocatore '
                 'che rende di più per ogni credito speso, finché la rosa è '
                 'piena. Non è la più bella da raccontare, ma sui numeri è '
                 'quella che fa più punti in una stagione — e le altre cinque '
                 'qui sotto dichiarano quanto costa preferirle.'),
        'rischio': ('Viene fuori una rosa senza un\'identità precisa: nessun '
                    'reparto domina, e se l\'asta prende una piega strana non '
                    'hai un piano di riserva già in testa.'),
    },
    {
        'chiave': 'difesa',
        'quote': {'P': .13, 'D': .40, 'C': .27, 'A': .20},
        'titolo': 'Corazzata dietro',
        'idea': ('Il grosso del budget su portiere e difesa. Nella tua lega il '
                 'modificatore premia le medie voto, e il difensore medio è molto '
                 'più scarso dell\'attaccante medio: un top in difesa ti stacca '
                 'dal sostituto più di quanto faccia un top là davanti.'),
        'rischio': ('Se il modificatore rende meno del previsto — una difesa che '
                    'prende gol manda in fumo tutto il blocco — resti con un '
                    'attacco che non buca.'),
    },
    {
        'chiave': 'attacco',
        'quote': {'P': .07, 'D': .18, 'C': .24, 'A': .51},
        'titolo': 'Peso in attacco',
        'idea': ('Crediti concentrati davanti. Costa di più a parità di resa, ma '
                 'un centravanti da venti gol non lo sostituisci con niente e ti '
                 'tiene in corsa anche nelle giornate in cui non gira.'),
        'rischio': ('Dietro ti arrangi, e col modificatore acceso è un handicap '
                    'che paghi tutte le settimane, non solo quando l\'attaccante '
                    'non segna.'),
    },
    {
        'chiave': 'centrocampo',
        'quote': {'P': .07, 'D': .21, 'C': .40, 'A': .32},
        'titolo': 'Centrocampo che fa i bonus',
        'idea': ('Il grosso in mezzo, dove trequartisti e ali prendono bonus da '
                 'attaccante al prezzo di un centrocampista. È l\'asimmetria più '
                 'sfruttabile del Classic: lo stesso gol vale uguale, ma lì la '
                 'concorrenza per comprarselo è minore.'),
        'rischio': ('Dipendi da giocatori che il bonus lo fanno a intermittenza: '
                    'quando le ali non pungono, l\'undici non ha un riferimento.'),
    },
    {
        'chiave': 'due_top',
        'quote': {'P': .07, 'D': .22, 'C': .28, 'A': .43},
        'titolo': 'Due fuoriclasse e via',
        'due_ancore': True,
        'idea': ('Due nomi da prima fascia presi senza guardare il prezzo, e il '
                 'resto costruito con quello che avanza. È la scommessa che due '
                 'giocatori sopra tutti valgano più di undici buoni: in una lega '
                 'da dieci, chi ha i due migliori del campionato parte avanti.'),
        'rischio': ('Se uno dei due si fa male a ottobre, hai speso metà budget '
                    'per guardarlo dalla panchina. Sui numeri rende meno delle '
                    'altre, perché il resto della rosa lo paghi in scarti: è una '
                    'scommessa sul fatto che i due migliori facciano la '
                    'differenza da soli.'),
    },
    {
        'chiave': 'nessun_top',
        'quote': {'P': .09, 'D': .26, 'C': .30, 'A': .35},
        'titolo': 'Nessun big, tutti titolari',
        'tetto': 45,
        'idea': ('Nessun giocatore sopra i quarantacinque crediti: al loro posto '
                 'undici titolari veri, di quelli che giocano sempre e fanno il '
                 'loro compitino. Il budget si spalma e non c\'è nessun buco da '
                 'coprire con gli scarti a un credito.'),
        'rischio': ('Nessuno che ti vinca la giornata da solo. Contro una rosa '
                    'con due fuoriclasse in forma, le settimane storte le perdi.'),
    },
]


def carattere(r, cfg):
    """Due parole che dicono che tipo di squadra e'."""
    sp = r['spesa']
    tot = sum(sp.values()) or 1
    quote = {ru: sp[ru] / float(tot) for ru in RUOLI}
    b = r.get('blocco')
    if quote['D'] + quote['P'] >= 0.45:
        titolo = 'Corazzata dietro'
        idea = ('Quasi metà del budget su portiere e difesa. Nella tua lega il '
                'modificatore premia le medie voto, e il difensore medio è molto '
                'più scarso dell\'attaccante medio: è lì che un top vale di più.')
    elif quote['A'] >= 0.42:
        titolo = 'Peso in attacco'
        idea = ('I crediti concentrati davanti. Costa di più a parità di resa, ma '
                'un centravanti che segna venti gol non lo sostituisci con niente '
                'e ti tiene in corsa anche nelle giornate storte.')
    elif quote['C'] >= 0.33:
        titolo = 'Centrocampo che fa i bonus'
        idea = ('Il grosso a centrocampo, dove trequartisti e ali prendono bonus '
                'da attaccante a prezzo di centrocampista: è l\'asimmetria più '
                'sfruttabile del ruolo Classic.')
    else:
        titolo = 'Equilibrata'
        idea = ('Nessun reparto sacrificato: un riferimento vero ovunque e nessun '
                'buco. È la rosa che rischia meno se l\'asta prende una piega strana.')
    if b:
        idea += ' Blocco difensivo da %.2f di media voto.' % b['mv']
    return titolo, idea


def sei_proposte(d, asta, cfg, massimi, quante=6):
    """Sei rose costruite ognuna con un'idea diversa in testa.

    La versione di prima generava una ventina di squadre ancorate a big diversi e
    ne teneva tre poco sovrapposte. Funzionava per tre, ma per sei sarebbe finita
    a proporre sei volte la stessa idea con due nomi cambiati: la varieta' dei
    nomi non e' varieta' di strategia.

    Adesso ogni proposta parte da una convinzione dichiarata — il modificatore
    vale piu' dell'attacco, due fuoriclasse valgono piu' di undici buoni, e cosi'
    via — e la rosa viene costruita per servire quella convinzione. Poi le
    confronto tutte sullo stesso metro: quanti fantapunti fanno in una stagione.
    """
    presi = set(asta['acquisti'])
    liberi = sorted([p for p in d['giocatori']
                     if p['id'] not in presi and p['pv_proiettate'] >= 20],
                    key=lambda x: -x['valore'])
    big = [p['nome'] for p in liberi[:6]]

    fatte = []
    for st_ in STRATEGIE:
        ancore = tuple(big[:2]) if st_.get('due_ancore') else ()
        if st_['quote'] is None:
            r = costruisci_rosa(d, asta, cfg, massimi, ancore,
                                tetto_singolo=st_.get('tetto'))
        else:
            r = costruisci_a_quote(d, asta, cfg, massimi, st_['quote'], ancore,
                                   tetto=st_.get('tetto'))
        if r['avanzo'] < 0 or len(r['rosa']) < sum(cfg['slot'].values()):
            continue
        r['chiave'] = st_['chiave']
        r['titolo'] = st_['titolo']
        r['idea'] = st_['idea']
        r['rischio'] = st_['rischio']
        r['ancore'] = ancore
        r['punteggio'] = punteggio_rosa(r['rosa'], cfg)
        fatte.append(r)

    # due strategie diverse possono finire sulla stessa rosa, se il mercato
    # rimasto non concede alternative: in quel caso la seconda non aggiunge niente
    scelte = []
    for r in sorted(fatte, key=lambda x: -x['punteggio']):
        ids = {p['id'] for p in r['rosa']}
        if any(len(ids & {q['id'] for q in s2['rosa']}) > 0.85 * len(ids)
               for s2 in scelte):
            continue
        scelte.append(r)

    # se ne restano poche, completo col vecchio metodo: rose ancorate a un big
    for nome in big:
        if len(scelte) >= quante:
            break
        r = costruisci_rosa(d, asta, cfg, massimi, (nome,))
        if r['avanzo'] < 0 or len(r['rosa']) < sum(cfg['slot'].values()):
            continue
        ids = {p['id'] for p in r['rosa']}
        if any(len(ids & {q['id'] for q in s2['rosa']}) > 0.85 * len(ids)
               for s2 in scelte):
            continue
        r['chiave'] = 'ancora'
        r['punteggio'] = punteggio_rosa(r['rosa'], cfg)
        r['titolo'], r['idea'] = carattere(r, cfg)
        r['titolo'] = '%s · su %s' % (r['titolo'], nome)
        r['rischio'] = ('Costruita attorno a %s: se lui salta, la rosa perde il '
                        'suo perno.' % nome)
        r['ancore'] = (nome,)
        scelte.append(r)

    # la rosa senza vincoli sta sempre in testa, anche se per un soffio non e'
    # la piu' alta: e' il metro con cui si leggono le altre cinque
    scelte = sorted(scelte, key=lambda x: (x['chiave'] != 'ottima',
                                           -x['punteggio']))[:quante]
    migliore = max([r['punteggio'] for r in scelte] or [0])
    for n, r in enumerate(scelte):
        r['formazione'] = formazione(r['rosa'], r['costo'], r['gia_miei'],
                                     cfg['modificatore_difesa'])
        r['posto'] = n + 1
        r['scarto_punti'] = r['punteggio'] - migliore
        r['confronto'] = confronto_proposta(r, scelte, cfg)
    return scelte


def confronto_proposta(r, tutte, cfg):
    """La riga che dice in cosa questa rosa e' diversa dalle altre cinque.

    Un elenco di sei squadre senza un metro di paragone e' sei volte lo stesso
    problema. Qui il confronto e' sui numeri: quanto rende rispetto alla
    migliore, dove spende piu' delle altre, quanti titolari veri ha.
    """
    pezzi = []
    if abs(r['scarto_punti']) < 1:
        pezzi.append('<b>È quella che rende di più</b> delle sei')
    else:
        pezzi.append('Costa <b>%.0f punti</b> in una stagione rispetto alla '
                     'migliore' % abs(r['scarto_punti']))

    # dove spende piu' delle altre, in punti percentuali
    tot = sum(r['spesa'].values()) or 1
    medie = {}
    for ru in RUOLI:
        valori = [s2['spesa'][ru] / float(sum(s2['spesa'].values()) or 1)
                  for s2 in tutte]
        medie[ru] = sum(valori) / len(valori) if valori else 0
    scarti = {ru: r['spesa'][ru] / float(tot) - medie[ru] for ru in RUOLI}
    su = max(scarti, key=lambda x: scarti[x])
    if scarti[su] >= 0.05:
        articolo = 'sugli' if su == 'A' else 'sui'
        pezzi.append('mette il <b>%+.0f%%</b> di budget in più %s %s'
                     % (scarti[su] * 100, articolo, RUOLO_NOME[su].lower()))

    sempre = sum(1 for p in r['rosa'] if p['pv_proiettate'] >= 30)
    pezzi.append('<b>%d</b> giocatori da trenta presenze o più' % sempre)

    if r.get('blocco') and cfg['modificatore_difesa']:
        pezzi.append('blocco da <b>%.2f</b>' % r['blocco']['mv'])
    return ' · '.join(pezzi)


def tre_proposte(d, asta, cfg, massimi):
    """Le prime tre delle sei, per chi vuole solo un'occhiata veloce."""
    return sei_proposte(d, asta, cfg, massimi, quante=3)


def scelta_undici(schierabili, nd, nc, na, mod_attivo):
    """L'undici migliore per un modulo, modificatore compreso.

    Ordinare i difensori per fantamedia attesa e prendere i primi quattro e'
    sbagliato quando c'e' il modificatore: li' conta il voto, non il fantavoto,
    e conta solo la media dei tre piu' alti. Un difensore da 6.3 di media voto
    ma senza bonus puo' valere piu' di uno che ogni tanto segna e prende 5.5.
    Le combinazioni sono poche — al massimo qualche centinaio — quindi le provo
    tutte e tengo quella che massimizza fantapunti totali piu' modificatore.
    """
    per_ruolo = {ru: sorted([v for v in schierabili if v['p']['R'] == ru],
                            key=lambda v: -v['atteso']) for ru in 'PDCA'}
    centro, attacco = per_ruolo['C'][:nc], per_ruolo['A'][:na]
    portieri, difensori = per_ruolo['P'][:3], per_ruolo['D'][:10]
    if not portieri or len(difensori) < nd or len(centro) < nc or len(attacco) < na:
        return None
    resto = sum(v['atteso'] for v in centro + attacco)
    migliore = None
    for gk in portieri:
        for combo in itertools.combinations(difensori, nd):
            media, punti = None, 0.0
            if mod_attivo and nd >= M.DIFENSORI_NEL_BLOCCO + 1:
                media = M.media_blocco(gk['mv'], [v['mv'] for v in combo])
                punti = M.punti_modificatore(media) if media is not None else 0.0
            tot = gk['atteso'] + sum(v['atteso'] for v in combo) + resto + punti
            if migliore is None or tot > migliore['totale']:
                migliore = {'undici': [gk] + list(combo) + centro + attacco,
                            'media': media, 'punti': punti, 'totale': tot}
    return migliore
