# -*- coding: utf-8 -*-
"""I gol attesi: quanto uno *costruisce*, non quanto gli e' riuscito.

Tutte le fonti del programma dicono cos'e' successo — cinque gol, due assist,
sette ammonizioni. Nessuna dice quanto quei numeri siano ripetibili, e all'asta
e' la domanda che conta: chi ha segnato cinque gol su tre occasioni vere sta per
tornare sulla terra, chi ne ha costruite dieci senza segnare sta per esplodere.

Gli expected goals rispondono a questo. Ogni tiro vale una frazione di gol
secondo la posizione, il piede, la pressione: la somma e' quanti gol un
giocatore *avrebbe segnato* con un realizzatore nella media. Chi sta molto sopra
il suo xG ha avuto una settimana fortunata, e la fortuna non si compra a
centoventi crediti.

Understat li pubblica per la Serie A senza chiedere account. Da li' arrivano
anche due cose che nessun'altra nostra fonte ha:

- i **minuti veri**, invece delle presenze: uno che entra all'ottantottesimo
  oggi vale come uno che ne ha giocati novanta, e questo gonfia le proiezioni
  di tutte le riserve;
- **xGChain**, quanto un giocatore partecipa alle azioni che finiscono in gol
  anche quando non segna e non serve l'assist: e' la misura di quanto pesa nel
  gioco della squadra, che finora avevo approssimato coi soli bonus.

L'abbinamento coi nostri calciatori e' la parte delicata — li' si chiamano
"Lautaro Martínez", nel listone "Martinez L." — e funziona solo perche' il
programma si porta dietro i nomi per esteso. Chi non viene abbinato con
sicurezza resta senza xG: meglio un dato mancante di un dato di un altro.
"""
import difflib
import gzip
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import fanta_modello as M
import radice

BASE = radice.cartella()
GREZZO = os.path.join(BASE, 'dati', 'html', 'understat.json')
OUT = os.path.join(BASE, 'dati', 'understat.json')
URL = 'https://understat.com/main/getPlayersStats/'
STAGIONE = '2026'

# Understat chiama le squadre all'inglese: quasi tutte combaciano con i nostri
# slug, queste no
ALIAS_SQUADRA = {
    'ac milan': 'milan',
    'parma calcio 1913': 'parma',
    'hellas verona': 'verona',
    'internazionale': 'inter',
}


