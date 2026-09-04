# -*- coding: utf-8 -*-
"""Le domande che ti vengono in mente durante l'asta, e le risposte coi numeri di adesso.

Una premessa onesta, perche' e' l'unica cosa che conta per fidarsi di questa
pagina: **qui dentro non c'e' nessuna intelligenza artificiale**. Non c'e' un
modello linguistico, non c'e' una connessione a un servizio che pensa. C'e' un
interprete che riconosce le domande che si fanno davvero a un'asta e risponde
usando il motore di calcolo del programma, con lo stato del mercato aggiornato al
secondo in cui premi Invio.

La differenza si sente in due modi opposti. In male: se scrivi una domanda che non
ho previsto, non improvviso — te lo dico e ti mostro cosa so fare. In bene: quando
rispondo, i numeri sono veri. Non sono un riassunto plausibile di quello che di
solito si dice sui difensori, sono il prezzo ricalcolato sui rilanci di stasera, i
tuoi crediti residui, gli slot che ti restano, e fin dove puo' spingersi la squadra
seduta di fronte a te.

Le domande che capisco:

- **un nome** — "Dimarco", "quanto vale Lautaro" -> il massimo che pagherei oggi,
  perche', e chi te lo puo' portare via;
- **un nome e una cifra** — "posso arrivare a 90 su Lautaro?", "Kean a 45" -> se
  quella cifra sta in piedi, e soprattutto *cosa ti resta dopo*;
- **due nomi** — "Dimarco o Bastoni?" -> il confronto, con la ragione della scelta;
- **come sto** — crediti, slot, dove sei scoperto, quanto puoi ancora permetterti;
- **cosa mi manca** — i buchi in rosa e chi li riempie a ogni fascia di prezzo;
- **un ruolo e un budget** — "difensore da 20", "attaccanti sotto 30";
- **chi resta** — le scorte di un ruolo, per capire se conviene aspettare;
- **gli avversari** — chi ha ancora crediti, fin dove puo' rilanciare, cosa gli manca;
- **occasioni** — chi oggi vale piu' di quanto costera'.
"""
import difflib
import re

import fanta_modello as M
import strategia as S
import tema as T

RUOLI = ['P', 'D', 'C', 'A']
RUOLO_NOME = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti',
              'A': 'Attaccanti'}
RUOLO_SING = {'P': 'portiere', 'D': 'difensore', 'C': 'centrocampista',
              'A': 'attaccante'}

# le parole della domanda che non sono mai un cognome: senza questa lista
# "come sto messo" trova il centrocampista Como e la conversazione va a rotoli
FERMATE = {
    'come', 'sto', 'stai', 'messo', 'quanto', 'vale', 'valgo', 'prezzo', 'prezzi',
    'posso', 'possiamo', 'arrivare', 'spingere', 'spingermi', 'offrire', 'offro',
    'pago', 'pagare', 'pagarlo', 'compro', 'comprare', 'prendo', 'prendere',
    'conviene', 'meglio', 'peggio', 'oppure', 'contro', 'che', 'cosa', 'chi',
    'quale', 'quali', 'quanti', 'quante', 'mi', 'manca', 'mancano', 'resta',
    'restano', 'rimane', 'rimangono', 'ancora', 'adesso', 'ora', 'oggi', 'per',
    'con', 'senza', 'del', 'della', 'dei', 'delle', 'dal', 'dalla', 'sul',
    'sulla', 'nel', 'nella', 'una', 'uno', 'gli', 'lui', 'suo', 'mio', 'mia',
    'sono', 'siamo', 'ho', 'hai', 'crediti', 'credito', 'budget', 'soldi',
    'squadra', 'squadre', 'rosa', 'slot', 'fascia', 'ruolo', 'reparto',
    'situazione', 'aiuto', 'grazie', 'okay', 'bene', 'male', 'devo', 'deve',
    'fare', 'faccio', 'dire', 'dimmi', 'dammi', 'fammi', 'vedere', 'sapere',
    'occasioni', 'affari', 'affare', 'scorte', 'avversari', 'avversario',
    'rilanci', 'rilanciare', 'rilancio', 'top', 'titolare', 'titolari',
    'portiere', 'portieri', 'difensore', 'difensori', 'centrocampista',
    'centrocampisti', 'attaccante', 'attaccanti', 'sotto', 'sopra', 'entro',
    'massimo', 'minimo', 'circa', 'euro', 'punti', 'buono', 'buoni', 'forte',
    'forti', 'meno', 'piu', 'anche', 'solo', 'gia', 'poi', 'ma', 'se', 'non',
}

ESEMPI = [
    'Quanto vale Dimarco?',
    'Posso arrivare a 90 su Lautaro Martinez?',
    'Dimarco o Bastoni?',
    'Come sto messo?',
    'Cosa mi manca?',
    'Difensore da 20 crediti',
    'Chi resta in attacco?',
    'Chi può rilanciarmi?',
    'Occasioni adesso',
    'Come sta andando l\'asta?',
]


# ------------------------------------------------------------ riconoscere
def parole(testo):
    return [w for w in re.split(r'[^0-9a-zà-ÿ]+', (testo or '').lower()) if w]


def numeri(testo):
    """I numeri scritti nella domanda, esclusi quelli attaccati a un nome."""
    return [int(x) for x in re.findall(r'\b(\d{1,3})\b', testo or '')]


def ruolo_citato(testo):
    t = ' %s ' % (testo or '').lower()
    for ru, chiavi in (('P', ('portier', 'porta')),
                       ('D', ('difensor', 'difesa', 'dietro')),
                       ('C', ('centrocampist', 'centrocampo', 'mediana')),
                       ('A', ('attaccant', 'attacco', 'punta', 'davanti'))):
        if any(k in t for k in chiavi):
            return ru
    return None


