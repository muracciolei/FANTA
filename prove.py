# -*- coding: utf-8 -*-
"""Controlli rapidi: si lancia dopo ogni modifica e dice se qualcosa si e' rotto.

Non e' una suite di test seria e non pretende di esserlo. E' la rete che serve a me
quando cambio il motore o l'interfaccia: verifica che i dati siano coerenti, che le
funzioni di calcolo non esplodano su casi limite, e che i numeri chiave stiano dentro
intervalli plausibili. Se una riga dice KO, qualcosa e' cambiato in peggio.

    python prove.py
"""
import io
import json
import os
import sys

import radice

BASE = radice.cartella()
DATI = os.path.join(BASE, 'dati')

esiti = []


def prova(nome, condizione, dettaglio=''):
    esiti.append((bool(condizione), nome, dettaglio))
    print('  %s  %-52s %s' % ('ok' if condizione else 'KO', nome, dettaglio))
    return bool(condizione)


def carica():
    with io.open(os.path.join(DATI, 'valutazioni.json'), encoding='utf-8') as f:
        return json.load(f)


def dati_di_base(d):
    print('\ndati')
    g = d['giocatori']
    prova('almeno 500 calciatori', len(g) >= 500, '%d' % len(g))
    prova('venti squadre', len({p['squadra'] for p in g}) == 20)
    prova('tutti hanno un ruolo valido',
          all(p['R'] in ('P', 'D', 'C', 'A') for p in g))
    prova('tutti hanno un prezzo non negativo',
          all((p.get('prezzo') or 0) >= 0 for p in g))
    prova('nessun prezzo oltre il budget della lega',
          max(p['prezzo'] for p in g) <= d['config']['crediti'],
          'massimo %d' % max(p['prezzo'] for p in g))
    prova('le presenze proiettate stanno fra 0 e 38',
          all(0 <= p['pv_proiettate'] <= 38 for p in g))
    prova('le fantamedie attese sono plausibili',
          all(2.0 <= p['fm_att'] <= 12.0 for p in g),
          'da %.2f a %.2f' % (min(p['fm_att'] for p in g), max(p['fm_att'] for p in g)))


def voti_e_giornate(d):
    print('\nvoti di giornata')
    voti = [x for p in d['giocatori'] for x in (p.get('giornate') or [])
            if x.get('fv') is not None]
    prova('ci sono voti di giornata', len(voti) > 100, '%d voti' % len(voti))
    prova('i voti secchi stanno fra 1 e 10',
          all(1 <= x['v'] <= 10 for x in voti if x.get('v') is not None))
    prova('i fantavoti stanno fra -5 e 25',
          all(-5 <= x['fv'] <= 25 for x in voti),
          'massimo %.1f' % max(x['fv'] for x in voti))
    # il caso che aveva rotto tutto: un fantavoto alto schiacciato a un decimo
    alti = [x for x in voti if x['fv'] >= 10]
    prova('i fantavoti alti sono sopravvissuti alla scala', len(alti) > 0,
          '%d sopra il 10' % len(alti))


