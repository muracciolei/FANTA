# -*- coding: utf-8 -*-
"""Trasforma le pagine in dati/html/ in un unico dataset: dati/dataset.json."""
import glob
import html as H
import json
import os
import re
import sys

import fanta_sosfanta as SOS
import radice

BASE = radice.cartella()
HTML = os.path.join(BASE, 'dati', 'html')
OUT = os.path.join(BASE, 'dati', 'dataset.json')
STAGIONE = '2026-27'

RIGA_RE = re.compile(r'<tr class="player-row"(.*?)</tr>', re.S)
ATTR_RE = re.compile(r'data-([a-z-]+)="([^"]*)"')
CELLA_RE = re.compile(r'data-col-key="([^"]+)"[^>]*>(.*?)</t[dh]>', re.S)
LINK_RE = re.compile(r'<a class="player-name player-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
HREF_RE = re.compile(r'/squadre/([^/]+)/([^/]+)/(\d+)')
MANTRA_RE = re.compile(r'role role-mantra" data-value="([^"]+)"')

MESI = {'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
        'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11,
        'dicembre': 12}


def pulisci(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def numero(s):
    s = pulisci(s).replace('.', '').replace(',', '.')
    if s in ('', '-', 'ND'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def leggi(nome):
    p = os.path.join(HTML, nome)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None


# ------------------------------------------------------------ listone e stats
def righe_giocatore(doc):
    for m in RIGA_RE.finditer(doc):
        blk = m.group(0)
        link = LINK_RE.search(blk)
        if not link:
            continue
        hm = HREF_RE.search(link.group(1))
        if not hm:
            continue
        yield {
            'id': hm.group(3),
            'slug': hm.group(2),
            'team_slug': hm.group(1),
            'nome': pulisci(link.group(2)),
            'attr': dict(ATTR_RE.findall(blk)),
            'celle': {k: pulisci(v) for k, v in CELLA_RE.findall(blk)},
            'mantra': [x.upper() for x in MANTRA_RE.findall(blk)],
        }


def parse_listone():
    doc = leggi('quotazioni.html')
    out = []
    for r in righe_giocatore(doc):
        c = r['celle']
        out.append({
            'id': r['id'], 'nome': r['nome'], 'slug': r['slug'],
            'team_slug': r['team_slug'], 'squadra': c.get('sq', ''),
            'R': (r['attr'].get('filter-role-classic') or '').upper(),
            'RM': r['mantra'],
            'qi': numero(c.get('c_qi')), 'qa': numero(c.get('c_qa')),
            'fvm': numero(c.get('c_fvm')),
        })
    return out


def parse_stats(nome):
    doc = leggi(nome)
    out = {}
    if not doc:
        return out
    for r in righe_giocatore(doc):
        c = r['celle']
        rig = pulisci(c.get('rig', ''))
        rs = rt = None
        if '/' in rig:
            a, b = rig.split('/')[:2]
            rs, rt = numero(a), numero(b)
        out[r['id']] = {
            'nome': r['nome'], 'squadra': c.get('sq', ''),
            'R': (r['attr'].get('filter-role-classic') or '').upper(),
            'pv': numero(c.get('pg')), 'mv': numero(c.get('mv')), 'fm': numero(c.get('mfv')),
            'gol': numero(c.get('gol')), 'gs': numero(c.get('gs')), 'ass': numero(c.get('ass')),
            'amm': numero(c.get('amm')), 'esp': numero(c.get('esp')),
            'rig_seg': rs, 'rig_tir': rt, 'rig_par': numero(c.get('rp')),
        }
    return out


# ------------------------------------------------------------------ voti
BONUS_ORDINE = ['gol', 'gs', 'autogol', 'rig_seg', 'rig_sba', 'rig_par', 'ass', 'mvp']
TR_RE = re.compile(r'<tr>(.*?)</tr>', re.S)
# Il cartellino non e' un dato a se': e' una classe CSS attaccata al voto —
# <span class="player-grade yellow-card"> — e per questo la riga di un ammonito
# non somigliava alle altre. La vecchia regola pretendeva la classe esatta
# "player-grade " e buttava via quelle righe: dieci giocatori a giornata, sempre
# gli stessi, sempre gli ammoniti. Ora la classe la leggo invece di ignorarla, e
# in cambio ho i cartellini giornata per giornata.
GRADE_RE = re.compile(r'<span class="player-grade([^"]*)" data-value="([^"]*)"></span>\s*'
                      r'<span class="player-fanta-grade[^"]*" data-value="([^"]*)"></span>')
BONUS_RE = re.compile(r'<span class="player-bonus cell (?:bonus|malus)" data-value="([^"]*)"')
SUBENTRO_RE = re.compile(r'title="Subentrato"')


def voto(s):
    """I voti a volte sono scritti "5,5" e a volte "55": normalizzo su scala 0-10.

    La soglia e' 30 e non 10, e non e' un dettaglio: il fantavoto puo' superare il 10
    per davvero — Malen alla prima giornata ha fatto tre gol e ha preso 17,5 — mentre un
    voto scritto senza virgola parte da 30 in su solo se e' "35", "55", "65". Con la
    soglia sbagliata i fantavoti alti finivano divisi per dieci, cioe' i giocatori che
    avevano fatto la partita della vita risultavano i peggiori della giornata.
    """
    v = numero(s)
    if v is not None and v >= 30:
        v = v / 10.0
    return v


def parse_voti(giornata):
    doc = leggi('voti_%s_%02d.html' % (STAGIONE, giornata))
    out = {}
    if not doc:
        return out
    for m in TR_RE.finditer(doc):
        blk = m.group(1)
        link = LINK_RE.search(blk)
        if not link:
            continue
        hm = HREF_RE.search(link.group(1))
        if not hm:
            continue
        voti = GRADE_RE.findall(blk)
        if not voti:
            continue
        classe, v, fv = voti[0][0], voto(voti[0][1]), voto(voti[0][2])
        if v is None:
            continue
        bonus = [numero(x) or 0 for x in BONUS_RE.findall(blk)]
        d = {'v': v, 'fv': fv, 'sub': bool(SUBENTRO_RE.search(blk)),
             'amm': 1 if 'yellow' in classe else 0,
             'esp': 1 if 'red' in classe else 0}
        for i, k in enumerate(BONUS_ORDINE):
            if i < len(bonus):
                d[k] = bonus[i]
        out[hm.group(3)] = d
    return out


# --------------------------------------------------------- indisponibili
CARD_RE = re.compile(r'<div id="team-\d+" class="card team-card">(.*?)(?=<div id="team-\d+" '
                     r'class="card team-card">|</main>)', re.S)
NOME_SQ_RE = re.compile(r'<span class="team-name">([^<]+)</span>')
SEZIONE_RE = re.compile(r'aria-label="(Infortunati|Squalificati|Diffidati)"', re.I)
ITEM_RE = re.compile(r'<strong class="item-name">([^<]*)</strong>\s*'
                     r'(?:<div class="item-description">(.*?)</div>)?', re.S)


def parse_indisponibili():
    doc = leggi('indisponibili.html')
    out = []
    if not doc:
        return out
    for m in CARD_RE.finditer(doc):
        blocco = m.group(1)
        sq = NOME_SQ_RE.search(blocco)
        squadra = pulisci(sq.group(1)) if sq else '?'
        # divido il blocco squadra nelle sue sezioni
        tagli = [(t.start(), t.group(1).capitalize()) for t in SEZIONE_RE.finditer(blocco)]
        for i, (pos, tipo) in enumerate(tagli):
            fine = tagli[i + 1][0] if i + 1 < len(tagli) else len(blocco)
            for it in ITEM_RE.finditer(blocco[pos:fine]):
                nome = pulisci(it.group(1))
                if not nome or nome.lower() == 'nessuno':
                    continue
                out.append({'squadra': squadra, 'tipo': tipo, 'nome': nome,
                            'nota': pulisci(it.group(2) or '')})
    return out


# ------------------------------------------------------------- calendario
STATUS_RE = re.compile(r'data-match-status="(\d+)"')
SQUADRA_RE = re.compile(r'itemprop="(homeTeam|awayTeam)".*?/squadre/([a-z0-9-]+)"', re.S)
SCORE_RE = re.compile(r'<span class="score-home">(\d*)</span>.*?'
                      r'<span class="score-away">(\d*)</span>', re.S)
DATA_RE = re.compile(r'<span class="date h6[^>]*>\s*([^<]+)')


def parse_calendario():
    out = []
    for f in sorted(glob.glob(os.path.join(HTML, 'calendario_*.html'))):
        g = int(re.search(r'calendario_(\d+)', f).group(1))
        doc = open(f, encoding='utf-8').read()
        # associo a ogni partita l'ultima intestazione di data che la precede
        date = [(m.start(), pulisci(m.group(1))) for m in DATA_RE.finditer(doc)]
        liste = [m.group(1) for m in
                 re.finditer(r'<ul class="match-list">(.*?)</ul>', doc, re.S)]
        principale = ''.join(liste)
        base = doc.find(principale[:200]) if principale else 0
        doc_p = principale
        tagli = [m for m in STATUS_RE.finditer(doc_p)]
        for i, m in enumerate(tagli):
            fine = tagli[i + 1].start() if i + 1 < len(tagli) else len(doc_p)
            blocco = doc_p[m.start():fine]
            sq = dict(SQUADRA_RE.findall(blocco))
            if 'homeTeam' not in sq or 'awayTeam' not in sq:
                continue
            sc = SCORE_RE.search(blocco)
            giocata = m.group(1) != '0'
            data = ''
            for pos, testo in date:
                if pos < base + m.start():
                    data = testo
            out.append({
                'giornata': g, 'casa': sq['homeTeam'], 'trasferta': sq['awayTeam'],
                'data': data, 'giocata': giocata,
                'gol_casa': int(sc.group(1)) if giocata and sc and sc.group(1) else None,
                'gol_trasferta': int(sc.group(2)) if giocata and sc and sc.group(2) else None,
            })
    return out


# -------------------------------------------------------- probabili XI
PITCH_RE = re.compile(r'<div class="team team-(home|away)" data-team-formation="([^"]*)">'
                      r'(.*?)</ul>', re.S)


def parse_probabili():
    doc = leggi('probabili.html')
    out = {}
    if not doc:
        return out
    # ogni partita: prima i due <label> con le squadre, poi i due blocchi campo
    blocchi = doc.split('class="pitch"')
    for i in range(1, len(blocchi)):
        testa = blocchi[i - 1]
        sq = dict(SQUADRA_RE.findall(testa[-6000:]))
        campi = PITCH_RE.findall('<div class="team team-' +
                                 blocchi[i].split('<div class="team team-', 1)[-1]
                                 if '<div class="team team-' in blocchi[i] else '')
        for lato, modulo, corpo in campi[:2]:
            nome_sq = sq.get('homeTeam' if lato == 'home' else 'awayTeam')
            if not nome_sq:
                continue
            ids = [m.group(3) for m in
                   (HREF_RE.search(l.group(1)) for l in LINK_RE.finditer(corpo)) if m]
            if ids:
                out[nome_sq] = {'modulo': modulo, 'xi': ids}
    return out


# ------------------------------------------------------------------- main
def main():
    schede = {}
    p = os.path.join(BASE, 'dati', 'schede.json')
    if os.path.exists(p):
        schede = json.load(open(p, encoding='utf-8'))

    voti = {}
    for g in range(1, 39):
        v = parse_voti(g)
        if v:
            voti[str(g)] = v

    dati = {
        'stagione': STAGIONE,
        'listone': parse_listone(),
        'stats': {s: parse_stats('stats_%s.html' % s)
                  for s in [STAGIONE, '2025-26', '2024-25', '2023-24']},
        'voti': voti,
        'indisponibili': parse_indisponibili(),
        'calendario': parse_calendario(),
        'probabili': parse_probabili(),
        'sos': SOS.parse(),
        'schede': schede,
    }
    json.dump(dati, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)

    print('listone        %d' % len(dati['listone']))
    for s, v in dati['stats'].items():
        print('stats %-8s %d' % (s, len(v)))
    print('voti giornate  %s' % sorted(int(k) for k in voti))
    print('indisponibili  %d' % len(dati['indisponibili']))
    print('calendario     %d partite (%d giocate)'
          % (len(dati['calendario']), sum(1 for x in dati['calendario'] if x['giocata'])))
    print('probabili XI   %d squadre (riserva fantacalcio.it)' % len(dati['probabili']))
    print('SosFanta       %d squadre, %d partite'
          % (len(dati['sos']['squadre']), len(dati['sos']['partite'])))
    print('schede         %d giocatori' % len(schede))
    return 0


if __name__ == '__main__':
    sys.exit(main())
