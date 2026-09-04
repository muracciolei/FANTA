# -*- coding: utf-8 -*-
"""I conti che cambiano mentre l'asta va avanti.

Il prezzo di un giocatore non e' un numero scritto una volta: dipende da quanti
crediti sono ancora in giro, da quante caselle restano da riempire, da quanto la
lega sta pagando quel ruolo rispetto ai miei consigli. Qui dentro c'e' tutta
questa aritmetica, tenuta separata dall'interfaccia per due motivi: la pagina
dell'asta e la pagina Chiedimi la usano tutte e due, e cosi' si puo' provare
senza aprire una finestra.
"""
import json
import os

import fanta_modello as M
import radice

RUOLI = ['P', 'D', 'C', 'A']


def acquisti_di(asta, i):
    return {pid: v['prezzo'] for pid, v in asta['acquisti'].items() if v['squadra'] == i}


def miei(asta):
    """Gli acquisti della mia squadra: id del giocatore -> prezzo pagato."""
    return acquisti_di(asta, asta['mia'])


def calibrazione(giocatori, asta):
    """Quanto la lega sta davvero pagando rispetto ai miei consigli.

    Guardo i giocatori gia' venduti e confronto il prezzo pagato con quello che
    avevo consigliato. Lo faccio a tre livelli — tutta la lega, il singolo ruolo,
    il singolo slot — perche' un'asta non si scalda in modo uniforme: capita che
    volino i primi attaccanti e restino fermi i terzi portieri.

    Con pochi acquisti alle spalle il dato e' rumoroso, quindi ogni livello viene
    tirato verso quello piu' generale finche' i numeri non sono abbastanza.
    """
    per_id = {p['id']: p for p in giocatori}
    tutto = [0.0, 0.0, 0]
    per_ruolo, per_slot = {}, {}
    for pid, v in asta['acquisti'].items():
        p = per_id.get(pid)
        if not p:
            continue
        atteso = max(1, p['prezzo_prudente'])
        for conto in (tutto, per_ruolo.setdefault(p['R'], [0.0, 0.0, 0]),
                      per_slot.setdefault((p['R'], p['slot']), [0.0, 0.0, 0])):
            conto[0] += v['prezzo']
            conto[1] += atteso
            conto[2] += 1

    def rapporto(conto, ripiego, forza=4.0):
        if not conto or conto[2] == 0 or conto[1] <= 0:
            return ripiego
        peso = conto[2] / (conto[2] + forza)
        return peso * (conto[0] / conto[1]) + (1 - peso) * ripiego

    lega = rapporto(tutto, 1.0, 6.0)
    ruoli = {r: rapporto(per_ruolo.get(r), lega) for r in RUOLI}
    slot = {}
    for r in RUOLI:
        for s in list(range(1, 16)) + [None]:
            slot[(r, s)] = rapporto(per_slot.get((r, s)), ruoli[r], 3.0)
    return {'lega': lega, 'ruoli': ruoli, 'slot': slot,
            'venduti': tutto[2], 'per_ruolo_n': {r: per_ruolo.get(r, [0, 0, 0])[2]
                                                 for r in RUOLI}}