def scarica(stagione=STAGIONE):
    """Una richiesta sola per aggiornamento, e la risposta la tengo su disco."""
    corpo = urllib.parse.urlencode({'league': 'Serie_A', 'season': stagione}).encode()
    req = urllib.request.Request(URL, data=corpo, headers={
        'User-Agent': 'Mozilla/5.0 (FantAiuto, uso personale)',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded'})
    grezzo = urllib.request.urlopen(req, timeout=60).read()
    if grezzo[:2] == b'\x1f\x8b':
        grezzo = gzip.decompress(grezzo)
    testo = grezzo.decode('utf-8', 'replace')
    os.makedirs(os.path.dirname(GREZZO), exist_ok=True)
    with open(GREZZO, 'w', encoding='utf-8') as f:
        f.write(testo)
    return json.loads(testo)


def leggi_grezzo():
    if not os.path.exists(GREZZO):
        return None
    try:
        with open(GREZZO, encoding='utf-8') as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def squadre_di(voce):
    """Un giocatore ceduto a gennaio risulta con due squadre, separate da virgola."""
    fuori = []
    for pezzo in (voce.get('team_title') or '').split(','):
        k = M.chiave(pezzo.strip())
        fuori.append(M.chiave(ALIAS_SQUADRA.get(pezzo.strip().lower(), pezzo.strip())))
    return [x for x in fuori if x]


def cognome(nome):
    """L'ultima parola del nome, che nel listone italiano e' quasi sempre quella
    che compare da sola."""
    pezzi = [p for p in (nome or '').split() if len(p) > 1]
    return M.chiave(pezzi[-1]) if pezzi else ''


def pezzi_nome(nome):
    """Tutte le parole del nome, non solo l'ultima.

    "Matìas Soulè Malvano" nel listone e' "Soulé": il cognome che si usa e'
    quello di mezzo, e cercando solo l'ultima parola non lo si trova mai. Gli
    spagnoli e i sudamericani portano due cognomi, e non c'e' modo di sapere in
    anticipo quale dei due useranno i giornali italiani.
    """
    return [M.chiave(x) for x in (nome or '').split() if len(M.chiave(x)) >= 3]


def forme(p):
    """Come possiamo chiamarlo noi, per confrontarlo con come lo chiamano loro."""
    fuori = {M.chiave(p['nome'])}
    if p.get('nome_completo'):
        fuori.add(M.chiave(p['nome_completo']))
        fuori.add(cognome(p['nome_completo']))
    # "Martinez L." -> "martinez": l'iniziale puntata non aiuta il confronto
    primo = p['nome'].split()[0] if p['nome'].split() else ''
    if len(primo) > 2:
        fuori.add(M.chiave(primo))
    return {x for x in fuori if len(x) >= 3}


def plausibile(nostro, nome_loro):
    """La controprova per gli abbinamenti dedotti, non per quelli esatti.

    Serve per un caso preciso e insidioso: "Kevin Omoruyi" era finito su "Kevin
    Carlos", due giocatori diversi uniti dal nome proprio. La regola e' che a
    fare da prova dev'essere un pezzo di COGNOME — cioe' una parola che non sia
    la prima — e che quella parola si ritrovi nel nome per esteso del nostro
    giocatore. "Douvikas" si ritrova dentro "Anastasios Douvikas", "Omoruyi" non
    si ritrova da nessuna parte dentro "Kevin Carlos".
    """
    mio = M.chiave((nostro.get('nome_completo') or '') + ' ' + nostro['nome'])
    parole = pezzi_nome(nome_loro)
    for parola in parole[1:] or parole:      # salto il nome proprio
        if len(parola) >= 4 and parola in mio:
            return True
    # nomi cortissimi (Dia, Coco): li accetto solo se combaciano per intero
    return bool(parole) and parole[-1] == M.chiave(nostro['nome'])


def abbina(giocatori, voci):
    """Da chi e' chi: per squadra, poi per nome, e solo alla fine per somiglianza.

    L'ordine non e' un dettaglio. Cercare prima la somiglianza farebbe finire
    Thuram su Thuram K.: si parte sempre dalle certezze e si scende.
    """
    per_squadra = {}
    for p in giocatori:
        per_squadra.setdefault(M.chiave(p['team_slug']), []).append(p)

    fuori, presi, orfani = {}, set(), []
    incerti, respinti = [], []
    for v in voci:
        squadre = squadre_di(v)
        candidati = []
        for sq in squadre:
            candidati.extend(per_squadra.get(sq, []))
        if not candidati:      # squadra sconosciuta: cerco in tutto il listone
            candidati = giocatori
        candidati = [p for p in candidati if p['id'] not in presi]

        loro_nome = M.chiave(v['player_name'])
        loro_cognome = cognome(v['player_name'])

        scelto, come = None, ''
        for p in candidati:
            if loro_nome in forme(p):
                scelto, come = p, 'nome intero'
                break
        if not scelto:
            pari = []
            for parola in pezzi_nome(v['player_name']):
                pari = [p for p in candidati if parola in forme(p)]
                if pari:
                    break
            if len(pari) == 1:
                scelto, come = pari[0], 'cognome'
            elif len(pari) > 1:
                # due con lo stesso cognome nella stessa squadra: decide il nome
                vicini = difflib.get_close_matches(
                    loro_nome, [M.chiave(q.get('nome_completo') or q['nome'])
                                for q in pari], n=1, cutoff=0.7)
                if vicini:
                    scelto = next(q for q in pari
                                  if M.chiave(q.get('nome_completo')
                                              or q['nome']) == vicini[0])
                    come = 'cognome + nome'
                else:
                    incerti.append((v['player_name'], [q['nome'] for q in pari]))
        if not scelto:
            indice = {}
            for p in candidati:
                for f in forme(p):
                    indice.setdefault(f, p)
            vicini = difflib.get_close_matches(loro_nome, list(indice), n=1,
                                               cutoff=0.86)
            if not vicini and loro_cognome:
                vicini = difflib.get_close_matches(loro_cognome, list(indice), n=1,
                                                   cutoff=0.88)
            if vicini:
                scelto, come = indice[vicini[0]], 'somiglianza'

        # secondo giro, fuori dalla squadra: il mercato si muove e le due fonti
        # non sono mai allineate lo stesso giorno — Kean per Understat e' ancora
        # alla Fiorentina, per il listone e' gia' al Como. Qui pero' accetto solo
        # prove forti: il nome intero, o una parola che in tutta la Serie A
        # appartiene a un solo giocatore.
        if not scelto:
            liberi = [q for q in giocatori if q['id'] not in presi]
            per_nome = [q for q in liberi if loro_nome in forme(q)]
            if len(per_nome) == 1:
                scelto, come = per_nome[0], 'nome intero, altra squadra'
            else:
                for parola in pezzi_nome(v['player_name']):
                    quali = [q for q in liberi if parola in forme(q)]
                    if len(quali) == 1:
                        scelto, come = quali[0], 'cognome unico, altra squadra'
                        break
                    if len(quali) > 1:
                        incerti.append((v['player_name'],
                                        [q['nome'] for q in quali[:4]]))
                        break

        if scelto and come != 'nome intero' and not plausibile(scelto,
                                                                v['player_name']):
            respinti.append((v['player_name'], scelto['nome'], come))
            scelto = None

        if not scelto:
            orfani.append(v['player_name'])
            continue
        presi.add(scelto['id'])
        fuori[scelto['id']] = misure(v, come)
    return fuori, orfani, incerti, respinti


def misure(v, come=''):
    """I numeri che ci servono, gia' puliti e per novanta minuti dove ha senso."""
    def num(k, virgola=True):
        try:
            return float(v.get(k) or 0)
        except (TypeError, ValueError):
            return 0.0

    minuti = num('time')
    novanta = minuti / 90.0
    gol, xg = num('goals'), num('xG')
    ass, xa = num('assists'), num('xA')
    return {
        'nome_understat': v.get('player_name'),
        'come': come,
        'minuti': int(minuti),
        'partite': int(num('games')),
        'gol': int(gol), 'assist': int(ass), 'gol_su_azione': int(num('npg')),
        'xg': round(xg, 2), 'npxg': round(num('npxG'), 2), 'xa': round(xa, 2),
        'tiri': int(num('shots')), 'passaggi_chiave': int(num('key_passes')),
        'xgchain': round(num('xGChain'), 2),
        'xgbuildup': round(num('xGBuildup'), 2),
        # quanto ha reso rispetto a quanto ha costruito: sopra zero e' stato
        # fortunato, sotto zero e' in credito col pallone
        'scarto_gol': round(gol - xg, 2),
        # senza rigori: i rigori li conta gia' la gerarchia dei rigoristi, e
        # sommarli qui vorrebbe dire penalizzare due volte chi non li tira
        'scarto_azione': round(num('npg') - num('npxG'), 2),
        'scarto_assist': round(ass - xa, 2),
        'xg90': round(xg / novanta, 3) if novanta >= 0.5 else None,
        'xa90': round(xa / novanta, 3) if novanta >= 0.5 else None,
        'xgchain90': round(num('xGChain') / novanta, 3) if novanta >= 0.5 else None,
        'minuti_a_partita': round(minuti / num('games'), 1) if num('games') else None,
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    import fanta_parse as P
    try:
        dati = scarica()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        print('  KO scaricamento: %s' % e)
        dati = leggi_grezzo()
        if not dati:
            print('  nessun dato in cache: salto')
            return 0
    voci = dati.get('players') or []
    print('Understat: %d giocatori scaricati' % len(voci))

    listone = P.parse_listone()
    # il nome per esteso sta nelle schede, ed e' quello che rende possibile
    # l'abbinamento: senza, "Martinez L." non incontra mai "Lautaro Martínez"
    schede = {}
    perc = os.path.join(BASE, 'dati', 'schede.json')
    if os.path.exists(perc):
        with open(perc, encoding='utf-8') as f:
            schede = json.load(f)
    for p in listone:
        p['nome_completo'] = (schede.get(p['id'], {}).get('corrente') or {}).get('completo')

    fuori, orfani, incerti, respinti = abbina(listone, voci)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(fuori, f, ensure_ascii=False)

    quanti = {}
    for v in fuori.values():
        quanti[v['come']] = quanti.get(v['come'], 0) + 1
    print('abbinati %d su %d  (%s)'
          % (len(fuori), len(voci),
             ', '.join('%s %d' % (k, n) for k, n in sorted(quanti.items()))))
    if orfani:
        print('senza corrispondenza: %d' % len(orfani))
        for n in orfani[:12]:
            print('    %s' % n)
    for nome, pari in incerti[:6]:
        print('    ambiguo: %s -> %s' % (nome, ', '.join(pari)))
    if respinti:
        print('scartati perche non convincenti: %d' % len(respinti))
        for loro, nostro, come in respinti[:8]:
            print('    %s -> %s (%s)' % (loro, nostro, come))
    return 0


if __name__ == '__main__':
    sys.exit(main())