def cartellini(d):
    print('\ncartellini')
    g = d['giocatori']
    prova('tutti hanno il blocco cartellini', all(p.get('cartellini') for p in g))
    noti = [p for p in g if p['cartellini'].get('amm_partita') is not None]
    prova('la media gialli e nota per almeno 300 giocatori', len(noti) >= 300,
          '%d' % len(noti))
    prova('i gialli a partita sono plausibili',
          all(0 <= p['cartellini']['amm_partita'] <= 1.0 for p in noti),
          'massimo %.2f' % max(p['cartellini']['amm_partita'] for p in noti))
    prova('le giornate di squalifica attese sono plausibili',
          all(0 <= (p['cartellini'].get('giornate_squalifica') or 0) <= 12
              for p in noti))
    somma = sum(p['cartellini']['amm_totali'] for p in g)
    prova('i gialli storici sono tanti quanti ne sono stati dati', somma > 2000,
          '%g in quattro stagioni' % somma)

    # la riga di un ammonito ha una classe CSS diversa e per un pezzo veniva
    # scartata in blocco: dieci giocatori a giornata, sempre gli stessi
    per_giornata = {}
    for p in g:
        for x in p.get('giornate') or []:
            if x.get('v') is not None:
                per_giornata.setdefault(x['g'], []).append(x)
    if per_giornata:
        piu_piccola = min(len(v) for v in per_giornata.values())
        prova('nessuna giornata perde righe', piu_piccola >= 300,
              'la piu magra ha %d voti' % piu_piccola)
        gialli = sum(x.get('amm') or 0 for v in per_giornata.values() for x in v)
        prova('i cartellini di giornata ci sono', gialli > 0,
              '%d gialli in %d giornate' % (gialli, len(per_giornata)))
        # controprova: il totale ricostruito deve coincidere con quello dichiarato
        storti = 0
        for p in g:
            dichiarato = (p.get('corrente') or {}).get('amm') or 0
            dedotto = sum(x.get('amm') or 0 for x in (p.get('giornate') or []))
            if abs(dichiarato - dedotto) > 0.01:
                storti += 1
        prova('i gialli di giornata quadrano con i totali di stagione', storti == 0,
              '%d discordanti' % storti)
        conteggiati = [p for p in g if p.get('gialli_stagione')]
        prova('il conto alla squalifica c e per tutti gli ammoniti',
              all(1 <= p['al_quinto'] <= 5 for p in conteggiati),
              '%d ammoniti' % len(conteggiati))
        prova('chi e a quattro gialli risulta diffidato',
              all(p['diffidato'] for p in g if (p.get('gialli_stagione') or 0) % 5 == 4))


def scomposizione(d):
    print('\nscomposizione della fantamedia')
    import statistiche as S
    scarti = []
    for p in d['giocatori']:
        r = (p.get('storico') or {}).get('2025-26')
        if r and (r.get('pv') or 0) >= 10:
            sc = S.scomposizione(r)
            if sc and sc['scarto'] is not None:
                scarti.append(abs(sc['scarto']))
    if not scarti:
        return prova('ci sono giocatori da scomporre', False)
    medio = sum(scarti) / len(scarti)
    prova('la fantamedia ricostruita coincide con quella vera', medio < 0.05,
          'scarto medio %.3f su %d giocatori' % (medio, len(scarti)))
    prova('nessuna ricostruzione lontana piu di mezzo punto', max(scarti) < 0.5,
          'peggiore %.2f' % max(scarti))


def classifiche(d):
    print('\nclassifiche')
    import statistiche as S
    righe = S.tabellone(d, '2025-26', False)
    prova('il tabellone della scorsa stagione non e vuoto', len(righe) > 200,
          '%d giocatori' % len(righe))
    tutte = S.tutte(righe, quanti=5)
    prova('escono tutte le classifiche', len(tutte) >= 12, '%d' % len(tutte))
    prova('ogni classifica e ordinata',
          all(all(
              (c['righe'][i][c['campo']] >= c['righe'][i + 1][c['campo']])
              == c['alto_meglio']
              or c['righe'][i][c['campo']] == c['righe'][i + 1][c['campo']]
              for i in range(len(c['righe']) - 1)) for c in tutte))
    corr = S.tabellone(d, 'in corso', True, minime=1)
    prova('esiste anche la stagione in corso', len(corr) > 100, '%d' % len(corr))
    if d['giornate_giocate']:
        gio = S.per_giornata(d, 1, 5)
        prova('la classifica di giornata funziona', len(gio) == 5,
              'primo: %s %.1f' % (gio[0]['nome'], gio[0]['fv']) if gio else '')
    sq = S.squadre(d, '2025-26', False)
    prova('le statistiche di squadra tornano', len(sq) >= 18, '%d squadre' % len(sq))


