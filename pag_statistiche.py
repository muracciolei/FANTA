# -*- coding: utf-8 -*-
"""La pagina delle statistiche.

Sta in un file suo perche' e' cresciuta: quattro stagioni, diciassette classifiche,
la scomposizione della fantamedia, i cartellini giornata per giornata e il
confronto fra due giocatori non stanno dentro una funzione di trenta righe senza
diventare illeggibili.

L'ordine delle sezioni non e' casuale, segue le domande in ordine di frequenza:
prima il colpo d'occhio sulla stagione, poi le classifiche, poi i cartellini (che
sono la parte nuova), poi il singolo giocatore, poi le squadre, e in fondo il
tabellone completo per chi vuole guardarsi tutto.
"""
import streamlit as st

import risorse as R
import statistiche as S
import tema as T


def _html(x):
    st.markdown(x, unsafe_allow_html=True)


def _squadra(sigla):
    return T.stemma(sigla) + T.e(sigla)


def _pillola_cartellino(amm, esp):
    return T.cartellini(amm, esp, sagome=1)


# ------------------------------------------------------------- riassunto
def riassunto(d, righe, etichetta):
    gol = sum(r['gol'] for r in righe)
    amm = sum(r['amm'] for r in righe)
    esp = sum(r['esp'] for r in righe)
    mv = [r['mv'] for r in righe if r['mv'] is not None]
    _html(T.riquadri([
        ('Calciatori', len(righe), etichetta, ''),
        ('Gol', '%g' % gol, 'segnati in totale', 'ciano'),
        ('Ammonizioni', '%g' % amm,
         '%.2f a partita giocata' % (amm / max(1, sum(r['pv'] for r in righe))), 'ambra'),
        ('Espulsioni', '%g' % esp, 'in tutto il campionato', 'rosso'),
        ('Media voto', '%.2f' % (sum(mv) / len(mv)) if mv else '—',
         'la media della lega', ''),
    ]))


# ------------------------------------------------------------- classifiche
GRUPPI = [
    ('Chi fa i bonus', ['gol', 'ass', 'bonus_pg']),
    ('Chi rende', ['fm', 'mv', 'pv']),
    ('Chi prende cartellini', ['amm', 'amm_pg', 'esp']),
    ('Chi non li prende mai', ['puliti']),
    ('Dal dischetto e in porta', ['rig_seg', 'rig_par', 'gs_pg']),
]