def alias(p):
    """Tutti i modi in cui uno puo' scrivere il nome di questo giocatore.

    Nel listone Lautaro Martinez si chiama "Martinez L." e Nico Paz si chiama
    "Paz N.": chi li cerca per nome proprio non li troverebbe mai. Quindi metto
    insieme il nome del listone, il cognome senza l'iniziale puntata, i pezzi
    dello slug e — quando c'e' — il nome per esteso preso dalla scheda.
    """
    fuori = set()
    for pezzo in (p.get('nome'), p.get('nome_completo')):
        if not pezzo:
            continue
        fuori.add(M.chiave(pezzo))
        for parola in re.split(r'[^0-9A-Za-zÀ-ÿ]+', pezzo):
            # l'iniziale puntata del nome proprio non e' un alias: "L." di
            # "Martinez L." troverebbe mezzo campionato
            if len(parola) >= 3:
                fuori.add(M.chiave(parola))
    for parte in (p.get('slug') or '').split('-'):
        if len(parte) >= 3:
            fuori.add(M.chiave(parte))
    return {a for a in fuori if len(a) >= 3}


def citazioni(testo, giocatori):
    """Chi e' nominato, e con quale parola.

    Sapere QUALE parola ha trovato chi e' la differenza fra un confronto e un
    equivoco: "Dimarco o Bastoni" sono due parole diverse e vanno confrontati,
    "Thuram" e' una parola sola che ne trova due — Marcus e Khephren — e li' non
    c'e' niente da confrontare, c'e' da capire di quale dei due stiamo parlando.
    """
    tutte = [M.chiave(w) for w in parole(testo)]
    ps = [w for w in tutte if len(w) >= 3 and w not in FERMATE]
    if not ps:
        return []
    # le coppie si fanno con TUTTE le parole, iniziali puntate comprese: "Thuram
    # K." e' Khephren, e la K da sola verrebbe buttata via come rumore
    coppie = [tutte[i] + tutte[i + 1] for i in range(len(tutte) - 1)
              if tutte[i] and tutte[i + 1] and (tutte[i] in ps or tutte[i + 1] in ps)]
    cercate = list(dict.fromkeys(ps + coppie))

    per_parola = {}
    for p in giocatori:
        suoi = alias(p)
        for w in cercate:
            if w not in suoi:
                continue
            # a parita' di parola vince chi si chiama proprio cosi': scrivendo
            # "thuram" intendi quello che nel listone e' "Thuram", non "Thuram K."
            punti = (2 if M.chiave(p['nome']) == w else 0,
                     len(w), p.get('valore') or 0)
            if w not in per_parola or punti > per_parola[w][0]:
                per_parola[w] = (punti, p)

    # se una parola e' contenuta in una piu' lunga gia' trovata, la scarto:
    # "carlos" e "carlosaugusto" sono la stessa citazione
    scelte, visti = [], set()
    for w in sorted(per_parola, key=len, reverse=True):
        p = per_parola[w][1]
        if p['id'] in visti or any(w in altra for altra in visti_parole(scelte)):
            continue
        scelte.append((w, p))
        visti.add(p['id'])
    return scelte


def visti_parole(scelte):
    return [w for w, _ in scelte]


def giocatori_citati(testo, giocatori, quanti=2):
    """I calciatori nominati nella domanda, i piu' probabili per primi.

    Il confronto e' fra PAROLE INTERE, mai fra pezzi di frase: cercando i cognomi
    come sottostringhe, "quanto vale" conteneva Antov ("qu-ANTO-V-ale") e "chi
    resta in attacco" conteneva Atta. In Serie A ci sono decine di cognomi da tre
    o quattro lettere — Dia, Coco, Atta, Gila — e nessuno di loro sopravvive a un
    confronto per sottostringa.
    """
    scelte = citazioni(testo, giocatori)
    if scelte:
        scelte.sort(key=lambda x: -len(x[0]))
        return [p for _, p in scelte[:quanti]]

    # nessun nome esatto: perdono un refuso, ma solo su parole lunghe
    ps = [M.chiave(w) for w in parole(testo)]
    ps = [w for w in ps if len(w) >= 5 and w not in FERMATE]
    indice = {}
    for p in giocatori:
        for a in alias(p):
            if len(a) >= 5:
                indice.setdefault(a, p)
    fuori, visti = [], set()
    for w in ps:
        vicini = difflib.get_close_matches(w, list(indice), n=1, cutoff=0.8)
        if vicini:
            p = indice[vicini[0]]
            if p['id'] not in visti:
                fuori.append(p)
                visti.add(p['id'])
    return fuori[:quanti]


def omonimi(testo, giocatori):
    """Quando la parola che hai scritto e' di piu' di un giocatore.

    In Serie A ci sono due Thuram, due Martinez e due Lautaro: se scrivi solo il
    cognome mentre stai per rilanciare, la cosa peggiore che posso fare e'
    scegliere io e darti il prezzo dell'altro.

    Due casi non sono ambigui e vanno lasciati passare. Se uno dei due si chiama
    ESATTAMENTE come hai scritto — "Thuram" e' Marcus, Khephren nel listone e'
    "Thuram K." — allora intendevi quello. E se hai scritto due parole che
    insieme fanno un nome solo — "Lautaro Martinez" — hai gia' sciolto tu il
    dubbio.
    """
    scelte = citazioni(testo, giocatori)
    if len(scelte) != 1:
        return []
    parola, _ = scelte[0]
    stessi = [p for p in giocatori if parola in alias(p)]
    if len(stessi) < 2:
        return []
    if any(M.chiave(p['nome']) == parola for p in stessi):
        return []
    return sorted(stessi, key=lambda p: -(p.get('valore') or 0))


def squadra_citata(testo, asta):
    """Quale delle squadre della lega e' nominata nella domanda.

    Il numero si cerca per primo e sul testo grezzo: la normalizzazione butta via
    le cifre, quindi "Squadra 2" e "Squadra 3" diventerebbero la stessa parola e
    chiederesti di una e ti risponderei dell'altra.
    """
    grezzo = (testo or '').lower()
    for i, nome in enumerate(asta['squadre']):
        n = nome.lower().strip()
        if len(n) >= 4 and re.search(r'(?<![0-9a-zà-ÿ])%s(?![0-9a-zà-ÿ])'
                                     % re.escape(n), grezzo):
            return i
    m = re.search(r'squadra\s*(\d{1,2})', grezzo)
    if m:
        i = int(m.group(1)) - 1
        if 0 <= i < len(asta['squadre']):
            return i
    return None