def prezzi_live(giocatori, cfg, asta, cal=None):
    """Ricalcola i prezzi tenendo conto di tre cose che cambiano minuto per minuto:
    chi e' gia' stato venduto, quanti crediti restano davvero sul tavolo, e a che
    prezzi la lega sta comprando ogni slot. E' la differenza tra un listino
    stampato e un consiglio che vale adesso."""
    cal = cal or calibrazione(giocatori, asta)
    presi = set(asta['acquisti'])
    spesi = sum(v['prezzo'] for v in asta['acquisti'].values())
    crediti_totali = cfg['squadre'] * cfg['crediti']
    rimasti = max(1, crediti_totali - spesi)

    per_id = {p['id']: p for p in giocatori}
    slot_presi = {r: 0 for r in RUOLI}
    for pid in presi:
        if pid in per_id:
            slot_presi[per_id[pid]['R']] += 1

    # primo giro: per ogni ruolo calcolo il valore ancora sul mercato
    reparti = {}
    for ru in RUOLI:
        slot_rim = max(0, cfg['squadre'] * cfg['slot'][ru] - slot_presi[ru])
        liberi = sorted([p for p in giocatori if p['R'] == ru and p['id'] not in presi],
                        key=lambda x: -x['valore'])
        vor, somma, sostituto = [], 0.0, 0.0
        if liberi and slot_rim:
            k = min(slot_rim, len(liberi) - 1)
            sostituto = liberi[k]['valore']
            vor = [max(0.0, p['valore'] - sostituto) for p in liberi]
            somma = sum(vor)
        reparti[ru] = {'liberi': liberi, 'vor': vor, 'somma': somma,
                       'slot_rim': slot_rim}

    # i crediti che restano si dividono fra i reparti in proporzione al valore
    # ancora disponibile e a quanto la lega sta pagando quel reparto, non secondo
    # una quota fissa: se gli attaccanti buoni sono finiti quei soldi migrano
    # altrove, e se invece vanno a ruba il reparto se ne prende una fetta piu'
    # grande, perche' e' li' che i crediti finiranno davvero
    pesi = {ru: cfg['quote'][ru] * reparti[ru]['somma'] * cal['ruoli'][ru]
            for ru in RUOLI}
    tot_pesi = sum(pesi.values()) or 1.0

    out = {}
    for ru in RUOLI:
        r = reparti[ru]
        if not r['liberi']:
            continue
        if not r['slot_rim'] or r['somma'] <= 0:
            for p in r['liberi']:
                out[p['id']] = 1
            continue
        budget = rimasti * pesi[ru] / tot_pesi
        allocabile = max(0.0, budget - r['slot_rim'])

        # dentro il reparto, gli slot su cui la lega sta spendendo di piu' si
        # prendono una fetta maggiore: la somma pero' resta quella, e' solo una
        # redistribuzione
        grezzi, fattori = [], []
        for p, v in zip(r['liberi'], r['vor']):
            f = cal['slot'].get((ru, p.get('slot')), cal['ruoli'][ru])
            grezzi.append(v)
            fattori.append(f)
        pesata = sum(v * f for v, f in zip(grezzi, fattori)) or 1.0

        for p, v, f in zip(r['liberi'], grezzi, fattori):
            modello = 1 if v <= 0 else 1 + allocabile * (v * f) / pesata
            # il mercato conosce cose che i numeri non vedono (gerarchie, mercato
            # estivo, voci di spogliatoio): il valore equo e' la media dei due
            out[p['id']] = max(1, int(round(0.6 * modello + 0.4 * p['prezzo_mercato'])))
    return out


def scarsita(giocatori, cfg, asta):
    """Quanti ne restano rispetto a quanti ne servono ancora, slot per slot.

    All'inizio ogni slot ha esattamente una squadra che lo cerca e un giocatore
    che lo puo' riempire: il rapporto vale 1. Sale quando quella fascia si svuota
    piu' in fretta di quanto cali il numero di squadre che la cercano — ed e'
    esattamente quando conviene pagare un sovrapprezzo, perche' dopo non c'e' piu'.
    """
    per_id = {p['id']: p for p in giocatori}
    ha = {}      # (squadra, ruolo, slot) -> quanti
    per_ruolo = {}
    for pid, v in asta['acquisti'].items():
        p = per_id.get(pid)
        if not p:
            continue
        ha[(v['squadra'], p['R'], p.get('slot'))] = \
            ha.get((v['squadra'], p['R'], p.get('slot')), 0) + 1
        per_ruolo[(v['squadra'], p['R'])] = per_ruolo.get((v['squadra'], p['R']), 0) + 1

    liberi = {}
    for p in giocatori:
        if p['id'] not in asta['acquisti']:
            k = (p['R'], p.get('slot'))
            liberi[k] = liberi.get(k, 0) + 1

    out = {}
    for ru in RUOLI:
        # solo le fasce che esistono davvero per quel ruolo, piu' il fondo lista
        for s in list(range(1, cfg['slot'][ru] + 1)) + [None]:
            domanda = sum(1 for i in range(len(asta['squadre']))
                          if not ha.get((i, ru, s))
                          and per_ruolo.get((i, ru), 0) < cfg['slot'][ru])
            offerta = liberi.get((ru, s), 0)
            out[(ru, s)] = min(2.5, max(0.4, domanda / float(max(1, offerta))))
    return out


