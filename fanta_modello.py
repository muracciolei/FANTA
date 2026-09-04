# -*- coding: utf-8 -*-
"""Motore di valutazione: rendimento atteso, rischio disponibilita', prezzi d'asta,
forma e consigli di formazione. Legge dati/dataset.json, scrive dati/valutazioni.json.
"""
import datetime
import json
import os
import re
import statistics as st
import sys
import unicodedata

import giudizio as G
import radice

BASE = radice.cartella()
DATI = os.path.join(BASE, 'dati')
CONFIG = os.path.join(DATI, 'config.json')

STAGIONE = '2026-27'
RUOLI = ['P', 'D', 'C', 'A']
RUOLO_NOME = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti', 'A': 'Attaccanti'}
PESI_STORICI = [('2025-26', 0.60), ('2024-25', 0.28), ('2023-24', 0.12)]
PESI = PESI_STORICI          # sostituito a ogni giro da pesi_stagionali()
GIORNATE = 38
PRIOR_N = 6.0

CONFIG_DEFAULT = {
    'squadre': 10,
    'crediti': 500,
    'slot': {'P': 3, 'D': 8, 'C': 8, 'A': 6},
    # con il modificatore di difesa conviene spostare crediti su portiere e difesa
    'quote': {'P': 0.08, 'D': 0.22, 'C': 0.28, 'A': 0.42},
    'modificatore_difesa': True,
    'modalita': 'Classic',
    # squadre impegnate nelle coppe europee: ruotano di piu' in campionato
    'europa': [],
}


def carica_config():
    cfg = dict(CONFIG_DEFAULT)
    if os.path.exists(CONFIG):
        try:
            cfg.update(json.load(open(CONFIG, encoding='utf-8')))
        except ValueError:
            pass
    return cfg


def salva_config(cfg):
    json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


# --------------------------------------------------------------- utilita'
# le lettere che non sono una lettera latina con un segno sopra: la
# normalizzazione Unicode non le tocca, e senza questa tabella la o barrata di
# Hojlund sparisce invece di diventare una o
LETTERE_INTERE = {
    'ø': 'o', 'Ø': 'o', 'æ': 'ae', 'Æ': 'ae', 'å': 'a', 'Å': 'a',
    'ß': 'ss', 'đ': 'd', 'Đ': 'd', 'ð': 'd', 'Ð': 'd', 'þ': 'th', 'Þ': 'th',
    'ł': 'l', 'Ł': 'l', 'ı': 'i', 'œ': 'oe', 'Œ': 'oe',
}


def chiave(nome):
    """Normalizza un nome per confronti tolleranti (accenti, punti, maiuscole)."""
    s = ''.join(LETTERE_INTERE.get(c, c) for c in (nome or ''))
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', s.lower())


def eta(nascita, oggi=None):
    if not nascita:
        return None
    oggi = oggi or datetime.date.today()
    a, m, g = (int(x) for x in nascita.split('-'))
    return oggi.year - a - ((oggi.month, oggi.day) < (m, g))


def blocchi_assenza(stati, minimo=3):
    """Dalla striscia di stato giornata per giornata separa le assenze.

    Un blocco lungo di assenze conta come probabile infortunio solo se il giocatore
    stava giocando prima e torna a giocare dopo: e' quella la firma di uno stop.
    Un blocco lungo a inizio o fine stagione conta solo se il giocatore e' comunque
    un titolare, altrimenti e' semplicemente una riserva che non gioca.
    """
    if not stati:
        return 0, 0, 0
    s = [c for c in stati if c != '.']
    if not s:
        return 0, 0, 0
    presenze = sum(1 for c in s if c in ('0', '1'))
    quota = presenze / float(len(s))
    squalifiche = sum(1 for c in s if c == '2')

    infortunio = panchina = 0
    i = 0
    while i < len(s):
        if s[i] in ('3', '4'):
            j = i
            while j < len(s) and s[j] in ('3', '4'):
                j += 1
            lung = j - i
            prima = i > 0 and s[i - 1] in ('0', '1')
            dopo = j < len(s) and s[j] in ('0', '1')
            if lung >= minimo and ((prima and dopo) or ((prima or dopo) and quota >= 0.5)):
                infortunio += lung
            else:
                panchina += lung
            i = j
        else:
            i += 1
    return infortunio, panchina, squalifiche


def pesi_stagionali(giocate):
    """Quanto pesa la stagione in corso rispetto alle precedenti.

    Alla terza giornata due partite non dicono niente e lo storico deve comandare;
    a dicembre e' il contrario, e continuare a valutare un giocatore sull'anno
    scorso sarebbe assurdo. Il peso della stagione in corso cresce quindi con le
    giornate giocate fino a diventare maggioranza, e il resto si ridistribuisce
    sulle stagioni passate mantenendone le proporzioni.
    """
    w = min(0.62, 0.052 * max(0, giocate))
    resto = 1.0 - w
    return ([(STAGIONE, w)] if w > 0 else []) +            [(s, p * resto) for s, p in PESI_STORICI]


def scala_stagione(pv, stagione, giocate):
    """Le partite della stagione in corso vanno riportate al passo di un'annata
    intera, altrimenti a settembre risulterebbero tutti dei panchinari."""
    if stagione != STAGIONE or not giocate:
        return pv
    return min(GIORNATE, (pv or 0) * GIORNATE / float(giocate))


# --------------------------------------------------------- rendimento atteso
def calcola_attese(d, giocate=0):
    listone, stats, schede = d['listone'], d['stats'], d['schede']
    pesi = pesi_stagionali(giocate)

    base_fm, base_mv = {}, {}
    for ru in RUOLI:
        fm = [r['fm'] for r in stats['2025-26'].values()
              if r['R'] == ru and (r.get('pv') or 0) >= 15 and r.get('fm') is not None]
        mv = [r['mv'] for r in stats['2025-26'].values()
              if r['R'] == ru and (r.get('pv') or 0) >= 15 and r.get('mv') is not None]
        base_fm[ru] = st.median(fm) if fm else 6.0
        base_mv[ru] = st.median(mv) if mv else 6.0

    for p in listone:
        presenti = [(w, s, stats[s][p['id']]) for s, w in pesi if p['id'] in stats[s]]
        p['storico'] = {s: stats[s].get(p['id']) for s, _ in PESI_STORICI}
        p['corrente'] = stats.get(STAGIONE, {}).get(p['id'])
        if presenti:
            tw = sum(w for w, _, _ in presenti)
            p['pv_att'] = min(GIORNATE,
                              sum(w * scala_stagione(r.get('pv') or 0, s, giocate)
                                  for w, s, r in presenti) / tw)
        else:
            p['pv_att'] = None
        num_f = num_m = den = 0.0
        for w, s, r in presenti:
            pv = r.get('pv') or 0
            if pv >= 3 and r.get('fm') is not None:
                num_f += w * pv * r['fm']
                num_m += w * pv * (r.get('mv') or r['fm'])
                den += w * pv
        if den > 0:
            p['fm_att'] = (num_f + PRIOR_N * base_fm[p['R']]) / (den + PRIOR_N)
            p['mv_att'] = (num_m + PRIOR_N * base_mv[p['R']]) / (den + PRIOR_N)
            p['stima'] = False
        else:
            p['fm_att'] = p['mv_att'] = None
            p['stima'] = True

    # chi non ha storico in Serie A: stima dai simili per FVM nello stesso ruolo
    noti = [q for q in listone if not q['stima'] and q['fvm']]
    for p in listone:
        if not p['stima']:
            continue
        fvm = p['fvm'] or 1
        vicini = sorted([q for q in noti if q['R'] == p['R']],
                        key=lambda q: abs((q['fvm'] or 1) - fvm))[:11]
        if vicini:
            p['fm_att'] = st.median([q['fm_att'] for q in vicini])
            p['mv_att'] = st.median([q['mv_att'] for q in vicini])
            p['pv_att'] = st.median([q['pv_att'] for q in vicini]) * 0.85
        else:
            p['fm_att'] = base_fm[p['R']] - 0.3
            p['mv_att'] = base_mv[p['R']]
            p['pv_att'] = 12.0

    return base_fm, base_mv


