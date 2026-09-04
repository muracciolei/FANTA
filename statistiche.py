# -*- coding: utf-8 -*-
"""Le classifiche: chi segna, chi fa assist, chi prende cartellini, chi non salta mai.

Una pagina di statistiche puo' essere due cose molto diverse. Puo' essere un elenco
di numeri — e allora tanto vale guardare il sito — oppure puo' rispondere alle
domande che uno si fa davvero: chi rende piu' di quanto costa, chi e' il piu'
falloso del suo ruolo, chi in questa stagione sta andando meglio dell'anno scorso.
Qui costruisco le seconde.

Due scelte che vale la pena spiegare.

**Per partita, non in totale.** Le classifiche assolute premiano sempre chi ha
giocato di piu': un attaccante con dieci gol in trentasei partite sta davanti a uno
con otto gol in quindici, e non e' quello che serve sapere all'asta. Quindi ogni
classifica ha la sua versione per partita giocata, con una soglia minima di
presenze sotto la quale il dato non e' un dato ma un caso.

**I cartellini si leggono in due modi.** Per le stagioni passate ci sono i totali.
Per quella in corso c'e' il dettaglio di giornata, ma nascosto: fantacalcio.it il
cartellino non lo pubblica come dato, lo attacca al voto come classe CSS
(player-grade yellow-card). Il fantavoto che stampa non lo conta nemmeno — il malus
lo mette la lega al momento del calcolo — quindi qui i cartellini di giornata si
sommano a parte. Il totale ricostruito coincide con quello dichiarato per tutti e
592 i calciatori: e' un dato letto, non stimato.
"""
import radice

RUOLI = ['P', 'D', 'C', 'A']
RUOLO_NOME = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti',
              'A': 'Attaccanti'}
MINIME = {'stagione': 8, 'corrente': 2}


def stagioni(d):
    """Le stagioni disponibili, dalla piu' recente."""
    viste = set()
    for p in d['giocatori']:
        viste.update(k for k, v in (p.get('storico') or {}).items() if v)
        if p.get('corrente'):
            viste.add(d['config'].get('stagione') or 'in corso')
    return sorted(viste, reverse=True)


def riga(p, stagione, in_corso):
    """I numeri di un giocatore in una stagione, o None se non l'ha giocata."""
    r = p['corrente'] if in_corso else (p.get('storico') or {}).get(stagione)
    if not r or not r.get('pv'):
        return None
    pv = float(r['pv'])
    return {
        'p': p, 'nome': p['nome'], 'squadra': r.get('squadra') or p['squadra'],
        'R': p['R'], 'pv': pv, 'mv': r.get('mv'), 'fm': r.get('fm'),
        'gol': r.get('gol') or 0, 'ass': r.get('ass') or 0, 'gs': r.get('gs') or 0,
        'amm': r.get('amm') or 0, 'esp': r.get('esp') or 0,
        'rig_seg': r.get('rig_seg') or 0, 'rig_tir': r.get('rig_tir') or 0,
        'rig_par': r.get('rig_par') or 0,
        'gol_pg': (r.get('gol') or 0) / pv,
        'ass_pg': (r.get('ass') or 0) / pv,
        'bonus_pg': ((r.get('gol') or 0) + (r.get('ass') or 0)) / pv,
        'gs_pg': (r.get('gs') or 0) / pv,
        'amm_pg': (r.get('amm') or 0) / pv,
        'cart_pesati': (r.get('amm') or 0) + 3 * (r.get('esp') or 0),
        'cart_pg': ((r.get('amm') or 0) + 3 * (r.get('esp') or 0)) / pv,
    }


def tabellone(d, stagione, in_corso, ruolo=None, squadra=None, minime=None):
    """Tutte le righe di una stagione, filtrate e pronte per essere ordinate."""
    minime = MINIME['corrente' if in_corso else 'stagione'] if minime is None else minime
    fuori = []
    for p in d['giocatori']:
        if ruolo and p['R'] != ruolo:
            continue
        if squadra and p['squadra'] != squadra:
            continue
        r = riga(p, stagione, in_corso)
        if r and r['pv'] >= minime:
            fuori.append(r)
    return fuori


# ------------------------------------------------------------- classifiche
# nome, etichetta, campo, come si legge, se piu' alto e' meglio, ruoli a cui si
# applica (None = tutti), e la soglia di presenze sotto la quale non ha senso
CLASSIFICHE = [
    ('gol', 'Gol', 'gol', '%g', True, None),
    ('gol_pg', 'Gol a partita', 'gol_pg', '%.2f', True, None),
    ('ass', 'Assist', 'ass', '%g', True, None),
    ('ass_pg', 'Assist a partita', 'ass_pg', '%.2f', True, None),
    ('bonus_pg', 'Bonus a partita', 'bonus_pg', '%.2f', True, None),
    ('fm', 'Fantamedia', 'fm', '%.2f', True, None),
    ('mv', 'Media voto', 'mv', '%.2f', True, None),
    ('pv', 'Presenze', 'pv', '%g', True, None),
    ('amm', 'Ammonizioni', 'amm', '%g', True, None),
    ('amm_pg', 'Gialli a partita', 'amm_pg', '%.2f', True, None),
    ('esp', 'Espulsioni', 'esp', '%g', True, None),
    ('cart_pg', 'Cartellini pesati a partita', 'cart_pg', '%.2f', True, None),
    ('puliti', 'I piu’ corretti', 'cart_pg', '%.2f', False, None),
    ('rig_seg', 'Rigori segnati', 'rig_seg', '%g', True, None),
    ('rig_par', 'Rigori parati', 'rig_par', '%g', True, 'P'),
    ('gs', 'Gol subiti', 'gs', '%g', False, 'P'),
    ('gs_pg', 'Gol subiti a partita', 'gs_pg', '%.2f', False, 'P'),
]