def prezzi_massimi(giocatori, cfg, asta, equi, scar):
    """Il tetto: oltre questa cifra quel giocatore non conviene piu'.

    Parte dal valore equo e ci aggiunge un premio di scarsita', perche' un
    giocatore che non ha piu' sostituti vale di piu' del suo puro rendimento.
    Poi taglia con quello che ti puoi permettere davvero: i crediti che ti restano
    meno uno per ogni slot che dovrai ancora riempire.
    """
    mia = miei(asta)
    residuo = cfg['crediti'] - sum(mia.values())
    slot_liberi_miei = max(0, sum(cfg['slot'].values()) - len(mia))
    tetto_borsa = max(1, residuo - max(0, slot_liberi_miei - 1))

    out = {}
    for p in giocatori:
        equo = equi.get(p['id'])
        if equo is None:
            continue
        s = scar.get((p['R'], p.get('slot')), 1.0)
        premio = min(0.60, max(-0.15, 0.5 * (s - 1)))
        out[p['id']] = max(1, min(tetto_borsa, int(round(equo * (1 + premio)))))
    return out, tetto_borsa


def offerta_massima(asta, cfg, i):
    """Fin dove puo' spingersi una squadra su un singolo giocatore: quello che le
    resta, meno un credito per ogni casella che dovra' ancora riempire dopo."""
    acq = acquisti_di(asta, i)
    residuo = cfg['crediti'] - sum(acq.values())
    mancanti = sum(cfg['slot'].values()) - len(acq)
    return max(0, residuo - max(0, mancanti - 1))


def rivale_piu_ricco(asta, cfg):
    altri = [(offerta_massima(asta, cfg, i), asta['squadre'][i])
             for i in range(len(asta['squadre'])) if i != asta['mia']]
    return max(altri) if altri else (0, '')


# ------------------------------------------------ a quanto verra' battuto
def portafogli(cfg, asta, per_id):
    """La fotografia di ogni squadra: crediti, caselle, fame per ruolo.

    Serve a smettere di ragionare come se tutti avessero il portafoglio pieno.
    A meta' asta le squadre non sono intercambiabili: c'e' chi ha speso tutto e
    non puo' piu' rilanciare su niente, e chi ha ancora quattrocento crediti e
    dodici caselle vuote e ti soffia qualunque cosa.
    """
    fuori = []
    for i in range(len(asta['squadre'])):
        acq = acquisti_di(asta, i)
        conta = {ru: 0 for ru in RUOLI}
        for pid in acq:
            p = per_id.get(pid)
            if p:
                conta[p['R']] += 1
        residuo = cfg['crediti'] - sum(acq.values())
        mancanti = sum(cfg['slot'].values()) - len(acq)
        fuori.append({
            'i': i, 'nome': asta['squadre'][i], 'residuo': residuo,
            'mancanti': max(0, mancanti),
            'tetto': max(0, residuo - max(0, mancanti - 1)),
            'manca_ruolo': {ru: max(0, cfg['slot'][ru] - conta[ru]) for ru in RUOLI},
            # quanto puo' permettersi per casella: e' questo che separa chi
            # rilancia sul serio da chi puo' solo guardare
            'per_casella': residuo / float(max(1, mancanti)),
        })
    return fuori


