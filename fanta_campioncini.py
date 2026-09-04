# -*- coding: utf-8 -*-
"""Scarica i ritratti dei calciatori (i "campioncini" di fantacalcio.it).

Servono al campo della pagina Consigli: una formazione con le facce si legge in
un secondo, un elenco di cognomi no.

Li tengo in locale invece di richiamarli dal sito a ogni schermata: sono sei mega
in tutto, e all'asta la connessione e' l'ultima cosa di cui fidarsi. Il download
e' incrementale, e chi non ha il ritratto viene semplicemente saltato: al suo
posto il campo disegna le iniziali.
"""
import os
import sys
import time
import urllib.error
import urllib.request

import radice

BASE = radice.cartella()
CARTELLA = os.path.join(BASE, 'dati', 'campioncini')
URL = 'https://content.fantacalcio.it/web/campioncini/21/small/%s.png'
PAUSA = 0.12


def percorso(pid):
    return os.path.join(CARTELLA, '%s.png' % pid)


def scarica(pid):
    dest = percorso(pid)
    if os.path.exists(dest):
        return os.path.getsize(dest) > 0
    req = urllib.request.Request(URL % pid, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        dati = urllib.request.urlopen(req, timeout=30).read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        # niente ritratto per questo giocatore: segno il buco con un file vuoto
        # cosi' al prossimo giro non lo richiedo di nuovo
        open(dest, 'wb').close()
        return False
    with open(dest, 'wb') as f:
        f.write(dati)
    time.sleep(PAUSA)
    return True


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(CARTELLA, exist_ok=True)
    import fanta_parse as P
    listone = P.parse_listone()
    mancanti = [p for p in listone if not os.path.exists(percorso(p['id']))]
    print('ritratti da scaricare: %d' % len(mancanti))
    presi = 0
    for n, p in enumerate(mancanti, 1):
        if scarica(p['id']):
            presi += 1
        if n % 150 == 0:
            print('  %d/%d' % (n, len(mancanti)))
    totali = sum(1 for p in listone if os.path.getsize(percorso(p['id'])) > 0
                 if os.path.exists(percorso(p['id'])))
    print('fatto: %d nuovi, %d ritratti disponibili su %d calciatori'
          % (presi, totali, len(listone)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