# -------------------------------------------------------------- mattoncini
def _riga_prezzo(p, ctx, prezzo=None):
    massimo = prezzo if prezzo is not None else ctx['massimi'].get(p['id'], 1)
    return massimo


def _chi_e(p):
    return '<b>%s</b> (%s, %s)' % (T.e(p['nome']), T.e(p['squadra']),
                                   RUOLO_SING[p['R']])


def _tabella_giocatori(elenco, ctx, colonna='Max da pagare'):
    righe = []
    for p in elenco:
        righe.append([
            T.pillola(p['R'], T.RUOLO_COLORE[p['R']]),
            T.e(p['nome']), T.e(p['squadra']),
            '%d' % ctx['massimi'].get(p['id'], 1),
            '%.2f' % p['fm_att'], '%.0f' % p['pv_proiettate'],
            T.e(' · '.join(p['note'][:1])),
        ])
    return T.tabella([('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
                      (colonna, 'big'), ('FM att.', 'num'), ('PV att.', 'num'),
                      ('Nota', 'nota')], righe)


def _rivali_su(p, ctx, quanti=4):
    """Chi puo' portartelo via, e fin dove puo' spingersi.

    Non basta chi ha piu' crediti: conta chi ha ancora una casella libera in quel
    ruolo. Una squadra ricchissima che ha gia' tre portieri non ti rilancia su un
    portiere."""
    asta, cfg = ctx['asta'], ctx['cfg']
    per_id = ctx['per_id']
    out = []
    for i, nome in enumerate(asta['squadre']):
        if i == asta['mia']:
            continue
        acq = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
               if v['squadra'] == i}
        pieni = sum(1 for pid in acq if per_id.get(pid, {}).get('R') == p['R'])
        if pieni >= cfg['slot'][p['R']]:
            continue
        out.append({'nome': nome, 'tetto': ctx['offerta_massima'](i),
                    'liberi': cfg['slot'][p['R']] - pieni})
    out.sort(key=lambda x: -x['tetto'])
    return out[:quanti]


# --------------------------------------------------------------- risposte
def _titolo(p, coda=''):
    """Il nome come lo chiamerebbe uno allo stadio, non come sta nel listone."""
    nome = p['nome']
    if p.get('nome_completo') and M.chiave(p['nome_completo']) != M.chiave(nome):
        nome = p['nome_completo']
    return '%s (%s)%s' % (nome, p['squadra'], coda)


def risposta_venduto(p, preso, ctx):
    """Un giocatore gia' battuto: quanto e' stato pagato rispetto a quanto valeva.

    Il prezzo massimo qui non c'entra piu' niente — il motore lo azzera appena uno
    esce dal mercato — e mostrarlo direbbe "vale 1 credito", che e' falso e
    confonde. Quello che serve sapere e' se chi l'ha preso ha fatto un affare."""
    chi = ctx['asta']['squadre'][preso['squadra']]
    mio = preso['squadra'] == ctx['asta']['mia']
    valeva = p['prezzo']
    scarto = preso['prezzo'] - valeva
    box = [('Pagato', preso['prezzo'], 'da %s' % chi, 'ciano' if mio else ''),
           ('Valeva', valeva, 'il mio prezzo consigliato', ''),
           ('Differenza', ('+%d' % scarto) if scarto > 0 else '%d' % scarto,
            'strapagato' if scarto > 0
            else 'preso sotto prezzo' if scarto < 0 else 'prezzo esatto',
            'rosso' if scarto > 0 else 'verde' if scarto < 0 else ''),
           ('FM attesa', '%.2f' % p['fm_att'], 'fantamedia prevista', '')]
    giudizio = ('<b>È tuo.</b> ' if mio
                else '<b>Via, l’ha preso %s.</b> ' % T.e(chi))
    if scarto > max(4, valeva * 0.2):
        giudizio += ('Pagato %d piu’ di quanto valesse: %d crediti in meno per '
                     'tutto il resto della sua asta.' % (scarto, scarto))
    elif scarto < -max(3, valeva * 0.15):
        giudizio += 'Preso %d sotto il suo valore: buon colpo.' % -scarto
    else:
        giudizio += 'Prezzo giusto, ne’ affare ne’ sciocchezza.'
    return {'titolo': _titolo(p, ' — già venduto'),
            'corpo': T.riquadri(box) + T.nota(giudizio, 'ok' if mio else '')}


def risposta_giocatore(p, ctx, offerta=None):
    """Un nome, e tutto quello che serve per decidere in dieci secondi."""
    preso = ctx['asta']['acquisti'].get(p['id'])
    if preso:
        return risposta_venduto(p, preso, ctx)
    massimo = ctx['massimi'].get(p['id'], 1)
    mercato = p['prezzo_mercato']
    sit = ctx['sit']

    pezzi = []
    att = (ctx.get('attesi') or {}).get(p['id']) or {}
    box = [('Il mio massimo', massimo, 'crediti, oggi', 'ciano')]
    if att.get('quanti'):
        box.append(('Finirà a', att['atteso'], 'prezzo di aggiudicazione', ''))
        box.append(('Per batterli', att['per_prenderlo'], 'quanto devi mettere tu',
                    'rosso' if att['per_prenderlo'] > massimo else 'verde'))
    else:
        box.append(('Mercato', '%d' % mercato, 'quanto costerà in giro', ''))
    box.append(('FM attesa', '%.2f' % p['fm_att'], 'fantamedia prevista', ''))
    box.append(('Partite attese', '%.0f' % p['pv_proiettate'], 'su 38', ''))
    if offerta is not None:
        sfora = offerta - massimo
        box.insert(0, ('La tua offerta', offerta,
                       'sopra di %d' % sfora if sfora > 0
                       else 'dentro di %d' % -sfora,
                       'rosso' if sfora > 0 else 'verde'))
    pezzi.append(T.riquadri(box))

    pezzi.append(pronostico(p, att, massimo, ctx))

    # il giudizio, con le sue ragioni
    ragioni = list(p.get('motivi_pro') or [])[:3]
    contro = list(p.get('motivi_contro') or [])[:2]
    if ragioni or contro:
        righe = ''.join('<li class="pro">%s</li>' % T.e(r) for r in ragioni)
        righe += ''.join('<li class="contro">%s</li>' % T.e(r) for r in contro)
        pezzi.append('<ul class="motivi">%s</ul>' % righe)

    # il verdetto sull'offerta: la parte che conta davvero
    if offerta is not None:
        pezzi.append(_verdetto_offerta(p, offerta, massimo, ctx, sit))

    rivali = _rivali_su(p, ctx)
    if rivali:
        elenco = ' · '.join('<b>%s</b> fino a %d' % (T.e(r['nome']), r['tetto'])
                            for r in rivali)
        pezzi.append(T.nota('<b>Chi te lo può portare via:</b> %s.<br>'
                            '<span style="font-size:.82rem">Sono le squadre che '
                            'hanno ancora una casella libera da %s. Il numero è fin '
                            'dove possono spingersi tenendo un credito per ogni '
                            'slot che gli resta.</span>'
                            % (elenco, RUOLO_SING[p['R']])))
    return {'titolo': _titolo(p), 'corpo': ''.join(pezzi)}


