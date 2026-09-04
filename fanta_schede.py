# -*- coding: utf-8 -*-
"""Scarica le schede giocatore da fantacalcio.it e ne estrae eta', altezza e lo
stato giornata per giornata (titolare / subentrato / assente) per ogni stagione.

Lo stato giornata per giornata e' la base del modello di rischio disponibilita':
un blocco lungo di assenze consecutive e' quasi sempre un infortunio, mentre
assenze sparse sono rotazione o panchina.

Il download e' incrementale: quello che e' gia' finito in dati/schede.json non viene
riscaricato. Cancella quel file per rifare tutto da capo.

L'HTML grezzo delle schede non viene tenuto: sono 260 MB di pagine da cui servono tre
informazioni, e schede.json le contiene gia' tutte.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import fanta_parse as P
import radice

BASE = radice.cartella()
OUT = os.path.join(BASE, 'dati', 'schede.json')
STAGIONI = ['', '2025-26', '2024-25']
PAUSA = 0.35

CODICI = {'0': 'titolare', '1': 'entrato', '2': 'squalificato',
          '3': 'infortunato', '4': 'assente'}
MESI = {'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
        'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12}

STRIPE_RE = re.compile(r'<ul class="dot-stripe">(.*?)</ul>', re.S)
STATUS_RE = re.compile(r'player-status status-(\w*)"')


def scarica(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    testo = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    time.sleep(PAUSA)
    return testo


NOME_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)


def estrai(h):
    d = {}
    # il nome per esteso, che nel listone non c'e': li' Lautaro Martinez si chiama
    # "Martinez L." e chi lo cerca per nome proprio non lo trova
    m = NOME_RE.search(h)
    if m:
        nome = re.sub(r'<[^>]+>', ' ', m.group(1))
        d['completo'] = re.sub(r'\s+', ' ', nome).strip()[:60]
    testa = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h[:h.find('donut-summary')]))
    m = re.search(r'Nato il (\d{1,2}) (\w{3})\w* (\d{4})', testa)
    if m:
        d['nascita'] = '%s-%02d-%02d' % (m.group(3), MESI.get(m.group(2)[:3].lower(), 1),
                                         int(m.group(1)))
    m = re.search(r'Altezza (\d+)\s*cm', testa)
    if m:
        d['altezza'] = int(m.group(1))
    seg = h[h.find('donut-summary'):][:6000]
    for lab in ['Titolare', 'Entrato', 'Squalificato', 'Infortunato', 'Inutilizzato']:
        i = seg.find('>' + lab + '<')
        m = re.search(r'itemprop="value">([^<]*)</span>', seg[i:i + 400]) if i > 0 else None
        if m and '-' in m.group(1):
            d[lab.lower()] = int(m.group(1).split('-')[0].strip())
    # la striscia di stato: prendo la piu' lunga della pagina
    strisce = [STATUS_RE.findall(b) for b in STRIPE_RE.findall(h)]
    strisce = [s for s in strisce if s]
    # stringa vuota se la pagina non ha la striscia: cosi' la scheda risulta
    # comunque gia' scaricata e al giro dopo non la richiedo di nuovo
    s = max(strisce, key=len) if strisce else []
    d['stati'] = ''.join(c if c else '.' for c in s)
    return d


def main():
    listone = P.parse_listone()
    stats = {s: P.parse_stats('stats_%s.html' % s) for s in STAGIONI if s}
    out = {}
    if os.path.exists(OUT):
        out = json.load(open(OUT, encoding='utf-8'))

    lavori = []
    for p in listone:
        for st in STAGIONI:
            chiave = st or 'corrente'
            # le stagioni passate le chiedo solo a chi in quella stagione c'era
            if st and p['id'] not in stats.get(st, {}):
                continue
            gia = out.get(p['id'], {}).get(chiave)
            # la stagione in corso la rifaccio se le manca il nome per esteso:
            # e' un campo aggiunto dopo, e senza non si cerca per nome proprio
            if gia is not None and (st or 'completo' in gia):
                continue
            lavori.append((p, st, chiave))

    print('schede da scaricare: %d' % len(lavori))
    errori = 0
    for n, (p, st, chiave) in enumerate(lavori, 1):
        url = 'https://www.fantacalcio.it/serie-a/squadre/%s/%s/%s%s' % (
            p['team_slug'], p['slug'], p['id'], '/' + st if st else '')
        try:
            h = scarica(url)
            out.setdefault(p['id'], {})[chiave] = estrai(h)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            errori += 1
            print('  errore %s %s: %s' % (p['nome'], chiave, e))
        if n % 100 == 0:
            print('  %d/%d' % (n, len(lavori)))
            json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('fatto: %d giocatori, %d errori' % (len(out), errori))


if __name__ == '__main__':
    sys.exit(main())