# ------------------------------------------------------ modificatore difesa
# La regola della lega: si schierano portiere piu' almeno quattro difensori, ma
# nella media entrano solo il portiere e i TRE difensori con il voto migliore.
# Da 6,00 in su si sale di un punto ogni 0,25 di media.
DIFENSORI_NEL_BLOCCO = 3
SOGLIA_MOD = 6.0
PASSO_MOD = 0.25
MAX_MOD = 5.0


def punti_modificatore(media):
    """Quanti punti vale una media di reparto.

    La tabella e' a scalini, ma per valutare un giocatore uso la versione
    smussata: dove finira' davvero la media del blocco non lo so, e il valore
    atteso di una scala di gradini vista da lontano e' la retta che li unisce.
    Sotto il 6 non si prende niente e sopra il 7 non si prende di piu': sono i
    due estremi che una formula lineare sbaglierebbe.
    """
    if media is None:
        return 0.0
    x = (media - (SOGLIA_MOD - PASSO_MOD / 2.0)) / PASSO_MOD
    return max(0.0, min(MAX_MOD, x))


def media_blocco(portiere_mv, difensori_mv):
    """La media che conta: il portiere e i tre difensori col voto piu' alto."""
    tre = sorted(difensori_mv, reverse=True)[:DIFENSORI_NEL_BLOCCO]
    if portiere_mv is None or len(tre) < DIFENSORI_NEL_BLOCCO:
        return None
    return (portiere_mv + sum(tre)) / (1.0 + DIFENSORI_NEL_BLOCCO)


def blocco_di_riferimento(d, cfg):
    """Il reparto che si ritrova una squadra qualunque della lega: serve da metro
    per dire quanto vale un difensore *in piu'* rispetto al normale."""
    def mediana(ruolo, quanti):
        # ordino per valore di mercato: e' il modo piu' semplice di individuare
        # chi verra' davvero schierato, e qui serve solo quello
        lst = sorted([p for p in d['listone'] if p['R'] == ruolo and p['mv_att']
                      and p['pv_proiettate'] >= 18],
                     key=lambda x: -(x['fvm'] or 0))[:quanti]
        mv = sorted(p['mv_att'] for p in lst)
        return st.median(mv) if mv else 6.0
    por = mediana('P', cfg['squadre'])
    dif = mediana('D', cfg['squadre'] * DIFENSORI_NEL_BLOCCO)
    return {'portiere': por, 'difensore': dif,
            'media': media_blocco(por, [dif] * DIFENSORI_NEL_BLOCCO)}


def valore_modificatore(p, rif):
    """Quanto vale questo giocatore per il modificatore, in fantapunti di stagione.

    Non guardo la sua media voto in assoluto ma quanto sposta la media del blocco
    rispetto a chi ci sarebbe al suo posto. Un difensore da 6,30 in un reparto
    normale vale molto; lo stesso difensore in un reparto gia' fortissimo vale
    poco, perche' nella media entrano solo i tre migliori.
    """
    if not rif or p['R'] not in ('P', 'D') or p['mv_att'] is None:
        return 0.0
    if p['R'] == 'P':
        con = media_blocco(p['mv_att'], [rif['difensore']] * DIFENSORI_NEL_BLOCCO)
    else:
        con = media_blocco(rif['portiere'],
                           [p['mv_att']] + [rif['difensore']] * (DIFENSORI_NEL_BLOCCO - 1))
    delta = punti_modificatore(con) - punti_modificatore(rif['media'])
    return delta * p['pv_proiettate']


def indizio_europa(d, quante=6):
    """Un tentativo di indovinare chi gioca le coppe, da correggere a mano.

    Non esiste una pagina da cui leggerlo in modo affidabile, quindi propongo le
    squadre che l'anno scorso avevano la miglior differenza reti — di solito sono
    quelle che si qualificano — e lascio all'utente l'ultima parola.
    """
    gf, gs, pv = {}, {}, {}
    for r in d['stats'].get('2025-26', {}).values():
        sq = r.get('squadra')
        if not sq:
            continue
        gf[sq] = gf.get(sq, 0) + (r.get('gol') or 0)
        if r['R'] == 'P':
            gs[sq] = gs.get(sq, 0) + (r.get('gs') or 0)
            pv[sq] = pv.get(sq, 0) + (r.get('pv') or 0)
    vive = {p['squadra'] for p in d['listone'] if p['squadra']}
    punteggio = {}
    for sq in vive:
        if sq in gf and pv.get(sq):
            punteggio[sq] = gf[sq] - gs.get(sq, 0) * 38.0 / pv[sq]
    return sorted(punteggio, key=lambda x: -punteggio[x])[:quante]


def applica_coppe(d, cfg):
    """Chi gioca in Europa ruota: i titolarissimi saltano qualche partita di
    campionato in piu', e in compenso le riserve ne giocano qualcuna in piu'.
    Lo storico non lo sa se la squadra le coppe le ha appena conquistate.
    """
    in_europa = set(cfg.get('europa') or [])
    for p in d['listone']:
        p['coppe'] = p['squadra'] in in_europa
        if not p['coppe']:
            continue
        perc = p.get('perc_titolarita')
        if perc is not None:
            perno = perc >= 85
        else:
            perno = (p.get('fvm') or 0) >= 60
        p['pv_proiettate'] = min(GIORNATE, p['pv_proiettate']
                                 * (0.94 if perno else 1.08))


