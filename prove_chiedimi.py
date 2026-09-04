# -*- coding: utf-8 -*-
"""Il pezzo di collaudo che riguarda la pagina Chiedimi.

Sta in un file suo perche' ha bisogno di un'asta finta a meta' strada — qualche
acquisto mio, parecchi degli altri — e costruirla dentro prove.py avrebbe
sporcato tutto il resto.
"""
import mercato as MK
import strategia as S


def asta_finta(d, cfg):
    """Un'asta a meta': io ho speso quasi tutto, gli altri hanno ancora fame."""
    asta = {'squadre': ['La mia squadra'] + ['Squadra %d' % i for i in range(2, 11)],
            'mia': 0, 'acquisti': {}}
    per_valore = sorted(d['giocatori'], key=lambda p: -p['valore'])
    for p, prezzo in zip([q for q in per_valore if q['R'] != 'P'][:4],
                         (150, 110, 70, 50)):
        asta['acquisti'][p['id']] = {'squadra': 0, 'prezzo': prezzo}
    for n, p in enumerate(per_valore[8:30]):
        asta['acquisti'][p['id']] = {'squadra': (n % 9) + 1,
                                     'prezzo': int(p['prezzo'])}
    return asta


def contesto(d, cfg, asta):
    g = d['giocatori']
    cal = MK.calibrazione(g, asta)
    prezzi = MK.prezzi_live(g, cfg, asta, cal)
    scar = MK.scarsita(g, cfg, asta)
    massimi, tetto = MK.prezzi_massimi(g, cfg, asta, prezzi, scar)
    return {'d': d, 'asta': asta, 'cfg': cfg, 'massimi': massimi, 'scar': scar,
            'cal': cal, 'tetto': tetto, 'per_id': {p['id']: p for p in g},
            'attesi': MK.prezzi_attesi(g, cfg, asta, prezzi),
            'temperatura': MK.temperatura(g, cfg, asta),
            'sit': S.situazione(d, asta, cfg, MK.miei(asta)),
            'offerta_massima': lambda i: MK.offerta_massima(asta, cfg, i)}


