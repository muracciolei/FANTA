# -*- coding: utf-8 -*-
"""Gli stemmi delle venti squadre.

Servono all'interfaccia: una riga con lo stemma si riconosce prima di una riga con
la sigla, e in una tabella di seicento calciatori il colpo d'occhio conta.

Il nome del file non e' indovinabile — atalanta2026_d.png, inter2021_d.png,
sassuolooriginal_d.png — quindi non provo a costruirlo: lo leggo dalla pagina delle
quotazioni, dove ogni riga di squadra porta il suo stemma accanto al nome. Sono
venti immagini da tre kilobyte, si scaricano una volta e restano li'.
"""
import html as H
import os
import re
import sys
import time
import urllib.error
import urllib.request

import radice

BASE = radice.cartella()
PAGINA = os.path.join(BASE, 'dati', 'html', 'quotazioni.html')
CARTELLA = os.path.join(BASE, 'dati', 'loghi')
RIGA_RE = re.compile(
    r'<tr data-name="([^"]+)"[^>]*>.*?src="(https://content\.fantacalcio\.it'
    r'/web/img/team/ico/[^"]+\.png)"', re.S)


def sigla(nome, listone):
    """Dal nome esteso alla sigla di tre lettere usata ovunque nel programma."""
    n = nome.strip().lower()
    for p in listone:
        if (p.get('squadra_estesa') or '').lower() == n:
            return p['squadra']
        if (p.get('team_slug') or '').lower() == n.replace(' ', '-'):
            return p['squadra']
    return None


def coppie():
    """(nome squadra, indirizzo dello stemma) dalla pagina delle quotazioni."""
    if not os.path.exists(PAGINA):
        return []
    doc = open(PAGINA, encoding='utf-8').read()
    fuori, visti = [], set()
    for nome, url in RIGA_RE.findall(doc):
        nome = H.unescape(nome).strip()
        if nome not in visti:
            visti.add(nome)
            fuori.append((nome, url))
    return fuori


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(CARTELLA, exist_ok=True)
    import fanta_parse as P
    listone = P.parse_listone()
    per_nome = {}
    for p in listone:
        per_nome.setdefault((p.get('team_slug') or '').replace('-', ' ').lower(),
                            p['squadra'])

    presi = saltati = 0
    for nome, url in coppie():
        codice = per_nome.get(nome.lower())
        if not codice:
            # la pagina scrive "Verona", il listone dice "Hellas Verona": provo
            # a incrociare sull'inizio del nome
            codice = next((v for k, v in per_nome.items()
                           if k.startswith(nome.lower()[:4])), None)
        if not codice:
            print('  ? nessuna sigla per %s' % nome)
            continue
        dest = os.path.join(CARTELLA, '%s.png' % codice)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            saltati += 1
            continue
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            dati = urllib.request.urlopen(req, timeout=30).read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as err:
            print('  KO %s: %s' % (nome, err))
            continue
        with open(dest, 'wb') as f:
            f.write(dati)
        presi += 1
        time.sleep(0.15)
    quanti = len([x for x in os.listdir(CARTELLA) if x.endswith('.png')])
    print('stemmi: %d nuovi, %d gia presenti, %d in tutto' % (presi, saltati, quanti))
    return 0


if __name__ == '__main__':
    sys.exit(main())