def prezzi_attesi(giocatori, cfg, asta, equi):
    """Non quanto vale, ma a quanto verra' battuto davvero.

    In un'asta al rialzo il prezzo non lo fa chi vince: lo fa il secondo. Tu paghi
    un credito piu' di quanto era disposto a mettere l'ultimo che si e' ritirato.
    Quindi per sapere dove finira' un giocatore non basta sapere quanto vale:
    bisogna guardare chi lo vuole ancora, quanti crediti ha in mano, e quanto e'
    disposto a spingersi.

    La valutazione che attribuisco a ogni squadra e' il prezzo equo corretto per
    quanto quella squadra e' ricca rispetto alle altre — chi ha il doppio dei
    crediti per casella paga di piu', ed e' quello che si vede a ogni asta —
    tagliata sul suo tetto vero, che sono i crediti meno uno per ogni buco che
    dovra' comunque riempire.
    """
    per_id = {p['id']: p for p in giocatori}
    borse = portafogli(cfg, asta, per_id)
    vivi = [b for b in borse if b['mancanti'] > 0]
    media = (sum(b['per_casella'] for b in vivi) / len(vivi)) if vivi else 1.0
    media = max(0.5, media)

    presi = set(asta['acquisti'])
    out = {}
    for p in giocatori:
        if p['id'] in presi:
            continue
        equo = equi.get(p['id'])
        if equo is None:
            continue
        offerte = []
        for b in borse:
            if not b['manca_ruolo'][p['R']] or b['tetto'] < 1:
                continue
            # la ricchezza relativa muove la disponibilita' a pagare, ma con
            # moderazione: nessuno paga il triplo solo perche' ha il triplo
            fattore = min(1.7, max(0.55, (b['per_casella'] / media) ** 0.55))
            offerte.append((min(b['tetto'], max(1.0, equo * fattore)), b))
        offerte.sort(key=lambda x: -x[0])

        if not offerte:
            out[p['id']] = {'atteso': 1, 'chi': None, 'secondo': None, 'quanti': 0,
                            'per_prenderlo': 1, 'rivali': [], 'pari': 0}
            continue
        if len(offerte) == 1:
            # un solo interessato: parte da un credito e nessuno lo rilancia
            atteso = 1
        else:
            atteso = min(offerte[0][0], offerte[1][0] + 1)

        # a inizio asta le squadre sono tutte uguali e il "vincitore" sarebbe
        # solo la prima dell'elenco: se sono appaiate lo dico, invece di
        # inventarmi un nome
        testa = offerte[0][0]
        pari = sum(1 for v, _ in offerte if v >= testa - 1)
        stacca = pari == 1

        # e il numero che serve a te: quanto devi mettere per batterli tutti
        rivali = [(v, b) for v, b in offerte if b['i'] != asta['mia']]
        mio = next((b for b in borse if b['i'] == asta['mia']), None)
        per_prenderlo = int(round(rivali[0][0] + 1)) if rivali else 1
        if mio:
            per_prenderlo = min(per_prenderlo, max(1, mio['tetto']))

        out[p['id']] = {
            'atteso': max(1, int(round(atteso))),
            'chi': offerte[0][1]['nome'] if stacca else None,
            'chi_i': offerte[0][1]['i'] if stacca else None,
            'pari': 0 if stacca else pari,
            'secondo': offerte[1][1]['nome'] if len(offerte) > 1 else None,
            'quanti': len(offerte),
            'per_prenderlo': max(1, per_prenderlo),
            'fuori_portata': bool(mio and rivali and rivali[0][0] >= mio['tetto']),
            'rivali': [(b['nome'], b['i'], int(round(v))) for v, b in rivali[:5]],
            'offerte': [(b['nome'], b['i'], int(round(v))) for v, b in offerte[:6]],
        }
    return out