def formazione(d):
    print('\nformazione e modificatore')
    import fanta_modello as M
    import strategia as S
    # la scala e' smussata apposta: il gradino del 6,00 diventa una rampa che
    # parte da 5,875 e arriva a 6,125, perche' dove finira' la media del blocco
    # non si sa e il valore atteso di un gradino visto da lontano e' la rampa
    prova('il modificatore da zero sotto la rampa',
          M.punti_modificatore(5.87) == 0 and M.punti_modificatore(5.0) == 0)
    prova('il modificatore vale un punto sulla soglia',
          abs(M.punti_modificatore(6.0) - 0.5) < 1e-9
          and abs(M.punti_modificatore(6.125) - 1.0) < 1e-9)
    prova('il modificatore si ferma al tetto',
          M.punti_modificatore(9.0) == M.MAX_MOD)
    prova('il modificatore e crescente',
          M.punti_modificatore(6.5) > M.punti_modificatore(6.2) > 0)
    prova('il blocco vuole portiere e tre difensori',
          M.media_blocco(None, [6, 6, 6]) is None
          and M.media_blocco(6.0, [6, 6]) is None)
    prova('il blocco fa la media dei tre migliori',
          abs(M.media_blocco(6.0, [7.0, 6.0, 5.0, 4.0]) - 6.0) < 1e-9)
    # un undici finto, per vedere se l'ottimizzatore sceglie e non esplode
    finti = []
    for ru, quanti in (('P', 2), ('D', 6), ('C', 6), ('A', 4)):
        for i in range(quanti):
            finti.append({'p': {'id': '%s%d' % (ru, i), 'R': ru,
                                'nome': '%s%d' % (ru, i)},
                          'atteso': 6.0 + i * 0.1, 'mv': 6.0 + (quanti - i) * 0.05})
    con = S.scelta_undici(finti, 4, 3, 3, True)
    senza = S.scelta_undici(finti, 4, 3, 3, False)
    prova('l undici esce completo', con and len(con['undici']) == 11)
    prova('col modificatore acceso il totale e piu alto',
          con and senza and con['totale'] >= senza['totale'],
          '%.2f contro %.2f' % (con['totale'], senza['totale']) if con and senza else '')
    prova('con tre difensori il modificatore non si prende',
          (S.scelta_undici(finti, 3, 4, 3, True) or {}).get('media') is None)