# ------------------------------------------------------- cartellini
# In Serie A la quinta ammonizione fa saltare una giornata, e poi si riparte:
# in pratica una squalifica ogni cinque gialli, piu' una (a volte due) per ogni
# rosso. Non e' una regola che si puo' applicare all'indietro sui numeri di
# fantacalcio.it, che danno solo i totali di stagione, ma in avanti serve: dice
# quante giornate un giocatore rischia di perdere per come gioca, non per come
# si fa male.
GIALLI_PER_SQUALIFICA = 5.0
GIORNATE_PER_ROSSO = 1.3
FALLOSO = 0.28          # gialli a partita: sopra questa soglia e' un cattivo
PULITO = 0.10           # sotto, non lo vede mai nessun arbitro


def cartellini(d, cfg=None):
    """Ammonizioni ed espulsioni per giocatore: storiche, a partita, proiettate.

    I cartellini stanno nelle statistiche di stagione, non nei tabellini di
    giornata: fantacalcio.it nella pagina dei voti pubblica solo gol, assist,
    autoreti e rigori, e il fantavoto che stampa non li conta nemmeno. Quindi
    qui si lavora sui totali per stagione — che pero' bastano, perche' quello
    che interessa e' la frequenza, non il giorno esatto in cui e' successo.

    Il numero che conta davvero non e' quanti gialli ha preso, e' quanti ne
    prende per partita giocata: dodici gialli in trentacinque partite sono un
    difensore normale, otto in dodici partite sono un problema.
    """
    for p in d['listone']:
        per_stagione, amm, esp, pv = {}, 0.0, 0.0, 0.0
        for stagione, peso in [(STAGIONE, 1.0)] + PESI_STORICI:
            r = (d['stats'].get(stagione) or {}).get(p['id'])
            if not r or not r.get('pv'):
                continue
            voce = {'amm': r.get('amm') or 0, 'esp': r.get('esp') or 0,
                    'pv': r.get('pv') or 0}
            per_stagione[stagione] = voce
            # le stagioni vecchie contano meno, come per tutto il resto
            amm += voce['amm'] * peso
            esp += voce['esp'] * peso
            pv += voce['pv'] * peso

        totali = {'amm': sum(v['amm'] for v in per_stagione.values()),
                  'esp': sum(v['esp'] for v in per_stagione.values()),
                  'pv': sum(v['pv'] for v in per_stagione.values())}
        per_partita = (amm / pv) if pv >= 5 else None
        rossi_partita = (esp / pv) if pv >= 5 else None
        attese = (per_partita * p['pv_proiettate']) if per_partita is not None else None
        rossi_attesi = (rossi_partita * p['pv_proiettate']) if rossi_partita is not None else None

        p['cartellini'] = {
            'stagioni': per_stagione,
            'amm_totali': totali['amm'], 'esp_totali': totali['esp'],
            'pv_totali': totali['pv'],
            'amm_partita': round(per_partita, 3) if per_partita is not None else None,
            'esp_partita': round(rossi_partita, 4) if rossi_partita is not None else None,
            # la media su una stagione intera: e' la lettura con cui si ragiona
            # all'asta ("quello prende dieci gialli l'anno"), e a differenza di
            # amm_attese non dipende da quante partite ci si aspetta che giochi
            'amm_stagione': round(per_partita * GIORNATE, 1)
            if per_partita is not None else None,
            'esp_stagione': round(rossi_partita * GIORNATE, 2)
            if rossi_partita is not None else None,
            'stagioni_viste': len(per_stagione),
            'amm_attese': round(attese, 1) if attese is not None else None,
            'esp_attese': round(rossi_attesi, 2) if rossi_attesi is not None else None,
            'giornate_squalifica': round(
                (attese or 0) / GIALLI_PER_SQUALIFICA
                + (rossi_attesi or 0) * GIORNATE_PER_ROSSO, 1)
            if per_partita is not None else None,
            'indice': ('Falloso' if (per_partita or 0) >= FALLOSO
                       else 'Pulito' if per_partita is not None and per_partita <= PULITO
                       else 'Normale' if per_partita is not None else 'Ignoto'),
        }

    # la classifica interna al ruolo: essere il piu' falloso dei difensori vuol
    # dire un'altra cosa che esserlo fra gli attaccanti
    for ru in RUOLI:
        quelli = [q for q in d['listone']
                  if q['R'] == ru and q['cartellini']['amm_partita'] is not None]
        ordinati = sorted(quelli, key=lambda q: q['cartellini']['amm_partita'])
        for i, q in enumerate(ordinati):
            q['cartellini']['percentile_ruolo'] = (
                round(100.0 * i / max(1, len(ordinati) - 1)) if len(ordinati) > 1 else 50)


# ------------------------------------------------------- gol attesi (xG)
MINUTI_FIDUCIA = 450.0   # cinque partite piene: sotto, il dato conta a meta'
FRENO_XG = 0.55          # quanto dello scarto correggo davvero
TETTO_XG = 0.6           # non piu' di sei decimi di fantamedia, in nessun caso


def applica_understat(d, giocate=0):
    """Corregge la fantamedia attesa per la fortuna sotto porta.

    Il ragionamento in una riga: un gol vale tre punti di fantavoto, e se uno ne
    ha segnati due in piu' di quanti ne abbia costruiti, sei punti della sua
    fantamedia sono un prestito che il pallone si riprendera'.

    Tre cautele, perche' e' facile esagerare in senso opposto:

    - **solo i gol su azione.** I rigori li conta gia' la gerarchia dei
      rigoristi, e toglierli di nuovo qui vorrebbe dire punire due volte chi non
      li tira.
    - **la fiducia cresce coi minuti.** Su centoventi minuti lo scarto e'
      rumore; su cinque partite piene comincia a essere un dato.
    - **correggo poco piu' della meta'.** Certi attaccanti stanno stabilmente
      sopra il loro xG perche' calciano meglio degli altri: e' un merito, non
      un colpo di fortuna, e azzerarlo sarebbe sbagliato quanto ignorarlo.

    E vale solo per la parte di fantamedia che viene da questa stagione: alla
    terza giornata pesa il quindici per cento, e la correzione con lei.
    """
    dati = d.get('understat') or {}
    if not dati:
        return 0
    peso_corrente = dict(pesi_stagionali(giocate)).get(STAGIONE, 0.0)
    toccati = 0
    for p in d['listone']:
        v = dati.get(p['id'])
        p['xg'] = v
        if not v or not v.get('partite') or p['fm_att'] is None:
            continue
        # i fantapunti presi in prestito, per partita giocata
        prestito = (v['scarto_azione'] * 3.0 + v['scarto_assist'] * 1.0) / v['partite']
        fiducia = min(1.0, v['minuti'] / MINUTI_FIDUCIA)
        # per chi non ha storico in Serie A la fantamedia non viene dalle
        # stagioni passate — non ne ha — ma dai giocatori con quotazione simile,
        # che e' poco piu' di un'ipotesi. Li' quello che sta facendo adesso e'
        # l'unica cosa vera che sappiamo, e deve pesare quasi tutto.
        peso = max(peso_corrente, fiducia * 0.9) if p.get('stima') else peso_corrente
        correzione = -prestito * FRENO_XG * fiducia * peso
        correzione = max(-TETTO_XG, min(TETTO_XG, correzione))
        if abs(correzione) < 0.01:
            v['correzione'] = 0.0
            continue
        p['fm_att'] += correzione
        v['correzione'] = round(correzione, 3)
        toccati += 1
    return toccati