def pronostico(p, att, massimo, ctx=None):
    """Dove finira' quel giocatore, e cosa vuol dire per te.

    Il massimo da pagare dice quando smettere di rilanciare. Questo dice se devi
    rilanciare adesso: se per batterli bastano quaranta e il tuo massimo e'
    novanta, quei cinquanta crediti sono ancora tuoi.

    Una cautela che serve piu' di quanto sembri: a inizio asta tutte le squadre
    hanno lo stesso portafoglio, quindi valutano tutte allo stesso modo e la
    soglia per batterle esce sempre un credito sopra il valore. Li' dire
    "lascialo andare" sarebbe una sciocchezza — vuol dire solo che quel giocatore
    costa quanto vale.
    """
    if not att:
        return ''
    if not att.get('quanti'):
        return T.nota('<b>Non lo vuole nessuno.</b> Nessun avversario ha ancora una '
                      'casella libera in quel ruolo: te lo prendi a un credito.',
                      'ok')
    soglia = att['per_prenderlo']
    if att.get('fuori_portata'):
        return T.nota('<b>Fuori portata.</b> Chi te lo contende può salire più in '
                      'alto di quanto puoi permetterti tenendo un credito per ogni '
                      'casella che ti resta da riempire.', 'allarme')

    chi = (('favorita <b>%s</b>' % T.e(att['chi'])) if att.get('chi')
           else '<b>%d squadre appaiate</b>' % att.get('pari', 0))
    scarto = soglia - massimo
    tolleranza = max(2, massimo * 0.04)

    if abs(scarto) <= tolleranza:
        testo = ('<b>Costa esattamente quello che vale.</b> Per batterli servono '
                 '<b>%d</b> contro un massimo di %d: se lo vuoi, il prezzo è '
                 'quello.' % (soglia, massimo))
        variante = ''
    elif scarto > 0:
        testo = ('<b>Andrà oltre quello che vale.</b> Per prenderlo servono '
                 '<b>%d</b>, %d più del mio massimo: lascialo andare.'
                 % (soglia, scarto))
        variante = 'allarme'
    else:
        testo = ('<b>Non serve arrivare a %d.</b> Per batterli bastano <b>%d</b>: '
                 'sono %d crediti che restano tuoi.' % (massimo, soglia, -scarto))
        variante = 'ok'

    coda = ''
    if att.get('pari', 0) >= 6:
        coda = ('<br><span style="font-size:.82rem">Sono appaiate perché l\'asta è '
                'appena cominciata e hanno tutte lo stesso portafoglio: qui il '
                'prezzo lo fa il valore, non la fame di crediti. Più avanti questa '
                'riga diventerà molto più utile.</span>')
    elif att.get('rivali'):
        coda = ('<br><span style="font-size:.82rem">Te lo contendono: %s.</span>'
                % ' · '.join('%s fino a %d' % (T.e(n), v)
                             for n, _, v in att['rivali'][:3]))
    return T.nota('%s Lo vogliono <b>%d squadre</b>, %s.%s'
                  % (testo, att['quanti'], chi, coda), variante)


def _verdetto_offerta(p, offerta, massimo, ctx, sit):
    """Non "sì" o "no", ma: e dopo che l'hai pagato, con cosa finisci la rosa?"""
    residuo = sit['residuo'] - offerta
    altri_slot = sit['slot_mancanti'] - 1
    if offerta > sit['residuo']:
        return T.nota('<b>Non puoi.</b> Hai %d crediti e ne servirebbero %d.'
                      % (sit['residuo'], offerta), 'allarme')
    if altri_slot > 0 and residuo < altri_slot:
        return T.nota('<b>Non puoi arrivarci.</b> Dopo averlo pagato %d ti '
                      'resterebbero %d crediti per %d caselle: te ne serve almeno '
                      'uno a testa. Il tuo tetto vero su questo giocatore è '
                      '<b>%d</b>.' % (offerta, residuo, altri_slot,
                                      sit['residuo'] - altri_slot), 'allarme')

    per_slot = (residuo / float(altri_slot)) if altri_slot > 0 else 0
    sopra = offerta - massimo
    att = (ctx.get('attesi') or {}).get(p['id']) or {}
    soglia = att.get('per_prenderlo')
    if sopra <= 0:
        testa = ('<b>Sì, e sei sotto il mio massimo di %d.</b>' % massimo)
        variante = 'ok'
    elif sopra <= max(3, massimo * 0.12):
        testa = ('<b>Sì, ma sei sopra di %d rispetto al mio massimo.</b> È uno '
                 'scarto piccolo: se lo vuoi davvero, si può.' % sopra)
        variante = ''
    else:
        testa = ('<b>Sopra di %d rispetto al mio massimo di %d.</b> A quel prezzo '
                 'lo stai pagando per motivi che non sono i numeri.'
                 % (sopra, massimo))
        variante = 'allarme'

    coda = ''
    # se per batterli basta molto meno, dirlo prima di tutto il resto: e' la
    # differenza fra vincere l'asta e vincere la lega
    if soglia and att.get('quanti') and offerta - soglia >= max(4, offerta * 0.15):
        coda += ('<br><b>Ma non serve arrivarci:</b> per batterli bastano %d, '
                 'cioè %d crediti in meno di quelli che stavi mettendo.'
                 % (soglia, offerta - soglia))
    if altri_slot > 0:
        coda = ('<br>Dopo: <b>%d crediti</b> per <b>%d caselle</b>, cioè %.1f a '
                'testa.' % (residuo, altri_slot, per_slot))
        if per_slot < 3:
            coda += (' <span class="giu">Con meno di tre a slot il resto della '
                     'rosa lo riempi con gli avanzi.</span>')
        elif per_slot >= 12:
            coda += ' <span class="su">Ti resta in mano un\'asta comoda.</span>'
    return T.nota(testa + coda, variante)