def _luminanza(hexa):
    h = hexa.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrasto(a, b):
    la, lb = _luminanza(a), _luminanza(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def movimento(_d):
    """Il sistema di movimento: che ci sia, che sia coerente, che si sappia spegnere."""
    print()
    print('movimento')
    import tema as T
    for scuro in (True, False):
        f = T.foglio(scuro)
        nome = 'scuro' if scuro else 'chiaro'
        prova('il foglio %s si compone' % nome, len(f) > 20000, '%d caratteri' % len(f))

    f = T.foglio(True)
    durate = ['--t-tocco', '--t-breve', '--t-medio', '--curva', '--molla']
    mancanti = [x for x in durate if x + ':' not in f]
    prova('le durate del movimento sono dichiarate una volta sola', not mancanti,
          'mancano: %s' % ', '.join(mancanti) if mancanti else ', '.join(durate))

    # chi chiede meno movimento non deve vederne
    i = f.find('@media (prefers-reduced-motion: reduce)')
    prova('esiste la resa per chi non vuole animazioni', i > 0,
          'blocco a %d caratteri dalla fine' % (len(f) - i) if i > 0 else '')
    blocco = f[i:i + 700] if i > 0 else ''
    for pezzo in ('.carta', '.cifra', 'data-mossa'):
        prova('  spegne anche %s' % pezzo, pezzo in blocco, '')

    # i numeri che salgono devono comunque avere un valore di arrivo
    prova('il contatore CSS ha la sua proprieta', '@property --n' in f
          and 'counter(n)' in f, '')
    prova('il numero senza --fine non si anima', T.numero('ciao') == 'ciao', '')
    prova('il numero intero diventa un contatore', '--fine:168' in T.numero(168),
          T.numero(168)[:46])
    # due cose diverse non devono chiamarsi allo stesso modo: il contatore
    # animato e l'etichetta "quanti sono" si erano scontrati, e ogni sezione
    # stampava uno zero in fondo al proprio conteggio
    prova('il contatore di sezione non e il contatore animato',
          'class="conta"' in T.banda('x', '3 voci')
          and 'class="cifra"' in T.numero(3), '')
    prova('il numero decimale resta scritto', T.numero('6.28') == '6.28', '')


def leggibilita(_d):
    """Che i colori si leggano davvero, in tutti e due i temi.

    Non e' pignoleria da manuale: la pastiglia dello slot 1 — il titolarissimo,
    quella che in asta si guarda piu' di tutte — aveva 1,68 di contrasto, cioe'
    era una macchia blu con dentro un buco nero."""
    print()
    print('leggibilita')
    import tema as T
    scuro, chiaro = T.SCURO, T.CHIARO

    # le pastiglie: sfondo colorato, testo scuro fisso
    inchiostro = '#0A0D11'
    tinte = {'arancio': T.ARANCIO, 'ambra': T.AMBRA, 'rosso': T.ROSSO,
             'ciano': T.CIANO, 'verde': T.VERDE, 'viola': T.VIOLA}
    peggio = min((contrasto(inchiostro, c), n) for n, c in tinte.items())
    prova('le pastiglie si leggono', peggio[0] >= 4.5,
          'la peggiore e %s con %.2f:1' % (peggio[1], peggio[0]))

    # le tinte degli slot le decide l'app: le rileggo da li'
    import re
    sorgente = io.open('app.py', encoding='utf-8').read()
    m = re.search(r"tinte = \[([^\]]+)\]", sorgente)
    if m:
        colori = re.findall(r"'(#[0-9A-Fa-f]{6})'", m.group(1))
        colori += [T.CIANO, T.AMBRA] if len(colori) < 8 else []
        brutti = [c for c in colori if contrasto(inchiostro, c) < 4.5]
        prova('le pastiglie degli slot si leggono', not brutti,
              'illeggibili: %s' % ', '.join(brutti) if brutti else '%d tinte' % len(colori))

    # i colori usati come inchiostro devono reggere su tutti e due i fondi
    for nome, fondo in (('scuro', scuro['fondo']), ('chiaro', chiaro['fondo'])):
        tavolozza = scuro if nome == 'scuro' else chiaro
        male = [k for k in ('su', 'giu', 'attenzione', 'info')
                if contrasto(fondo, tavolozza[k]) < 4.5]
        prova('il testo colorato si legge sul tema %s' % nome, not male,
              'sotto soglia: %s' % ', '.join(male) if male else '')

    # e il testo normale, che e' quello che si legge di piu'
    for nome, tav in (('scuro', scuro), ('chiaro', chiaro)):
        prova('il testo normale si legge sul tema %s' % nome,
              contrasto(tav['fondo'], tav['testo']) >= 7,
              '%.1f:1' % contrasto(tav['fondo'], tav['testo']))
        prova('il testo tenue si legge sul tema %s' % nome,
              contrasto(tav['fondo'], tav['tenue']) >= 4.0,
              '%.1f:1' % contrasto(tav['fondo'], tav['tenue']))


def moduli(_d):
    """Che tutti i pezzi si importino: un errore di sintassi in un file che l'app
    carica solo quando apri una certa pagina lo scopriresti all'asta."""
    print()
    print('moduli')
    import importlib
    for nome in ('radice', 'tema', 'statistiche', 'risorse', 'pag_statistiche',
                 'strategia', 'giudizio', 'fanta_modello', 'fanta_parse',
                 'fanta_scarica', 'fanta_schede', 'fanta_sosfanta',
                 'fanta_fantapazz', 'fanta_rigoristi', 'fanta_redazioni',
                 'fanta_campioncini', 'fanta_loghi', 'aggiorna'):
        try:
            importlib.import_module(nome)
            esito, dettaglio = True, ''
        except Exception as err:
            esito, dettaglio = False, '%s: %s' % (type(err).__name__, err)
        prova('si importa %s' % nome, esito, dettaglio)


def vestito(d):
    """I mattoncini grafici: che rispondano, e che il foglio di stile si formi.

    Il foglio di stile passa da un %-format: basta una percentuale scritta senza
    raddoppiarla e tutta l'interfaccia sparisce con un TypeError. E' successo, e
    da allora c'e' questo controllo."""
    print()
    print('vestito')
    import tema as T
    prova('il foglio di stile si compone', len(T.foglio(True)) > 8000
          and len(T.foglio(False)) > 8000)
    prova('il chiaro e lo scuro hanno le stesse chiavi',
          set(T.SCURO) == set(T.CHIARO))
    finto = {'R': 'A', 'nome': 'Prova', 'squadra': 'INT', 'id': '1'}
    pezzi = {
        'pillola': T.pillola('x', T.ARANCIO),
        'riquadri': T.riquadri([('a', 1, 'b', '')]),
        'banda': T.banda('x'),
        'nota': T.nota('x'),
        'tabella': T.tabella([('a', '')], [['1']]),
        'con_barra': T.con_barra(3, .5),
        'linea_forma': T.linea_forma([6, 7, 5]),
        'radar': T.radar([('a', .5), ('b', .8), ('c', .3)]),
        'anello': T.anello(.5, 'x'),
        'carta': T.carta(finto, prezzo=10),
        'righello': T.righello(10, 20, 30, 'tizio', 40),
        'stemma': T.stemma('INT', dato='AAA'),
    }
    vuoti = [k for k, v in pezzi.items() if not v or '<' not in v]
    prova('tutti i mattoncini disegnano qualcosa', not vuoti, ', '.join(vuoti))
    # il campo vuole una formazione fatta come si deve
    # il campo vuole coppie (giocatore, prezzo), non solo giocatori
    forma = {ru: [({'nome': '%s%d' % (ru, i), 'id': '%s%d' % (ru, i)}, 10 + i)
                  for i in range(n)]
             for ru, n in (('P', 1), ('D', 4), ('C', 3), ('A', 3))}
    try:
        campo = T.campo(forma)
        prova('il campo si disegna', '<svg' in campo or '<div' in campo)
    except Exception as err:
        prova('il campo si disegna', False, '%s: %s' % (type(err).__name__, err))


def sei_rose(d):
    """Sei proposte: che siano sei, diverse fra loro, e tutte dentro il budget."""
    print()
    print('le sei rose')
    import mercato as MK
    import strategia as S
    cfg = d['config']
    asta = {'squadre': ['Io'] + ['S%d' % i for i in range(2, 11)],
            'mia': 0, 'acquisti': {}}
    g = d['giocatori']
    cal = MK.calibrazione(g, asta)
    eq = MK.prezzi_live(g, cfg, asta, cal)
    sc = MK.scarsita(g, cfg, asta)
    massimi, _ = MK.prezzi_massimi(g, cfg, asta, eq, sc)
    sei = S.sei_proposte(d, asta, cfg, massimi)

    prova('escono sei proposte', len(sei) == 6, '%d' % len(sei))
    prova('nessuna sfora il budget', all(r['avanzo'] >= 0 for r in sei),
          'avanzi: %s' % ', '.join(str(r['avanzo']) for r in sei))
    prova('tutte hanno la rosa completa',
          all(len(r['rosa']) == sum(cfg['slot'].values()) for r in sei),
          'rose da %s' % ', '.join(str(len(r['rosa'])) for r in sei))
    prova('tutte schierano un undici',
          all(r['formazione'] for r in sei),
          'moduli: %s' % ', '.join((r['formazione'] or {}).get('modulo', '—')
                                   for r in sei))

    # diverse davvero: due proposte non devono avere la stessa rosa
    coppie_uguali = []
    for i in range(len(sei)):
        for j in range(i + 1, len(sei)):
            a_ = {p['id'] for p in sei[i]['rosa']}
            b_ = {p['id'] for p in sei[j]['rosa']}
            q = len(a_ & b_) / float(len(a_))
            if q > 0.85:
                coppie_uguali.append('%s/%s %.0f%%'
                                     % (sei[i]['titolo'][:12], sei[j]['titolo'][:12],
                                        q * 100))
    prova('sono davvero diverse fra loro', not coppie_uguali,
          '; '.join(coppie_uguali[:2]) if coppie_uguali
          else 'nessuna coppia oltre l 85%% di sovrapposizione')

    # ognuna deve avere la sua spiegazione e il suo rischio
    prova('ognuna dice perche e cosa rischia',
          all(len(r.get('idea') or '') > 60 and len(r.get('rischio') or '') > 30
              for r in sei), '%d spiegazioni' % len(sei))

    # la prima e' quella senza vincoli, e nessuna la batte
    prova('la prima e la piu redditizia',
          sei[0]['punteggio'] >= max(r['punteggio'] for r in sei) - 0.5,
          '%.0f punti contro %.0f della seconda'
          % (sei[0]['punteggio'], sei[1]['punteggio']))

    # le spese per reparto devono rispecchiare le idee
    dietro = next((r for r in sei if r['chiave'] == 'difesa'), None)
    avanti = next((r for r in sei if r['chiave'] == 'attacco'), None)
    if dietro and avanti:
        prova('la corazzata spende dietro piu di chi punta sull attacco',
              dietro['spesa']['D'] > avanti['spesa']['D'],
              'D %d contro %d' % (dietro['spesa']['D'], avanti['spesa']['D']))
        prova('chi punta sull attacco spende davanti piu della corazzata',
              avanti['spesa']['A'] > dietro['spesa']['A'],
              'A %d contro %d' % (avanti['spesa']['A'], dietro['spesa']['A']))


def blocchi_e_scommesse(d):
    """I blocchi a fasce di prezzo e il piano delle scommesse."""
    print()
    print('blocchi e scommesse')
    import mercato as MK
    import strategia as S
    cfg = d['config']
    asta = {'squadre': ['Io'] + ['S%d' % i for i in range(2, 11)],
            'mia': 0, 'acquisti': {}}
    g = d['giocatori']
    cal = MK.calibrazione(g, asta)
    eq = MK.prezzi_live(g, cfg, asta, cal)
    sc = MK.scarsita(g, cfg, asta)
    massimi, _ = MK.prezzi_massimi(g, cfg, asta, eq, sc)

    bl = S.blocchi_difesa(d, asta, cfg, massimi)
    prova('escono piu blocchi difensivi', len(bl) >= 3, '%d fasce' % len(bl))
    prova('ogni blocco ha portiere e tre difensori',
          all(len(b['blocco']) == 4 and b['blocco'][0]['R'] == 'P'
              and all(q['R'] == 'D' for q in b['blocco'][1:]) for b in bl), '')
    prova('i blocchi costano quanto la loro fascia',
          all(b['costo'] <= b['tetto'] for b in bl),
          ', '.join('%d/%d' % (b['costo'], b['tetto']) for b in bl))
    prova('chi spende di piu ottiene di piu',
          all(bl[i]['mv'] <= bl[i + 1]['mv'] + 0.02 for i in range(len(bl) - 1)),
          ' < '.join('%.2f' % b['mv'] for b in bl))
    prova('i blocchi pescano da squadre diverse',
          all(b['squadre'] >= 2 for b in bl),
          'squadre per blocco: %s' % ', '.join(str(b['squadre']) for b in bl))

    pi = S.piano_scommesse(d, asta, cfg, massimi)
    prova('le scommesse coprono i tre reparti di movimento',
          len(pi['per_ruolo']) == 3, ', '.join(sorted(pi['per_ruolo'])))
    magre = [ru for ru, v in pi['per_ruolo'].items() if len(v['quali']) < 3]
    prova('ogni reparto ha almeno tre scommesse', not magre,
          'scarsi: %s' % ', '.join(magre) if magre
          else ', '.join('%s %d' % (ru, len(v['quali']))
                         for ru, v in sorted(pi['per_ruolo'].items())))
    prova('ogni scommessa ha una ragione scritta',
          all(x['motivi'] for v in pi['per_ruolo'].values() for x in v['quali']), '')
    prova('il budget da tenere da parte e sensato',
          0 < pi['da_tenere'] < cfg['crediti'] * 0.5,
          '%d crediti su %d' % (pi['da_tenere'], cfg['crediti']))


def gol_attesi(d):
    """Gli xG: che ci siano, che siano abbinati bene, che non stravolgano nulla."""
    print()
    print('gol attesi')
    con = [p for p in d['giocatori'] if (p.get('xg') or {}).get('partite')]
    prova('gli xG sono arrivati', len(con) > 250, '%d giocatori' % len(con))

    # solo chi ha davvero giocato: Understat elenca chi e' sceso in campo, e un
    # titolare annunciato che non ha ancora esordito non puo' avere xG. Misurare
    # la copertura su di lui farebbe fallire il controllo ogni volta che le
    # probabili formazioni cambiano, senza che nulla sia rotto.
    def ha_giocato(p):
        return any(x.get('v') is not None for x in (p.get('giornate') or []))

    titolari = [p for p in d['giocatori']
                if (p.get('perc_titolarita') or 0) >= 70 and ha_giocato(p)]
    coperti = [p for p in titolari if (p.get('xg') or {}).get('partite')]
    prova('coprono i titolari che hanno giocato',
          not titolari or len(coperti) >= len(titolari) * 0.95,
          '%d su %d' % (len(coperti), len(titolari)))

    # l'abbinamento: il nome di Understat deve somigliare al nostro
    import fanta_modello as MM
    storti = []
    for p in con:
        loro = MM.chiave(p['xg'].get('nome_understat') or '')
        nostro = MM.chiave((p.get('nome_completo') or '') + p['nome'])
        pezzi = [x for x in (p['xg'].get('nome_understat') or '').split()
                 if len(MM.chiave(x)) >= 4]
        if not any(MM.chiave(x) in nostro for x in pezzi):
            storti.append('%s -> %s' % (p['xg']['nome_understat'], p['nome']))
    prova('ogni abbinamento ha un pezzo di nome in comune', not storti,
          '; '.join(storti[:3]) if storti else '%d controllati' % len(con))

    # la correzione non deve mai essere violenta
    corr = [abs(p['xg'].get('correzione') or 0) for p in con]
    prova('la correzione resta prudente', not corr or max(corr) <= 0.61,
          'la piu grande vale %.2f di fantamedia' % (max(corr) if corr else 0))

    # e i valori devono restare sensati
    fm = [p['fm_att'] for p in d['giocatori'] if p.get('fm_att')]
    prova('le fantamedie restano plausibili dopo la correzione',
          min(fm) > 2.5 and max(fm) < 11, '%.2f - %.2f' % (min(fm), max(fm)))


def chiedimi(d):
    """La pagina Chiedimi: che risponda, e che non risponda a sproposito."""
    print()
    print('chiedimi')
    import prove_chiedimi
    prove_chiedimi.controlla(d, prova)


def consigli(d):
    print('\nconsigli di giornata')
    c = d['consigli']
    prova('ci sono consigli per la prossima giornata', len(c) > 300, '%d' % len(c))
    con_atteso = [v for v in c.values() if v.get('atteso') is not None]
    prova('gli attesi sono plausibili',
          all(-2 <= v['atteso'] <= 15 for v in con_atteso))
    prova('la media voto attesa e plausibile',
          all(3 <= v['mv_atteso'] <= 9 for v in con_atteso if v.get('mv_atteso')))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print('FantAiuto — controlli')
    d = carica()
    print('dati del %s, giornata %d' % (d['aggiornato'], d['prossima_giornata']))
    for blocco in (dati_di_base, voti_e_giornate, cartellini, scomposizione,
                   classifiche, formazione, moduli, vestito, leggibilita,
                   movimento,
                   consigli, chiedimi, gol_attesi, sei_rose,
                   blocchi_e_scommesse):
        try:
            blocco(d)
        except Exception as err:
            prova('%s non e nemmeno arrivato in fondo' % blocco.__name__, False,
                  '%s: %s' % (type(err).__name__, err))
    quanti = len(esiti)
    male = [x for x in esiti if not x[0]]
    print('\n%d controlli, %d falliti' % (quanti, len(male)))
    for _, nome, dettaglio in male:
        print('  KO  %s  %s' % (nome, dettaglio))
    return 1 if male else 0


if __name__ == '__main__':
    sys.exit(main())