# ---------------------------------------------------------- rigoristi
# quanti rigori prende in media una squadra in una stagione, e come si dividono
# fra primo, secondo e terzo della gerarchia
RIGORI_A_SQUADRA = 5.0
REALIZZAZIONE = 0.78
QUOTA_ORDINE = {1: 0.80, 2: 0.15, 3: 0.05}


def correggi_rigori(d, rigoristi, giocate=0):
    """Toglie dalla fantamedia i rigori del passato e ci rimette quelli attesi.

    I rigori dell'anno scorso sono gia' dentro la fantamedia storica, ma la
    designazione cambia: chi tirava a Genova puo' non tirare a Milano, e viceversa
    un giocatore che non ne ha mai tirato uno puo' essere il rigorista designato
    della sua nuova squadra. Tolgo quindi il contributo storico e rimetto quello
    che ci si aspetta dalla gerarchia dichiarata oggi.
    """
    pesi = dict(pesi_stagionali(giocate))
    quota_rig = rigoristi.get('rigori', {})
    piazzati = rigoristi.get('piazzati', {})

    for p in d['listone']:
        p['rigorista'] = quota_rig.get(p['id'])
        p['piazzati'] = piazzati.get(p['id'])
        p['rigori_storici_fm'] = 0.0
        p['rigori_attesi_fm'] = 0.0
        if p.get('fm_att') is None:
            continue

        # il contributo storico, pesato come lo e' la fantamedia
        num = den = 0.0
        for stagione, w in pesi.items():
            r = d['stats'].get(stagione, {}).get(p['id'])
            if not r or not (r.get('pv') or 0) >= 3:
                continue
            num += w * (r.get('rig_seg') or 0)
            den += w * (r.get('pv') or 0)
        storico = (num / den * 3.0) if den > 0 and not p['stima'] else 0.0

        atteso = 0.0
        if p['rigorista']:
            quota = QUOTA_ORDINE.get(p['rigorista']['ordine'], 0.0)
            atteso = RIGORI_A_SQUADRA * quota * REALIZZAZIONE * 3.0 / GIORNATE

        p['rigori_storici_fm'] = storico
        p['rigori_attesi_fm'] = atteso
        p['fm_att'] = p['fm_att'] - storico + atteso


# --------------------------------------------------------------- SosFanta
def mappa_sos(d):
    """Abbina i dati SosFanta ai giocatori del listone.

    Restituisce tre dizionari: la probabilita' di giocare per ogni calciatore,
    chi e' indisponibile (con la giornata di rientro quando la redazione la dice)
    e la partita che ogni squadra ha davanti.
    """
    sos = d.get('sos') or {}
    squadre_sos = sos.get('squadre') or {}
    per = {}
    slug_di = {}
    for p in d['listone']:
        per[(chiave(p['team_slug']), chiave(p['nome']))] = p
        slug_di[chiave(p['team_slug'])] = p['team_slug']

    prob, indisp, partite, senza_nome = {}, {}, {}, []
    for nome_sq, s in squadre_sos.items():
        k = chiave(nome_sq)
        slug = slug_di.get(k)
        if not slug:
            continue
        partite[slug] = {
            'modulo': s['modulo'], 'avversario': slug_di.get(chiave(s['avversario'])),
            'avversario_nome': s['avversario'], 'in_casa': s['in_casa'],
            'data': s['data'], 'ora': s['ora'], 'ballottaggi': s['ballottaggi'],
        }
        for dove in ('titolari', 'panchina'):
            for g in s[dove]:
                q = per.get((k, chiave(g['nome'])))
                if q:
                    prob[q['id']] = {'perc': g['perc'], 'dove': dove}
                else:
                    senza_nome.append('%s / %s' % (nome_sq, g['nome']))
        for x in s['indisponibili']:
            q = per.get((k, chiave(x['nome'])))
            if q:
                indisp[q['id']] = dict(x, squadra=nome_sq, fonte='SosFanta')
            else:
                senza_nome.append('%s / %s' % (nome_sq, x['nome']))
    return prob, indisp, partite, senza_nome


def fattore_probabili(p, prob, stop_ora):
    """Quanto correggere le partite attese in base alle probabili di questa
    settimana. Il ritocco resta contenuto: la percentuale vale per una giornata
    sola, mentre lo storico parla di un'intera stagione. Per il portiere invece
    la gerarchia e' quasi assoluta, o gioca o non gioca."""
    if stop_ora:
        return 1.0, None
    v = prob.get(p['id'])
    perc = v['perc'] if v and v['perc'] else None
    titolare = bool(v and v['dove'] == 'titolari')
    if p['R'] == 'P':
        if titolare:
            return 0.85 + 0.15 * (perc or 90) / 100.0, perc
        return 0.30, perc
    if titolare:
        return 0.80 + 0.20 * (perc or 80) / 100.0, perc
    if v:                      # in panchina
        return 0.82, perc
    return 0.78, perc          # non nominato dalla redazione


