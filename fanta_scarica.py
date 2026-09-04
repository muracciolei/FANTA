# -*- coding: utf-8 -*-
"""Scarica da fantacalcio.it tutte le pagine che servono all'app.

Le pagine che non cambiano piu' (statistiche di stagioni concluse, voti di
giornate gia' giocate) vengono scaricate una volta sola e riusate dalla cache in
dati/html/. Tutto il resto viene riscaricato a ogni giro.
"""
import os
import re
import sys
import time
import urllib.error
import urllib.request

import radice

BASE = radice.cartella()
HTML = os.path.join(BASE, 'dati', 'html')
STAGIONE = '2026-27'
STAGIONI_PASSATE = ['2025-26', '2024-25', '2023-24']
PAUSA = 0.4


def prendi(url, nome, riusa=False):
    """Scarica url in dati/html/nome. Con riusa=True salta se gia' presente."""
    dest = os.path.join(HTML, nome)
    if riusa and os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return open(dest, encoding='utf-8').read()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    testo = urllib.request.urlopen(req, timeout=90).read().decode('utf-8', 'replace')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(testo)
    time.sleep(PAUSA)
    return testo


def giornata_giocata(html):
    """Una giornata e' giocata se la pagina voti contiene voti veri."""
    voti = re.findall(r'player-grade " data-value="([^"]*)"', html)
    return sum(1 for v in voti if v not in ('', '0')) > 50


def main():
    os.makedirs(HTML, exist_ok=True)
    passi = []

    passi.append(('listone e quotazioni', lambda: prendi(
        'https://www.fantacalcio.it/quotazioni-fantacalcio', 'quotazioni.html')))
    passi.append(('statistiche stagione in corso', lambda: prendi(
        'https://www.fantacalcio.it/statistiche-serie-a', 'stats_%s.html' % STAGIONE)))
    for s in STAGIONI_PASSATE:
        passi.append(('statistiche %s' % s, (lambda s=s: prendi(
            'https://www.fantacalcio.it/statistiche-serie-a/%s' % s,
            'stats_%s.html' % s, riusa=True))))
    passi.append(('indisponibili', lambda: prendi(
        'https://www.fantacalcio.it/indisponibili-serie-a', 'indisponibili.html')))
    passi.append(('probabili formazioni (fantacalcio.it, riserva)', lambda: prendi(
        'https://www.fantacalcio.it/probabili-formazioni-serie-a', 'probabili.html')))
    # SosFanta: probabili con percentuale di titolarita', ballottaggi e
    # indisponibili con la giornata di rientro. E' la fonte principale.
    passi.append(('probabili e indisponibili (SosFanta)', lambda: prendi(
        'https://www.sosfanta.com/lista-formazioni/probabili-formazioni-serie-a/',
        'sos_formazioni.html')))

    for nome, fn in passi:
        try:
            fn()
            print('  ok  %s' % nome)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print('  KO  %s: %s' % (nome, e))

    # calendario: tutte le 38 giornate (le passate restano in cache)
    ultima_giocata = 0
    for g in range(1, 39):
        try:
            prendi('https://www.fantacalcio.it/serie-a/calendario/%d' % g,
                   'calendario_%02d.html' % g, riusa=(g <= ultima_giocata))
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print('  KO  calendario %d: %s' % (g, e))
    print('  ok  calendario (38 giornate)')

    # voti: giornata per giornata, mi fermo alla prima non ancora giocata
    for g in range(1, 39):
        nome = 'voti_%s_%02d.html' % (STAGIONE, g)
        gia = os.path.exists(os.path.join(HTML, nome))
        try:
            h = prendi('https://www.fantacalcio.it/voti-fantacalcio-serie-a/%s/%d'
                       % (STAGIONE, g), nome, riusa=gia and g < ultima_giocata)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print('  KO  voti giornata %d: %s' % (g, e))
            break
        if not giornata_giocata(h):
            os.remove(os.path.join(HTML, nome))
            break
        ultima_giocata = g
    print('  ok  voti fino alla giornata %d' % ultima_giocata)
    return 0


if __name__ == '__main__':
    sys.exit(main())