def risposta_confronto(a, b, ctx):
    venduti = [q for q in (a, b) if q['id'] in ctx['asta']['acquisti']]
    if len(venduti) == 2:
        return {'titolo': 'Venduti tutti e due',
                'corpo': (risposta_venduto(a, ctx['asta']['acquisti'][a['id']],
                                           ctx)['corpo']
                          + risposta_venduto(b, ctx['asta']['acquisti'][b['id']],
                                             ctx)['corpo'])}
    if venduti:
        via = venduti[0]
        resta = b if via is a else a
        r = risposta_giocatore(resta, ctx)
        r['corpo'] = (T.nota('<b>%s è gia’ venduto</b>, non c’e’ piu’ niente '
                             'da confrontare: ti dico di %s.'
                             % (T.e(via['nome']), T.e(resta['nome'])), 'allarme')
                      + r['corpo'])
        return r
    ma, mb = ctx['massimi'].get(a['id'], 1), ctx['massimi'].get(b['id'], 1)
    # a parita' di crediti, chi rende di piu': e' la domanda vera del confronto
    resa_a = a['valore'] / max(1.0, float(ma))
    resa_b = b['valore'] / max(1.0, float(mb))
    vince = a if (a['valore'] - ma) >= (b['valore'] - mb) else b
    perde = b if vince is a else a

    righe = []
    for et, va, vb, fmt in (
            ('Il mio massimo', ma, mb, '%d'),
            ('Valore atteso', a['valore'], b['valore'], '%.1f'),
            ('Resa per credito', resa_a, resa_b, '%.2f'),
            ('FM attesa', a['fm_att'], b['fm_att'], '%.2f'),
            ('Partite attese', a['pv_proiettate'], b['pv_proiettate'], '%.0f'),
            ('Gialli a stagione', (a.get('cartellini') or {}).get('amm_stagione'),
             (b.get('cartellini') or {}).get('amm_stagione'), '%s')):
        def celle(v, altro, meglio_se_alto=True):
            if v is None:
                return '—'
            testo = fmt % v if fmt != '%s' else ('%.1f' % v)
            if altro is None or v == altro:
                return testo
            su = (v > altro) if meglio_se_alto else (v < altro)
            return '<b class="%s">%s</b>' % ('su' if su else '', testo)
        alto = et not in ('Il mio massimo', 'Gialli a stagione')
        righe.append([T.e(et), celle(va, vb, alto), celle(vb, va, alto)])

    tabella = T.tabella([('', 'nome'), (a['nome'], 'num'), (b['nome'], 'num')], righe)

    scarto = abs((a['valore'] - ma) - (b['valore'] - mb))
    if scarto < 3:
        verdetto = T.nota('<b>Sono equivalenti.</b> La differenza fra i due, al '
                          'netto di quello che costano, è meno di tre punti: '
                          'prendi quello che ti capita per primo, o quello che '
                          'costa meno sul momento.')
    else:
        verdetto = T.nota('<b>%s.</b> Al netto del prezzo rende %.0f punti in più '
                          'in una stagione. %s costa %d contro %d.'
                          % (T.e(vince['nome']), scarto, T.e(vince['nome']),
                             ctx['massimi'].get(vince['id'], 1),
                             ctx['massimi'].get(perde['id'], 1)), 'ok')
    return {'titolo': '%s o %s' % (a['nome'], b['nome']),
            'corpo': tabella + verdetto}


def risposta_come_sto(ctx):
    sit, cfg, asta = ctx['sit'], ctx['cfg'], ctx['asta']
    spesi = cfg['crediti'] - sit['residuo']
    pieni = sum(sit['ho'].values())
    totale_slot = sum(cfg['slot'].values())
    altri = [i for i in range(len(asta['squadre'])) if i != asta['mia']]
    tetti = sorted((ctx['offerta_massima'](i) for i in altri), reverse=True)

    box = [('Crediti', sit['residuo'], 'te ne restano', 'ciano'),
           ('Spesi', spesi, 'su %d' % cfg['crediti'], ''),
           ('Rosa', '%d/%d' % (pieni, totale_slot), 'caselle riempite', ''),
           ('Puoi arrivare a', ctx['offerta_massima'](asta['mia']),
            'su un singolo giocatore', 'verde')]
    if tetti:
        box.append(('Il rivale più ricco', tetti[0], 'fin dove può spingersi',
                    'rosso' if tetti[0] > ctx['offerta_massima'](asta['mia'])
                    else ''))
    pezzi = [T.riquadri(box)]

    righe = []
    quote = S.budget_per_reparto(cfg, sit)
    for ru in RUOLI:
        ho, manca = sit['ho'][ru], sit['manca'][ru]
        speso_ru = sum(v['prezzo'] for pid, v in asta['acquisti'].items()
                       if v['squadra'] == asta['mia']
                       and ctx['per_id'].get(pid, {}).get('R') == ru)
        righe.append([
            T.pillola(ru, T.RUOLO_COLORE[ru]),
            T.e(RUOLO_NOME[ru]),
            '%d/%d' % (ho, cfg['slot'][ru]),
            '%d' % speso_ru,
            '%d' % quote[ru],
            (T.pillola('completo', T.VERDE) if not manca
             else T.pillola('ne mancano %d' % manca,
                            T.ROSSO if manca >= cfg['slot'][ru] else '')),
        ])
    pezzi.append(T.tabella([('R', ''), ('Reparto', 'nome'), ('Presi', 'num'),
                            ('Spesi', 'num'), ('Da spendere', 'num'),
                            ('Stato', '')], righe))

    if sit['slot_mancanti']:
        media = sit['residuo'] / float(sit['slot_mancanti'])
        pezzi.append(T.nota('Ti restano <b>%d crediti</b> per <b>%d caselle</b>: '
                            '%.1f a testa in media. La colonna <i>da spendere</i> '
                            'è come li dividerei fra i reparti.'
                            % (sit['residuo'], sit['slot_mancanti'], media)))
    else:
        pezzi.append(T.nota('<b>Rosa completa.</b> Non ti manca nessuno.', 'ok'))
    return {'titolo': 'Come stai messo', 'corpo': ''.join(pezzi)}