# ------------------------------------------------------ rischio disponibilita'
def calcola_rischio(d, indisp_per_id, prob, giornata):
    schede = d['schede']
    oggi = datetime.date.today()
    for p in d['listone']:
        sch = schede.get(p['id'], {})
        p['eta'] = eta((sch.get('corrente') or {}).get('nascita'), oggi)
        p['altezza'] = (sch.get('corrente') or {}).get('altezza')
        # nel listone si chiama "Martinez L.": il nome per esteso serve a chi lo
        # cerca come lo chiamano tutti, cioe' Lautaro
        p['nome_completo'] = (sch.get('corrente') or {}).get('completo')

        perse = {}
        for stagione in ['2025-26', '2024-25']:
            s = (sch.get(stagione) or {}).get('stati')
            if s:
                lunghe, sparse, squal = blocchi_assenza(s)
                perse[stagione] = {'infortunio': lunghe, 'panchina': sparse,
                                   'squalifica': squal}
        p['assenze'] = perse

        # media pesata delle giornate perse per assenza lunga
        if perse:
            pesi = {'2025-26': 0.65, '2024-25': 0.35}
            tw = sum(pesi[s] for s in perse)
            inf_att = sum(pesi[s] * perse[s]['infortunio'] for s in perse) / tw
        else:
            inf_att = None

        # correttivo eta': dopo i 30 anni la fragilita' cresce
        if inf_att is not None and p['eta']:
            inf_att += max(0, p['eta'] - 30) * 0.5

        p['giornate_perse_attese'] = inf_att

        # stato attuale: chi e' fuori adesso e per quanto ancora.
        # Quando la redazione dice la giornata di rientro il conto e' esatto;
        # solo in mancanza di quella ricado sulla stima dal testo della nota.
        stato = indisp_per_id.get(p['id'])
        p['stato_attuale'] = dict(stato) if stato else None
        stop_ora = 0
        if stato:
            if stato.get('rientro'):
                stop_ora = max(0, int(stato['rientro']) - giornata)
            elif stato['tipo'].startswith('Infortun'):
                stop_ora = stima_stop(stato.get('nota'), oggi)
            else:
                stop_ora = 1
            p['stato_attuale']['turni_di_stop'] = stop_ora
            p['stato_attuale']['stimato'] = not stato.get('rientro')
        p['giornate_stop_ora'] = stop_ora

        if inf_att is None:
            p['rischio'] = 'Ignoto'
        elif inf_att >= 8:
            p['rischio'] = 'Alto'
        elif inf_att >= 3:
            p['rischio'] = 'Medio'
        else:
            p['rischio'] = 'Basso'

        # proiezione finale delle partite a voto: parto dall'empirico e correggo
        # solo con cio' che lo storico non puo' sapere, cioe' lo stop in corso e
        # le gerarchie attuali lette dalle probabili formazioni
        pv = p['pv_att'] or 0
        pv = max(0.0, pv - stop_ora * (pv / GIORNATE) * 1.6)
        fattore, perc = fattore_probabili(p, prob, stop_ora)
        p['perc_titolarita'] = perc
        p['dove_probabili'] = (prob.get(p['id']) or {}).get('dove')
        p['fuori_probabili'] = (p['dove_probabili'] != 'titolari') if not stop_ora else None
        p['pv_proiettate'] = min(GIORNATE, pv * fattore)


MESI_N = {'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
          'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11,
          'dicembre': 12}


def stima_stop(nota, oggi):
    """Legge la nota della redazione e stima quante giornate salta ancora.
    Se trova un mese di rientro calcola le settimane che mancano, altrimenti
    usa la gravita' descritta a parole."""
    t = (nota or '').lower()
    for mese, n in MESI_N.items():
        if mese in t:
            anno = oggi.year + (1 if n < oggi.month - 6 else 0)
            giorno = 5 if 'inizio' in t else 25 if 'fine' in t else 15
            try:
                rientro = datetime.date(anno, n, giorno)
            except ValueError:
                continue
            return max(0, round((rientro - oggi).days / 7.0))
    if any(k in t for k in ('crociato', 'tendine d\'achille', 'intervento chirurgico',
                            'operato')):
        return 12
    if any(k in t for k in ('lesione', 'stiramento', 'frattura')):
        return 5
    if any(k in t for k in ('affaticamento', 'risentimento', 'da valutare',
                            'fastidio', 'in dubbio')):
        return 1
    return 2


# ------------------------------------------------------------ forza squadre
def forza_squadre(d):
    """Attacco e difesa di ogni squadra: gol fatti e subiti la scorsa stagione,
    aggiornati con i risultati gia' visti quest'anno."""
    gf, gs, part = {}, {}, {}
    st25 = d['stats']['2025-26']
    for r in st25.values():
        sq = r['squadra']
        if not sq:
            continue
        gf[sq] = gf.get(sq, 0) + (r.get('gol') or 0)
        if r['R'] == 'P':
            gs[sq] = gs.get(sq, 0) + (r.get('gs') or 0)
            part[sq] = part.get(sq, 0) + (r.get('pv') or 0)

    sigle = {}
    for p in d['listone']:
        sigle[p['team_slug']] = p['squadra']

    att, dif = {}, {}
    for slug, sigla in sigle.items():
        n = max(1, part.get(sigla, 0))
        att[slug] = gf.get(sigla, 0) / 38.0 if sigla in gf else None
        dif[slug] = gs.get(sigla, 0) / n if sigla in gs else None
    noti_a = [v for v in att.values() if v]
    noti_d = [v for v in dif.values() if v]
    media_a = st.mean(noti_a) if noti_a else 1.3
    media_d = st.mean(noti_d) if noti_d else 1.3
    # le neopromosse non hanno storico: le metto un gradino sotto la media
    for slug in sigle:
        if not att[slug]:
            att[slug] = media_a * 0.80
        if not dif[slug]:
            dif[slug] = media_d * 1.20

    # aggiorno con i risultati della stagione in corso (peso crescente)
    gfc, gsc, ng = {}, {}, {}
    for m in d['calendario']:
        if not m['giocata'] or m['gol_casa'] is None:
            continue
        for a, b, gv, gp in ((m['casa'], m['trasferta'], m['gol_casa'], m['gol_trasferta']),
                             (m['trasferta'], m['casa'], m['gol_trasferta'], m['gol_casa'])):
            gfc[a] = gfc.get(a, 0) + gv
            gsc[a] = gsc.get(a, 0) + gp
            ng[a] = ng.get(a, 0) + 1
    for slug in sigle:
        n = ng.get(slug, 0)
        if n:
            w = min(0.6, n / 12.0)
            att[slug] = (1 - w) * att[slug] + w * (gfc[slug] / n)
            dif[slug] = (1 - w) * dif[slug] + w * (gsc[slug] / n)
    return {'attacco': att, 'difesa': dif, 'media_attacco': media_a, 'media_difesa': media_d}


# ------------------------------------------------------------------ valore
def calcola_valore(d, cfg, base_fm, base_mv):
    d['_rif_blocco'] = blocco_di_riferimento(d, cfg)
    for p in d['listone']:
        pv = p['pv_proiettate']
        v = (p['fm_att'] - base_fm[p['R']]) * pv
        p['valore_rendimento'] = v
        mod = 0.0
        if cfg['modificatore_difesa']:
            mod = valore_modificatore(p, d.get('_rif_blocco'))
        p['valore_modificatore'] = mod
        p['valore'] = v + mod


def mercato_multiplo(d, cfg):
    """Due stime di mercato indipendenti, riportate alla stessa scala.

    Il FVM ufficiale di fantacalcio.it e la quotazione di Fantapazz nascono da
    metodi diversi e non sempre concordano; dove divergono di molto c'e' quasi
    sempre qualcosa da capire, e per questo tengo entrambe e mostro la media.
    """
    grezzi = {'fc': {p['id']: p['fvm'] for p in d['listone'] if p['fvm']},
              'fp': abbina_fantapazz(d)}
    scalati = {k: scala_sui_crediti(v, d['listone'], cfg) for k, v in grezzi.items()}

    for p in d['listone']:
        p['mercato_fc'] = scalati['fc'].get(p['id'])
        p['mercato_fp'] = scalati['fp'].get(p['id'])
        stime = [v for v in (p['mercato_fc'], p['mercato_fp']) if v is not None]
        p['prezzo_mercato'] = int(round(sum(stime) / len(stime))) if stime else 0
        p['fonti_prezzo'] = len(stime)
        p['discordanza'] = (abs(p['mercato_fc'] - p['mercato_fp'])
                            if len(stime) == 2 else None)
    return len(grezzi['fp'])