def controlla(d, prova):
    """Le domande che devono funzionare, e i tranelli che devono non scattare."""
    import consulente as C
    cfg = d['config']
    asta = asta_finta(d, cfg)
    ctx = contesto(d, cfg, asta)

    # 1. nessuna domanda deve far esplodere niente
    domande = ['quanto vale Dimarco?', 'come sto messo?', 'cosa mi manca?',
               'difensore da 20 crediti', 'chi resta in attacco?',
               'chi puo rilanciarmi?', 'occasioni adesso', 'aiuto',
               'quanto ha Squadra 3?', 'ma quindi domani piove?', '',
               'Dimarco o Bastoni?', 'posso arrivare a 90 su Thuram?']
    rotte = []
    for q in domande:
        try:
            r = C.rispondi(q, ctx)
            if not r.get('titolo') or not r.get('corpo'):
                rotte.append(q)
        except Exception as err:
            rotte.append('%s (%s)' % (q, err))
    prova('nessuna domanda fa saltare il consulente', not rotte,
          '; '.join(rotte[:3]) if rotte else '%d domande' % len(domande))

    # 2. i tranelli: parole comuni che contengono cognomi veri
    tranelli = [('come sto messo?', 'Come stai messo'),
                ('chi resta in attacco?', 'resta'),
                ('cosa mi manca?', 'Cosa ti manca'),
                ('occasioni adesso', 'ccasioni')]
    sbagliati = [q for q, atteso in tranelli
                 if atteso.lower() not in C.rispondi(q, ctx)['titolo'].lower()]
    prova('le parole comuni non diventano cognomi', not sbagliati,
          'sbagliate: %s' % ', '.join(sbagliati) if sbagliati else
          'quanto vale / attacco / manca')

    # 3. gli omonimi: chiedo quale, tranne quando lo hai gia' detto tu
    casi = [('Thuram', 'thuram'), ('Thuram K.', 'khephren'),
            ('Lautaro', 'quale'), ('Lautaro Martinez', 'martinez')]
    male = [q for q, atteso in casi
            if atteso not in C.rispondi(q, ctx)['titolo'].lower()]
    prova('gli omonimi vengono sciolti', not male,
          'sbagliati: %s' % ', '.join(male) if male else 'Thuram, Lautaro, Martinez')

    # 4. il verdetto sull'offerta deve cambiare con la cifra
    libero = next(p for p in sorted(d['giocatori'], key=lambda x: -x['valore'])
                  if p['id'] not in asta['acquisti'])
    residuo = ctx['sit']['residuo']
    bassa = C.rispondi('%s a 5' % libero['nome'], ctx)['corpo']
    alta = C.rispondi('%s a %d' % (libero['nome'], residuo * 3), ctx)['corpo']
    prova('sotto il massimo dice di si', 'Sì' in bassa or 'sotto il mio massimo' in bassa,
          '%s a 5 crediti' % libero['nome'])
    prova('oltre i crediti dice di no', 'Non puoi' in alta,
          'offerta da %d con %d crediti' % (residuo * 3, residuo))

    # 5. il prezzo di aggiudicazione: chi non ha crediti non fa prezzo
    att = ctx['attesi']
    liberi = [p for p in sorted(d['giocatori'], key=lambda x: -x['valore'])
              if p['id'] not in asta['acquisti']][:40]
    coerenti = [p for p in liberi
                if att[p['id']]['atteso'] <= max(1, ctx['massimi'][p['id']] * 3)]
    prova('il prezzo atteso resta nel mondo reale', len(coerenti) == len(liberi),
          '%d giocatori controllati' % len(liberi))

    senza_rivali = [p for p in liberi if not att[p['id']]['quanti']]
    prova('chi non ha compratori costa un credito',
          all(att[p['id']]['atteso'] == 1 for p in senza_rivali),
          '%d senza compratori' % len(senza_rivali))

    # il tetto di ogni squadra non puo' essere superato dal prezzo atteso
    tetti = max(ctx['offerta_massima'](i) for i in range(len(asta['squadre'])))
    sforati = [p for p in liberi if att[p['id']]['atteso'] > tetti + 1]
    prova('nessuno paga piu di quanto ha in tasca', not sforati,
          'tetto massimo della lega: %d' % tetti)

    # 6. il domino: un acquisto sopra prezzo muove i simili
    import copy
    import mercato as MK2
    bersaglio = next(p for p in liberi if p['R'] == 'D')
    asta2 = copy.deepcopy(asta)
    asta2['acquisti'][bersaglio['id']] = {'squadra': 5,
                                          'prezzo': int(ctx['massimi'][bersaglio['id']] * 1.5) + 5}
    cal2 = MK2.calibrazione(d['giocatori'], asta2)
    eq2 = MK2.prezzi_live(d['giocatori'], cfg, asta2, cal2)
    sc2 = MK2.scarsita(d['giocatori'], cfg, asta2)
    m2, _ = MK2.prezzi_massimi(d['giocatori'], cfg, asta2, eq2, sc2)
    v = MK2.variazioni(ctx['massimi'], m2, d['giocatori'], set(asta2['acquisti']))
    prova('strapagare un difensore muove gli altri prezzi', v['quanti'] > 0,
          '%d prezzi mossi (%d su, %d giù)' % (v['quanti'], v['mossi_su'],
                                               v['mossi_giu']))
    saliti_d = [x for x in v['su'] if x['p']['R'] == 'D']
    prova('a salire sono soprattutto i difensori',
          len(saliti_d) >= len(v['su']) / 2.0 if v['su'] else True,
          '%d difensori su %d in salita' % (len(saliti_d), len(v['su'])))

    # 7. un giocatore gia' venduto non vale "1 credito"
    venduto = next(pid for pid, v in asta['acquisti'].items() if v['squadra'] != 0)
    nome = ctx['per_id'][venduto]['nome']
    r = C.rispondi(nome, ctx)
    prova('i venduti non risultano da 1 credito',
          'venduto' in r['titolo'].lower() and 'Valeva' in r['corpo'], nome)