def classifica(righe, chiave, quanti=15):
    """Una classifica sola, gia' ordinata e tagliata."""
    voce = next((c for c in CLASSIFICHE if c[0] == chiave), None)
    if not voce:
        return None
    _, etichetta, campo, formato, alto_meglio, solo_ruolo = voce
    dentro = [r for r in righe if r.get(campo) is not None
              and (not solo_ruolo or r['R'] == solo_ruolo)]
    if chiave in ('puliti',):
        # essere corretti conta solo se giochi: chi entra dieci minuti non vince
        dentro = [r for r in dentro if r['pv'] >= 15]
    dentro.sort(key=lambda r: (-r[campo] if alto_meglio else r[campo], -r['pv']))
    return {'chiave': chiave, 'etichetta': etichetta, 'campo': campo,
            'formato': formato, 'alto_meglio': alto_meglio,
            'righe': dentro[:quanti], 'quanti_totali': len(dentro)}


def tutte(righe, quanti=15, chiavi=None):
    fuori = []
    for c in CLASSIFICHE:
        if chiavi and c[0] not in chiavi:
            continue
        cl = classifica(righe, c[0], quanti)
        if cl and cl['righe']:
            fuori.append(cl)
    return fuori


# ------------------------------------------------------------- per giornata
def per_giornata(d, giornata, quanti=15):
    """Il tabellino di una giornata: chi ha fatto il fantavoto piu' alto."""
    fuori = []
    for p in d['giocatori']:
        for x in p.get('giornate') or []:
            if x['g'] == giornata and x.get('fv') is not None:
                fuori.append({'p': p, 'nome': p['nome'], 'squadra': p['squadra'],
                              'R': p['R'], 'v': x.get('v'), 'fv': x['fv'],
                              'sub': x.get('sub'),
                              'gol': x.get('gol') or 0, 'ass': x.get('ass') or 0,
                              'gs': x.get('gs') or 0,
                              'rig_par': x.get('rig_par') or 0,
                              'mvp': x.get('mvp') or 0,
                              'amm': x.get('amm') or 0,
                              'esp': x.get('esp') or 0})
    fuori.sort(key=lambda r: -r['fv'])
    return fuori[:quanti]


def andamento(p):
    """La stagione in corso giornata per giornata, buchi compresi."""
    return [{'g': x['g'], 'v': x.get('v'), 'fv': x.get('fv'),
             'sub': x.get('sub'), 'gioca': x.get('v') is not None,
             'amm': x.get('amm') or 0, 'esp': x.get('esp') or 0,
             'bonus': sum(1 for k in ('gol', 'ass', 'rig_par') if x.get(k)),
             'malus': sum(1 for k in ('gs', 'autogol', 'rig_sba') if x.get(k))}
            for x in (p.get('giornate') or [])]


def cartellini_giornate(p):
    """In quali giornate ha preso il cartellino, quest'anno.

    Serve a distinguere due cose che il totale confonde: chi ne prende uno ogni
    tanto e chi ne ha presi tre nelle ultime quattro partite ed e' a un passo
    dalla squalifica."""
    fuori = []
    for x in p.get('giornate') or []:
        if x.get('amm') or x.get('esp'):
            fuori.append({'g': x['g'], 'tipo': 'rosso' if x.get('esp') else 'giallo',
                          'v': x.get('v')})
    return fuori