def scala_sui_crediti(valori, listone, cfg):
    """Porta una lista di quotazioni sulla scala dei crediti realmente in palio.

    Ogni fonte usa una scala sua: il FVM di fantacalcio.it sommato sui giocatori che
    verranno davvero comprati fa il 118% del budget della lega, Fantapazz il 95%.
    Riportando entrambe al 100% diventano confrontabili fra loro e con i miei prezzi,
    e smettono di essere un indice astratto: diventano quanto quel giocatore costera'
    davvero nella tua asta.
    """
    totale = cfg['squadre'] * cfg['crediti']
    comprati = []
    for ru in RUOLI:
        lst = sorted([p for p in listone if p['R'] == ru and p['id'] in valori],
                     key=lambda x: -valori[x['id']])
        comprati += lst[:cfg['squadre'] * cfg['slot'][ru]]
    somma = sum(valori[p['id']] for p in comprati) or 1.0
    k = totale / float(somma)
    return {pid: int(round(v * k)) for pid, v in valori.items()}


def abbina_fantapazz(d):
    """Abbina i nomi di Fantapazz al listone. Le abbreviazioni non coincidono
    ("Martinez J." contro "Martinez Jo."), quindi dopo il confronto esatto provo
    il prefisso, ma solo quando il candidato e' uno solo: un abbinamento sbagliato
    qui falserebbe il prezzo."""
    import fanta_fantapazz as FP
    per_ns, per_n, per_sq = {}, {}, {}
    for p in d['listone']:
        per_ns[(chiave(p['squadra']), chiave(p['nome']))] = p
        per_n.setdefault(chiave(p['nome']), []).append(p)
        per_sq.setdefault(chiave(p['squadra']), []).append(p)

    def combacia(k, elenco):
        c = [p for p in elenco
             if chiave(p['nome']).startswith(k) or k.startswith(chiave(p['nome']))]
        return c[0] if len(c) == 1 else None

    out = {}
    for x in FP.parse():
        k, s = chiave(x['nome']), chiave(x['squadra'])
        q = per_ns.get((s, k))
        if q is None and len(per_n.get(k, [])) == 1:
            q = per_n[k][0]
        if q is None and s in per_sq:
            q = combacia(k, per_sq[s])
        if q is None:
            q = combacia(k, d['listone'])
        if q is not None and q['id'] not in out:
            out[q['id']] = x['quota']
    return out


def assegna_slot(d, cfg):
    """Lo slot e' la fascia che il giocatore occupa nel suo ruolo: con 10 squadre,
    i primi 10 attaccanti sono lo slot 1 (il centravanti titolare di ognuno), i
    successivi 10 lo slot 2, e cosi' via. Ordino per prezzo di mercato perche' e'
    cosi' che l'asta li mettera' in fila davvero."""
    sq = cfg['squadre']
    for ru in RUOLI:
        lst = sorted([p for p in d['listone'] if p['R'] == ru],
                     key=lambda x: (-x['prezzo_mercato'], -x['valore']))
        for i, p in enumerate(lst):
            s = i // sq + 1
            p['slot'] = s if s <= cfg['slot'][ru] else None
            p['rank_mercato'] = i + 1


def calcola_prezzi(d, cfg):
    listone = d['listone']
    sq, cred = cfg['squadre'], cfg['crediti']
    totale = sq * cred
    for ru in RUOLI:
        lst = sorted([p for p in listone if p['R'] == ru], key=lambda x: -x['valore'])
        k = sq * cfg['slot'][ru]
        sostituto = lst[k]['valore'] if k < len(lst) else 0.0
        vor = [max(0.0, p['valore'] - sostituto) for p in lst]
        somma = sum(vor) or 1.0
        allocabili = max(0.0, totale * cfg['quote'][ru] - sq * cfg['slot'][ru])
        for p, v in zip(lst, vor):
            p['vor'] = v
            p['prezzo'] = 1 if v <= 0 else int(round(1 + allocabili * v / somma))
            p['scarto'] = p['prezzo'] - p['prezzo_mercato']
            # il mercato sa cose che i numeri non sanno (gerarchie, mercato estivo,
            # voci di spogliatoio): il prezzo prudente e' la media pesata dei due
            p['prezzo_prudente'] = int(round(0.6 * p['prezzo'] + 0.4 * p['prezzo_mercato']))
        for i, p in enumerate(lst, 1):
            p['rank_ruolo'] = i
            p['titolarita'] = 'da rosa' if i <= k else 'fuori rosa'


# ------------------------------------------------------------------- forma
def calcola_forma(d):
    voti = d['voti']
    giornate = sorted((int(g) for g in voti), reverse=True)
    for p in d['listone']:
        storia = []
        for g in sorted(giornate):
            v = voti[str(g)].get(p['id'])
            storia.append({'g': g, **v} if v else {'g': g, 'v': None})
        p['giornate'] = storia
        fatte = [x for x in storia if x.get('fv') is not None]
        ultime = fatte[-5:]
        p['forma_fv'] = round(st.mean([x['fv'] for x in ultime]), 2) if ultime else None
        p['presenze_stagione'] = len(fatte)
        p['da_titolare'] = sum(1 for x in fatte if not x.get('sub'))


# ------------------------------------------------- consiglio di formazione
def prossima_giornata(d):
    fatte = [m['giornata'] for m in d['calendario'] if m['giocata']]
    return (max(fatte) + 1) if fatte else 1


def date_giornate(d):
    """La data di ogni giornata, per tradurre "rientro alla 6a" in una data vera."""
    out = {}
    for m in d['calendario']:
        if m.get('data') and m['giornata'] not in out:
            out[m['giornata']] = m['data']
    return out