def temperatura(giocatori, cfg, asta):
    """Quanto e' caldo il mercato adesso, e quindi se conviene comprare o aspettare.

    Il numero e' semplice: quanti crediti restano in tutta la lega per ogni casella
    ancora da riempire. All'inizio e' esattamente il budget diviso gli slot — da
    voi venti — e da li' si muove. Sopra, i portafogli sono pieni rispetto a quello
    che resta da comprare e si strapaga; sotto, i soldi sono finiti prima dei
    giocatori ed e' il momento degli affari.
    """
    spesi = sum(v['prezzo'] for v in asta['acquisti'].values())
    crediti = cfg['squadre'] * cfg['crediti'] - spesi
    caselle = cfg['squadre'] * sum(cfg['slot'].values()) - len(asta['acquisti'])
    partenza = cfg['crediti'] / float(sum(cfg['slot'].values()))
    ora = crediti / float(max(1, caselle))
    return {'crediti': crediti, 'caselle': caselle, 'per_casella': ora,
            'partenza': partenza, 'rapporto': ora / partenza,
            'stato': ('mercato caldo' if ora > partenza * 1.12
                      else 'mercato freddo' if ora < partenza * 0.88
                      else 'mercato in equilibrio')}


# ------------------------------------------------------- l'effetto domino
def variazioni(prima, dopo, giocatori, presi, quante=6, soglia=2):
    """Chi si e' mosso, e di quanto, dopo l'ultimo colpo di martello.

    E' la cosa che all'asta non si vede mai: quando qualcuno paga novanta un
    centrocampista, i centrocampisti simili valgono di piu' un secondo dopo — i
    crediti sono finiti li' e non ci sono piu' per gli altri, e le alternative a
    quella fascia sono una di meno. Il numero si muove da solo dentro il motore;
    questo serve a farlo vedere.
    """
    fuori = []
    for p in giocatori:
        if p['id'] in presi:
            continue
        a, b = prima.get(p['id']), dopo.get(p['id'])
        if a is None or b is None or a < 3:
            continue
        delta = b - a
        if abs(delta) < soglia:
            continue
        fuori.append({'p': p, 'prima': a, 'dopo': b, 'delta': delta,
                      'quota': delta / float(a)})
    su = sorted([v for v in fuori if v['delta'] > 0], key=lambda v: -v['quota'])
    giu = sorted([v for v in fuori if v['delta'] < 0], key=lambda v: v['quota'])
    return {'su': su[:quante], 'giu': giu[:quante],
            'quanti': len(fuori), 'mossi_su': len(su), 'mossi_giu': len(giu)}


def scatto(giocatori, cfg, asta, cal=None):
    """Una riga di diario dell'asta: dove siamo e quanto si sta pagando."""
    cal = cal or calibrazione(giocatori, asta)
    t = temperatura(giocatori, cfg, asta)
    return {'n': len(asta['acquisti']),
            'spesi': cfg['squadre'] * cfg['crediti'] - t['crediti'],
            'per_casella': round(t['per_casella'], 2),
            'lega': round(cal['lega'], 3),
            'ruoli': {r: round(cal['ruoli'][r], 3) for r in RUOLI}}


ANDAMENTO = os.path.join(radice.cartella(), 'dati', 'andamento.json')


def leggi_andamento():
    """Il diario dell'asta: una riga per ogni giocatore battuto."""
    if not os.path.exists(ANDAMENTO):
        return []
    try:
        with open(ANDAMENTO, encoding='utf-8') as f:
            return json.load(f)
    except (ValueError, OSError):
        return []


def registra_andamento(giocatori, cfg, asta, cal=None):
    """Aggiunge una riga al diario, o riscrive l'ultima se siamo allo stesso punto.

    Serve a vedere la corsa dei prezzi mentre succede: se la lega ha cominciato
    pagando il venti per cento sopra i miei consigli e adesso paga sotto, il
    momento buono per comprare e' adesso.
    """
    diario = leggi_andamento()
    riga = scatto(giocatori, cfg, asta, cal)
    if diario and diario[-1]['n'] == riga['n']:
        diario[-1] = riga
    else:
        diario.append(riga)
    diario = diario[-400:]
    try:
        os.makedirs(os.path.dirname(ANDAMENTO), exist_ok=True)
        with open(ANDAMENTO, 'w', encoding='utf-8') as f:
            json.dump(diario, f, ensure_ascii=False)
    except OSError:
        pass
    return diario


def azzera_andamento():
    try:
        if os.path.exists(ANDAMENTO):
            os.remove(ANDAMENTO)
    except OSError:
        pass
