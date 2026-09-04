# -*- coding: utf-8 -*-
"""Conta di chi parlano le redazioni, e in che termini.

Non leggo gli articoli per capirli: leggo titoli e sommari delle rubriche di
consigli e asta, cerco i nomi del listone e guardo con quali parole compaiono.
Ne esce un segnale grezzo ma onesto — *quante testate lo stanno indicando, e come*
— che serve a due cose: far emergere le scommesse di cui si parla, e segnalare i
nomi su cui qualcuno mette in guardia.

Non e' un parere di merito, e' un termometro di quanto un giocatore e' sulla bocca
di tutti. Che all'asta conta, perche' i nomi molto citati si pagano di piu'.
"""
import html as H
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

import radice

BASE = radice.cartella()
CARTELLA = os.path.join(BASE, 'dati', 'html')
OUT = os.path.join(BASE, 'dati', 'redazioni.json')
PAUSA = 0.4

PAGINE = [
    ('SosFanta', 'https://www.sosfanta.com/consigli-fantacalcio/', 'sos_consigli.html'),
    ('SosFanta', 'https://www.sosfanta.com/consigli-fantacalcio/pagina-2/',
     'sos_consigli2.html'),
    ('SosFanta', 'https://www.sosfanta.com/asta-fantacalcio/', 'sos_asta.html'),
    ('SosFanta', 'https://www.sosfanta.com/guida-asta-fantacalcio/', 'sos_guida.html'),
    ('SosFanta', 'https://www.sosfanta.com/chi-schierare-fantacalcio/', 'sos_schierare.html'),
    ('fantacalcio.it', 'https://www.fantacalcio.it/consigli-fantacalcio',
     'fc_consigli.html'),
    ('fantacalcio.it', 'https://www.fantacalcio.it/consigli-fantacalcio/portieri',
     'fc_consigli_p.html'),
    ('fantacalcio.it', 'https://www.fantacalcio.it/consigli-fantacalcio/difensori',
     'fc_consigli_d.html'),
    ('fantacalcio.it', 'https://www.fantacalcio.it/consigli-fantacalcio/centrocampisti',
     'fc_consigli_c.html'),
    ('fantacalcio.it', 'https://www.fantacalcio.it/consigli-fantacalcio/attaccanti',
     'fc_consigli_a.html'),
]

# come parlano di un giocatore, non se e' forte: il tono del titolo
PAROLE_PRO = ['sottovalutat', 'scommess', 'occasion', 'da prendere', 'affare',
              'low cost', 'a poco prezzo', 'conviene', 'puntare', 'sorpres',
              'da comprare', 'colpo', 'chi prendere', 'consigliat']
PAROLE_CONTRO = ['attenzione', 'trappol', 'sopravvalutat', 'evitare', 'rischio',
                 'perche no', 'non comprare', 'dubbi', 'flop', 'delusion',
                 'da evitare']

TITOLO_RE = re.compile(r'<h[1-4][^>]*>\s*(?:<a[^>]*>)?\s*([^<]{12,200})', re.S)
SOMMARIO_RE = re.compile(r'<p[^>]*>([^<]{40,400})</p>', re.S)


def pulisci(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def senza_accenti(s):
    s = unicodedata.normalize('NFKD', s or '')
    return ''.join(c for c in s if not unicodedata.combining(c))


def scarica(url, nome):
    dest = os.path.join(CARTELLA, nome)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        testo = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(testo)
        time.sleep(PAUSA)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print('  KO %s: %s' % (nome, e))
    return open(dest, encoding='utf-8').read() if os.path.exists(dest) else ''


def articoli():
    """Titoli e sommari delle rubriche di consigli, con la testata che li firma."""
    out = []
    for fonte, url, nome in PAGINE:
        doc = scarica(url, nome)
        if not doc:
            continue
        pezzi = [pulisci(t) for t in TITOLO_RE.findall(doc)]
        pezzi += [pulisci(t) for t in SOMMARIO_RE.findall(doc)]
        visti = set()
        for t in pezzi:
            if len(t) < 20 or t in visti:
                continue
            visti.add(t)
            out.append({'fonte': fonte, 'testo': t})
    return out


def nome_cercabile(nome):
    """Dal nome del listone ricavo la parola da cercare nei titoli.

    "Martinez L." si cerca come "Martinez", "Paz N." come "Paz". I nomi troppo
    corti o troppo comuni li scarto: un falso positivo qui vale meno di zero.
    """
    base = re.sub(r'\s+[A-Z][a-z]?\.$', '', nome).strip()
    base = base.split(' ')[-1] if ' ' in base and len(base.split(' ')[-1]) > 4 else base
    return base if len(base) >= 5 else None


COMUNI = {'rossi', 'russo', 'conti', 'costa', 'ferrari', 'greco', 'marino', 'colombo',
          'bruno', 'gallo', 'villa', 'monti', 'bianco', 'grande'}


def analizza(listone):
    testi = articoli()
    grezzi = []
    for p in listone:
        n = nome_cercabile(p['nome'])
        if n and senza_accenti(n).lower() not in COMUNI:
            grezzi.append((p, n))

    # due Thuram nello stesso campionato: se il cognome da solo e' ambiguo, la
    # citazione conta solo quando il testo porta anche l'iniziale del nome.
    # Attribuire un consiglio al fratello sbagliato sarebbe peggio che non contarlo.
    quanti = {}
    for _, n in grezzi:
        quanti[n] = quanti.get(n, 0) + 1

    cercabili = []
    for p, n in grezzi:
        rex = re.compile(r'\b%s\b' % re.escape(n))
        iniziale = None
        if quanti[n] > 1:
            m = re.search(r'\b([A-Z][a-z]?)\.', p['nome'])
            if not m:
                continue
            iniziale = re.compile(r'\b%s\.?\s*%s\b|\b%s\s+%s\.'
                                  % (re.escape(m.group(1)), re.escape(n),
                                     re.escape(n), re.escape(m.group(1))))
        cercabili.append((p, n, rex, iniziale))

    out = {}
    for a in testi:
        t = a['testo']
        piano = senza_accenti(t).lower()
        pro = any(k in piano for k in PAROLE_PRO)
        contro = any(k in piano for k in PAROLE_CONTRO)
        for p, n, rex, iniziale in cercabili:
            if not rex.search(t):
                continue
            if iniziale is not None and not iniziale.search(t):
                continue
            v = out.setdefault(p['id'], {'citazioni': 0, 'pro': 0, 'contro': 0,
                                         'fonti': set(), 'titoli': []})
            v['citazioni'] += 1
            v['pro'] += 1 if pro else 0
            v['contro'] += 1 if contro else 0
            v['fonti'].add(a['fonte'])
            if len(v['titoli']) < 4:
                v['titoli'].append(t[:150])
    for v in out.values():
        v['fonti'] = sorted(v['fonti'])
    return {'articoli': len(testi), 'giocatori': out}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(CARTELLA, exist_ok=True)
    import fanta_parse as P
    listone = P.parse_listone()
    d = analizza(listone)
    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    per = {p['id']: p for p in listone}
    print('brani letti: %d  ·  giocatori citati: %d' % (d['articoli'], len(d['giocatori'])))
    top = sorted(d['giocatori'].items(), key=lambda x: -x[1]['citazioni'])[:12]
    for pid, v in top:
        print('  %-20s citazioni %-3d pro %-2d contro %-2d  %s'
              % (per.get(pid, {}).get('nome', pid), v['citazioni'], v['pro'],
                 v['contro'], v['titoli'][0][:70] if v['titoli'] else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