def tabella_classifica(cl, quanti=10):
    righe = []
    for i, r in enumerate(cl['righe'][:quanti], 1):
        righe.append([
            '<span class="posto">%d</span>' % i,
            T.pillola(r['R'], T.RUOLO_COLORE[r['R']]),
            T.e(r['nome']), _squadra(r['squadra']),
            T.con_barra(cl['formato'] % r[cl['campo']],
                        (r[cl['campo']] / max(abs(cl['righe'][0][cl['campo']]), 1e-9))
                        if cl['alto_meglio'] else 0.3,
                        T.ARANCIO),
            '%g' % r['pv'],
        ])
    return T.tabella([('#', 'num'), ('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
                      (cl['etichetta'], 'big'), ('Pg', 'num')], righe)


def classifiche(d, righe):
    for titolo, chiavi in GRUPPI:
        presenti = [S.classifica(righe, k, 10) for k in chiavi]
        presenti = [c for c in presenti if c and c['righe']]
        if not presenti:
            continue
        _html(T.banda(titolo, '%d classifiche' % len(presenti)))
        for colonna, cl in zip(st.columns(len(presenti)), presenti):
            with colonna:
                _html('<div class="titoletto">%s</div>' % T.e(cl['etichetta']))
                _html(tabella_classifica(cl))


# ------------------------------------------------------------- cartellini
def cartellini(d, righe, stagione, in_corso):
    _html(T.banda('Cartellini', '%g gialli e %g rossi'
                  % (sum(r['amm'] for r in righe),
                     sum(r['esp'] for r in righe))))
    _html(T.nota(
        'Le ammonizioni pesano in due modi: mezzo punto ciascuna sulla fantamedia — '
        'un punto le espulsioni — e una giornata di squalifica ogni cinque gialli. '
        'Un difensore da dieci gialli l’anno butta via cinque fantapunti e salta due '
        'partite: vale quanto un gol e mezzo di un attaccante.<br>'
        '<span style="font-size:.82rem">Detto questo, teniamo le proporzioni: anche '
        'il più falloso della Serie A si mangia circa <b>un quarto di punto</b> di '
        'fantamedia a partita. È un criterio per scegliere fra due giocatori simili, '
        'non un motivo per scartarne uno bravo.</span>'))

    a, b = st.columns([3, 2])
    with a:
        _html('<div class="titoletto">Chi rischia di piu’ nella stagione che viene</div>')
        rischio = sorted(
            [p for p in d['giocatori']
             if (p.get('cartellini') or {}).get('giornate_squalifica') is not None
             and p['cartellini']['pv_totali'] >= 25],
            key=lambda p: -p['cartellini']['giornate_squalifica'])[:12]
        _html(T.tabella(
            [('R', ''), ('Calciatore', 'nome'), ('Sq', ''), ('Gialli/pg', 'num'),
             ('Rossi attesi', 'num'), ('Giornate a rischio', 'big'), ('Costo', 'nota')],
            [[T.pillola(p['R'], T.RUOLO_COLORE[p['R']]), T.e(p['nome']),
              _squadra(p['squadra']),
              '%.2f' % p['cartellini']['amm_partita'],
              '%.1f' % (p['cartellini']['esp_attese'] or 0),
              T.con_barra(p['cartellini']['giornate_squalifica'],
                          min(1, p['cartellini']['giornate_squalifica'] / 4.0), T.ROSSO),
              T.e('%.1f fantapunti buttati'
                  % (S.costo_cartellini(p) or {}).get('punti', 0))]
             for p in rischio]))
    with b:
        _html('<div class="titoletto">Quest’anno, giornata per giornata</div>')
        presi = [(p, S.cartellini_giornate(p)) for p in d['giocatori']]
        presi = sorted([x for x in presi if x[1]], key=lambda x: -len(x[1]))[:12]
        if presi:
            _html(T.tabella(
                [('Calciatore', 'nome'), ('Sq', ''), ('Quando', 'nota'),
                 ('Alla squalifica', 'num')],
                [[T.e(p['nome']), _squadra(p['squadra']),
                  ' '.join(T.pillola('%da' % x['g'],
                                     T.ROSSO if x['tipo'] == 'rosso' else T.AMBRA)
                           for x in g),
                  ('<b>%d</b>' % p['al_quinto']) if p.get('al_quinto') else '—']
                 for p, g in presi]))
        else:
            _html(T.vuoto('Ancora nessun cartellino',
                          'Si riempie da sola dalla prossima giornata: qui finiscono '
                          'i gialli e i rossi partita per partita.'))

    diffidati = [p for p in d['giocatori'] if p.get('diffidato')]
    if diffidati:
        _html(T.nota('<b>In diffida adesso:</b> %s. Al prossimo giallo saltano una '
                     'giornata.' % T.e(', '.join('%s (%s)' % (p['nome'], p['squadra'])
                                                 for p in diffidati)), 'allarme'))
    else:
        _html(T.vuoto('Nessun diffidato',
                      'Per essere in diffida servono quattro ammonizioni, e siamo '
                      'alla %da giornata. Il conto lo tengo io: quando qualcuno ci '
                      'arriva compare qui e nella pagina Formazione.'
                      % d['prossima_giornata']))


# ------------------------------------------------------------- il giocatore
def scheda(d, p, stagione, in_corso):
    r = S.riga(p, stagione, in_corso)
    if not r:
        _html(T.nota('In questa stagione non ha giocato nemmeno una partita.'))
        return
    sc = S.scomposizione(r)
    conf = S.confronto_ruolo(d, p, stagione, in_corso)

    _html(T.riquadri([
        ('Presenze', '%g' % r['pv'], 'in questa stagione', ''),
        ('Fantamedia', '%.2f' % r['fm'] if r['fm'] else '—', 'media voto %.2f' % r['mv'],
         'ciano'),
        ('Gol e assist', '%g + %g' % (r['gol'], r['ass']),
         '%.2f bonus a partita' % r['bonus_pg'], 'verde'),
        ('Cartellini', '%g / %g' % (r['amm'], r['esp']),
         '%.2f gialli a partita' % r['amm_pg'], 'ambra'),
    ]))
    _html('<div class="titoletto">Cartellini presi</div>' + T.cartellini(r['amm'], r['esp']))

    if sc:
        _html(T.banda('Da dove viene la sua fantamedia'))
        pezzi = [['<b>Media voto</b>', '', '%.2f' % sc['voto'],
                  T.e('il punto di partenza')]]
        for v in sc['voci']:
            pezzi.append([
                T.e(v['etichetta']), '%g' % v['quanti'],
                '<span class="%s">%+.2f</span>' % ('su' if v['punti'] > 0 else 'giu',
                                                   v['punti']),
                T.con_barra(abs(v['punti']), min(1, abs(v['punti']) / 2.0),
                            T.VERDE if v['punti'] > 0 else T.ROSSO)])
        pezzi.append(['<b>Fantamedia</b>', '', '<b>%.2f</b>' % sc['fantamedia_ricostruita'],
                      T.e('dichiarata %.2f' % sc['fantamedia_dichiarata']
                          if sc['fantamedia_dichiarata'] else '')])
        _html(T.tabella([('Voce', 'nome'), ('Quante', 'num'),
                         ('Punti di fantamedia', 'big'), ('', 'nota')], pezzi))

    if conf:
        _html(T.banda('Rispetto agli altri del suo ruolo'))
        _html(T.tabella(
            [('Cosa', 'nome'), ('Lui', 'big'), ('Mediana del ruolo', 'num'),
             ('Percentile', 'nota')],
            [[T.e(v['etichetta']), '%.2f' % v['valore'], '%.2f' % v['mediana'],
              T.con_barra('%d°' % v['percentile'], v['percentile'] / 100.0,
                          T.VERDE if v['percentile'] >= 60
                          else T.AMBRA if v['percentile'] >= 35 else T.ROSSO)]
             for v in conf.values()]))

    and_ = S.andamento(p)
    if and_ and any(x['gioca'] for x in and_):
        _html(T.banda('Questa stagione, giornata per giornata'))
        righe = []
        for x in and_:
            if not x['gioca']:
                righe.append([x['g'], '—', '—',
                              T.pillola('non ha giocato', '', vuota=True), '', ''])
                continue
            righe.append([
                x['g'], '%.1f' % x['v'], '<b>%.1f</b>' % x['fv'],
                T.pillola('subentrato', T.AMBRA) if x['sub']
                else T.pillola('titolare', T.VERDE),
                _pillola_cartellino(x['amm'], x['esp']),
                T.e('%d bonus, %d malus' % (x['bonus'], x['malus'])),
            ])
        _html(T.tabella([('Giornata', 'num'), ('Voto', 'num'), ('Fantavoto', 'big'),
                         ('Come', ''), ('Cartellini', ''), ('Bonus', 'nota')], righe))

    storico = [(s, v) for s, v in sorted((p.get('storico') or {}).items(), reverse=True)
               if v]
    if storico:
        _html(T.banda('Le stagioni precedenti'))
        _html(T.tabella(
            [('Stagione', ''), ('Sq', ''), ('Pg', 'num'), ('MV', 'num'), ('FM', 'big'),
             ('Gol', 'num'), ('Assist', 'num'), ('Gialli', 'num'), ('Rossi', 'num')],
            [[T.e(s), T.e(v.get('squadra') or ''), '%g' % (v.get('pv') or 0),
              '%.2f' % v['mv'] if v.get('mv') else '—',
              '%.2f' % v['fm'] if v.get('fm') else '—',
              '%g' % (v.get('gol') or 0), '%g' % (v.get('ass') or 0),
              '%g' % (v.get('amm') or 0), '%g' % (v.get('esp') or 0)]
             for s, v in storico]))


# ------------------------------------------------------------- squadre
def squadre(d, stagione, in_corso):
    sq = S.squadre(d, stagione, in_corso)
    if not sq:
        return
    massimo = max(s['gol'] for s in sq) or 1
    _html(T.tabella(
        [('Squadra', 'nome'), ('Gol fatti', 'big'), ('Assist', 'num'),
         ('Gol subiti', 'num'), ('Subiti a partita', 'num'),
         ('Fantamedia media', 'num'), ('Gialli', 'num'), ('Rossi', 'num')],
        [[_squadra(s['squadra']),
          T.con_barra('%g' % s['gol'], s['gol'] / massimo, T.VERDE),
          '%g' % s['ass'], '%g' % s['gs'],
          '%.2f' % s['gs_partita'] if s['gs_partita'] is not None else '—',
          '%.2f' % s['fm_media'] if s['fm_media'] else '—',
          '%g' % s['amm'], '%g' % s['esp']] for s in sq]))


# ------------------------------------------------------------- tabellone
COLONNE_TABELLONE = [
    ('pv', 'Pg'), ('mv', 'MV'), ('fm', 'FM'), ('gol', 'Gol'), ('ass', 'Ass'),
    ('amm', 'Gialli'), ('esp', 'Rossi'), ('gs', 'Subiti'), ('rig_seg', 'Rig'),
]


def tabellone(righe, ordina='fm'):
    righe = sorted(righe, key=lambda r: -(r.get(ordina) or 0))[:60]
    _html(T.tabella(
        [('R', ''), ('Calciatore', 'nome'), ('Sq', '')]
        + [(et, 'num') for _, et in COLONNE_TABELLONE],
        [[T.pillola(r['R'], T.RUOLO_COLORE[r['R']]), T.e(r['nome']), _squadra(r['squadra'])]
         + [('%.2f' % r[c] if c in ('mv', 'fm') and r[c] is not None
             else '%g' % (r[c] or 0)) for c, _ in COLONNE_TABELLONE]
         for r in righe]))


# ------------------------------------------------------------- la pagina
def pagina(d):
    nomi_stagioni = S.stagioni(d)
    a, b, c = st.columns([2, 1, 1])
    stagione = a.segmented_control('Stagione', nomi_stagioni, default=nomi_stagioni[0],
                                   key='stat_stagione') or nomi_stagioni[0]
    in_corso = stagione == 'in corso'
    ruolo = b.selectbox('Ruolo', ['Tutti'] + S.RUOLI, key='stat_ruolo')
    squadra = c.selectbox('Squadra', ['Tutte'] + sorted({p['squadra'] for p in d['giocatori']}),
                          key='stat_squadra')

    righe = S.tabellone(d, stagione, in_corso,
                        ruolo=None if ruolo == 'Tutti' else ruolo,
                        squadra=None if squadra == 'Tutte' else squadra,
                        minime=1 if in_corso else None)
    if not righe:
        _html(T.nota('Con questi filtri non resta nessuno.'))
        return

    etichetta = 'stagione in corso' if in_corso else 'stagione %s' % stagione
    riassunto(d, righe, etichetta)

    schede = st.tabs(['Classifiche', 'Cartellini', 'Il giocatore', 'Le squadre',
                      'Tabellone'])
    with schede[0]:
        classifiche(d, righe)
    with schede[1]:
        cartellini(d, righe, stagione, in_corso)
    with schede[2]:
        elenco = sorted(d['giocatori'], key=lambda p: p['nome'])
        nomi = ['%s — %s' % (p['nome'], p['squadra']) for p in elenco]
        scelto = st.selectbox('Calciatore', nomi, key='stat_giocatore')
        scheda(d, elenco[nomi.index(scelto)], stagione, in_corso)
    with schede[3]:
        squadre(d, stagione, in_corso)
    with schede[4]:
        ordini = {'Fantamedia': 'fm', 'Media voto': 'mv', 'Gol': 'gol',
                  'Assist': 'ass', 'Presenze': 'pv', 'Ammonizioni': 'amm',
                  'Espulsioni': 'esp'}
        scelta = st.segmented_control('Ordina per', list(ordini), default='Fantamedia',
                                      key='stat_ordine') or 'Fantamedia'
        tabellone(righe, ordini[scelta])
