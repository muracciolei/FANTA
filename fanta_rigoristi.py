# -*- coding: utf-8 -*-
"""Le gerarchie dei rigoristi e dei calci piazzati, aggiornate a mercato chiuso.

Dedurre i rigoristi dai rigori tirati l'anno prima e' il modo peggiore di farlo:
la designazione cambia con gli allenatori e non viaggia con il giocatore quando
cambia squadra. Qui prendo l'ordine dichiarato — primo, secondo, terzo — dalla
pagina dei rigoristi di fantacalcio.it, dove ogni nome porta con se' l'id del
giocatore: nessun abbinamento per nome, nessun rischio di sbagliare persona.

Sapere che uno e' il *secondo* rigorista non e' un dettaglio: vale se il primo si
ferma, ed e' esattamente il genere di informazione che all'asta nessuno prezza.
"""
import html as H
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import radice

BASE = radice.cartella()
PAGINA = os.path.join(BASE, 'dati', 'html', 'rigoristi.html')
OUT = os.path.join(BASE, 'dati', 'rigoristi.json')
URL = 'https://www.fantacalcio.it/rigoristi-serie-a'

CARD_RE = re.compile(r'<div id="team-\d+" class="card team-card">(.*?)(?=<div id="team-\d+"'
                     r' class="card team-card">|</main>)', re.S)
NOME_SQ_RE = re.compile(r'<span class="team-name">([^<]+)</span>')
SEZIONE_RE = re.compile(r'<header[^>]*>\s*(Rigori|Calci piazzati)\s*</header>\s*'
                        r'<ol[^>]*>(.*?)</ol>', re.S | re.I)
GIOCATORE_RE = re.compile(r'/squadre/[^/]+/[^/]+/(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*'
                          r'<span>([^<]+)</span>', re.S)


def pulisci(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def scarica():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    testo = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    with open(PAGINA, 'w', encoding='utf-8') as f:
        f.write(testo)
    time.sleep(0.3)
    return testo


def parse(percorso=PAGINA):
    if not os.path.exists(percorso):
        return {'rigori': {}, 'piazzati': {}, 'squadre': {}}
    doc = open(percorso, encoding='utf-8').read()
    rigori, piazzati, squadre = {}, {}, {}
    for m in CARD_RE.finditer(doc):
        blocco = m.group(1)
        sq = NOME_SQ_RE.search(blocco)
        squadra = pulisci(sq.group(1)) if sq else '?'
        for tipo, lista in SEZIONE_RE.findall(blocco):
            ordinati = [(pid, pulisci(nome))
                        for pid, nome in GIOCATORE_RE.findall(lista)]
            dove = rigori if tipo.lower().startswith('rigor') else piazzati
            for posto, (pid, nome) in enumerate(ordinati, 1):
                dove[pid] = {'ordine': posto, 'nome': nome, 'squadra': squadra}
            if dove is rigori and ordinati:
                squadre[squadra] = [n for _, n in ordinati]
    return {'rigori': rigori, 'piazzati': piazzati, 'squadre': squadre}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(os.path.dirname(PAGINA), exist_ok=True)
    try:
        scarica()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as err:
        print('  KO scaricamento: %s' % err)
    d = parse()
    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('rigoristi: %d nomi su %d squadre  ·  calci piazzati: %d nomi'
          % (len(d['rigori']), len(d['squadre']), len(d['piazzati'])))
    for sq, elenco in list(d['squadre'].items())[:6]:
        print('  %-12s %s' % (sq, ' > '.join(elenco)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