# ------------------------------------------------------------- confronti
def confronto_ruolo(d, p, stagione, in_corso):
    """Come sta il giocatore rispetto agli altri del suo ruolo, in percentili."""
    righe = tabellone(d, stagione, in_corso, ruolo=p['R'])
    mia = next((r for r in righe if r['p']['id'] == p['id']), None)
    if not mia or len(righe) < 5:
        return None
    fuori = {}
    for campo, etichetta, alto_meglio in [
            ('fm', 'Fantamedia', True), ('mv', 'Media voto', True),
            ('bonus_pg', 'Bonus a partita', True), ('pv', 'Presenze', True),
            ('amm_pg', 'Gialli a partita', False)]:
        valori = sorted([r[campo] for r in righe if r.get(campo) is not None])
        if not valori or mia.get(campo) is None:
            continue
        sotto = sum(1 for v in valori if v < mia[campo])
        perc = round(100.0 * sotto / max(1, len(valori) - 1))
        fuori[campo] = {'etichetta': etichetta, 'valore': mia[campo],
                        'percentile': perc if alto_meglio else 100 - perc,
                        'mediana': valori[len(valori) // 2],
                        'alto_meglio': alto_meglio}
    return fuori


def squadre(d, stagione, in_corso):
    """La stessa storia vista dalle squadre: gol fatti, subiti, cartellini."""
    fuori = {}
    for p in d['giocatori']:
        r = riga(p, stagione, in_corso)
        if not r:
            continue
        s = fuori.setdefault(r['squadra'], {
            'squadra': r['squadra'], 'gol': 0, 'ass': 0, 'amm': 0, 'esp': 0,
            'gs': 0, 'pv_portieri': 0, 'giocatori': 0, 'fm': [], 'rig_seg': 0})
        s['gol'] += r['gol']
        s['ass'] += r['ass']
        s['amm'] += r['amm']
        s['esp'] += r['esp']
        s['rig_seg'] += r['rig_seg']
        s['giocatori'] += 1
        if r['fm'] is not None:
            s['fm'].append(r['fm'])
        if r['R'] == 'P':
            s['gs'] += r['gs']
            s['pv_portieri'] += r['pv']
    for s in fuori.values():
        s['fm_media'] = round(sum(s['fm']) / len(s['fm']), 2) if s['fm'] else None
        s['gs_partita'] = (round(s['gs'] / s['pv_portieri'], 2)
                           if s['pv_portieri'] else None)
        s['cartellini'] = s['amm'] + 3 * s['esp']
        del s['fm']
    return sorted(fuori.values(), key=lambda s: -s['gol'])


# ------------------------------------------------------- da dove vengono i punti
# I pesi del regolamento. Non li ho copiati da un sito: li ho ritrovati facendo
# una regressione su (fantamedia - media voto) x presenze per 625 giocatori di due
# stagioni, e sono usciti +2,89 il gol, +1,01 l'assist, -0,49 l'ammonizione,
# -1,0 il gol subito, +2,98 il rigore parato. Cioe' esattamente il regolamento.
# Serviva saperlo per una ragione precisa: **la fantamedia della fonte i cartellini
# li conta gia'**. Toglierli un'altra volta nel modello avrebbe punito due volte
# gli stessi giocatori.
PESI = [
    ('gol', 'Gol', 3.0),
    ('rig_seg', 'Rigori segnati', 0.0),      # gia' dentro i gol, non li conto due volte
    ('ass', 'Assist', 1.0),
    ('rig_par', 'Rigori parati', 3.0),
    ('gs', 'Gol subiti', -1.0),
    ('amm', 'Ammonizioni', -0.5),
    ('esp', 'Espulsioni', -1.0),
]


def scomposizione(r):
    """Da dove arriva la fantamedia: quanto dal voto, quanto dai bonus, quanto
    perso in cartellini. Tutto in punti di fantamedia, cioe' per partita giocata.

    E' il numero che spiega i casi strani: un difensore con 6,20 di media voto e
    6,05 di fantamedia non e' sfortunato, e' uno che si mangia un quarto di punto
    a partita in ammonizioni.
    """
    if not r or not r.get('pv') or r.get('mv') is None:
        return None
    voci, totale = [], 0.0
    for campo, etichetta, peso in PESI:
        if not peso or not r.get(campo):
            continue
        punti = peso * r[campo] / r['pv']
        totale += punti
        voci.append({'campo': campo, 'etichetta': etichetta,
                     'quanti': r[campo], 'punti': round(punti, 3)})
    voci.sort(key=lambda v: -abs(v['punti']))
    atteso = r['mv'] + totale
    return {
        'voto': round(r['mv'], 2),
        'voci': voci,
        'bonus': round(sum(v['punti'] for v in voci if v['punti'] > 0), 2),
        'malus': round(sum(v['punti'] for v in voci if v['punti'] < 0), 2),
        'cartellini': round(sum(v['punti'] for v in voci
                                if v['campo'] in ('amm', 'esp')), 2),
        'fantamedia_ricostruita': round(atteso, 2),
        'fantamedia_dichiarata': round(r['fm'], 2) if r.get('fm') is not None else None,
        'scarto': round(atteso - r['fm'], 2) if r.get('fm') is not None else None,
    }


def costo_cartellini(p):
    """Quanto costano i cartellini in una stagione intera, in fantapunti.

    Mezzo punto per giallo e uno per rosso sembrano niente. Su un difensore da
    dieci gialli l'anno sono cinque fantapunti buttati, piu' una o due giornate
    di squalifica: vale quanto un gol e mezzo di un attaccante.
    """
    c = p.get('cartellini') or {}
    if c.get('amm_attese') is None:
        return None
    punti = 0.5 * (c['amm_attese'] or 0) + 1.0 * (c['esp_attese'] or 0)
    return {'punti': round(punti, 1),
            'gialli': c['amm_attese'], 'rossi': c['esp_attese'],
            'giornate': c.get('giornate_squalifica'),
            'indice': c.get('indice'),
            'percentile_ruolo': c.get('percentile_ruolo')}