def risposta_cosa_manca(ctx):
    sit = ctx['sit']
    if not sit['slot_mancanti']:
        return {'titolo': 'Non ti manca niente',
                'corpo': T.nota('<b>Rosa completa</b>: %d caselle su %d.'
                                % (sum(sit['ho'].values()),
                                   sum(ctx['cfg']['slot'].values())), 'ok')}
    pian = S.piano(ctx['d'], ctx['asta'], ctx['cfg'], ctx['massimi'])
    pezzi = []
    for ru in RUOLI:
        manca = sit['manca'][ru]
        if not manca:
            continue
        scelti = pian['scelti'][ru]
        n_riemp, costo_riemp = pian['riempitivi'][ru]
        pezzi.append(T.banda('%s — ne mancano %d' % (RUOLO_NOME[ru], manca),
                             '%d crediti da spendere qui' % pian['quote'][ru]))
        if scelti:
            pezzi.append(_tabella_giocatori([p for p, _ in scelti], ctx))
        if n_riemp:
            pezzi.append(T.nota('E %d caselle da riempire con chi capita, '
                                'per circa %d crediti in tutto.'
                                % (n_riemp, costo_riemp)))
        if not scelti and not n_riemp:
            pezzi.append(T.vuoto('Budget finito per questo reparto',
                                 'Con i crediti che restano non ci sta nessuno '
                                 'sopra i quattro crediti: qui si va di occasioni.'))
    return {'titolo': 'Cosa ti manca', 'corpo': ''.join(pezzi)}


def risposta_per_budget(ru, budget, ctx):
    presi = set(ctx['asta']['acquisti'])
    liberi = [p for p in ctx['d']['giocatori']
              if p['id'] not in presi and (ru is None or p['R'] == ru)
              and ctx['massimi'].get(p['id'], 1) <= budget and p['valore'] > 0]
    liberi.sort(key=lambda p: -p['valore'])
    che = RUOLO_NOME[ru].lower() if ru else 'calciatori'
    if not liberi:
        return {'titolo': 'Niente entro %d crediti' % budget,
                'corpo': T.vuoto('Nessun %s a questo prezzo' % che,
                                 'Con %d crediti non prendi nessuno che valga la '
                                 'pena in questo ruolo: o alzi, o aspetti che il '
                                 'mercato si svuoti.' % budget)}
    return {'titolo': 'I migliori %s entro %d crediti' % (che, budget),
            'corpo': (_tabella_giocatori(liberi[:12], ctx)
                      + T.nota('In ordine di valore atteso, non di prezzo: il '
                               'primo della lista è quello che rende di più, '
                               'non quello che costa di più.'))}


def risposta_scorte(ru, ctx):
    presi = set(ctx['asta']['acquisti'])
    fasce = S.per_fascia(ctx['d'], ctx['asta'], ctx['massimi'], ru)
    rimasti = sum(1 for p in ctx['d']['giocatori']
                  if p['R'] == ru and p['id'] not in presi and p['valore'] > 0)
    sc = ctx['scar'].get((ru, 1), 1.0)
    stato = ('agli sgoccioli' if sc >= 1.6 else 'scarseggiano' if sc >= 1.15
             else 'ce ne sono in abbondanza' if sc <= 0.7 else 'situazione normale')
    pezzi = [T.riquadri([
        ('Rimasti', rimasti, '%s che valgono qualcosa' % RUOLO_NOME[ru].lower(), ''),
        ('Fascia alta', len(fasce['alto']), 'sopra i 40 crediti', ''),
        ('Fascia media', len(fasce['medio']), 'fra 12 e 40', ''),
        ('Scorte', stato, 'per la prima fascia',
         'rosso' if sc >= 1.6 else 'ambra' if sc >= 1.15 else 'verde'),
    ])]
    for et, chiave in (('Fascia alta', 'alto'), ('Fascia media', 'medio'),
                       ('Fascia bassa', 'basso')):
        if fasce[chiave]:
            pezzi.append(T.banda(et, '%d disponibili' % len(fasce[chiave])))
            pezzi.append(_tabella_giocatori(fasce[chiave][:8], ctx))
    return {'titolo': 'Cosa resta: %s' % RUOLO_NOME[ru].lower(),
            'corpo': ''.join(pezzi)}