def consigli_formazione(d, forza, giornata, prob, partite_sos):
    partite = [m for m in d['calendario'] if m['giornata'] == giornata]
    avversario = {}
    for m in partite:
        avversario[m['casa']] = (m['trasferta'], True, m['data'])
        avversario[m['trasferta']] = (m['casa'], False, m['data'])
    # dove SosFanta ha gia' la partita del turno, uso data e ora sue
    for slug, s in partite_sos.items():
        if s['avversario']:
            avversario[slug] = (s['avversario'], s['in_casa'],
                                '%s %s' % (s['data'], s['ora']))

    out = {}
    for p in d['listone']:
        info = avversario.get(p['team_slug'])
        if not info:
            out[p['id']] = {'gioca': False, 'motivo': 'turno di riposo'}
            continue
        avv, in_casa, data = info
        v = prob.get(p['id'])
        titolare_previsto = bool(v and v['dove'] == 'titolari')
        perc = v['perc'] if v else None

        # difficolta' dell'avversario, dal punto di vista del ruolo
        if p['R'] in ('P', 'D'):
            # a un difensore interessa quanto segna l'avversario
            rif = forza['attacco'].get(avv, forza['media_attacco'])
            diff = rif / forza['media_attacco']
        else:
            rif = forza['difesa'].get(avv, forza['media_difesa'])
            diff = rif / forza['media_difesa']
            diff = 2 - diff  # un avversario che subisce tanto e' una partita facile
        vantaggio_campo = 0.12 if in_casa else -0.12

        atteso = p['fm_att'] + vantaggio_campo
        # il voto secco serve a parte: il modificatore di difesa guarda quello,
        # non la fantamedia, e si muove in un intervallo molto piu' stretto
        mv_atteso = p['mv_att'] + vantaggio_campo * 0.4
        if p['R'] in ('P', 'D'):
            atteso -= (diff - 1) * 0.45
            mv_atteso -= (diff - 1) * 0.30
        else:
            atteso += (1 - diff) * 0.45
            mv_atteso += (1 - diff) * 0.20

        # chi rischia di non prendere voto vale meno a prescindere da quanto e'
        # bravo: pesare la fantamedia per la probabilita' di scendere in campo e'
        # il modo onesto di metterli in fila
        if titolare_previsto and perc:
            atteso -= (100 - perc) / 100.0 * 1.4
            mv_atteso -= (100 - perc) / 100.0 * 0.5
        elif v:                       # dato per panchinaro
            atteso -= 3.0 if p['R'] == 'P' else 1.6
            mv_atteso -= 1.2 if p['R'] == 'P' else 0.8
        else:                         # la redazione non lo nomina proprio
            atteso -= 3.5 if p['R'] == 'P' else 2.0
            mv_atteso -= 1.5 if p['R'] == 'P' else 1.0

        stato = p.get('stato_attuale')
        out[p['id']] = {
            'gioca': not bool(stato),
            'avversario': avv, 'in_casa': in_casa, 'data': data,
            'titolare_previsto': titolare_previsto,
            'perc': perc,
            'dove': (v or {}).get('dove'),
            'difficolta': round(diff, 2),
            'atteso': round(atteso, 2),
            'mv_atteso': round(mv_atteso, 2),
            'stato': stato,
            'ballottaggi': [b for b in partite_sos.get(p['team_slug'], {})
                            .get('ballottaggi', [])
                            if chiave(p['nome']) in (chiave(b['favorito']),
                                                     chiave(b['sfidante']))],
        }
    return out


# -------------------------------------------------------------------- note
SOGLIA_RACCONTO = 0.9   # gol di scarto sotto i quali non vale la pena parlarne


def nota_xg(p):
    """La riga sui gol attesi, quando c'e' qualcosa da dire.

    Non la scrivo mai per scarti piccoli: su due partite mezzo gol di differenza
    e' come parlare del tempo."""
    v = p.get('xg') or {}
    if not v.get('partite') or v['minuti'] < 120:
        return None
    scarto = v['scarto_azione']
    if abs(scarto) < SOGLIA_RACCONTO:
        return None
    if scarto > 0:
        return ("Ha segnato %.1f gol più di quanti ne costruisce: parte di "
                "questo rendimento non si ripeterà" % scarto)
    return ("Ha costruito %.1f gol più di quanti ne ha segnati: è in credito "
            "col pallone" % -scarto)


def costruisci_note(p):
    n = []
    stato = p.get('stato_attuale')
    if stato:
        salta = p.get('giornate_stop_ora') or 0
        if stato.get('rientro'):
            coda = ': atteso in campo dalla %da giornata' % stato['rientro']
        elif salta:
            coda = ': stimate %d giornate di stop' % salta
        else:
            coda = ''
        n.append('OGGI %s%s' % (stato['tipo'].upper(), coda))
    r = p['storico'].get('2025-26')
    if p['stima']:
        n.append('Nessuno storico in Serie A: valore stimato')
    if r:
        if (r.get('rig_tir') or 0) >= 3:
            n.append('Rigorista (%g su %g)' % (r.get('rig_seg') or 0, r['rig_tir']))
        if (r.get('gol') or 0) >= 10:
            n.append('%d gol lo scorso anno' % int(r['gol']))
        if (r.get('ass') or 0) >= 6:
            n.append('%d assist lo scorso anno' % int(r['ass']))
        if (r.get('pv') or 0) >= 32:
            n.append('Sempre presente')
        if (r.get('amm') or 0) >= 10 or (r.get('esp') or 0) >= 2:
            n.append('Falloso: %d gialli%s' % (
                int(r.get('amm') or 0),
                ' e %d rossi' % int(r['esp']) if (r.get('esp') or 0) else ''))
        if r.get('squadra') and r['squadra'] != p['squadra']:
            n.append('Cambio squadra: era al %s' % r['squadra'])
    c = p.get('cartellini') or {}
    if (c.get('giornate_squalifica') or 0) >= 1.5:
        # dire "tot gialli a partita" quando il rischio viene dai rossi e' una
        # mezza verita': cito il motivo vero
        pezzi = ['%.2f gialli a partita' % c['amm_partita']]
        if (c.get('esp_attese') or 0) >= 0.25:
            pezzi.append('%.1f espulsioni attese' % c['esp_attese'])
        n.append('Rischia %.1f giornate di squalifica: %s'
                 % (c['giornate_squalifica'], ' e '.join(pezzi)))
    elif c.get('indice') == 'Pulito' and (c.get('pv_totali') or 0) >= 40:
        n.append('Non prende cartellini: %g gialli in %d partite'
                 % (c['amm_totali'], int(c['pv_totali'])))
    xg = nota_xg(p)
    if xg:
        n.append(xg)
    a = p.get('assenze', {}).get('2025-26')
    if a and a['infortunio'] >= 5:
        n.append('%d giornate consecutive fuori nel 25/26, probabile infortunio'
                 % a['infortunio'])
    if a and a['infortunio'] < 5 and a['panchina'] >= 15:
        n.append('Nel 25/26 fuori %d giornate senza infortuni: riserva'
                 % a['panchina'])
    if p.get('perc_titolarita') and p.get('dove_probabili') == 'titolari':
        if p['perc_titolarita'] < 70:
            n.append('Titolare in dubbio: dato al %d%%' % p['perc_titolarita'])
    elif p.get('fuori_probabili'):
        n.append('Dato in panchina per la prossima giornata'
                 if p.get('dove_probabili') else 'Non nelle liste della prossima giornata')
    if p.get('eta') and p['eta'] >= 33:
        n.append('%d anni' % p['eta'])
    return n


