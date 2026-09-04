# -*- coding: utf-8 -*-
"""FantAiuto - assistente per l'asta e per la formazione del fantacalcio.

Avvio:  doppio clic su FantAiuto (menu Start o Desktop)
        oppure  pythonw avvia.py  /  python -m streamlit run app.py
Il vestito grafico (DORFic) sta tutto in tema.py.
"""
import base64
import json
import os
import subprocess
import sys

import streamlit as st

import fanta_modello as M
import consulente as CO
import giudizio as GD
import pag_statistiche as PS
import risorse as R
import strategia as S
import mercato as MK
import pag_chiedimi
import tema as T
import radice

BASE = radice.cartella()
DATI = os.path.join(BASE, 'dati')
ASTA = os.path.join(DATI, 'asta.json')
VAL = os.path.join(DATI, 'valutazioni.json')

RUOLI = ['P', 'D', 'C', 'A']
RUOLO_NOME = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti', 'A': 'Attaccanti'}
RUOLO_SING = {'P': 'Portiere', 'D': 'Difensore', 'C': 'Centrocampista', 'A': 'Attaccante'}
TITOLARI_TIPO = {'P': 1, 'D': 4, 'C': 4, 'A': 2}

st.set_page_config(page_title='FantAiuto', page_icon='⚽', layout='wide',
                   initial_sidebar_state='collapsed')
if 'tema' not in st.session_state:
    st.session_state['tema'] = 'Scuro'
st.markdown(T.foglio(st.session_state['tema'] == 'Scuro'), unsafe_allow_html=True)
# gli stemmi definiti una volta sola: le celle poi li richiamano per classe
st.markdown(R.foglio_stemmi(), unsafe_allow_html=True)


# ------------------------------------------------------------------ dati
@st.cache_data(show_spinner=False, ttl=60)
def carica(mtime):
    # la chiave e' la data di modifica del file, cosi' quando l'aggiornamento
    # automatico riscrive i dati l'app se ne accorge da sola
    return json.load(open(VAL, encoding='utf-8'))


def dati():
    if not os.path.exists(VAL):
        st.error('Manca dati/valutazioni.json. Lancia prima:  python aggiorna.py')
        st.stop()
    return carica(os.path.getmtime(VAL))


def html(x):
    st.markdown(x, unsafe_allow_html=True)


ritratto = R.ritratto
stemma = R.stemma


def squadra_con_stemma(sigla, grande=False):
    return T.stemma(sigla, grande) + T.e(sigla)


@st.cache_data(show_spinner=False, max_entries=4)
def sigle_per_slug(coppie):
    """Da "hellas-verona" a VER. Oggi le prime tre lettere basterebbero, ma vale
    solo finche' non arriva una neopromossa con un nome che non collabora."""
    return dict(coppie)


def sigla_squadra(d, slug):
    m = sigle_per_slug(tuple(sorted({(p['team_slug'], p['squadra'])
                                     for p in d['giocatori'] if p.get('team_slug')})))
    return m.get(slug, (slug or '')[:3].upper())


# --------------------------------------------------------- stato dell'asta
@st.cache_data(show_spinner=False, ttl=600)
def prezzi_di_partenza(mtime, _giocatori, cfg):
    """I prezzi com'erano prima che l'asta cominciasse.

    Servono per la tendenza: dire che Dimarco vale 109 non dice niente, dire che
    era partito da 96 e adesso vale 109 perche' i difensori stanno andando a ruba
    dice cosa fare. Si calcolano una volta e restano in cache: un'asta vuota non
    cambia."""
    vuota = {'squadre': ['x'] * cfg['squadre'], 'mia': 0, 'acquisti': {}}
    cal = MK.calibrazione(_giocatori, vuota)
    equi = MK.prezzi_live(_giocatori, cfg, vuota, cal)
    scar = MK.scarsita(_giocatori, cfg, vuota)
    massimi, _ = MK.prezzi_massimi(_giocatori, cfg, vuota, equi, scar)
    return massimi


def carica_asta(cfg):
    """L'asta e' l'elenco delle squadre della lega piu' tutti gli acquisti fatti,
    di chiunque. Legge anche il vecchio formato a due liste (mia / altrui)."""
    a = {'squadre': [], 'mia': 0, 'acquisti': {}}
    if os.path.exists(ASTA):
        try:
            grezzo = json.load(open(ASTA, encoding='utf-8'))
        except ValueError:
            grezzo = {}
        if 'acquisti' in grezzo:
            a.update(grezzo)
        else:
            for pid, prezzo in (grezzo.get('mia') or {}).items():
                a['acquisti'][pid] = {'squadra': 0, 'prezzo': prezzo}
            for pid, prezzo in (grezzo.get('altrui') or {}).items():
                a['acquisti'][pid] = {'squadra': 1, 'prezzo': prezzo}

    nomi = list(a.get('squadre') or [])
    # tengo almeno tante squadre quante ne dice la configurazione, e non ne tolgo
    # mai una a cui e' gia' stato assegnato qualcuno
    massimo_usato = max([v['squadra'] for v in a['acquisti'].values()] + [-1])
    quante = max(cfg['squadre'], massimo_usato + 1)
    while len(nomi) < quante:
        nomi.append('La mia squadra' if not nomi else 'Squadra %d' % (len(nomi) + 1))
    a['squadre'] = nomi[:quante]
    a['mia'] = min(a.get('mia', 0), len(a['squadre']) - 1)
    return a