def risposta_avversari(ctx, solo=None):
    asta, cfg, per_id = ctx['asta'], ctx['cfg'], ctx['per_id']
    righe = []
    for i, nome in enumerate(asta['squadre']):
        if solo is not None and i != solo:
            continue
        acq = {pid: v['prezzo'] for pid, v in asta['acquisti'].items()
               if v['squadra'] == i}
        conta = {ru: sum(1 for pid in acq
                         if per_id.get(pid, {}).get('R') == ru) for ru in RUOLI}
        mancano = [ru for ru in RUOLI if conta[ru] < cfg['slot'][ru]]
        righe.append([
            ('★ ' if i == asta['mia'] else '') + T.e(nome),
            '%d' % (cfg['crediti'] - sum(acq.values())),
            '%d' % ctx['offerta_massima'](i),
            '%d/%d' % (len(acq), sum(cfg['slot'].values())),
            ' '.join(T.pillola('%s%d' % (ru, cfg['slot'][ru] - conta[ru]),
                               T.RUOLO_COLORE[ru]) for ru in mancano) or
            T.pillola('completa', T.VERDE),
        ])
    righe.sort(key=lambda r: -int(r[2]))
    tab = T.tabella([('Squadra', 'nome'), ('Crediti', 'num'),
                     ('Può arrivare a', 'big'), ('Rosa', 'num'),
                     ('Gli manca', '')], righe)
    return {'titolo': 'Gli avversari' if solo is None else asta['squadre'][solo],
            'corpo': tab + T.nota('<b>Può arrivare a</b> è quanto può mettere su '
                                  'un singolo giocatore tenendosi un credito per '
                                  'ogni casella che dovrà ancora riempire. È il '
                                  'numero che dice fin dove ti possono seguire.')}


