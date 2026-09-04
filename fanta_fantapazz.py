# -*- coding: utf-8 -*-
"""Legge il listone di Fantapazz, che tiene una propria quotazione di mercato.

Serve come secondo parere sul prezzo: il FVM di fantacalcio.it e la quotazione di
Fantapazz sono due stime indipendenti, e dove non vanno d'accordo c'e' quasi sempre
qualcosa da capire.

La scala e' diversa (Fantapazz quota Svilar 36 dove l'altro dice 18), quindi i numeri
grezzi non si possono confrontare: la normalizzazione la fa il modello.

Nota: SosFanta ha una sezione quotazioni ma ripubblica il listone ufficiale di Leghe
Fantacalcio, cioe' lo stesso FVM che ho gia'. Come terzo parere non aggiungerebbe nulla.
"""
import html as H
import os
import re
import sys

import radice

BASE = radice.cartella()
PAGINA = os.path.join(BASE, 'dati', 'html', 'fantapazz.html')
URL = 'https://www.fantapazz.com/fantacalcio/listone-e-quotazioni'

RIGA_RE = re.compile(r'<tr\s*>(.*?)</tr>', re.S)
RUOLO_RE = re.compile(r"<span class='Ruolo Ruolo_\d+'>([PDCA])</span>")
NOME_RE = re.compile(r'<td class="Calciatore">(.*?)</td>', re.S)
QUOTA_RE = re.compile(r'<td class="Quotazione">(.*?)</td>', re.S)
CLUB_RE = re.compile(r'<td class="Club">(.*?)</td>', re.S)


def pulisci(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def parse(percorso=PAGINA):
    if not os.path.exists(percorso):
        return []
    doc = open(percorso, encoding='utf-8').read()
    out = []
    for m in RIGA_RE.finditer(doc):
        blocco = m.group(1)
        nome = NOME_RE.search(blocco)
        quota = QUOTA_RE.search(blocco)
        if not nome or not quota:
            continue
        ruolo = RUOLO_RE.search(blocco)
        club = CLUB_RE.search(blocco)
        try:
            valore = float(pulisci(quota.group(1)).replace(',', '.'))
        except ValueError:
            continue
        out.append({
            'nome': pulisci(nome.group(1)),
            'quota': valore,
            'R': ruolo.group(1) if ruolo else '',
            'squadra': pulisci(club.group(1)) if club else '',
        })
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = parse()
    print('calciatori letti da Fantapazz: %d' % len(d))
    import collections
    print('per ruolo:', dict(collections.Counter(x['R'] for x in d)))
    print('senza club:', sum(1 for x in d if not x['squadra']))
    for x in sorted(d, key=lambda x: -x['quota'])[:8]:
        print('  %-18s %-4s %-4s %g' % (x['nome'], x['R'], x['squadra'], x['quota']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