def salva_asta(a):
    json.dump(a, open(ASTA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def assegna(asta, pid, squadra, prezzo):
    asta['acquisti'][pid] = {'squadra': int(squadra), 'prezzo': int(prezzo)}
    salva_asta(asta)


def libera(asta, pid):
    asta['acquisti'].pop(pid, None)
    salva_asta(asta)


def miei(asta):
    return MK.miei(asta)


def applica_modificatore_personale(d, asta, cfg):
    """Riscrive il valore di portieri e difensori in base al TUO reparto.

    Nella media del modificatore entrano il portiere e i tre difensori migliori:
    il quarto e il quinto servono per poterlo schierare ma nella media non ci
    vanno. Quindi il valore di un difensore non e' un numero assoluto — dipende
    da chi hai gia'. Il primo difensore da voto alto vale tantissimo, il quarto
    quasi niente. Nessun listino stampato puo' dirtelo: bisogna guardare la tua
    rosa, e cambia a ogni acquisto.
    """
    if not cfg['modificatore_difesa']:
        return None
    rif = d.get('blocco_riferimento')
    if not rif:
        return None
    per_id = {p['id']: p for p in d['giocatori']}
    mia = [per_id[pid] for pid in miei(asta) if pid in per_id]
    portieri = sorted([q for q in mia if q['R'] == 'P'],
                      key=lambda x: -x['pv_proiettate'])
    difensori = sorted([q['mv_att'] for q in mia if q['R'] == 'D'], reverse=True)

    def blocco(extra=None):
        por = extra['mv_att'] if (extra and extra['R'] == 'P') else (
            portieri[0]['mv_att'] if portieri else rif['portiere'])
        dif = list(difensori)
        if extra and extra['R'] == 'D':
            dif.append(extra['mv_att'])
        while len(dif) < M.DIFENSORI_NEL_BLOCCO:
            dif.append(rif['difensore'])
        return M.media_blocco(por, dif)

    base = M.punti_modificatore(blocco())
    for q in d['giocatori']:
        if q['R'] not in ('P', 'D') or q['mv_att'] is None:
            q['modificatore_personale'] = 0.0
            continue
        if q['id'] in asta['acquisti']:
            q['modificatore_personale'] = q.get('valore_modificatore', 0.0)
            continue
        guadagno = (M.punti_modificatore(blocco(q)) - base) * q['pv_proiettate']
        q['modificatore_personale'] = guadagno
        q['valore'] = q['valore'] - q.get('valore_modificatore', 0.0) + guadagno
    return {'base': base, 'blocco': blocco(),
            'portieri': len(portieri), 'difensori': len(difensori)}


# ------------------------------------------------- ricalcolo prezzi in asta
# ------------------------------------------------------------- componenti
def testo_rientro(stato, prefisso='Rientro previsto: '):
    """Traduce la previsione di rientro in una frase leggibile."""
    if not stato:
        return ''
    if stato.get('rientro'):
        turni = stato.get('turni_di_stop')
        quando = ('gia\' in dubbio per questa giornata' if not turni
                  else 'fra %d turn%s' % (turni, 'o' if turni == 1 else 'i'))
        data = ' — %s' % stato['data_rientro'] if stato.get('data_rientro') else ''
        return '%s%da giornata%s (%s)' % (prefisso, stato['rientro'], data, quando)
    turni = stato.get('turni_di_stop') or 0
    if turni:
        return '%scirca %d giornate, stima mia dal referto' % (prefisso, turni)
    return ''


def comparatore(p, giocatori, asta, prezzi, massimi):
    """Chi e' paragonabile a questo giocatore, e quanto e' costato.

    E' la domanda vera dell'asta: se Paz N. e' andato a 70, gli altri centrocampisti
    della stessa fascia quanto valgono? Metto in fila i pari-slot piu' vicini per
    valore atteso, segnando quelli gia' venduti col prezzo che hanno spuntato.
    """
    pari = [q for q in giocatori
            if q['R'] == p['R'] and q.get('slot') == p.get('slot') and q['id'] != p['id']]
    if not pari:
        pari = [q for q in giocatori if q['R'] == p['R'] and q['id'] != p['id']]
    pari.sort(key=lambda q: abs(q['valore'] - p['valore']))
    pari = pari[:9]

    venduti = [(q, asta['acquisti'][q['id']]['prezzo']) for q in pari
               if q['id'] in asta['acquisti']]
    html(T.banda('Comparatore · chi vale come %s' % p['nome']))
    if venduti:
        media = sum(pr for _, pr in venduti) / float(len(venduti))
        html(T.nota("Dei suoi pari-fascia ne sono già stati venduti <b>%d</b>, "
                    'a una media di <b>%d crediti</b>. Il tetto che ti propongo qui '
                    "sotto tiene già conto di quei prezzi."
                    % (len(venduti), round(media))))
    else:
        html(T.nota("Nessuno dei suoi pari-fascia è ancora stato venduto: "
                    "il primo prezzo che si farà su questa fascia detta il mercato "
                    'per tutti gli altri.'))

    righe = []
    for q in [p] + pari:
        preso = asta['acquisti'].get(q['id'])
        if preso:
            esito = T.pillola('venduto a %d' % preso['prezzo'], T.GRAFITE)
            sq = T.e(asta['squadre'][preso['squadra']])
        else:
            esito = T.pillola('libero', T.VERDE)
            sq = ''
        righe.append([
            (T.pillola('lui', T.ARANCIO) if q['id'] == p['id'] else '') + T.e(q['nome']),
            T.e(q['squadra']), etichetta_slot(q),
            '%.0f' % q['valore'], '%.2f' % q['fm_att'], '%.0f' % q['pv_proiettate'],
            massimi.get(q['id'], '—') if not preso else '—',
            esito, sq,
        ])
    html(T.tabella([('Calciatore', 'nome'), ('Sq', ''), ('Slot', ''),
                    ('Valore', 'num'), ('FM attesa', 'num'), ('PV', 'num'),
                    ('Max da pagare', 'big'), ('Stato', ''), ('A chi', '')], righe))


def scheda_giocatore(p, prezzo=None, massimo=None, scars=1.0, tetto=None,
                     basi=None, storia=None):
    a, b = st.columns([3, 2])
    with a:
        pill = (T.pillola(RUOLO_SING[p['R']], T.RUOLO_COLORE[p['R']]) +
                T.pillola('rischio ' + p['rischio'], T.RISCHIO_COLORE[p['rischio']]))
        if p.get('eta'):
            pill += T.pillola('%d anni' % p['eta'], '', vuota=True)
        note = ''.join('<li>%s</li>' % T.e(n) for n in p['note'])
        html('<div class="dorf-scheda"><div class="nome">%s<span class="sq">%s</span></div>'
             '<div style="margin-top:.45rem">%s</div><ul>%s</ul></div>'
             % (T.e(p['nome']), T.e(p['squadra']), pill, note))
    with b:
        equo = prezzo if prezzo is not None else p['prezzo_prudente']
        html('<div class="dorf-prezzi">'
             '<div class="dorf-prezzo primo"><span class="et">Max da pagare</span>'
             '<div class="val">%s</div></div>'
             '<div class="dorf-prezzo"><span class="et">Valore equo</span>'
             '<div class="val">%d</div></div>'
             '<div class="dorf-prezzo"><span class="et">Scorte slot</span>'
             '<div class="val">%s</div></div></div>'
             % (massimo if massimo is not None else equo, equo,
                ('%+d%%' % round((scars - 1) * 100)) if scars else '—'))
        if storia:
            html(storia)
        fonti = []
        if p.get('mercato_fc') is not None:
            fonti.append('fantacalcio.it <b>%d</b>' % p['mercato_fc'])
        if p.get('mercato_fp') is not None:
            fonti.append('Fantapazz <b>%d</b>' % p['mercato_fp'])
        discorde = (p.get('discordanza') or 0) >= max(8, 0.4 * (p['prezzo_mercato'] or 1))
        if massimo is not None and tetto is not None and massimo >= tetto:
            html(T.nota("Il tetto qui è la tua borsa, non il suo valore: con i "
                        'crediti che ti restano e gli slot da riempire oltre <b>%d</b> '
                        'non puoi andare.' % tetto, 'allarme'))
        html(T.nota('Mercato secondo le fonti: %s%s<br>'
                    'Slot <b>%s</b> &nbsp;·&nbsp; quotazione di partenza <b>%s</b> '
                    '&nbsp;·&nbsp; attesa 2026/27: fantamedia <b>%.2f</b> su <b>%.0f</b> '
                    'partite a voto, <b>%.0f</b> fantapunti sopra la media di ruolo'
                    % (' &nbsp;·&nbsp; '.join(fonti) or 'nessuna',
                       ' — le due stime non vanno d\'accordo' if discorde else '',
                       ('%s%d' % (p['R'], p['slot'])) if p.get('slot') else 'fuori rosa',
                       int(p['qi'] or 0), p['fm_att'],
                       p['pv_proiettate'], p['valore'])))
    if p['R'] in ('P', 'D') and p.get('modificatore_personale') is not None:
        mp = p['modificatore_personale']
        if abs(mp) >= 0.5:
            html(T.nota('Per il <b>tuo</b> modificatore vale <b>%+.0f</b> fantapunti: '
                        'entrano nella media solo il portiere e i tre difensori col '
                        'voto migliore, quindi quanto ti serve dipende da chi hai '
                        'già preso.' % mp, 'ok' if mp > 2 else ''))
        else:
            html(T.nota('Per il tuo modificatore non aggiunge nulla: nella media '
                        'entrano solo portiere e tre difensori, e il tuo blocco è '
                        'già più alto del suo voto.'))

    stato = p.get('stato_attuale')
    if stato:
        html(T.nota('<b>%s.</b> %s<br>%s' % (T.e(stato['tipo']), T.e(stato.get('nota') or ''),
                                             T.e(testo_rientro(stato))), 'allarme'))

    if basi:
        a2, b2 = st.columns([1, 2])
        with a2:
            html('<div style="font-family:Saira Condensed,sans-serif;text-transform:'
                 'uppercase;letter-spacing:.11em;font-size:.72rem;color:var(--fioco);'
                 'margin-bottom:.2rem">Profilo</div>' + T.radar(profilo(p, basi)))
        with b2:
            forma = [x.get('fv') for x in (p.get('giornate') or [])]
            html('<div style="font-family:Saira Condensed,sans-serif;text-transform:'
                 'uppercase;letter-spacing:.11em;font-size:.72rem;color:var(--fioco);'
                 'margin-bottom:.2rem">Andamento in questa stagione</div>'
                 + T.linea_forma(forma, larghezza=300, altezza=54))
            html(T.nota('Il profilo confronta il giocatore con la media del suo ruolo '
                        'su cinque assi: quanto rende, quanto gioca, quanto è solido '
                        'nel voto, quanto pesa nel gioco della sua squadra e quanto è '
                        'affidabile. Due giocatori con la stessa fantamedia disegnano '
                        'quasi sempre figure diverse, ed è lì che si vede chi ti serve '
                        'davvero.'))

    testo = GD.racconta(p)
    if testo or p.get('verdetto'):
        extra = []
        if p.get('peso_squadra') is not None and p['R'] != 'P':
            extra.append('pesava il <b>%d%%</b> dei bonus del suo club'
                         % round(p['peso_squadra'] * 100))
        if p.get('posizione'):
            extra.append('gioca da <b>%s</b>' % T.e(p['posizione']))
        if p.get('bonus_partita') is not None:
            extra.append('voto <b>%.2f</b> più <b>%+.2f</b> di bonus a partita'
                         % (p['mv_att'], p['bonus_partita']))
        red = p.get('redazioni')
        if red:
            extra.append('citato in <b>%d</b> articoli (%s)'
                         % (red['citazioni'], T.e(', '.join(red['fonti']))))
        html('<div class="dorf-scheda" style="border-left-color:%s">'
             '<div style="font-family:Saira Condensed,sans-serif;text-transform:'
             'uppercase;letter-spacing:.1em;font-size:.8rem;color:#61707C">'
             'Il mio giudizio</div>'
             '<div style="font-size:1.5rem;font-family:Saira Condensed,sans-serif;'
             'font-weight:700;text-transform:uppercase;margin:.1rem 0 .4rem">%s</div>'
             '<div style="font-size:.9rem">%s</div>'
             '<div style="font-size:.82rem;color:#61707C;margin-top:.45rem">%s</div>'
             '</div>'
             % (T.ARANCIO, T.e(p.get('verdetto') or ''), T.e(testo),
                ' &nbsp;·&nbsp; '.join(extra)))

    righe = []
    for s in ['2025-26', '2024-25', '2023-24']:
        r = p['storico'].get(s)
        if not r:
            righe.append([s, '—', '—', '—', '—', '—', '—'])
            continue
        ass = p.get('assenze', {}).get(s)
        righe.append([
            s, r['pv'], r['mv'], r['fm'], r['gol'], r['ass'],
            ('%d infortunio / %d panchina' % (ass['infortunio'], ass['panchina']))
            if ass else '—'])
    html(T.tabella([('Stagione', ''), ('PV', 'num'), ('MV', 'num'), ('FM', 'num'),
                    ('Gol', 'num'), ('Assist', 'num'), ('Giornate fuori', '')], righe))


COLORE_VERDETTO = {'Da prendere': T.VERDE, 'Buon affare': T.VERDE,
                   'Al prezzo giusto': T.FUMO, 'Solo a un credito': T.FUMO,
                   'Occhio': T.ROSSO, 'Aspetta': T.AMBRA, 'Incognita': T.CIANO}


def etichetta_verdetto(p):
    v = p.get('verdetto') or ''
    return T.pillola(v, COLORE_VERDETTO.get(v, T.FUMO)) if v else ''


def etichetta_slot(p):
    """Lo slot e' la fascia del giocatore nel suo ruolo: con 10 squadre i primi 10
    attaccanti sono lo slot 1, cioe' il centravanti titolare di ogni fantallenatore."""
    if not p.get('slot'):
        return T.pillola('fuori', '', vuota=True)
    # sulla pastiglia il testo e' scuro, quindi la tinta dev'essere chiara: le due
    # di prima (blu notte per lo slot 1, grigio ferro per il 3) davano 1,68 e 2,75
    # di contrasto, cioe' illeggibili — e lo slot 1 e' il titolarissimo, la
    # pastiglia che in asta si guarda piu' di tutte
    tinte = ['#FFD166', T.CIANO, '#8FE3C4', T.AMBRA, '#B7C0C8', '#C3CBD2',
             '#CFD6DB', '#DBE0E4']
    return T.pillola('%s%d' % (p['R'], p['slot']),
                     tinte[min(p['slot'] - 1, len(tinte) - 1)])


def riquadro_xg(p):
    """Quanto costruisce contro quanto gli e' riuscito.

    Il numero che conta e' la differenza. Sopra lo zero uno sta segnando piu' di
    quanto le sue occasioni giustifichino, e prima o poi rientra; sotto lo zero
    e' in credito col pallone, e il credito di solito si riscuote.
    """
    v = p.get('xg') or {}
    if not v.get('partite'):
        return T.vuoto('Nessun dato sui gol attesi',
                       'Compare appena mette piede in campo: gli expected goals '
                       'si calcolano sui tiri, e chi non ha ancora giocato non '
                       'ne ha tirato nessuno.')
    scarto = v['scarto_azione']
    box = [
        ('Minuti', v['minuti'], '%d partite, %s a partita'
         % (v['partite'], ('%.0f' % v['minuti_a_partita'])
            if v.get('minuti_a_partita') else '—'), ''),
        ('Gol su azione', v['gol_su_azione'], 'rigori esclusi', ''),
        ('Gol costruiti', '%.2f' % v['npxg'], 'quanto valgono i suoi tiri', 'ciano'),
        ('Differenza', '%+.2f' % scarto,
         'sopra le sue occasioni' if scarto > 0.3
         else 'sotto le sue occasioni' if scarto < -0.3 else 'in linea',
         'rosso' if scarto > 0.9 else 'verde' if scarto < -0.9 else ''),
    ]
    righe = [
        ('Tiri', v['tiri'], 'quanti ne ha calciati'),
        ('Passaggi chiave', v['passaggi_chiave'], 'palle servite a chi ha tirato'),
        ('Assist costruiti', '%.2f' % v['xa'], 'contro %d serviti' % v['assist']),
        ('Peso nel gioco', '%.2f' % (v.get('xgchain90') or 0),
         'xGChain ogni 90 minuti: quanto partecipa alle azioni da gol'),
    ]
    tabella = T.tabella([('Dato', 'nome'), ('Valore', 'num'), ('Cosa vuol dire', 'nota')],
                        [[T.e(a), T.e(str(b)), T.e(c)] for a, b, c in righe])

    coda = ''
    corr = v.get('correzione')
    if corr:
        coda = T.nota('Per questo la fantamedia attesa è stata corretta di '
                      '<b>%+.2f</b>. La correzione è prudente: vale solo per la '
                      'quota di fantamedia che viene da questa stagione, cresce '
                      'con i minuti giocati, e si ferma a poco più della metà '
                      'dello scarto — perché certi attaccanti stanno sopra il '
                      'loro xG per merito, non per fortuna.' % corr)
    return T.riquadri(box) + tabella + coda


def profilo(p, basi):
    """I cinque assi del radar, ognuno riportato fra 0 e 1 rispetto a quello che
    fa un giocatore medio dello stesso ruolo."""
    bf, bm = basi['fm'][p['R']], basi['mv'][p['R']]
    rischio = {'Basso': 1.0, 'Medio': 0.62, 'Alto': 0.28, 'Ignoto': 0.5}
    return [
        ('resa', min(1.0, max(0.0, (p['fm_att'] - bf) / 1.4 + 0.15))),
        ('presenza', min(1.0, p['pv_proiettate'] / 34.0)),
        ('voto', min(1.0, max(0.0, (p['mv_att'] - bm) / 0.55 + 0.4))),
        ('peso', min(1.0, (p.get('peso_squadra') or 0) / 0.22)),
        ('tenuta', rischio.get(p['rischio'], 0.5)),
    ]


ORDINI = {
    'Prezzo massimo': lambda p, pr: -pr.get(p['id'], 0),
    'Valore atteso': lambda p, pr: -p['valore'],
    'Fantamedia attesa': lambda p, pr: -p['fm_att'],
    'Occasioni (vale più di quanto costerà)': lambda p, pr: -(pr.get(p['id'], 0) -
                                                              p['prezzo_mercato']),
    'Partite attese': lambda p, pr: -p['pv_proiettate'],
    'Nome': lambda p, pr: M.chiave(p['nome']),
}


def tabella_listone(sel, massimi, scar, mosse=None):
    """Il listone, ordinato per come si guarda davvero.

    Dodici colonne in fila sono un muro: qui sono quattro discorsi separati da un
    filo verticale. CHI E' (ruolo, nome, squadra) · QUANTO PAGARLO (il massimo, il
    giudizio, la fascia, le scorte rimaste) · QUANTO RENDE (fantamedia, presenze,
    forma) · COSA PUO' ANDARE STORTO (cartellini, rischio). Il prezzo sta subito
    dopo il nome perche' e' la ragione per cui questa tabella esiste.
    """
    tetto = max([massimi.get(p['id'], 1) for p in sel] or [1])
    # chi si e' mosso dall'ultimo colpo di martello: la riga si accende del
    # colore della direzione e si spegne da sola in due secondi
    spostati = {}
    for v in (mosse or {}).get('su', []) + (mosse or {}).get('giu', []):
        spostati[v['p']['id']] = v['delta']
    righe, attributi = [], []
    for p in sel:
        delta = spostati.get(p['id'])
        attributi.append('data-mossa="%s"' % ('su' if delta > 0 else 'giu')
                         if delta else '')
        sc = scar.get((p['R'], p.get('slot')), 1.0)
        prezzo = massimi.get(p['id'], 1)
        forma = [x.get('fv') for x in (p.get('giornate') or [])][-6:]
        righe.append([
            T.pillola(p['R'], T.RUOLO_COLORE[p['R']]),
            '%s<span class="sottonome">%s</span>'
            % (T.e(p['nome']), T.e(' · '.join(p['note'][:2]))),
            squadra_con_stemma(p['squadra']),
            T.con_barra(prezzo, prezzo / float(tetto)) + (
                '<span class="mossa %s">%s%d</span>'
                % ('su' if delta > 0 else 'giu', '+' if delta > 0 else '', delta)
                if delta else ''),
            etichetta_verdetto(p),
            etichetta_fascia(p, sc),
            T.con_barra('%.2f' % p['fm_att'],
                        max(0.0, (p['fm_att'] - 5.6) / 2.2), T.CIANO),
            T.con_barra('%.0f' % p['pv_proiettate'], p['pv_proiettate'] / 38.0,
                        T.VERDE),
            T.linea_forma(forma),
            etichetta_cartellini(p),
            T.pillola(p['rischio'], T.RISCHIO_COLORE[p['rischio']]),
        ])
    return T.tabella(
        [('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
         ('Max da pagare', 'big sep'), ('Giudizio', ''), ('Fascia', ''),
         ('FM att.', 'num sep'), ('PV att.', 'num'), ('Forma', ''),
         ('Cartellini', 'sep'), ('Rischio', '')], righe, alta=True,
        attributi=attributi)


def etichetta_cartellini(p):
    """Quanti cartellini prende in una stagione, sulle stagioni passate.

    Il numero grande e' la media su una stagione intera — e' cosi' che si ragiona
    all'asta, "quello prende dieci gialli l'anno" — e sotto ci sono i totali veri
    da cui viene fuori, perche' dieci gialli in due stagioni piene e dieci in
    mezza stagione non sono la stessa informazione. Passando sopra col mouse
    esce il dettaglio stagione per stagione."""
    c = p.get('cartellini') or {}
    if c.get('amm_stagione') is None:
        return ('<span title="Meno di cinque presenze in Serie A: non c’è '
                'abbastanza storia per dire quanti cartellini prende">%s</span>'
                % T.pillola('?', '', vuota=True))

    colore = (T.ROSSO if c['indice'] == 'Falloso'
              else T.VERDE if c['indice'] == 'Pulito' else '')
    testa = '%.1f' % c['amm_stagione']
    if (c.get('esp_stagione') or 0) >= 0.3:
        testa += ' + %.1f' % c['esp_stagione']

    dettaglio = ' · '.join(
        '%s: %g%s in %g' % (st[2:], v['amm'],
                            ' e %g rossi' % v['esp'] if v['esp'] else '', v['pv'])
        for st, v in sorted((c.get('stagioni') or {}).items(), reverse=True))
    sotto = '%g in %g presenze' % (c['amm_totali'], c['pv_totali'])

    return ('<span title="%s">%s<span class="duplice">%s</span></span>'
            % (T.e(dettaglio), T.pillola(testa, colore, vuota=not colore),
               T.e(sotto)))


def etichetta_fascia(p, s):
    """In che fascia sta e quante ne restano, in una cella sola.

    Erano due colonne, ma sono due lati della stessa domanda — questo giocatore
    e' un titolarissimo o una riserva, e ne trovo ancora di simili? — e messe
    vicine si leggono meglio che separate da mezza tabella."""
    resta = ('agli sgoccioli' if s >= 1.6 else 'scarseggia' if s >= 1.15
             else 'abbondano' if s <= 0.7 else None)
    colore = (T.ROSSO if s >= 1.6 else T.AMBRA if s >= 1.15 else '')
    sotto = ('<span class="duplice" style="color:%s">%s</span>'
             % (colore or 'var(--fioco)', resta)) if resta else ''
    return etichetta_slot(p) + sotto


def etichetta_scarsita(s):
    """Quante alternative restano per quello slot rispetto a quante squadre lo
    cercano ancora: sopra 1 significa che stanno finendo."""
    if s >= 1.6:
        return T.pillola('agli sgoccioli', T.ROSSO)
    if s >= 1.15:
        return T.pillola('scarseggia', T.AMBRA)
    if s <= 0.7:
        return T.pillola('abbondano', '', vuota=True)
    return T.pillola('normale', '', vuota=True)


# --------------------------------------------------------------- pagine
def tendenza(p, massimo, partenza, cal, scar, temp):
    """Quanto e' cambiato il prezzo dall'inizio dell'asta, e per colpa di cosa.

    Un numero da solo non dice se e' il momento di comprare. Sapere che quel
    difensore era partito da 96 e adesso ne vale 109 perche' la lega sta pagando
    la difesa il venti per cento sopra i miei consigli, invece, dice esattamente
    cosa fare: o lo prendi adesso o lo lasci a qualcun altro.
    """
    era = partenza.get(p['id'])
    if not era or era < 3:
        return ''
    delta = massimo - era
    quota = delta / float(era)
    if abs(delta) < 2:
        riga = ('Il prezzo non si è mosso dall\'inizio dell\'asta: era <b>%d</b>, '
                'è <b>%d</b>.' % (era, massimo))
        classe = ''
    else:
        riga = ('Era partito da <b>%d</b>, adesso vale <b>%d</b>: '
                '<span class="%s">%s%d crediti</span> (%s%.0f%%).'
                % (era, massimo, 'su' if delta > 0 else 'giu',
                   '+' if delta > 0 else '', delta,
                   '+' if delta > 0 else '', quota * 100))
        classe = 'ok' if delta < 0 else ''

    # le tre ragioni possibili, in ordine di peso
    cause = []
    f_ruolo = cal['ruoli'].get(p['R'], 1.0)
    if abs(f_ruolo - 1) > 0.08:
        cause.append('la lega sta pagando %s <b>%+d%%</b> rispetto ai miei consigli'
                     % (RUOLO_NOME[p['R']].lower(), round((f_ruolo - 1) * 100)))
    s_slot = scar.get((p['R'], p.get('slot')), 1.0)
    if s_slot >= 1.15:
        cause.append('la sua fascia <b>si sta svuotando</b> (%.1f squadre per ogni '
                     'giocatore rimasto)' % s_slot)
    elif s_slot <= 0.75:
        cause.append('di giocatori come lui <b>ce ne sono ancora tanti</b>')
    if abs(temp['rapporto'] - 1) > 0.12:
        cause.append('nella lega restano <b>%.1f crediti per casella</b> contro i '
                     '%.0f di partenza' % (temp['per_casella'], temp['partenza']))
    # il "perché" ha senso solo se qualcosa è successo: spiegare le ragioni di un
    # prezzo fermo è come giustificare una decisione che non è stata presa
    if cause and abs(delta) >= 2:
        riga += '<br><span style="font-size:.82rem">Perché: %s.</span>' % '; '.join(cause)
    return T.nota(riga, classe)


def pronostico_completo(p, att, massimo):
    """I tre numeri del pronostico piu' la riga che li spiega."""
    if not att:
        return ''
    testa = ''
    if att.get('quanti'):
        testa = T.riquadri_stretti([
            ('Finirà a', att['atteso'], 'prezzo finale', 'ciano'),
            ('Per batterli', att['per_prenderlo'], 'devi offrire',
             'rosso' if att['per_prenderlo'] > massimo + max(2, massimo * .04)
             else 'verde'),
            ('La vogliono', att['quanti'], 'squadre', ''),
        ])
    return testa + CO.pronostico(p, att, massimo)


def pannello_mosse(mosse, temp):
    """Chi e' salito e chi e' sceso dopo l'ultimo acquisto, in una riga sola."""
    def elenco(voci, classe):
        return ' · '.join(
            '<b>%s</b> %s<span class="%s">%s%d</span>'
            % (T.e(v['p']['nome']), v['dopo'], classe,
               '+' if v['delta'] > 0 else '', v['delta']) for v in voci)

    pezzi = []
    if mosse['su']:
        pezzi.append('<b>Salgono:</b> %s' % elenco(mosse['su'], 'su'))
    if mosse['giu']:
        pezzi.append('<b>Scendono:</b> %s' % elenco(mosse['giu'], 'giu'))
    coda = ('<br><span style="font-size:.82rem">Si sono mossi <b>%d</b> prezzi in '
            'tutto (%d su, %d giù). Nella lega restano <b>%.1f crediti per '
            'casella</b> da riempire: %s.</span>'
            % (mosse['quanti'], mosse['mossi_su'], mosse['mossi_giu'],
               temp['per_casella'], temp['stato']))
    return T.nota('<br>'.join(pezzi) + coda)


def banco(d, asta, cfg, sel, prezzi, massimi, scar, tetto_ruoli, attesi,
          partenza=None, cal=None, temp=None):
    """Il banco: il giocatore in battuta, con l'unico numero che conta.

    All'asta il tempo per decidere e' quello che passa fra un rilancio e l'altro.
    Tutto quello che serve in quei secondi sta qui e non si muove: chi e' in
    battuta, quanto pagherei io, fin dove posso arrivare, e fin dove puo'
    arrivare chi mi sta rilanciando contro.
    """
    with st.container(key='banco'):
        nomi = ['%s — %s' % (p['nome'], p['squadra']) for p in sel]
        scelta = st.selectbox('In battuta', nomi, label_visibility='collapsed',
                              placeholder='Chi e\' in battuta?')
        if scelta is None:
            html(T.nota('Scegli chi e\' in battuta.'))
            return
        p = sel[nomi.index(scelta)]

        massimo = massimi.get(p['id'], 1)
        note = []
        if p.get('slot'):
            note.append(('slot %d' % p['slot'], T.CIANO))
        if (p.get('rigorista') or {}).get('ordine') == 1:
            note.append(('rigorista', T.AMBRA))
        if p['rischio'] in ('Alto', 'Medio'):
            note.append(('rischio %s' % p['rischio'].lower(), T.ROSSO
                         if p['rischio'] == 'Alto' else T.AMBRA))
        if p.get('stato_attuale'):
            note.append((p['stato_attuale']['tipo'].lower(), T.ROSSO))
        if p.get('diffidato'):
            note.append(('diffidato', T.AMBRA))
        gia = asta['acquisti'].get(p['id'])
        if gia:
            note.insert(0, ('venduto a %s' % asta['squadre'][gia['squadra']],
                            T.FUMO))
        html(T.carta(p, ritratto(p['id']), None, massimo,
                     'max da pagare', note))

        # il numero da solo non convince nessuno: la ragione per cui lo pago
        # tanto (o per cui non lo pago) deve stare accanto al numero
        pro = (p.get('motivi_pro') or [])[:2]
        contro = (p.get('motivi_contro') or [])[:1]
        if pro or contro:
            html('<div class="perche">%s%s</div>'
                 % (''.join('<span class="si">%s</span>' % T.e(x) for x in pro),
                    ''.join('<span class="no">%s</span>' % T.e(x) for x in contro)))

        mio_tetto = MK.offerta_massima(asta, cfg, asta['mia'])
        loro, nome_loro = MK.rivale_piu_ricco(asta, cfg)
        storia = ''
        if partenza is not None:
            storia = tendenza(p, massimo, partenza, cal, scar, temp)
        if not gia:
            html(pronostico_completo(p, attesi.get(p['id']), massimo))
            if storia:
                html(storia)

        # tre comandi su una riga sola, in una colonna da trecento pixel,
        # significa un menu che mostra "★ l" e un tasto che dice "ASSE…".
        # Meglio due righe: il prezzo e la squadra sopra, il tasto sotto a tutta
        # larghezza — che e' anche piu' facile da colpire mentre si ha fretta.
        c = st.columns([1, 1.35])
        prezzo = c[0].number_input('Prezzo', 1, max(1, cfg['crediti']),
                                   max(1, massimo), key='banco_prezzo')
        ordine_sq = [asta['mia']] + [i for i in range(len(asta['squadre']))
                                     if i != asta['mia']]
        etichette = ['%s%s' % ('★ ' if i == asta['mia'] else '', asta['squadre'][i])
                     for i in ordine_sq]
        a_chi = c[1].selectbox('A chi va', etichette, key='banco_a_chi')
        # "Assegna a La mia squadra" e' scritto male in italiano, e questa e' la
        # frase che si legge mille volte in una serata
        mio = a_chi.startswith('★')
        etichetta_tasto = ('Me lo prendo io' if mio
                           else 'Assegna a %s' % a_chi)
        if st.button(etichetta_tasto, type='primary',
                     use_container_width=True, key='banco_assegna'):
            assegna(asta, p['id'], ordine_sq[etichette.index(a_chi)], int(prezzo))
            st.rerun()

        html(T.righello(int(prezzo), mio_tetto, loro, nome_loro,
                        max(massimo, mio_tetto, loro)))
        if prezzo > massimo:
            html(T.nota('Stai andando <b>%d crediti sopra</b> il massimo che '
                        'consiglierei.' % (prezzo - massimo), 'allarme'))
        elif prezzo > mio_tetto:
            html(T.nota('Con %d crediti non ti resterebbe abbastanza per riempire '
                        'gli slot.' % prezzo, 'allarme'))

        if p['id'] in asta['acquisti']:
            v = asta['acquisti'][p['id']]
            d1, d2 = st.columns([3, 1])
            with d1:
                html(T.nota('Preso da <b>%s</b> per %d crediti.'
                            % (T.e(asta['squadre'][v['squadra']]), v['prezzo'])))
            if d2.button('Libera', use_container_width=True):
                libera(asta, p['id'])
                st.rerun()

        with st.expander('La scheda completa'):
            scheda_giocatore(p, prezzi.get(p['id']), massimo,
                             scar.get((p['R'], p.get('slot')), 1.0), tetto_ruoli,
                             basi={'fm': d['base_fm'], 'mv': d['base_mv']},
                             storia=storia)
        with st.expander('Quanto costruisce'):
            html(riquadro_xg(p))
        with st.expander('Chi gli somiglia'):
            comparatore(p, d['giocatori'], asta, prezzi, massimi)


def pagina_asta(d, asta):
    cfg, giocatori = d['config'], d['giocatori']
    presi = set(asta['acquisti'])
    cal = MK.calibrazione(giocatori, asta)
    prezzi = MK.prezzi_live(giocatori, cfg, asta, cal)
    scar = MK.scarsita(giocatori, cfg, asta)
    massimi, tetto = MK.prezzi_massimi(giocatori, cfg, asta, prezzi, scar)
    attesi = MK.prezzi_attesi(giocatori, cfg, asta, prezzi)
    temp = MK.temperatura(giocatori, cfg, asta)
    partenza = prezzi_di_partenza(os.path.getmtime(VAL), giocatori, cfg)

    # cosa si e' mosso dall'ultimo colpo di martello
    prec = st.session_state.get('scatto_prezzi')
    mosse = None
    if prec and prec['n'] < len(presi):
        mosse = MK.variazioni(prec['massimi'], massimi, giocatori, presi)
        MK.registra_andamento(giocatori, cfg, asta, cal)
    st.session_state['scatto_prezzi'] = {'n': len(presi), 'massimi': dict(massimi)}
    if mosse and (mosse['su'] or mosse['giu']):
        html(pannello_mosse(mosse, temp))

    if cal['venduti'] >= 3:
        def segno(x):
            return ('<span class="su">+%d%%</span>' if x >= 0 else
                    '<span class="giu">%d%%</span>') % round(x)
        pezzi = ['<b>tutta la lega</b> %s' % segno((cal['lega'] - 1) * 100)]
        for ru in RUOLI:
            n = cal['per_ruolo_n'][ru]
            if n:
                pezzi.append('%s %s <span style="color:#9aa4ac">(%d)</span>'
                             % (RUOLO_NOME[ru].lower(),
                                segno((cal['ruoli'][ru] - 1) * 100), n))
        html(T.nota('Rispetto ai miei consigli la lega sta pagando: ' +
                    ' &nbsp;·&nbsp; '.join(pezzi) +
                    '<br><span style="font-size:.82rem">I prezzi qui sotto sono '
                    'gia\' corretti per questo, slot per slot.</span>'))

    lista, destra = st.columns([9.0, 3.0], gap='medium')

    with lista:
        f = st.columns([1.05, 1.05, .75, .95, 1.35, 1.5, .85])
        ruolo = f[0].selectbox('Ruolo', ['Tutti'] + [RUOLO_NOME[r] for r in RUOLI])
        squadra = f[1].selectbox('Squadra',
                                 ['Tutte'] + sorted({p['squadra'] for p in giocatori}))
        slot_f = f[2].selectbox('Slot',
                                ['Tutti'] + [str(i) for i in range(1, 9)] + ['fuori'])
        rischio = f[3].selectbox('Rischio', ['Tutti', 'Basso', 'Medio', 'Alto',
                                             'Ignoto'])
        cerca = f[4].text_input('Cerca')
        ordine = f[5].selectbox('Ordina per', list(ORDINI))
        f[6].markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        nascondi = f[6].checkbox('Solo liberi', True)

        sel = giocatori
        if ruolo != 'Tutti':
            sel = [p for p in sel if RUOLO_NOME[p['R']] == ruolo]
        if squadra != 'Tutte':
            sel = [p for p in sel if p['squadra'] == squadra]
        if slot_f != 'Tutti':
            sel = ([p for p in sel if not p.get('slot')] if slot_f == 'fuori'
                   else [p for p in sel if p.get('slot') == int(slot_f)])
        if rischio != 'Tutti':
            sel = [p for p in sel if p['rischio'] == rischio]
        if cerca:
            k = M.chiave(cerca)
            sel = [p for p in sel if k in M.chiave(p['nome'])]
        if nascondi:
            sel = [p for p in sel if p['id'] not in presi]
        sel = sorted(sel, key=lambda p: ORDINI[ordine](p, massimi))

        html('<div class="titoletto">%d calciatori · %d gia’ venduti in tutta la '
             'lega</div>' % (len(sel), len(presi)))
        if sel:
            html(tabella_listone(sel[:250], massimi, scar, mosse))
        else:
            html(T.nota('Nessun calciatore con questi filtri.'))

    with destra:
        if sel:
            banco(d, asta, cfg, sel, prezzi, massimi, scar, tetto, attesi,
                  partenza, cal, temp)


def riga_giocatore(q, costo, extra=None):
    return [
        T.pillola(q['R'], T.RUOLO_COLORE[q['R']]), etichetta_slot(q),
        T.e(q['nome']), squadra_con_stemma(q['squadra']), costo,
        '%.2f' % q['fm_att'], '%.2f' % q['mv_att'], '%.0f' % q['pv_proiettate'],
        etichetta_verdetto(q),
        T.e(extra if extra is not None
            else ' · '.join((q['motivi_pro'] or q['motivi_contro'])[:1])),
    ]


COL_GIOC = [('R', ''), ('Slot', ''), ('Calciatore', 'nome'), ('Sq', ''),
            ('Max', 'big'), ('FM', 'num'), ('MV', 'num'), ('PV', 'num'),
            ('Giudizio', ''), ('Perché', 'nota')]

SOTTOTITOLO = ('<div style="font-family:Saira Condensed,sans-serif;text-transform:'
               'uppercase;letter-spacing:.1em;font-size:.8rem;color:#61707C;'
               'margin:.7rem 0 .2rem">%s</div>')


def disegna_proposta(r, cfg):
    """Una proposta: intestazione, campo, panchina, e perche' la propongo."""
    f = r['formazione']
    dettagli = ('modulo <b>%s</b> · spesa <b>%d</b> · avanzo <b>%d</b>'
                % (f['modulo'] if f else '—', sum(r['spesa'].values()), r['avanzo']))
    if r['blocco'] and cfg['modificatore_difesa']:
        dettagli += (' · blocco <b>%.2f</b> = <b>%+.1f</b> a giornata'
                     % (r['blocco']['mv'], (f or {}).get('modificatore', 0.0)))
    dettagli += ('<br>P %d · D %d · C %d · A %d'
                 % tuple(r['spesa'][ru] for ru in RUOLI))
    html(T.testata(r['titolo'], dettagli))
    if f:
        html(T.campo(f, foto=ritratto))
        html(T.panchina(f['panchina']))
    html(T.nota(r.get('confronto') or '',
                'ok' if abs(r.get('scarto_punti') or 0) < 1 else ''))
    html('<div class="spiega"><p>%s</p><p class="rischio"><b>Il rischio.</b> %s</p>'
         '</div>' % (T.e(r['idea']), T.e(r.get('rischio') or '')))


def confronto_blocchi(blocchi):
    """La riga che conta: quanto costa passare da un blocco all'altro.

    Il primo blocco e l'ultimo differiscono di oltre cento crediti e di pochi
    centesimi di media. Detto cosi' sembra un dettaglio tecnico; tradotto in
    punti di una stagione, e' la ragione per cui conviene spendere altrove.
    """
    magro, ricco = blocchi[0], blocchi[-1]
    if len(blocchi) < 2 or ricco['costo'] <= magro['costo']:
        return ''
    crediti = ricco['costo'] - magro['costo']
    punti = (ricco['punti'] - magro['punti']) * 38
    per_credito = punti / max(1, crediti)
    giudizio = ('un affare' if per_credito >= 0.5
                else 'un prezzo onesto' if per_credito >= 0.28
                else 'caro: gli stessi crediti rendono di più altrove')
    return T.nota(
        'Dal blocco più magro al più ricco ci sono <b>%d crediti</b> di '
        'differenza, e comprano <b>%.0f punti</b> in una stagione: %.2f punti '
        'per credito. È %s.<br><span style="font-size:.82rem">Per confronto, un '
        'attaccante da cinquanta crediti in più rende in genere fra 0,3 e 0,5 '
        'punti per credito. Il modificatore non è mai una scommessa sbagliata, '
        'ma non è nemmeno un pozzo senza fondo: oltre una certa spesa i decimi '
        'di media costano cari.</span>'
        % (crediti, punti, per_credito, giudizio),
        'ok' if per_credito >= 0.4 else '')


def scheda_blocco(x, massimi):
    """Un blocco: i quattro nomi, cosa rende, e a che prezzo."""
    righe = []
    for n, q in enumerate(x['blocco']):
        ruolo = 'portiere' if q['R'] == 'P' else 'difensore %d' % n
        prezzo = ('già tuo' if q['nome'] in x['gia_miei']
                  else '%d' % massimi.get(q['id'], 1))
        righe.append([
            T.pillola(q['R'], T.RUOLO_COLORE[q['R']]),
            T.e(q['nome']), squadra_con_stemma(q['squadra']),
            '%.2f' % q['mv_att'], '%.0f' % q['pv_proiettate'], prezzo,
            T.e(ruolo),
        ])
    testata = T.testata(
        x['titolo'],
        'costo <b>%d</b> · media <b>%.2f</b> · <b>%+.1f</b> a giornata, '
        '<b>%+.0f</b> in una stagione · %d squadre diverse'
        % (x['costo'], x['mv'], x['punti'], x['punti'] * 38, x['squadre']))
    return testata + T.tabella(
        [('R', ''), ('Calciatore', 'nome'), ('Sq', ''), ('MV attesa', 'big'),
         ('PV', 'num'), ('Costo', 'num'), ('Ruolo nel blocco', 'nota')], righe)


def pagina_consigli(d, asta):
    cfg, giocatori = d['config'], d['giocatori']
    cal = MK.calibrazione(giocatori, asta)
    prezzi = MK.prezzi_live(giocatori, cfg, asta, cal)
    scar = MK.scarsita(giocatori, cfg, asta)
    massimi, tetto = MK.prezzi_massimi(giocatori, cfg, asta, prezzi, scar)
    pia = S.piano(d, asta, cfg, massimi)
    sit = pia['sit']
    proposte = S.sei_proposte(d, asta, cfg, massimi)
    ideale = proposte[0] if proposte else {'spesa': {r: 0 for r in RUOLI},
                                           'avanzo': sit['residuo']}

    html(T.riquadri([
        ('Crediti residui', sit['residuo'], 'da spendere',
         'rosso' if sit['residuo'] < sit['slot_mancanti'] else ''),
        ('Slot da riempire', sit['slot_mancanti'],
         ' · '.join('%s %d' % (r, sit['manca'][r]) for r in RUOLI
                    if sit['manca'][r]) or 'rosa completa', ''),
        ('Rosa proposta', sum(ideale['spesa'].values()),
         'crediti nella prima delle tre', 'ciano'),
        ('Avanzo', ideale['avanzo'], 'per i rilanci', ''),
        ('Tetto per giocatore', tetto, 'oltre non puoi andare', ''),
    ]))

    for tipo, testo in S.avvisi(d, asta, cfg, pia, scar, cal):
        html(T.nota(testo, {'allarme': 'allarme', 'ok': 'ok'}.get(tipo, '')))

    # ------------------------------------------------- le sei proposte
    html(T.banda('Sei rose che farei con i crediti che ti restano',
                 '%d proposte' % len(proposte)))
    html(T.nota("Non sono sei varianti della stessa idea: sono sei convinzioni "
                "diverse su come si vince una lega, e ognuna costruisce la rosa "
                "per servire la sua. <b>La prima non ha vincoli</b>: a ogni "
                "acquisto prende chi rende di più per credito speso, ed è la rosa "
                "che sui numeri fa più punti. Le altre cinque partono da un'idea "
                "— il modificatore vale più dell'attacco, due fuoriclasse valgono "
                "più di undici buoni — e sotto ciascuna trovi <b>quanto costa "
                "preferirla</b>, in punti su una stagione intera. "
                "Il modulo non lo impongo io: lo detta la rosa, perché non ha "
                "senso schierare un 3-4-3 a chi ha cinque difensori buoni e due "
                "attaccanti. In campo l'undici titolare col prezzo massimo che "
                "pagherei; sotto, il resto della rosa."))

    if not proposte:
        html(T.nota('Con i crediti rimasti non riesco a comporre una rosa completa.',
                    'allarme'))

    # tre per riga: sei campi affiancati sarebbero illeggibili
    for inizio in range(0, len(proposte), 3):
        fila = proposte[inizio:inizio + 3]
        colonne = st.columns(3)
        for col, r in zip(colonne, fila):
            with col:
                disegna_proposta(r, cfg)

    # ------------------------------------------------- reparto per reparto
    html(T.banda('Reparto per reparto: le alternative a ogni prezzo'))
    html(T.nota("Per ogni ruolo i migliori disponibili divisi in tre fasce di spesa. "
                "Serve per non restare fermi quando il nome che volevi vola via: "
                "sotto ogni top c'è quasi sempre qualcuno che rende l'ottanta per "
                "cento a un terzo del prezzo."))
    for ru in RUOLI:
        f = S.per_fascia(d, asta, massimi, ru)
        with st.expander('%s — %d top, %d di fascia media, %d low cost'
                         % (RUOLO_NOME[ru], len(f['alto']), len(f['medio']),
                            len(f['basso'])), expanded=(ru == 'A')):
            for et, chiave in (('Da 40 crediti in su', 'alto'),
                               ('Fascia media, da 12 a 39', 'medio'),
                               ('Low cost, sotto i 12', 'basso')):
                if not f[chiave]:
                    continue
                html(SOTTOTITOLO % et)
                html(T.tabella(COL_GIOC,
                               [riga_giocatore(q, massimi.get(q['id'], 1))
                                for q in f[chiave]]))

    # ------------------------------------------------- blocchi difensivi
    if cfg['modificatore_difesa']:
        blocchi = S.blocchi_difesa(d, asta, cfg, massimi)
        html(T.banda('Quanto costa il modificatore',
                     '%d modi di costruirlo' % len(blocchi)))
        html(T.nota(
            "Il modificatore guarda il <b>voto</b> del portiere e dei <b>tre "
            "difensori migliori</b>, non i bonus. Qui non trovi più i blocchi di "
            "una squadra sola — all'asta quattro giocatori dello stesso club non "
            "li prendi quasi mai, o te li soffiano o costano il doppio perché "
            "tutti hanno avuto la stessa idea. Trovi invece <b>lo stesso reparto "
            "comprato a quattro prezzi diversi</b>, pescando in tutto il mercato "
            "rimasto: serve a vedere quanto costa davvero ogni decimo di media."))
        if blocchi:
            html(confronto_blocchi(blocchi))
            for x in blocchi:
                html(scheda_blocco(x, massimi))

    # ------------------------------------------------- occasioni
    html(T.banda('Occasioni: valgono più di quanto costeranno'))
    html(T.nota('Il mio tetto sta sopra il prezzo di mercato: sono i giocatori su cui '
                'gli altri non si scalderanno e che tu puoi prendere sotto valore. '
                'Ordinati per fantapunti ottenuti per credito speso.'))
    html(T.tabella(COL_GIOC,
                   [riga_giocatore(x['p'], x['costo'],
                                   extra='mercato %d, io fino a %d · %.1f fantapunti '
                                         'per credito'
                                         % (x['mercato'], x['costo'], x['resa']))
                    for x in S.occasioni(d, asta, massimi)]))

    # ------------------------------------------------- rigoristi
    html(T.banda('I rigoristi'))
    html(T.nota('Il bonus più prevedibile che esista: tre punti che non dipendono dal '
                'gioco. Attenzione a chi ha cambiato squadra — la designazione non '
                'viaggia col giocatore, e nella rosa nuova la gerarchia è tutta da '
                'rifare.'))
    html(T.tabella(COL_GIOC,
                   [riga_giocatore(x['p'], x['costo'],
                                   extra='%g su %g lo scorso anno%s'
                                         % (x['segnati'], x['tirati'],
                                            ' — ma ha cambiato squadra'
                                            if x['dubbio'] else ''))
                    for x in S.rigoristi(d, asta, massimi)]))

    # ------------------------------------------------- sempre presenti
    html(T.banda('Quelli che non saltano mai'))
    html(T.nota("Trenta o più partite a voto previste. In un campionato da trentotto "
                "giornate la presenza è il bonus più sottovalutato che c'è: un buon "
                "giocatore che gioca sempre batte un fuoriclasse che gioca due volte "
                "su tre, e costa la metà."))
    html(T.tabella(COL_GIOC,
                   [riga_giocatore(q, massimi.get(q['id'], 1))
                    for q in S.sempre_presenti(d, asta, massimi)]))

    # ------------------------------------------------- scommesse
    html(T.banda('Scommesse: poco prezzo, molto margine'))
    piano_s = S.piano_scommesse(d, asta, cfg, massimi)
    html(T.nota(
        "In una rosa da venticinque, i giocatori che decidono il campionato sono "
        "cinque o sei: gli altri diciannove sono il problema che tutti "
        "sottovalutano. Le ultime caselle si riempiono a fine asta, di fretta, con "
        "quello che avanza — ed è lì che si perdono i punti, non sul top pagato "
        "dieci crediti di troppo. Costano poco <b>per il loro reparto</b> — il "
        "metro non è lo stesso per un difensore e per un attaccante, dove il "
        "listino parte più in alto — e hanno una <b>ragione concreta</b> per "
        "rendere di più: l'età, i rigori, un posto da "
        "titolare appena conquistato, il fatto che arrivino da fuori e il mercato "
        "non sappia ancora quanto valgono."))
    if piano_s['da_tenere']:
        html(T.riquadri([
            ('Da tenere da parte', piano_s['da_tenere'],
             'per le scommesse che ti servono', 'ciano'),
            ('Caselle da riempire',
             sum(v['caselle'] for v in piano_s['per_ruolo'].values()),
             'oltre i titolari veri', ''),
            ('Costo medio',
             '%d' % (piano_s['da_tenere']
                     / max(1, sum(v['caselle']
                                  for v in piano_s['per_ruolo'].values()))),
             'crediti a giocatore', ''),
        ]))
    for ru in RUOLI:
        voce = piano_s['per_ruolo'].get(ru)
        if not voce:
            continue
        html(T.banda('%s da scommessa' % RUOLO_NOME[ru],
                     ('%d caselle · %d crediti' % (voce['caselle'], voce['tenere']))
                     if voce['caselle'] else 'reparto completo'))
        if not voce['caselle']:
            html(T.nota('Questo reparto è pieno: se ne prendi un altro è perché '
                        'lo vuoi, non perché ti serve.'))
        html(T.tabella(COL_GIOC,
                       [riga_giocatore(x['p'], x['costo'],
                                       extra=' · '.join(x['motivi'][:3]))
                        for x in voce['quali']]))

    # ------------------------------------------------- redazioni
    citati = sorted([q for q in giocatori
                     if q.get('redazioni') and q['id'] not in asta['acquisti']],
                    key=lambda q: -(q['redazioni']['pro'] * 3
                                    + q['redazioni']['citazioni']))[:16]
    if citati:
        html(T.banda('Di chi parlano le redazioni'))
        html(T.nota("Ho letto titoli e sommari delle rubriche di consigli e asta di "
                    "SosFanta e fantacalcio.it e contato chi viene nominato, e con "
                    "che parole. Non è un parere di merito: è un termometro. I nomi "
                    "molto citati all'asta si pagano sopra il loro valore, e saperlo "
                    "prima ti serve per non rincorrerli."))
        righe = []
        for q in citati:
            r = q['redazioni']
            righe.append(riga_giocatore(
                q, massimi.get(q['id'], 1),
                extra='%d citazioni%s%s · %s'
                      % (r['citazioni'],
                         ', %d come occasione' % r['pro'] if r['pro'] else '',
                         ', %d con cautela' % r['contro'] if r['contro'] else '',
                         r['titoli'][0][:90] if r['titoli'] else '')))
        html(T.tabella(COL_GIOC, righe))

    html(T.nota('Su cosa ragiono: listone e statistiche di quattro stagioni da '
                'fantacalcio.it, probabili formazioni e infermeria da SosFanta, '
                'quotazioni da due fonti, i titoli delle rubriche di consigli di due '
                'testate, e i prezzi reali che stai battendo in questa asta. '
                'Il giudizio su ogni singolo giocatore lo trovi nella sua scheda, '
                'con le ragioni scritte per esteso.'))


def pagina_squadre(d, asta):
    cfg, giocatori = d['config'], d['giocatori']
    per_id = {p['id']: p for p in giocatori}
    slot_tot = sum(cfg['slot'].values())
    n = len(asta['squadre'])

    riepilogo = []
    for i, nome in enumerate(asta['squadre']):
        acq = MK.acquisti_di(asta, i)
        spesi = sum(acq.values())
        residuo = cfg['crediti'] - spesi
        mancanti = slot_tot - len(acq)
        # quanto puo' davvero rilanciare: deve tenere 1 credito per ogni slot
        # che gli resta da riempire dopo questo
        massima = max(0, residuo - max(0, mancanti - 1))
        conta = {r: sum(1 for pid in acq if per_id.get(pid, {}).get('R') == r)
                 for r in RUOLI}
        riepilogo.append({'i': i, 'nome': nome, 'acq': acq, 'spesi': spesi,
                          'residuo': residuo, 'mancanti': mancanti,
                          'massima': massima, 'conta': conta})

    tot_spesi = sum(r['spesi'] for r in riepilogo)
    html(T.riquadri([
        ('Squadre', n, 'nella lega', ''),
        ('Assegnati', len(asta['acquisti']), 'su %d slot totali' % (slot_tot * n), ''),
        ('Crediti spesi', tot_spesi, 'su %d sul tavolo' % (cfg['crediti'] * n), ''),
        ('Ancora in gioco', cfg['crediti'] * n - tot_spesi, 'crediti', 'ciano'),
    ]))

    html(T.banda('Nomi delle squadre'))
    html(T.nota('Scrivi qui i nomi dei tuoi avversari: li ritrovi nel menu a tendina '
                'della pagina Asta, così sai sempre a chi stai assegnando.'))
    with st.form('nomi_squadre'):
        nuovi = []
        colonne = st.columns(5)
        for i, nome in enumerate(asta['squadre']):
            nuovi.append(colonne[i % 5].text_input('Squadra %d' % (i + 1), nome,
                                                   key='ns%d' % i))
        f = st.columns([3, 1])
        quale = f[0].selectbox('Quale di queste sei tu', range(len(asta['squadre'])),
                               index=asta['mia'],
                               format_func=lambda i: nuovi[i] or 'Squadra %d' % (i + 1))
        f[1].markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        salva = f[1].form_submit_button('Salva i nomi', type='primary',
                                        use_container_width=True)
    if salva:
        asta['squadre'] = [n.strip() or 'Squadra %d' % (i + 1)
                           for i, n in enumerate(nuovi)]
        asta['mia'] = int(quale)
        salva_asta(asta)
        st.rerun()

    html(T.banda('Come stanno messe le squadre'))
    righe = []
    for r in sorted(riepilogo, key=lambda x: -x['residuo']):
        etichetta = T.e(r['nome'])
        if r['i'] == asta['mia']:
            etichetta = T.pillola('io', T.ARANCIO) + etichetta
        righe.append([
            etichetta, r['spesi'], r['residuo'], r['massima'],
            '%d/%d' % (len(r['acq']), slot_tot),
            r['conta']['P'], r['conta']['D'], r['conta']['C'], r['conta']['A'],
        ])
    html(T.tabella([('Squadra', 'nome'), ('Spesi', 'num'), ('Residui', 'big'),
                    ('Offerta max', 'num'), ('Rosa', 'num'),
                    ('P', 'num'), ('D', 'num'), ('C', 'num'), ('A', 'num')], righe))
    html(T.nota('<b>Offerta max</b> è quanto quella squadra può davvero mettere su un '
                'singolo giocatore tenendosi un credito per ogni slot che le resta: '
                'è il numero che dice fin dove ti possono rilanciare.'))

    html(T.banda('Rose e acquisti'))
    nomi_gioc = ['%s — %s' % (p['nome'], p['squadra']) for p in giocatori]
    for r in riepilogo:
        titolo = '%s%s — %d crediti spesi, %d residui, %d giocatori' % (
            '★ ' if r['i'] == asta['mia'] else '', r['nome'],
            r['spesi'], r['residuo'], len(r['acq']))
        with st.expander(titolo, expanded=(r['i'] == asta['mia'])):
            for ru in RUOLI:
                dentro = [(per_id[pid], pr) for pid, pr in r['acq'].items()
                          if pid in per_id and per_id[pid]['R'] == ru]
                if not dentro:
                    continue
                righe = [[T.pillola(ru, T.RUOLO_COLORE[ru]), T.e(q['nome']),
                          squadra_con_stemma(q['squadra']), pr,
                          q['prezzo_prudente'],
                          T.scarto(pr - q['prezzo_prudente']),
                          '%.2f' % q['fm_att'],
                          T.pillola(q['rischio'], T.RISCHIO_COLORE[q['rischio']])]
                         for q, pr in sorted(dentro, key=lambda x: -x[1])]
                html(T.tabella([('R', ''), ('Calciatore', 'nome'), ('Sq', ''),
                                ('Pagato', 'big'), ('Consiglio', 'num'),
                                ('Differenza', 'num'), ('FM attesa', 'num'),
                                ('Rischio', '')], righe))
            if not r['acq']:
                html(T.nota('Nessun acquisto ancora.'))

            g = st.columns([2.2, 1, 1, 1])
            agg = g[0].selectbox('Aggiungi un calciatore', ['—'] + nomi_gioc,
                                 key='add%d' % r['i'])
            pr = g[1].number_input('Prezzo', 1, max(1, cfg['crediti']), 1,
                                   key='pr%d' % r['i'])
            g[2].markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
            if g[2].button('Aggiungi', key='b%d' % r['i'], use_container_width=True):
                if agg != '—':
                    assegna(asta, giocatori[nomi_gioc.index(agg)]['id'], r['i'], pr)
                    st.rerun()
            togli = g[3].selectbox('Togli', ['—'] + [per_id[pid]['nome']
                                                     for pid in r['acq']
                                                     if pid in per_id],
                                   key='t%d' % r['i'])
            # prima bastava cambiare il menu e il giocatore era gia' liberato:
            # uno scorrimento di rotellina di troppo e l'acquisto spariva
            if togli != '—' and g[3].button('Conferma', key='ct%d' % r['i'],
                                            use_container_width=True):
                for pid in list(r['acq']):
                    if pid in per_id and per_id[pid]['nome'] == togli:
                        libera(asta, pid)
                        st.rerun()


def pagina_rosa(d, asta):
    cfg = d['config']
    per_id = {p['id']: p for p in d['giocatori']}
    mia = miei(asta)
    rosa = [(per_id[pid], pr) for pid, pr in mia.items() if pid in per_id]
    if not rosa:
        html(T.nota('Non hai ancora segnato nessun acquisto. Vai su <b>Asta</b>, '
                    'scegli il calciatore, lascia la tua squadra nel menu accanto '
                    'e premi <b>Assegna</b>.'))
        return

    spesi = sum(pr for _, pr in rosa)
    html(T.riquadri([
        ('Spesi', spesi, 'crediti', ''),
        ('Residui', cfg['crediti'] - spesi, 'crediti',
         'rosso' if cfg['crediti'] - spesi < 0 else ''),
        ('Rosa', '%d/%d' % (len(rosa), sum(cfg['slot'].values())), 'giocatori', ''),
        ('Valore rosa', '%.0f' % sum(p['valore'] for p, _ in rosa),
         'fantapunti sopra la media', 'ciano'),
        ('A rischio alto', sum(1 for p, _ in rosa if p['rischio'] == 'Alto'),
         'giocatori fragili', 'rosso'),
    ]))

    for ru in RUOLI:
        gruppo = sorted([(p, pr) for p, pr in rosa if p['R'] == ru],
                        key=lambda x: -x[0]['valore'])
        html(T.banda('%s — %d su %d, %d crediti'
                     % (RUOLO_NOME[ru], len(gruppo), cfg['slot'][ru],
                        sum(pr for _, pr in gruppo))))
        if not gruppo:
            html(T.nota('Reparto ancora vuoto.'))
            continue
        righe = []
        for p, pr in gruppo:
            stato = (p['stato_attuale'] or {}).get('tipo')
            righe.append([
                T.e(p['nome']), squadra_con_stemma(p['squadra']),
                pr, p['prezzo_prudente'],
                T.scarto(pr - p['prezzo_prudente']),
                '%.2f' % p['fm_att'], '%.0f' % p['pv_proiettate'],
                etichetta_cartellini(p),
                T.pillola(p['rischio'], T.RISCHIO_COLORE[p['rischio']]),
                T.pillola(stato, T.ROSSO) if stato
                else T.pillola('disponibile', '', vuota=True),
            ])
        html(T.tabella([('Calciatore', 'nome'), ('Sq', ''), ('Pagato', 'big'),
                        ('Consiglio era', 'num'), ('Differenza', 'num'),
                        ('FM attesa', 'num'), ('PV attese', 'num'),
                        ('Gialli/pg', ''), ('Rischio', ''), ('Stato oggi', '')],
                       righe))

    html(T.banda('Come sta messa la rosa'))
    for ru in RUOLI:
        gruppo = [p for p, _ in rosa if p['R'] == ru]
        pezzi = []
        manca = cfg['slot'][ru] - len(gruppo)
        if manca > 0:
            pezzi.append('mancano <b>%d</b> slot' % manca)
        alti = [p['nome'] for p in gruppo if p['rischio'] == 'Alto']
        if alti:
            pezzi.append('a rischio alto: %s' % T.e(', '.join(alti)))
        tit = sorted(gruppo, key=lambda p: -p['valore'])[:TITOLARI_TIPO[ru]]
        if tit:
            pezzi.append('fantamedia attesa dei titolari <b>%.2f</b>'
                         % (sum(p['fm_att'] for p in tit) / len(tit)))
        squalifiche = sum((q.get('cartellini') or {}).get('giornate_squalifica') or 0
                          for q in gruppo)
        if squalifiche >= 2:
            pezzi.append('<b>%.0f</b> giornate di squalifica attese in tutto il '
                         'reparto' % squalifiche)
        html(T.nota('<b>%s</b> — %s' % (RUOLO_NOME[ru], '; '.join(pezzi) or 'a posto')))


def pagina_formazione(d, asta):
    per_id = {p['id']: p for p in d['giocatori']}
    rosa = [per_id[pid] for pid in miei(asta) if pid in per_id]
    if not rosa:
        html(T.nota('Segna prima la tua rosa nella pagina Asta.'))
        return

    consigli = d['consigli']
    voci = []
    for p in rosa:
        c = consigli.get(p['id'], {})
        stato = p['stato_attuale']
        if not c.get('gioca'):
            voci.append({'p': p, 'atteso': None, 'mv': None,
                         'motivo': ((stato or {}).get('tipo')
                                    or c.get('motivo', 'non gioca')),
                         'rientro': (stato or {}).get('rientro'),
                         'turni': (stato or {}).get('turni_di_stop'),
                         'perc': None, 'ballottaggi': [],
                         'avv': c.get('avversario', '—'), 'casa': c.get('in_casa'),
                         'tit': False, 'diff': c.get('difficolta')})
            continue
        voci.append({'p': p, 'atteso': c['atteso'], 'mv': c.get('mv_atteso') or 6.0,
                     'motivo': '', 'rientro': None, 'turni': None,
                     'avv': c['avversario'], 'casa': c['in_casa'],
                     'tit': c['titolare_previsto'], 'diff': c['difficolta'],
                     'perc': c.get('perc'), 'dove': c.get('dove'),
                     'ballottaggi': c.get('ballottaggi') or []})

    schierabili = [v for v in voci if v['atteso'] is not None]
    mod_attivo = bool(d['config'].get('modificatore_difesa'))

    moduli = {'3-4-3': (3, 4, 3), '3-5-2': (3, 5, 2), '4-3-3': (4, 3, 3),
              '4-4-2': (4, 4, 2), '4-5-1': (4, 5, 1), '5-3-2': (5, 3, 2),
              '5-4-1': (5, 4, 1)}
    esiti = {}
    for nome, (nd, nc, na) in moduli.items():
        r = S.scelta_undici(schierabili, nd, nc, na, mod_attivo)
        if r:
            esiti[nome] = r

    if not esiti:
        html(T.riquadri([
            ('Giornata', d['prossima_giornata'], 'prossimo turno', ''),
            ('Schierabili', len(schierabili), 'su %d in rosa' % len(rosa), 'rosso'),
        ]))
        html(T.nota('Con %d giocatori schierabili non esce nessun modulo completo. '
                    'Controlla infortuni e squalifiche.' % len(schierabili), 'allarme'))
        return

    consigliato = max(esiti, key=lambda k: esiti[k]['totale'])
    etichette = ['Scelgo io per te (%s)' % consigliato] + list(moduli)
    scelta = st.selectbox('Modulo', etichette)
    modulo = consigliato if scelta.startswith('Scelgo') else scelta
    if modulo not in esiti:
        html(T.nota('Per il <b>%s</b> non hai abbastanza titolari schierabili: '
                    'ti mostro il <b>%s</b>.' % (modulo, consigliato), 'allarme'))
        modulo = consigliato
    scelto = esiti[modulo]
    titolari = scelto['undici']

    box = [('Giornata', d['prossima_giornata'], 'prossimo turno', ''),
           ('Schierabili', len(schierabili), 'su %d in rosa' % len(rosa), ''),
           ('Punti attesi', '%.0f' % scelto['totale'], 'undici + modificatore', 'ciano')]
    if mod_attivo:
        if scelto['media'] is None:
            box.append(('Modificatore', '0', 'il %s ci rinuncia' % modulo, 'rosso'))
        else:
            box.append(('Modificatore', '+%.1f' % scelto['punti'],
                        'blocco %.2f di media' % scelto['media'],
                        'verde' if scelto['punti'] >= 1 else 'ambra'))
    html(T.riquadri(box))

    def probabile(v):
        if v['atteso'] is None:
            return T.pillola('fuori', T.ROSSO)
        if v['tit']:
            colore = T.VERDE if (v['perc'] or 0) >= 70 else T.AMBRA
            return T.pillola('titolare %s%%' % (v['perc'] or '?'), colore)
        if v.get('dove') == 'panchina':
            return T.pillola('panchina', '', vuota=True)
        return T.pillola('non nelle liste', '', vuota=True)

    def nota_riga(v):
        if v['motivo']:
            pezzi = [v['motivo'].lower()]
            if v.get('rientro'):
                pezzi.append('rientro atteso in %da%s' % (
                    v['rientro'],
                    ', fra %d turni' % v['turni'] if v.get('turni') else ''))
            return T.pillola(' · '.join(pezzi), T.ROSSO)
        pezzi = ['avversario ' + ('difficile' if (v['diff'] or 1) > 1.1
                                  else 'abbordabile' if (v['diff'] or 1) < .9
                                  else 'nella media')]
        for b in v.get('ballottaggi') or []:
            q = b.get('quote') or []
            if len(q) == 2:
                rivale = (b['sfidante'] if M.chiave(b['favorito'])
                          == M.chiave(v['p']['nome']) else b['favorito'])
                pezzi.append('ballottaggio con %s (%d-%d)' % (rivale, q[0], q[1]))
        testo = T.e(' · '.join(pezzi))
        if v['p'].get('diffidato'):
            testo = T.pillola('diffidato', T.AMBRA) + ' ' + testo
        return testo

    nel_blocco = set()
    if scelto['media'] is not None:
        difensori = [v for v in titolari if v['p']['R'] == 'D']
        tre = sorted(difensori, key=lambda v: -v['mv'])[:M.DIFENSORI_NEL_BLOCCO]
        nel_blocco = {v['p']['id'] for v in tre} | {titolari[0]['p']['id']}

    def righe_da(elenco):
        out = []
        for v in elenco:
            p = v['p']
            mv = '%.2f' % v['mv'] if v['mv'] is not None else '—'
            if p['id'] in nel_blocco:
                mv = T.pillola(mv, T.CIANO)
            out.append([
                T.pillola(p['R'], T.RUOLO_COLORE[p['R']]),
                T.e(p['nome']), squadra_con_stemma(p['squadra']),
                squadra_con_stemma(sigla_squadra(d, v['avv'])) if v['avv'] else '—',
                'casa' if v['casa'] else 'trasferta' if v['casa'] is not None else '—',
                probabile(v),
                ('%.2f' % v['atteso']) if v['atteso'] is not None else '—',
                mv,
                nota_riga(v),
            ])
        return out

    COLONNE = [('R', ''), ('Calciatore', 'nome'), ('Sq', ''), ('Avversario', ''),
               ('Dove', ''), ('Probabili', ''), ('Atteso', 'big'), ('MV', 'num'),
               ('Nota', 'nota')]

    html(T.banda('Formazione consigliata · %s' % modulo))
    html(T.tabella(COLONNE, righe_da(titolari)))

    if mod_attivo:
        if scelto['media'] is None:
            html(T.nota('Il <b>%s</b> ti fa rinunciare al modificatore: con tre '
                        'difensori il bonus non si calcola. Conviene solo se il quarto '
                        'difensore che avresti schierato è nettamente peggiore del '
                        'centrocampista che entra al suo posto.' % modulo, 'allarme'))
        else:
            html(T.nota('Il blocco che conta è il portiere più i <b>tre difensori con '
                        'la media voto più alta</b>, in azzurro qui sopra: media '
                        '<b>%.2f</b>, che vale <b>+%.1f</b> punti. Il quarto difensore '
                        'devi schierarlo lo stesso ma nella media non entra: per quel '
                        'posto conviene chi porta bonus, non chi prende 6 fisso.'
                        % (scelto['media'], scelto['punti']),
                        'ok' if scelto['punti'] >= 1 else ''))

    diffidati = [v['p']['nome'] for v in titolari if v['p'].get('diffidato')]
    if diffidati:
        html(T.nota('In diffida fra i titolari: <b>%s</b>. Al prossimo giallo saltano '
                    'la giornata successiva: se hai un turno infrasettimanale vicino, '
                    'tieni pronto il cambio.' % T.e(', '.join(diffidati)), 'allarme'))

    def differenza(x):
        if x < -0.05:
            return '<span class="giu">%.1f punti</span>' % x
        if x > 0.05:
            return '<span class="su">+%.1f punti</span>' % x
        return 'pari'

    html(T.banda('Gli altri moduli'))
    righe = []
    for nome in moduli:
        r = esiti.get(nome)
        if not r:
            righe.append([T.e(nome), '—', '—', '—',
                          T.e('non hai abbastanza titolari')])
            continue
        righe.append([
            T.pillola(nome, T.CIANO) if nome == modulo else T.e(nome),
            '%.1f' % r['totale'],
            ('%.2f' % r['media']) if r['media'] is not None else '—',
            '+%.1f' % r['punti'] if r['punti'] else '0',
            T.e('modulo scelto') if nome == modulo else differenza(
                r['totale'] - scelto['totale']),
        ])
    html(T.tabella([('Modulo', ''), ('Punti attesi', 'big'), ('Blocco', 'num'),
                    ('Modificatore', 'num'), ('Differenza', 'nota')], righe))

    scelti = {v['p']['id'] for v in titolari}
    panca = sorted([v for v in voci if v['p']['id'] not in scelti],
                   key=lambda v: (v['atteso'] is None, -(v['atteso'] or 0)))
    html(T.banda('Panchina e indisponibili'))
    html(T.tabella(COLONNE, righe_da(panca)))
    html(T.nota('<b>Atteso</b> è la fantamedia prevista per questa partita: parte dalla '
                'fantamedia storica e la corregge per la forza dell’avversario, per il '
                'fattore campo e per la percentuale di titolarità di SosFanta. <b>MV</b> '
                'è la stessa previsione sul voto secco, quella che muove il '
                'modificatore. Non sono previsioni del voto, sono un ordinamento di chi '
                'conviene schierare.'))


def pagina_infermeria(d, asta):
    per_id = {p['id']: p for p in d['giocatori']}
    mia = set(miei(asta))
    tocca = [p for p in d['giocatori'] if p['id'] in mia and p['stato_attuale']]
    inf = [x for x in d['indisponibili'] if x['tipo'].startswith('Infortun')]
    lunghi = [x for x in d['indisponibili'] if (x.get('turni') or 0) >= 4]
    html(T.riquadri([
        ('Infortunati', len(inf), 'in tutta la Serie A', 'rosso'),
        ('Stop lunghi', len(lunghi), 'fuori 4+ giornate', ''),
        ('Nella tua rosa', len(tocca), 'da sostituire',
         'rosso' if tocca else 'ciano'),
    ]))

    if tocca:
        html(T.banda('Riguardano la tua rosa'))
        for p in tocca:
            s = p['stato_attuale']
            html(T.nota('<b>%s</b> (%s) — %s. %s<br><b>%s</b>'
                        % (T.e(p['nome']), T.e(p['squadra']), T.e(s['tipo']),
                           T.e(s.get('nota') or ''),
                           T.e(testo_rientro(s) or 'Rientro non ancora indicato')),
                        'allarme'))
    elif mia:
        html(T.nota('Nessuno dei tuoi è in infermeria.', 'ok'))

    # i cartellini non sono un'assenza di oggi, sono un'assenza di domani: chi e'
    # a quattro gialli salta la prossima volta che l'arbitro tira fuori il taccuino
    a_rischio = sorted([p for p in d['giocatori']
                        if (p.get('gialli_stagione') or 0) >= 3],
                       key=lambda p: (p.get('al_quinto') or 9,
                                      -(p.get('gialli_stagione') or 0)))
    if a_rischio:
        html(T.banda('A un passo dalla squalifica'))
        html(T.tabella(
            [('Calciatore', 'nome'), ('Sq', ''), ('Gialli', 'num'),
             ('Ne mancano', 'big'), ('Nella tua rosa', '')],
            [[T.e(p['nome']), squadra_con_stemma(p['squadra']),
              '%d' % p['gialli_stagione'],
              T.pillola('%d' % p['al_quinto'],
                        T.ROSSO if p['al_quinto'] <= 1 else T.AMBRA),
              T.pillola('tua', T.CIANO) if p['id'] in mia
              else T.pillola('no', '', vuota=True)]
             for p in a_rischio[:15]]))

    html(T.banda('Tutta la Serie A'))
    tipi = ['Tutti'] + sorted({x['tipo'] for x in d['indisponibili']})
    tipo = st.radio('Filtro', tipi, horizontal=True, label_visibility='collapsed')
    voci = d['indisponibili']
    if tipo != 'Tutti':
        voci = [x for x in voci if x['tipo'] == tipo]

    def riga_rientro(x):
        if not x.get('rientro'):
            return '—'
        turni = x.get('turni')
        quando = 'questa giornata' if not turni else 'fra %d' % turni
        return '<b>%da</b> · %s' % (x['rientro'], quando)

    for sq in sorted({x['squadra'] for x in voci}):
        della = sorted([v for v in voci if v['squadra'] == sq],
                       key=lambda x: -(x.get('rientro') or 0))
        with st.expander('%s — %d' % (sq, len(della))):
            html(T.tabella([('Calciatore', 'nome'), ('Tipo', ''), ('Rientro', ''),
                            ('Quando', ''), ('Nota della redazione', 'nota')],
                           [[T.e(x['nome']),
                             T.pillola(x['tipo'],
                                       T.ROSSO if x['tipo'].startswith('Infortun')
                                       else T.AMBRA),
                             riga_rientro(x),
                             T.e(x.get('data_rientro') or ''),
                             T.e(x['nota'])] for x in della]))
    html(T.nota('La giornata di rientro è quella indicata dalla redazione di SosFanta. '
                'Quando manca, resta un trattino: preferisco non inventarla.'))


def pagina_statistiche(d):
    # la pagina e' cresciuta troppo per stare qui dentro: vive in pag_statistiche.py
    PS.pagina(d)


def pagina_impostazioni(d, asta):
    cfg = M.carica_config()
    html(T.banda('La tua lega'))
    a, b = st.columns(2)
    cfg['squadre'] = a.number_input('Squadre', 2, 20, cfg['squadre'])
    cfg['crediti'] = b.number_input('Crediti per squadra', 100, 2000, cfg['crediti'],
                                    step=10)
    cfg['modificatore_difesa'] = st.checkbox('Modificatore di difesa',
                                             cfg['modificatore_difesa'])
    html(T.banda('Coppe europee'))
    html(T.nota('Chi gioca in Europa ruota: i titolarissimi saltano qualche '
                'giornata di campionato in più, e le riserve ne giocano '
                'qualcuna in più. Non esiste una pagina da cui leggerlo in modo '
                'affidabile, quindi te lo chiedo: spunta le squadre impegnate in '
                'Champions, Europa o Conference. Ti propongo un’ipotesi, '
                'correggila.'))
    squadre_tutte = sorted({q['squadra'] for q in d['giocatori'] if q['squadra']})
    predefinite = [x for x in (cfg.get('europa')
                               or d.get('europa_suggerite') or [])
                   if x in squadre_tutte]
    cfg['europa'] = st.multiselect('Squadre nelle coppe', squadre_tutte,
                                   default=predefinite)

    html(T.banda('Slot per ruolo'))
    cs = st.columns(4)
    for i, ru in enumerate(RUOLI):
        cfg['slot'][ru] = cs[i].number_input(RUOLO_NOME[ru], 1, 15, cfg['slot'][ru])
    html(T.banda('Quota di budget per reparto'))
    cq = st.columns(4)
    for i, ru in enumerate(RUOLI):
        cfg['quote'][ru] = cq[i].number_input(RUOLO_NOME[ru], 0.0, 1.0,
                                              float(cfg['quote'][ru]), step=0.01,
                                              format='%.2f', key='q' + ru)
    somma = sum(cfg['quote'].values())
    if abs(somma - 1) > 0.005:
        html(T.nota('Le quote sommano a <b>%.0f%%</b>: sistemale prima di salvare.'
                    % (somma * 100), 'allarme'))
    if st.button('Salva e ricalcola', type='primary'):
        M.salva_config(cfg)
        with st.spinner('Ricalcolo...'):
            M.elabora()
        st.cache_data.clear()
        st.rerun()

    html(T.banda('Azzera l\'asta'))
    html(T.nota('Cancella tutti gli acquisti segnati, i tuoi e quelli delle altre '
                'squadre. I nomi delle squadre, le impostazioni e i dati restano.'))
    quanti = len(asta['acquisti'])
    if st.button('Cancella gli acquisti', disabled=not quanti):
        st.session_state['conferma_azzera'] = True
    if st.session_state.get('conferma_azzera'):
        html(T.nota('Stai per cancellare <b>%d acquisti</b> di tutta la lega. '
                    'Non si torna indietro.' % quanti, 'allarme'))
        c1, c2 = st.columns([1, 3])
        if c1.button('Sì, cancella tutto', type='primary'):
            asta['acquisti'] = {}
            salva_asta(asta)
            MK.azzera_andamento()
            st.session_state.pop('scatto_prezzi', None)
            st.session_state['conferma_azzera'] = False
            st.rerun()
        if c2.button('No, lascia stare'):
            st.session_state['conferma_azzera'] = False
            st.rerun()


# ------------------------------------------------------------------ main
PAGINE = {
    'Asta': ('Asta', pagina_asta),
    'Chiedimi': ('Chiedimi', pag_chiedimi.pagina),
    'Consigli': ('I miei consigli', pagina_consigli),
    'Le squadre': ('Le squadre della lega', pagina_squadre),
    'La mia rosa': ('La mia rosa', pagina_rosa),
    'Formazione': ('Chi schierare', pagina_formazione),
    'Infermeria': ('Infermeria', pagina_infermeria),
    'Statistiche': ('Statistiche', pagina_statistiche),
    'Impostazioni': ('Impostazioni', pagina_impostazioni),
}


ETICHETTE = {
    'Asta': 'Asta', 'Chiedimi': 'Chiedimi', 'Consigli': 'Consigli',
    'Le squadre': 'Squadre',
    'La mia rosa': 'Rosa', 'Formazione': 'Formazione', 'Infermeria': 'Infermeria',
    'Statistiche': 'Statistiche', 'Impostazioni': 'Opzioni',
}


def stato_asta(d, asta, cfg):
    """I quattro numeri che devono stare sempre sotto gli occhi."""
    miei_acquisti = MK.acquisti_di(asta, asta['mia'])
    speso = sum(miei_acquisti.values())
    slot_totali = sum(cfg['slot'].values())
    residui = cfg['crediti'] - speso
    mancanti = slot_totali - len(miei_acquisti)
    # il tetto vero non e' quanto ti resta: e' quanto ti resta tenendo un
    # credito per ogni casella ancora da riempire
    tetto = max(0, residui - max(0, mancanti - 1))
    return {'speso': speso, 'residui': residui, 'slot': len(miei_acquisti),
            'slot_totali': slot_totali, 'tetto': tetto,
            'venduti': len(asta['acquisti']),
            'listone': len(d['giocatori'])}


def azioni(d, cfg):
    """Le cose che si fanno una volta ogni tanto: tema e aggiornamento dati."""
    with st.popover('⋯', use_container_width=False):
        html('<div class="titoletto">Aspetto</div>')
        st.radio('Tema', ['Scuro', 'Chiaro'], key='tema', horizontal=True,
                 label_visibility='collapsed')
        html('<div class="titoletto">Dati</div>')
        st.caption('Aggiornati da soli ogni ora. Ultimo giro: %s' % d['aggiornato'])
        if st.button('Aggiorna adesso', use_container_width=True):
            with st.spinner('Scarico e ricalcolo, ci vuole un minuto...'):
                # nell'eseguibile il python da chiamare e' l'eseguibile stesso,
                # che sa aggiornare i dati se glielo chiedi con un argomento
                comando = ([sys.executable, '--aggiorna'] if radice.portatile()
                           else [sys.executable, os.path.join(BASE, 'aggiorna.py')])
                subprocess.run(comando, cwd=BASE, check=False)
            st.cache_data.clear()
            st.rerun()
        html('<div class="titoletto">La lega</div>')
        st.caption('%d squadre · %d crediti · %s%s'
                   % (cfg['squadre'], cfg['crediti'], cfg.get('modalita', 'Classic'),
                      ' · modificatore di difesa' if cfg['modificatore_difesa']
                      else ''))


def barra(d, asta, cfg):
    """La plancia: marchio, navigazione e stato, incollati in cima allo schermo.

    La barra laterale non c'e' piu' per due motivi. Il primo e' che dentro la
    finestra di FantAiuto, se la chiudevi, non c'era piu' modo di riaprirla. Il
    secondo e' che all'asta i numeri che contano — quanto ti resta, fin dove
    puoi spingerti — stavano in fondo alla pagina, e li' non li guarda nessuno
    mentre un giocatore viene battuto.
    """
    s = stato_asta(d, asta, cfg)
    with st.container(key='plancia'):
        sinistra, centro, destra = st.columns([1.9, 9.1, 3.0],
                                              vertical_alignment='center')
        with sinistra:
            html('<div class="marchio">FantAiuto<span>%s</span></div>'
                 % T.e('%d giornata · dati %s'
                       % (d['prossima_giornata'], d['aggiornato'][:5])))
        with centro:
            if 'pagina' not in st.session_state:
                st.session_state['pagina'] = 'Asta'
            st.segmented_control(
                'Pagine', list(PAGINE), key='pagina',
                format_func=lambda x: ETICHETTE.get(x, x),
                label_visibility='collapsed')
        with destra:
            numeri, comandi = st.columns([5, 1], vertical_alignment='center')
        with numeri:
            html('<div class="stato">'
                 '<span><b class="cifra" style="--fine:%d"></b>crediti</span>'
                 '<span><b class="cifra" style="--fine:%d"></b>puoi offrire</span>'
                 '<span><b>%d/%d</b>slot</span>'
                 '<span><b>%d</b>venduti</span>'
                 '</div>'
                 % (s['residui'], s['tetto'], s['slot'], s['slot_totali'],
                    s['venduti']))
        with comandi:
            azioni(d, cfg)
    return st.session_state.get('pagina') or 'Asta'


def main():
    d = dati()
    cfg = d['config']
    asta = carica_asta(cfg)

    scelta = barra(d, asta, cfg)
    d['_mod'] = applica_modificatore_personale(d, asta, cfg)

    titolo, funzione = PAGINE[scelta]
    if scelta == 'Statistiche':
        funzione(d)
    else:
        funzione(d, asta)


main()