# -------------------------------------------------------------------- main
def elabora():
    d = json.load(open(os.path.join(DATI, 'dataset.json'), encoding='utf-8'))
    cfg = carica_config()

    g = prossima_giornata(d)
    # formazioni e infermeria arrivano da SosFanta: ha la percentuale di
    # titolarita', i ballottaggi e la giornata di rientro degli infortunati
    prob, indisp_per_id, partite_sos, non_abbinati = mappa_sos(d)

    # la lista da mostrare in Infermeria: prima SosFanta, poi cio' che aggiunge
    # fantacalcio.it (in particolare squalificati e diffidati, che SosFanta non
    # elenca separatamente)
    per_nome = {}
    for p in d['listone']:
        per_nome.setdefault(chiave(p['nome']), []).append(p)
    infermeria = []
    gia = set()
    date_g = date_giornate(d)
    for pid, x in indisp_per_id.items():
        r = x.get('rientro')
        infermeria.append({'squadra': x['squadra'], 'tipo': x['tipo'], 'nome': x['nome'],
                           'nota': x['nota'], 'rientro': r,
                           'turni': max(0, r - g) if r else None,
                           'data_rientro': date_g.get(r) if r else None,
                           'fonte': 'SosFanta'})
        gia.add((chiave(x['squadra']), chiave(x['nome'])))
    SINGOLARE = {'Infortunati': 'Infortunato', 'Squalificati': 'Squalificato',
                 'Diffidati': 'Diffidato'}
    diffidati = set()
    for x in d['indisponibili']:
        if x['tipo'].startswith('Diffid'):
            diffidati.add((chiave(x['squadra']), chiave(x['nome'])))
    for x in d['indisponibili']:
        if (chiave(x['squadra']), chiave(x['nome'])) in gia:
            continue
        voce = {'squadra': x['squadra'], 'tipo': SINGOLARE.get(x['tipo'], x['tipo']),
                'nome': x['nome'], 'nota': x['nota'], 'rientro': None,
                'turni': None, 'data_rientro': None, 'fonte': 'fantacalcio.it'}
        infermeria.append(voce)
        if voce['tipo'] == 'Squalificato':
            cand = [c for c in per_nome.get(chiave(x['nome']), [])
                    if chiave(c['team_slug']) == chiave(x['squadra'])]
            if len(cand) == 1 and cand[0]['id'] not in indisp_per_id:
                indisp_per_id[cand[0]['id']] = dict(voce)

    giocate = max(0, g - 1)
    base_fm, base_mv = calcola_attese(d, giocate)
    rigoristi = {}
    perc_xg = os.path.join(DATI, 'understat.json')
    if os.path.exists(perc_xg):
        try:
            with open(perc_xg, encoding='utf-8') as f:
                d['understat'] = json.load(f)
        except ValueError:
            d['understat'] = {}

    perc_rig = os.path.join(DATI, 'rigoristi.json')
    if os.path.exists(perc_rig):
        try:
            rigoristi = json.load(open(perc_rig, encoding='utf-8'))
        except ValueError:
            rigoristi = {}
    correggi_rigori(d, rigoristi, giocate)
    mossi_xg = applica_understat(d, giocate)
    calcola_rischio(d, indisp_per_id, prob, g)
    # dopo il rischio, perche' la titolarita' delle probabili dice chi e' un perno
    # e chi no, e prima del valore, perche' le presenze sono meta' del valore
    applica_coppe(d, cfg)
    cartellini(d, cfg)
    calcola_valore(d, cfg, base_fm, base_mv)
    # il livello di giudizio corregge il valore per cio' che lo storico non sa:
    # il cambio di contesto e la designazione rigori che non viaggia col giocatore
    red = {}
    perc_red = os.path.join(DATI, 'redazioni.json')
    if os.path.exists(perc_red):
        try:
            red = json.load(open(perc_red, encoding='utf-8'))
        except ValueError:
            red = {}
    G.analizza(d, base_fm, base_mv, red)
    quanti_fp = mercato_multiplo(d, cfg)
    assegna_slot(d, cfg)
    calcola_prezzi(d, cfg)
    calcola_forma(d)
    forza = forza_squadre(d)
    consigli = consigli_formazione(d, forza, g, prob, partite_sos)
    for p in d['listone']:
        # il diffidato gioca, ma al prossimo giallo salta: non e' un'assenza,
        # e' un rischio da sapere prima di schierarlo
        # la diffida in due modi: quella dichiarata da SosFanta, e quella che
        # conto da solo sui cartellini di giornata. La seconda arriva prima —
        # la redazione la pubblica quando le pare, i gialli invece li vedo io
        gialli = sum(x.get('amm') or 0 for x in (p.get('giornate') or []))
        rossi = sum(x.get('esp') or 0 for x in (p.get('giornate') or []))
        p['gialli_stagione'] = gialli
        p['rossi_stagione'] = rossi
        p['al_quinto'] = int(GIALLI_PER_SQUALIFICA - (gialli % GIALLI_PER_SQUALIFICA))             if gialli else None
        dichiarato = (chiave(p['squadra']), chiave(p['nome'])) in diffidati
        p['diffidato'] = dichiarato or (gialli > 0
                                        and gialli % GIALLI_PER_SQUALIFICA == 4)
        p['diffida_da'] = ('la redazione' if dichiarato
                           else 'i cartellini' if p['diffidato'] else None)
        p['note'] = costruisci_note(p)

    out = {
        'aggiornato': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
        'config': cfg,
        'base_fm': base_fm, 'base_mv': base_mv,
        'prossima_giornata': g,
        'giornate_giocate': giocate,
        'blocco_riferimento': d.get('_rif_blocco'),
        'europa_suggerite': indizio_europa(d),
        'date_giornate': date_giornate(d),
        'fonti_prezzo': {'fantacalcio.it (FVM)': sum(1 for p in d['listone']
                                                    if p.get('mercato_fc')),
                         'Fantapazz (quotazione)': quanti_fp},
        'redazioni': {'brani': red.get('articoli', 0),
                      'citati': len(red.get('giocatori', {}))},
        'forza': forza,
        'consigli': consigli,
        'giocatori': d['listone'],
        'indisponibili': infermeria,
        'calendario': d['calendario'],
        'partite_sos': partite_sos,
        'indisponibili_non_abbinati': non_abbinati,
    }
    json.dump(out, open(os.path.join(DATI, 'valutazioni.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    return out


def main():
    out = elabora()
    print('aggiornato %s - prossima giornata %d' % (out['aggiornato'], out['prossima_giornata']))
    print('indisponibili non abbinati: %s' % (out['indisponibili_non_abbinati'] or 'nessuno'))
    for ru in RUOLI:
        lst = sorted([p for p in out['giocatori'] if p['R'] == ru], key=lambda x: -x['valore'])
        print('\n== %s' % RUOLO_NOME[ru])
        for p in lst[:8]:
            print('  %-20s %-4s prezzo=%4d mercato=%4d  fm=%.2f pv=%.1f rischio=%-6s %s'
                  % (p['nome'], p['squadra'], p['prezzo'], p['prezzo_mercato'],
                     p['fm_att'], p['pv_proiettate'], p['rischio'],
                     '; '.join(p['note'][:2])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
