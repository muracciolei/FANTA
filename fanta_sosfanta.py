# -*- coding: utf-8 -*-
"""Legge le probabili formazioni di SosFanta.

Rispetto alla fonte precedente qui c'e' molto di piu': ogni giocatore ha la
percentuale di probabilita' di scendere in campo, ci sono i ballottaggi con le
rispettive quote, e gli indisponibili dicono in quale giornata e' atteso il
rientro. Sono esattamente le tre cose che al modello mancavano.

Tutto e' gia' nell'HTML della pagina, non serve un browser.
"""
import html as H
import os
import re
import sys

import radice

BASE = radice.cartella()
PAGINA = os.path.join(BASE, 'dati', 'html', 'sos_formazioni.html')
URL = 'https://www.sosfanta.com/lista-formazioni/probabili-formazioni-serie-a/'

ARTICOLO_RE = re.compile(r'<article\b(.*?)</article>', re.S)
SQUADRA_RE = re.compile(r'<h2[^>]*>([^<]+)</h2>')
MODULO_RE = re.compile(r'text-primary">\s*(\d(?:-\d)+)\s*</span>')
DATA_RE = re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}:\d{2})')
SEZIONE_RE = re.compile(r'<h3[^>]*>\s*(Titolari|Ballottaggi|Panchina|Indisponibili)\s*</h3>',
                        re.I)
UL_RE = re.compile(r'<ul\b[^>]*>(.*?)</ul>', re.S)
LI_RE = re.compile(r'<li\b[^>]*>(.*?)</li>', re.S)
NOME_RE = re.compile(r'truncate">\s*([^<]+?)\s*</span>', re.S)
PERC_RE = re.compile(r'>\s*(\d{1,3})%\s*<')
STATO_RE = re.compile(r'title="([^"]+)"')
DESCR_RE = re.compile(r'text-\[#7b809a\]">\s*(.*?)\s*</span>', re.S)
RIENTRO_RE = re.compile(r'per\s+la\s+(\d{1,2})\s*a\b', re.I)


def pulisci(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def sezioni(articolo):
    """Spezza l'articolo della partita nelle sue quattro sezioni."""
    out = {}
    tagli = list(SEZIONE_RE.finditer(articolo))
    for i, m in enumerate(tagli):
        fine = tagli[i + 1].start() if i + 1 < len(tagli) else len(articolo)
        out[m.group(1).capitalize()] = articolo[m.end():fine]
    return out


def due_liste(blocco):
    """In ogni sezione la prima lista e' la squadra di casa, la seconda l'ospite."""
    liste = UL_RE.findall(blocco)
    return (liste + ['', ''])[:2]


def giocatori(lista):
    out = []
    for li in LI_RE.findall(lista):
        nome = NOME_RE.search(li)
        if not nome:
            continue
        perc = PERC_RE.search(li)
        out.append({'nome': pulisci(nome.group(1)),
                    'perc': int(perc.group(1)) if perc else None})
    return out


def ballottaggi(lista):
    out = []
    for li in LI_RE.findall(lista):
        testo = NOME_RE.search(li)
        if not testo:
            continue
        quote = [int(x) for x in PERC_RE.findall(li)]
        parti = [p.strip() for p in pulisci(testo.group(1)).split(' - ')]
        if len(parti) == 2:
            out.append({'favorito': parti[0], 'sfidante': parti[1],
                        'quote': quote[:2]})
    return out


def indisponibili(lista):
    out = []
    for li in LI_RE.findall(lista):
        nome = NOME_RE.search(li)
        if not nome:
            continue
        stato = STATO_RE.search(li)
        descr = DESCR_RE.search(li)
        nota = pulisci(descr.group(1)) if descr else ''
        rientro = RIENTRO_RE.search(nota)
        out.append({
            'nome': pulisci(nome.group(1)),
            'tipo': (stato.group(1) if stato else 'Indisponibile'),
            'nota': nota,
            'rientro': int(rientro.group(1)) if rientro else None,
        })
    return out


def parse(percorso=PAGINA):
    if not os.path.exists(percorso):
        return {'squadre': {}, 'partite': []}
    doc = open(percorso, encoding='utf-8').read()
    squadre, partite = {}, []
    for m in ARTICOLO_RE.finditer(doc):
        art = m.group(1)
        nomi = [pulisci(x) for x in SQUADRA_RE.findall(art)]
        if len(nomi) < 2:
            continue
        moduli = MODULO_RE.findall(art)
        data = DATA_RE.search(art)
        sez = sezioni(art)

        tit = due_liste(sez.get('Titolari', ''))
        bal = due_liste(sez.get('Ballottaggi', ''))
        pan = due_liste(sez.get('Panchina', ''))
        ind = due_liste(sez.get('Indisponibili', ''))

        partita = {'casa': nomi[0], 'trasferta': nomi[1],
                   'data': data.group(1) if data else '',
                   'ora': data.group(2) if data else ''}
        partite.append(partita)
        for lato, i in (('casa', 0), ('trasferta', 1)):
            squadre[nomi[i]] = {
                'modulo': moduli[i] if i < len(moduli) else '',
                'avversario': nomi[1 - i],
                'in_casa': lato == 'casa',
                'data': partita['data'], 'ora': partita['ora'],
                'titolari': giocatori(tit[i]),
                'ballottaggi': ballottaggi(bal[i]),
                'panchina': giocatori(pan[i]),
                'indisponibili': indisponibili(ind[i]),
            }
    return {'squadre': squadre, 'partite': partite}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = parse()
    print('partite: %d  squadre: %d' % (len(d['partite']), len(d['squadre'])))
    for nome, s in list(d['squadre'].items())[:3]:
        print('\n== %s (%s) vs %s, %s %s'
              % (nome, s['modulo'], s['avversario'], s['data'], s['ora']))
        print('   titolari    :', ', '.join('%s %s%%' % (g['nome'], g['perc'])
                                            for g in s['titolari']))
        print('   ballottaggi :', '; '.join('%s %s%% / %s %s%%'
                                            % (b['favorito'], b['quote'][0],
                                               b['sfidante'], b['quote'][1])
                                            for b in s['ballottaggi'] if len(b['quote']) == 2))
        print('   panchina    : %d giocatori' % len(s['panchina']))
        for x in s['indisponibili']:
            print('   fuori       : %-16s %-14s rientro %s  %s'
                  % (x['nome'], x['tipo'], x['rientro'], x['nota'][:60]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
