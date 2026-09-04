# -*- coding: utf-8 -*-
"""Genera FantAiuto.ico: esagono arancione su grafite, nello stile DORFic.

Si lancia una volta sola; l'icona finita sta gia' nella cartella.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

import radice

BASE = radice.cartella()
GRAFITE = (22, 28, 33, 255)
ARANCIO = (255, 106, 0, 255)
ROSSO = (222, 44, 28, 255)
BIANCO = (255, 255, 255, 255)

LATO = 1024          # disegno grande e poi rimpicciolisco: bordi puliti
MISURE = [16, 24, 32, 48, 64, 128, 256]


def esagono(cx, cy, r, rotazione=math.pi / 6):
    return [(cx + r * math.cos(rotazione + i * math.pi / 3),
             cy + r * math.sin(rotazione + i * math.pi / 3)) for i in range(6)]


def disegna():
    img = Image.new('RGBA', (LATO, LATO), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = LATO / 2

    # piastrella grafite con l'angolo tagliato in basso a destra
    taglio = LATO * 0.22
    d.polygon([(0, 0), (LATO, 0), (LATO, LATO - taglio), (LATO - taglio, LATO), (0, LATO)],
              fill=GRAFITE)

    # esagono pieno arancione
    d.polygon(esagono(c, c * 0.96, LATO * 0.315), fill=ARANCIO)

    # esagono in filo bianco, piu' grande: le forme specchiate dello stile
    d.polygon(esagono(c, c * 0.96, LATO * 0.415), outline=BIANCO, width=int(LATO * 0.022))

    # taglio obliquo rosso nell'angolo, come le grafiche industriali
    d.polygon([(LATO - taglio, LATO), (LATO, LATO - taglio), (LATO, LATO)], fill=ROSSO)

    # due linee parallele bianche dentro l'esagono
    for k in (-0.10, 0.10):
        y = c * 0.96 + LATO * k
        d.line([(c - LATO * 0.16, y), (c + LATO * 0.16, y)],
               fill=BIANCO, width=int(LATO * 0.028))
    return img


def main():
    img = disegna()
    dest = os.path.join(BASE, 'FantAiuto.ico')
    img.resize((256, 256), Image.LANCZOS).save(
        dest, format='ICO',
        sizes=[(m, m) for m in MISURE])
    img.resize((256, 256), Image.LANCZOS).save(os.path.join(BASE, 'FantAiuto.png'))
    print('icona creata: %s' % dest)
    return 0


if __name__ == '__main__':
    sys.exit(main())