def risposta_occasioni(ctx):
    occ = S.occasioni(ctx['d'], ctx['asta'], ctx['massimi'], quante=12)
    if not occ:
        return {'titolo': 'Nessuna occasione adesso',
                'corpo': T.vuoto('Il mercato è allineato',
                                 'In questo momento non c\'è nessuno che valga '
                                 'molto più di quanto costerà. Ricontrolla dopo '
                                 'qualche acquisto: i prezzi si muovono.')}
    righe = []
    for o in occ:
        p = o['p']
        righe.append([
            T.pillola(p['R'], T.RUOLO_COLORE[p['R']]),
            T.e(p['nome']), T.e(p['squadra']),
            '%d' % o['mercato'], '%d' % o['costo'],
            '<span class="su">+%d</span>' % o['divario'],
            T.e(' · '.join(p['note'][:1])),
        ])
    return {'titolo': 'Occasioni adesso',
            'corpo': (T.tabella([('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
                                 ('Costerà', 'num'), ('Vale', 'big'),
                                 ('Divario', 'num'), ('Nota', 'nota')], righe)
                      + T.nota('<b>Costerà</b> è il prezzo di mercato, <b>vale</b> '
                               'è il mio massimo. Chi ha il divario più largo è '
                               'chi puoi prendere sotto il suo valore.'))}


def risposta_omonimi(elenco, ctx):
    """Due giocatori con lo stesso cognome: chiedo quale, non tiro a indovinare."""
    righe = []
    for p in elenco[:6]:
        preso = ctx['asta']['acquisti'].get(p['id'])
        # il nome per esteso e' proprio il motivo per cui sono ambigui: senza,
        # la tabella mostra due righe diverse e non si capisce perche' te lo chiedo
        nome = T.e(p['nome'])
        if p.get('nome_completo'):
            nome += '<span class="duplice">%s</span>' % T.e(p['nome_completo'])
        righe.append([
            T.pillola(p['R'], T.RUOLO_COLORE[p['R']]),
            nome, T.e(p['squadra']),
            ('venduto' if preso else '%d' % ctx['massimi'].get(p['id'], 1)),
            '%.2f' % p['fm_att'],
            T.e(' · '.join(p['note'][:1])),
        ])
    return {'titolo': 'Quale dei due?',
            'corpo': (T.tabella([('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
                                 ('Max', 'big'), ('FM att.', 'num'),
                                 ('Nota', 'nota')], righe)
                      + T.nota('Con quel nome ce n’è più di uno. Riscrivilo come '
                               'sta in tabella — per esempio <b>%s</b> — oppure per '
                               'esteso, <b>%s</b>, e ti rispondo su quello.'
                               % (T.e(elenco[0]['nome']),
                                  T.e(elenco[0].get('nome_completo')
                                      or elenco[0]['nome']))))}


def risposta_mercato(ctx):
    """Com'e' l'aria adesso: si sta strapagando o e' il momento di comprare."""
    t = ctx.get('temperatura') or {}
    cal = ctx.get('cal') or {}
    diario = ctx.get('andamento') or []

    scarto = (cal.get('lega', 1.0) - 1) * 100
    box = [('Crediti per casella', '%.1f' % t.get('per_casella', 0),
            'partenza %.0f' % t.get('partenza', 0),
            'rosso' if t.get('rapporto', 1) > 1.12
            else 'verde' if t.get('rapporto', 1) < 0.88 else ''),
           ('La lega paga', '%+.0f%%' % scarto, 'rispetto ai miei consigli',
            'rosso' if scarto > 8 else 'verde' if scarto < -8 else ''),
           ('Venduti', cal.get('venduti', 0), 'in tutta la lega', ''),
           ('Crediti in giro', t.get('crediti', 0), 'ancora da spendere', '')]
    pezzi = [T.riquadri(box)]

    if len(diario) >= 2:
        valori = [r['lega'] for r in diario]
        pezzi.append(T.banda('Come si è mossa l\'asta',
                             '%d colpi di martello' % len(diario)))
        pezzi.append(T.curva(valori, etichette=('primo acquisto', 'adesso')))
        pezzi.append(T.nota('La linea tratteggiata sono i miei prezzi consigliati. '
                            'Sopra, la lega sta strapagando; sotto, sta comprando '
                            'a sconto.'))

    righe = []
    for ru in RUOLI:
        f = (cal.get('ruoli') or {}).get(ru, 1.0)
        n = (cal.get('per_ruolo_n') or {}).get(ru, 0)
        # senza vendite in quel reparto il numero non e' suo: e' la media della
        # lega che gli viene prestata. Dire "conviene aspettare" sugli attaccanti
        # perche' e' stato strapagato un difensore sarebbe un consiglio inventato
        if n < 3:
            scritta = ('<span style="color:var(--fioco)">%+.0f%%</span>'
                       % ((f - 1) * 100))
            senso = ('nessuna vendita ancora' if not n
                     else 'solo %d vendut%s: troppo poco per dire qualcosa'
                          % (n, 'o' if n == 1 else 'i'))
        else:
            scritta = (('<span class="giu">%+.0f%%</span>' if f > 1 else
                        '<span class="su">%+.0f%%</span>') % ((f - 1) * 100))
            senso = ('conviene aspettare' if f > 1.12
                     else 'è il reparto da attaccare adesso' if f < 0.9
                     else 'prezzi giusti')
        righe.append([
            T.pillola(ru, T.RUOLO_COLORE[ru]), T.e(RUOLO_NOME[ru]),
            '%d' % n, scritta, T.e(senso),
        ])
    pezzi.append(T.banda('Reparto per reparto'))
    pezzi.append(T.tabella([('R', ''), ('Reparto', 'nome'), ('Venduti', 'num'),
                            ('Si paga', 'num'), ('Cosa vuol dire', 'nota')], righe))

    if cal.get('venduti', 0) < 5:
        pezzi.append(T.nota('<b>È ancora presto per leggere il mercato.</b> Con %d '
                            'giocatori battuti qualunque percentuale è rumore: '
                            'questa pagina diventa affidabile dopo una decina di '
                            'aggiudicazioni.' % cal.get('venduti', 0), 'allarme'))
        return {"titolo": "Come sta andando l’asta", "corpo": "".join(pezzi)}

    consiglio = ('Con %.1f crediti per casella contro i %.0f di partenza, i '
                 'portafogli sono <b>%s</b> di quello che serve per quello che '
                 'resta: %s.'
                 % (t.get('per_casella', 0), t.get('partenza', 0),
                    'più pieni' if t.get('rapporto', 1) > 1 else 'più vuoti',
                    'i prezzi saliranno ancora, chi compra adesso paga meno'
                    if t.get('rapporto', 1) > 1.12 else
                    'è il momento delle occasioni, chi ha crediti comanda'
                    if t.get('rapporto', 1) < 0.88 else
                    'il mercato è in equilibrio'))
    pezzi.append(T.nota(consiglio))
    return {'titolo': 'Come sta andando l\'asta', 'corpo': ''.join(pezzi)}


def risposta_aiuto(ctx=None):
    voci = ''.join('<li>%s</li>' % T.e(x) for x in ESEMPI)
    return {'titolo': 'Cosa puoi chiedermi',
            'corpo': ('<ul class="motivi">%s</ul>' % voci
                      + T.nota('Scrivi come ti viene. Riconosco i nomi dei '
                               'calciatori anche scritti male, le cifre, i ruoli e '
                               'i nomi delle squadre della tua lega. Quello che non '
                               'capisco te lo dico, invece di inventare.'))}


# --------------------------------------------------------------- l'inoltro
def rispondi(testo, ctx):
    """Da una frase alla risposta giusta.

    L'ordine dei controlli non e' casuale: prima le domande piu' specifiche —
    quelle con un nome e una cifra — poi via via le piu' generiche, cosi' "quanto
    vale Dimarco" non finisce nel ramo generico dei prezzi.
    """
    t = (testo or '').strip()
    if not t:
        return risposta_aiuto(ctx)
    basso = t.lower()

    if any(k in basso for k in ('aiuto', 'cosa posso chieder', 'come funziona',
                                'cosa sai fare')):
        return risposta_aiuto(ctx)

    citati = giocatori_citati(t, ctx['d']['giocatori'])
    nums = numeri(t)
    ru = ruolo_citato(t)

    doppi = omonimi(t, ctx['d']['giocatori'])
    if doppi:
        return risposta_omonimi(doppi, ctx)
    # due nomi si confrontano solo se li hai scritti tutti e due: due giocatori
    # trovati dalla stessa parola non sono un confronto, sono un equivoco
    distinte = citazioni(t, ctx['d']['giocatori'])
    if len(distinte) >= 2:
        return risposta_confronto(distinte[0][1], distinte[1][1], ctx)
    if citati:
        offerta = nums[0] if nums else None
        return risposta_giocatore(citati[0], ctx, offerta)

    if any(k in basso for k in ('come sto', 'come sono', 'situazione', 'come va',
                                'come siamo', 'a che punto', 'quanto mi resta',
                                'quanti crediti ho', 'come messo')):
        return risposta_come_sto(ctx)
    if any(k in basso for k in ('mi manca', 'devo prendere', 'cosa manca',
                                'chi manca', 'buchi', 'scoperto')):
        return risposta_cosa_manca(ctx)
    if any(k in basso for k in ('come va il mercato', 'come sta andando',
                                'andamento', 'temperatura', 'si sta pagando',
                                'come vanno i prezzi', 'inflazione', 'come va l',
                                'clima')):
        return risposta_mercato(ctx)
    if any(k in basso for k in ('occasion', 'affar', 'sottovalut', 'conviene')):
        return risposta_occasioni(ctx)

    squadra = squadra_citata(t, ctx['asta'])
    if squadra is not None or any(k in basso for k in (
            'avversar', 'rilanc', 'chi ha ancora', 'chi ha crediti', 'gli altri',
            'le altre', 'chi puo arrivare', 'chi può')):
        return risposta_avversari(ctx, squadra)

    if ru and any(k in basso for k in ('resta', 'restano', 'rimang', 'scorte',
                                       'quanti', 'ancora liberi', 'disponibil')):
        return risposta_scorte(ru, ctx)
    if nums:
        return risposta_per_budget(ru, nums[0], ctx)
    if ru:
        return risposta_scorte(ru, ctx)

    return {'titolo': 'Non ho capito',
            'corpo': (T.nota('<b>Questa non la so leggere.</b> Non provo a '
                             'indovinare: preferisco dirtelo e mostrarti cosa so '
                             'fare, invece di darti un numero inventato mentre stai '
                             'per rilanciare.', 'allarme')
                      + risposta_aiuto(ctx)['corpo'])}
