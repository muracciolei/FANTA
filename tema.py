# -*- coding: utf-8 -*-
"""Il vestito di FantAiuto: sistema di design, foglio di stile e componenti.

L'identita' resta quella scelta all'inizio — arancione che comanda, grafite,
angoli tagliati invece che stondati, niente smussi morbidi — ma costruita come
un sistema vero: una scala tipografica sola, un ritmo verticale solo, superfici
a tre livelli di profondita', e il colore usato per dire qualcosa, mai per
decorare.

La novita' piu' utile non e' estetica: dentro le tabelle i numeri non sono piu'
solo cifre. Un prezzo porta con se' la barra che dice quanto pesa rispetto agli
altri del suo ruolo, una fantamedia porta la linea delle ultime giornate. Si
legge una tabella con la coda dell'occhio invece di doverla studiare.

Due temi, scuro e chiaro: cambia solo il blocco di variabili in cima.
"""
import html as H

# ------------------------------------------------------------- palette
SCURO = {
    # Blu notte, non grigio ferro. Il grigio e' neutro e non dice niente; su un
    # fondo bluastro l'arancione — che gli sta all'opposto sulla ruota — si
    # accende invece di spegnersi, e i verdi e i rossi dei dati si staccano di
    # piu' senza doverli fare piu' vivi.
    'fondo': '#070A10', 'fondo2': '#0C1119',
    'sup': '#131B26', 'sup2': '#18222F', 'sup3': '#1F2C3B',
    'linea': '#243243', 'linea2': '#35485F',
    'testo': '#EAF2FA', 'tenue': '#94A6BB', 'fioco': '#64768D',
    'ombra': '0 1px 2px rgba(0,0,0,.5), 0 8px 24px -12px rgba(0,0,0,.7)',
    'vetro': 'rgba(21,27,34,.72)',
    'su': '#3FDE82', 'giu': '#FF6B5C', 'attenzione': '#FFB44F', 'info': '#4FD8FA',
}
CHIARO = {
    # anche il chiaro prende una punta di azzurro, per restare parente dell'altro
    'fondo': '#EDF1F6', 'fondo2': '#F6F9FC',
    'sup': '#FFFFFF', 'sup2': '#FFFFFF', 'sup3': '#F1F5FA',
    'linea': '#DEE5EE', 'linea2': '#C6D1DE',
    'testo': '#0B1220', 'tenue': '#576578', 'fioco': '#8492A4',
    'ombra': '0 1px 2px rgba(16,24,32,.06), 0 10px 26px -14px rgba(16,24,32,.28)',
    'vetro': 'rgba(255,255,255,.75)',
    'su': '#147A3D', 'giu': '#C0271A', 'attenzione': '#8A5200', 'info': '#0A6E8A',
}
ARANCIO = '#FF6A00'
AMBRA = '#FFA02B'
ROSSO = '#FF4A38'
CIANO = '#1FC8F0'
VERDE = '#2FCE72'
VIOLA = '#8B6DF0'

# nomi tenuti per compatibilita' con il resto del programma
GRAFITE = '#0F151B'
FUMO = '#8C9AA8'
BIANCO = '#FFFFFF'
ACCIAIO = '#28323C'
NEBBIA = '#151B22'

RUOLO_COLORE = {'P': CIANO, 'D': VIOLA, 'C': ARANCIO, 'A': ROSSO}
RISCHIO_COLORE = {'Basso': VERDE, 'Medio': AMBRA, 'Alto': ROSSO, 'Ignoto': FUMO}


def e(x):
    """Tutto quello che finisce nell'HTML passa da qui: i nomi arrivano da una
    pagina web e non devono poter iniettare markup."""
    return H.escape('' if x is None else str(x))


# ------------------------------------------------------------ il foglio
def foglio(scuro=True):
    c = dict(SCURO if scuro else CHIARO)
    c.update({'arancio': ARANCIO, 'ambra': AMBRA, 'rosso': ROSSO, 'ciano': CIANO,
              'verde': VERDE, 'viola': VIOLA,
              'trama': ('rgba(255,255,255,.028)' if scuro else 'rgba(16,24,32,.035)'),
              'evid': ('rgba(255,106,0,.13)' if scuro else 'rgba(255,106,0,.10)')})
    return _FOGLIO % c


_FOGLIO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Saira+Condensed:wght@500;600;700&display=swap');

:root {
  --fondo:%(fondo)s; --fondo2:%(fondo2)s;
  --sup:%(sup)s; --sup2:%(sup2)s; --sup3:%(sup3)s;
  --linea:%(linea)s; --linea2:%(linea2)s;
  --testo:%(testo)s; --tenue:%(tenue)s; --fioco:%(fioco)s;
  --arancio:%(arancio)s; --ambra:%(ambra)s; --rosso:%(rosso)s;
  --ciano:%(ciano)s; --verde:%(verde)s; --viola:%(viola)s;
  --ombra:%(ombra)s; --vetro:%(vetro)s; --evid:%(evid)s;
  --su:%(su)s; --giu:%(giu)s; --attenzione:%(attenzione)s; --info:%(info)s;
  --taglio: 10px;
  --r: 0px;
}

/* ------------------------------------------------------------ moto */
/* Un'app che si usa mentre il banditore conta non ha bisogno di essere
   divertente: ha bisogno di far capire cosa e' cambiato, in fretta. Quindi
   tre durate sole, una curva sola, e niente movimento che non spieghi
   qualcosa. Chi ha chiesto meno animazioni non ne vede nessuna.

   La curva: decelerazione decisa, come un oggetto che si ferma per attrito.
   La molla la uso solo dove serve la sensazione di tocco — un bottone che
   cede sotto il dito — e mai su qualcosa che si legge. */
:root {
  --t-tocco: 110ms;
  --t-breve: 190ms;
  --t-medio: 320ms;
  --curva: cubic-bezier(.2,.85,.25,1);
  --molla: linear(0, .402 7.4%%, .711 15.3%%, .938 23.7%%, 1.017 28.5%%,
           1.067 33.9%%, 1.08 38.4%%, 1.07 43.6%%, 1.017 55.5%%, .994 68%%, 1);
}

@keyframes entra { from { opacity: 0; transform: translateY(7px); }
                   to   { opacity: 1; transform: none; } }
@keyframes accendi { from { opacity: 0; transform: scale(.965); }
                     to   { opacity: 1; transform: none; } }

/* Le cose nuove entrano; quelle che c'erano gia' restano ferme.
   @starting-style anima SOLO alla prima comparsa nel DOM: siccome Streamlit
   riusa i nodi che non cambiano, il risultato e' che si muove soltanto cio'
   che e' davvero cambiato. Prima si rianimava tutto a ogni tasto premuto. */
.carta { animation: accendi var(--t-breve) var(--curva) both; }
.dorf-tile { animation: entra 240ms var(--curva) both; }
.dorf-tile:nth-child(2) { animation-delay: 40ms; }
.dorf-tile:nth-child(3) { animation-delay: 80ms; }
.dorf-tile:nth-child(4) { animation-delay: 120ms; }
.dorf-tile:nth-child(5) { animation-delay: 160ms; }
.righello .fatto { transition: width var(--t-medio) var(--curva); }

/* IL PREZZO CHE SI MUOVE.
   E' la cosa piu' utile di tutta questa pagina di stile. Quando qualcuno
   strapaga un difensore, tre secondi dopo i prezzi degli altri difensori sono
   cambiati — ma su una tabella di duecentocinquanta righe non se ne accorge
   nessuno. Adesso la riga si accende del colore della direzione e si spegne da
   sola: la si vede con la coda dell'occhio mentre si guarda altrove. */
@keyframes lampo-su {
  from { background: color-mix(in oklab, var(--su) 26%%, transparent); }
  to   { background: transparent; }
}
@keyframes lampo-giu {
  from { background: color-mix(in oklab, var(--giu) 22%%, transparent); }
  to   { background: transparent; }
}
/* il lampo sta sulle CELLE, non sulla riga: la riga ha gia' la sua animazione
   di rivelazione allo scorrimento, e due animation sullo stesso elemento si
   cancellano a vicenda — la seconda regola vince e la prima sparisce */
table.dorf tbody tr[data-mossa="su"] td { animation: lampo-su 2.4s var(--curva) both; }
table.dorf tbody tr[data-mossa="giu"] td { animation: lampo-giu 2.4s var(--curva) both; }
table.dorf tbody tr[data-mossa] td:first-child { position: relative; }
table.dorf tbody tr[data-mossa] td:first-child::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  animation: sbiadisci 2.4s var(--curva) both;
}
table.dorf tbody tr[data-mossa="su"] td:first-child::before { background: var(--su); }
table.dorf tbody tr[data-mossa="giu"] td:first-child::before { background: var(--giu); }
@keyframes sbiadisci { from { opacity: 1; } to { opacity: 0; } }

/* la freccina che dice di quanto si e' mosso, accanto al prezzo */
.mossa { font-size: .62rem; font-weight: 600; margin-left: .3rem;
  font-variant-numeric: tabular-nums; animation: sbiadisci 6s linear both; }
.mossa.su { color: var(--su); }
.mossa.giu { color: var(--giu); }

/* I NUMERI CHE SALGONO.
   Un numero che compare gia' scritto e' un'informazione; un numero che ci
   arriva davanti agli occhi e' un fatto che sta succedendo. Qui e' tutto CSS:
   @property rende animabile una variabile intera, e counter() la stampa.
   Nessun javascript, nessun contatore che si incanta. */
@property --n {
  syntax: '<integer>'; initial-value: 0; inherits: false;
}
.cifra { counter-reset: n var(--n); animation: sali 800ms var(--curva) forwards; }
.cifra::after { content: counter(n); }
@keyframes sali { to { --n: var(--fine); } }

/* Quello che scorre dentro la vista si rivela entrandoci.
   E' l'unico effetto qui dentro che esiste per il piacere di guardarlo, ed e'
   tarato per non farsi notare: parte gia' quasi opaco e finisce prima che
   l'occhio ci arrivi sopra. */
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .dorf-wrap.alta table.dorf tbody tr {
      animation: rivela linear both;
      animation-timeline: view(block);
      animation-range: entry 0%% entry 42%%;
    }
    @keyframes rivela {
      from { opacity: .25; transform: translateY(5px); }
      to   { opacity: 1; transform: none; }
    }
  }
}

/* La plancia si stacca dalla pagina solo quando c'e' qualcosa sopra di lei.
   Ferma in cima e' parte del foglio; appena la pagina scorre, si alza di un
   millimetro. E' il genere di dettaglio che non si nota e che pero' dice
   sempre a che punto sei. */
@supports (animation-timeline: scroll()) {
  .st-key-plancia {
    animation: stacca linear both;
    animation-timeline: scroll(root block);
    animation-range: 0 90px;
  }
  @keyframes stacca {
    from { box-shadow: none;
           border-bottom-color: var(--linea); }
    to   { box-shadow: 0 10px 26px -18px rgba(0,0,0,.75);
           border-bottom-color: var(--linea2); }
  }
}

@media (prefers-reduced-motion: reduce) {
  .carta, .dorf-tile, .cifra, .mossa,
  table.dorf tbody tr[data-mossa] { animation: none; }
  .cifra::after { content: counter(n); }
  .cifra { counter-reset: n var(--fine); }
  .righello .fatto { transition: none; }
  table.dorf tbody tr[data-mossa] td { animation: none; }
  table.dorf tbody tr[data-mossa="su"] { background:
    color-mix(in oklab, var(--su) 14%%, transparent); }
  table.dorf tbody tr[data-mossa="giu"] { background:
    color-mix(in oklab, var(--giu) 12%%, transparent); }
}

/* ---------------------------------------------------------- impianto */
.stApp {
  background:
    radial-gradient(1200px 600px at 12%% -8%%, rgba(255,106,0,.10), transparent 62%%),
    radial-gradient(900px 520px at 96%% 4%%, rgba(31,200,240,.07), transparent 60%%),
    linear-gradient(180deg, var(--fondo2) 0%%, var(--fondo) 46%%);
}
.stApp::before {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  opacity: .5;
  background-image:
    linear-gradient(var(--linea) 1px, transparent 1px),
    linear-gradient(90deg, var(--linea) 1px, transparent 1px);
  background-size: 68px 68px;
  mask-image: radial-gradient(1100px 700px at 50%% 0%%, #000 0%%, transparent 78%%);
}
.stApp > * { position: relative; z-index: 1;
  background-attachment: fixed;
  color: var(--testo);
  font-family: Inter, 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
  font-feature-settings: 'cv05','ss01';
}
.block-container { padding: 2.1rem 2.2rem 4rem; max-width: 1680px; }
* { scrollbar-width: thin; scrollbar-color: var(--linea2) transparent; }
*::-webkit-scrollbar { width: 9px; height: 9px; }
*::-webkit-scrollbar-thumb { background: var(--linea2); border-radius: 6px; }
*::-webkit-scrollbar-track { background: transparent; }

h1, h2, h3, h4 {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif !important;
  text-transform: uppercase; letter-spacing: .045em; font-weight: 700 !important;
  color: var(--testo) !important;
}
h1 {
  font-size: 3.1rem !important; line-height: .96 !important;
  margin: 0 0 .1rem !important;
  background: linear-gradient(96deg, var(--testo) 12%%, var(--arancio) 118%%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
h1::after {
  content: ''; display: block; width: 96px; height: 4px; margin-top: .5rem;
  background: linear-gradient(90deg, var(--arancio), var(--rosso) 62%%, transparent);
}
/* Streamlit annida il testo dei titoli in uno span con dimensione propria:
   senza questa riga il titolo resta minuscolo dentro un h1 grande */
h1 > span, h2 > span, h3 > span, h4 > span {
  font-size: inherit !important; font-weight: inherit !important;
  letter-spacing: inherit !important; color: inherit !important;
}
p, li, label, span { font-size: .93rem; }

/* ------------------------------------------------------ barra laterale */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--fondo2), var(--fondo));
  border-right: 1px solid var(--linea);
}
section[data-testid="stSidebar"]::after {
  content: ''; position: absolute; inset: 0 -1px 0 auto; width: 2px;
  background: linear-gradient(180deg, var(--arancio), transparent 55%%);
  pointer-events: none;
}
section[data-testid="stSidebar"] * { color: var(--tenue); }
section[data-testid="stSidebar"] h1 {
  font-size: 1.6rem !important; -webkit-text-fill-color: initial;
  background: none; color: var(--testo) !important; letter-spacing: .1em;
}
section[data-testid="stSidebar"] h1::after { display: none; }
section[data-testid="stSidebar"] [role="radiogroup"] { gap: .12rem; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .1em; font-size: 1.02rem; padding: .42rem .6rem .42rem .85rem;
  border-left: 2px solid transparent; position: relative;
  transition: background .14s ease, border-color .14s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: var(--sup); border-left-color: var(--linea2);
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(90deg, var(--evid), transparent 82%%);
  border-left-color: var(--arancio);
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
  color: var(--testo) !important; font-weight: 600;
}
section[data-testid="stSidebar"] [role="radiogroup"] svg,
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
  display: none;
}

/* -------------------------------------------------------- i riquadri */
.dorf-tiles {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(158px, 1fr));
  gap: 10px; margin: .3rem 0 1.3rem;
}
.dorf-tile {
  position: relative; background: var(--sup); border: 1px solid var(--linea);
  padding: .72rem .85rem .8rem; overflow: hidden; box-shadow: var(--ombra);
  clip-path: polygon(0 0, 100%% 0, 100%% calc(100%% - var(--taglio)),
                     calc(100%% - var(--taglio)) 100%%, 0 100%%);
}
.dorf-tile::before {
  content: ''; position: absolute; inset: 0 0 auto 0; height: 2px;
  background: linear-gradient(90deg, var(--arancio), transparent 72%%);
}
.dorf-tile.rosso::before { background: linear-gradient(90deg, var(--rosso), transparent 72%%); }
.dorf-tile.ciano::before { background: linear-gradient(90deg, var(--ciano), transparent 72%%); }
.dorf-tile .et {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .13em; font-size: .7rem; color: var(--fioco); display: block;
}
.dorf-tile .val {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 2.25rem; font-weight: 700;
  line-height: 1.02; color: var(--testo); font-variant-numeric: tabular-nums;
  letter-spacing: -.01em;
}
.dorf-tile .sub { font-size: .74rem; color: var(--tenue); }

/* -------------------------------------------------------- pastiglie */
.pill {
  display: inline-flex; align-items: center; gap: .25rem;
  padding: .1rem .48rem .14rem; font-size: .68rem; font-weight: 600;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .07em; color: #0A0D11; margin-right: 4px; white-space: nowrap;
  clip-path: polygon(0 0, 100%% 0, 100%% 68%%, calc(100%% - 5px) 100%%, 0 100%%);
}
.pill.vuota {
  background: transparent !important; color: var(--tenue);
  border: 1px solid var(--linea2); clip-path: none;
}

/* --------------------------------------------------------- tabelle */
.dorf-wrap {
  overflow-x: auto; border: 1px solid var(--linea); background: var(--sup);
  box-shadow: var(--ombra);
}
.dorf-wrap.alta { max-height: 640px; overflow-y: auto; }
.dorf-wrap.alta thead th { position: sticky; top: 0; z-index: 3; }
table.dorf { width: 100%%; border-collapse: collapse; font-size: .93rem; }
table.dorf thead th {
  background: var(--sup3); color: var(--tenue);
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .1em; font-weight: 600; font-size: .76rem;
  padding: .56rem .48rem; text-align: left; white-space: nowrap;
  border-bottom: 1px solid var(--linea);
  box-shadow: inset 0 -2px 0 -1px var(--arancio);
}
table.dorf tbody td {
  padding: .48rem .48rem; border-bottom: 1px solid var(--linea);
  white-space: nowrap; color: var(--testo);
}
table.dorf tbody tr:last-child td { border-bottom: 0; }
table.dorf tbody tr { transition: background .1s ease; }
table.dorf tbody tr:hover { background: var(--evid); }
table.dorf td.num { text-align: right; font-variant-numeric: tabular-nums; }
/* un filo verticale dove cambia il discorso: chi e' | quanto pagarlo | quanto
   rende | cosa puo' andare storto. Dodici colonne in fila sono un muro. */
table.dorf td.sep, table.dorf th.sep { border-left: 1px solid var(--linea2); }
table.dorf .duplice { display: block; font-size: .7rem; color: var(--fioco);
  margin-top: .05rem; font-variant-numeric: tabular-nums; }
table.dorf td.nome { font-weight: 600; }
table.dorf td.nota { white-space: normal; color: var(--tenue); font-size: .78rem;
                     min-width: 250px; line-height: 1.35; }
table.dorf td.big {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 1.34rem; font-weight: 700;
  color: var(--arancio); text-align: right; font-variant-numeric: tabular-nums;
}
.su { color: var(--su); font-weight: 600; }
.giu { color: var(--giu); font-weight: 600; }

/* barra dentro la cella: il numero si legge anche senza leggerlo */
.cella-barra { position: relative; display: block; }
.cella-barra i {
  position: absolute; left: 0; bottom: -3px; height: 3px; display: block;
  background: linear-gradient(90deg, var(--arancio), var(--ambra));
  opacity: .85;
}

/* Chi usa la tastiera deve sapere sempre dov'e'. Il contorno compare solo
   con :focus-visible, cioe' quando serve davvero: col mouse non lo vede
   nessuno, col tabulatore e' impossibile perderlo. */
:focus-visible {
  outline: 2px solid var(--arancio); outline-offset: 2px; border-radius: 1px;
}
.stButton > button:focus-visible { border-color: var(--arancio); }

/* La riga sotto il dito si scosta di un capello e accende un filo arancione a
   sinistra: dice "sono io" senza colorare mezza tabella. */
table.dorf tbody tr { position: relative;
  transition: background var(--t-tocco) ease; }
table.dorf tbody tr::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 0;
  background: var(--arancio); transition: width var(--t-tocco) var(--curva);
}
table.dorf tbody tr:hover::after { width: 2px; }

/* Mentre Streamlit ricalcola, una linea sottile in cima. Al posto della
   rotellina "RUNNING" che compariva in un angolo e che nessuno guardava. */
[data-testid="stStatusWidget"] { display: none !important; }
.stApp[data-test-script-state="running"]::before,
.stApp[data-test-script-state="rerunning"]::before {
  content: ''; position: fixed; top: 0; left: 0; right: 0; height: 2px;
  z-index: 10000; background: linear-gradient(90deg, transparent,
    var(--arancio), var(--ambra), transparent);
  background-size: 40%% 100%%; background-repeat: no-repeat;
  animation: scorri 1.1s ease-in-out infinite;
}
@keyframes scorri {
  from { background-position: -45%% 0; }
  to   { background-position: 145%% 0; }
}

/* La navigazione non deve MAI perdere una voce: se lo spazio non basta va a
   capo, non si taglia. Con l'arrivo di Chiedimi le voci sono nove, la barra
   chiedeva 886 pixel e ne aveva 774, e "Opzioni" era semplicemente sparita
   dallo schermo — una pagina irraggiungibile senza nessun avviso. */
.st-key-plancia [data-testid="stButtonGroup"] {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 1px;
}
.st-key-plancia [data-testid="stButtonGroup"] button {
  padding-left: .62rem !important; padding-right: .62rem !important;
  letter-spacing: .04em;
}

/* -------------------------------------------------------- controlli */
.stButton > button {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .11em; font-weight: 600; border-radius: 0 !important;
  border: 1px solid var(--linea2); background: var(--sup2); color: var(--testo);
  clip-path: polygon(0 0, 100%% 0, 100%% 62%%, calc(100%% - 9px) 100%%, 0 100%%);
  transition: border-color var(--t-tocco) ease, color var(--t-tocco) ease,
              background var(--t-tocco) ease, scale var(--t-breve) var(--molla);
}
.stButton > button:active { scale: .972; transition-duration: 60ms; }
.stButton > button:hover {
  border-color: var(--arancio); color: var(--arancio); background: var(--sup3);
}
.stButton > button[kind="primary"] {
  background: linear-gradient(96deg, var(--arancio), #FF8A2B);
  border-color: transparent; color: #10151A;
  box-shadow: 0 6px 18px -8px rgba(255,106,0,.85);
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(96deg, var(--rosso), var(--arancio));
  color: #fff;
}

/* Questi tre selettori parlavano a data-baseweb, che nella 1.63 non esiste piu':
   contati sulla pagina viva, zero elementi. Erano regole morte, ed e' il motivo
   per cui i menu a tendina restavano bianchi anche col tema scuro. Il nodo giusto
   e' [data-testid="stSelectbox"] div[role="group"], che invece c'e'. */
div[data-testid="stSelectbox"] div[role="group"],
div[data-testid="stMultiSelect"] div[role="group"],
.stTextInput input, .stNumberInput input {
  border-radius: 0 !important; border-color: var(--linea2) !important;
  background: var(--sup) !important; color: var(--testo) !important;
}
div[data-testid="stSelectbox"] div[role="group"]:focus-within,
div[data-testid="stMultiSelect"] div[role="group"]:focus-within,
.stTextInput input:focus {
  border-color: var(--arancio) !important; box-shadow: 0 0 0 2px var(--evid) !important;
}
div[data-testid="stSelectbox"] div[role="group"] * { color: var(--testo) !important; }
ul[role="listbox"] li:hover, li[role="option"]:hover {
  background: var(--evid) !important; }
.stTextInput label, .stNumberInput label, div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label p, .stCheckbox label, .stSlider label {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif !important; text-transform: uppercase;
  letter-spacing: .1em; font-size: .74rem !important; color: var(--fioco) !important;
}
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--arancio), var(--ambra));
}
.stProgress > div > div > div { background: var(--sup3); border-radius: 0; }

div[data-testid="stExpander"] {
  border: 1px solid var(--linea); border-radius: 0; background: var(--sup);
  box-shadow: var(--ombra); margin-bottom: .5rem;
}
div[data-testid="stExpander"] summary {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .09em; color: var(--testo);
}
div[data-testid="stExpander"] summary:hover { color: var(--arancio); }

/* ----------------------------------------------------- fasce e note */
.dorf-banda {
  display: flex; align-items: center; gap: .6rem;
  background: linear-gradient(90deg, var(--sup3), transparent 88%%);
  color: var(--testo); padding: .5rem .9rem; margin: 1.6rem 0 .7rem;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .13em; font-size: .94rem; font-weight: 600;
  border-left: 3px solid var(--arancio);
}
.dorf-nota {
  border-left: 2px solid var(--linea2); background: var(--sup);
  padding: .58rem .9rem; font-size: .84rem; color: var(--tenue); margin: .5rem 0;
  line-height: 1.45;
}
.dorf-nota b { color: var(--testo); }
.dorf-nota.allarme { border-left-color: var(--rosso);
                     background: linear-gradient(90deg, rgba(255,74,56,.12), var(--sup) 40%%); }
.dorf-nota.ok { border-left-color: var(--verde);
                background: linear-gradient(90deg, rgba(47,206,114,.12), var(--sup) 40%%); }

/* --------------------------------------------------- scheda giocatore */
.dorf-scheda {
  position: relative; border: 1px solid var(--linea); border-left: 3px solid var(--arancio);
  background: linear-gradient(135deg, var(--sup2) 0%%, var(--sup) 74%%);
  padding: 1rem 1.2rem; margin-bottom: .7rem; box-shadow: var(--ombra);
  clip-path: polygon(0 0, 100%% 0, 100%% calc(100%% - 14px),
                     calc(100%% - 14px) 100%%, 0 100%%);
}
.dorf-scheda .nome {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 2.2rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .02em; line-height: 1; color: var(--testo);
}
.dorf-scheda .sq { color: var(--fioco); font-size: 1rem; margin-left: .45rem; }
.dorf-scheda ul { margin: .6rem 0 0; padding-left: 1.05rem; font-size: .85rem;
                  color: var(--tenue); }
.dorf-scheda li { margin-bottom: .14rem; }
.dorf-scheda li::marker { color: var(--arancio); }

.dorf-prezzi { display: flex; gap: 8px; }
.dorf-prezzo {
  flex: 1; text-align: center; border: 1px solid var(--linea); background: var(--sup);
  padding: .48rem .3rem .55rem;
}
.dorf-prezzo.primo {
  background: linear-gradient(150deg, var(--arancio), #FF8A2B);
  border-color: transparent;
  box-shadow: 0 8px 22px -12px rgba(255,106,0,.9);
}
.dorf-prezzo.primo .et, .dorf-prezzo.primo .val { color: #10151A !important; }
.dorf-prezzo .et {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .1em; font-size: .66rem; color: var(--fioco); display: block;
}
.dorf-prezzo .val {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 2rem; font-weight: 700;
  line-height: 1.04; color: var(--testo); font-variant-numeric: tabular-nums;
}

/* ------------------------------------------------------------- campo */
.dorf-campo {
  position: relative; overflow: hidden;
  padding: 1.1rem .5rem .9rem; min-height: 430px;
  display: flex; flex-direction: column-reverse; justify-content: space-between;
  background:
    radial-gradient(130%% 90%% at 50%% 0%%, rgba(255,255,255,.12), transparent 58%%),
    repeating-linear-gradient(180deg, #2C8B4C 0 42px, #26793F 42px 84px);
  box-shadow: inset 0 -60px 90px -40px rgba(0,0,0,.55),
              inset 0 60px 90px -50px rgba(0,0,0,.35), var(--ombra);
}
.dorf-campo .righe {
  position: absolute; inset: 0; pointer-events: none;
}
.dorf-linea {
  display: flex; justify-content: space-evenly; align-items: flex-end;
  position: relative; z-index: 2; padding: 0 .2rem;
}
.dorf-uomo { width: 74px; text-align: center; }
.dorf-uomo .foto {
  width: 52px; height: 52px; margin: 0 auto; border-radius: 50%%;
  /* i campioncini sono mezzibusti: ancoro in alto o il cerchio taglia la testa */
  background: rgba(10,13,17,.55) center top/112%% auto no-repeat;
  border: 2px solid var(--arancio);
  box-shadow: 0 4px 12px -3px rgba(0,0,0,.65);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-weight: 700; font-size: 1.05rem;
  color: #fff; overflow: hidden;
}
.dorf-uomo.por .foto { border-color: var(--ciano); }
.dorf-uomo.dif .foto { border-color: var(--viola); }
.dorf-uomo.att .foto { border-color: var(--rosso); }
.dorf-uomo .nm {
  margin-top: 3px; background: rgba(9,12,16,.82); color: #F2F6F9;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-weight: 600; font-size: .7rem;
  letter-spacing: .04em; text-transform: uppercase; line-height: 1.5;
  padding: 0 .2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.dorf-uomo .pz {
  background: var(--arancio); color: #10151A;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-weight: 700; font-size: .74rem;
  line-height: 1.45; letter-spacing: .03em;
}
.dorf-uomo.mio .pz { background: var(--verde); }

.dorf-panca { display: flex; gap: .26rem; flex-wrap: wrap; margin-top: .5rem; }
.dorf-panca .voce {
  border: 1px solid var(--linea); background: var(--sup); font-size: .68rem;
  padding: .13rem .34rem; color: var(--tenue); white-space: nowrap;
}
.dorf-panca .voce b { color: var(--testo); }

.dorf-testata {
  background: linear-gradient(96deg, var(--sup3), var(--sup));
  border: 1px solid var(--linea); border-left: 4px solid var(--arancio);
  padding: .5rem .7rem .55rem;
}
.dorf-testata .t {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .07em; font-weight: 700; font-size: 1.04rem; line-height: 1.1;
  color: var(--testo);
}
.dorf-testata .d { font-size: .72rem; color: var(--tenue); margin-top: .16rem; }
.dorf-testata .d b { color: var(--attenzione); }

/* ----------------------------------------------------------- plancia */
/* la barra di comando incollata in cima: navigazione a sinistra, i numeri
   dell'asta a destra, e non se ne va mai mentre scorri il listone */
.st-key-plancia {
  position: sticky; top: 0; z-index: 999;
  background: linear-gradient(180deg, var(--fondo2) 0%%, var(--fondo2) 72%%,
              color-mix(in srgb, var(--fondo2) 88%%, transparent) 100%%);
  border-bottom: 1px solid var(--linea);
  margin: -2.1rem -2.2rem 1.1rem; padding: .55rem 2.2rem .5rem;
  backdrop-filter: blur(6px);
}
.st-key-plancia [data-testid="stElementContainer"] { margin-bottom: 0; }
.marchio { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  font-size: 1.32rem; letter-spacing: .04em; line-height: 1; color: var(--testo); }
.marchio::first-letter { color: var(--arancio); }
.marchio span { display: block; font-family: 'Inter', sans-serif;
  text-transform: none; font-size: .68rem; letter-spacing: .01em;
  color: var(--fioco); margin-top: .2rem; }
.stato { display: flex; gap: 1.05rem; justify-content: flex-end;
  align-items: baseline; }
/* le etichette dei quattro numeri non vanno mai a capo: "puoi arrivare a"
   spezzato su tre righe alzava la plancia di venti pixel per niente */
.stato span { white-space: nowrap; }
.stato span { display: flex; flex-direction: column; align-items: flex-end;
  font-size: .62rem; text-transform: uppercase; letter-spacing: .07em;
  color: var(--fioco); line-height: 1.25; }
.stato b { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 1.24rem;
  color: var(--testo); font-variant-numeric: tabular-nums; letter-spacing: .01em; }
.stato span:nth-child(2) b { color: var(--arancio); }
.st-key-plancia [data-testid="stPopover"] button {
  border-radius: 0; border-color: var(--linea); background: transparent;
  color: var(--tenue); min-height: 34px; padding: 0 .6rem; }
.st-key-plancia [data-testid="stPopover"] button:hover { color: var(--arancio);
  border-color: var(--arancio); }
.st-key-plancia [data-testid="stButtonGroup"] { justify-content: center; }
.st-key-plancia [data-testid="stButtonGroup"] button {
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .08em; font-size: .84rem; border-radius: 0;
  border-color: transparent; background: transparent; color: var(--tenue); }
.st-key-plancia [data-testid="stButtonGroup"] button:hover { color: var(--testo); }
/* aria-checked e' quello che la 1.63 mette davvero; kind="...Active" era morto */
.st-key-plancia [data-testid="stButtonGroup"] button[aria-checked="true"] {
  background: var(--arancio); color: #0B0F13; }

/* ------------------------------------------------------------- carta */
.carta { position: relative; display: flex; align-items: center; gap: .9rem;
  padding: .85rem 1rem; overflow: hidden;
  background: var(--sup2); border: 1px solid var(--linea);
  border-left: 3px solid var(--accento); }
.carta .alone { position: absolute; left: -40px; top: -60px; width: 190px;
  height: 190px; border-radius: 50%%; opacity: .16; pointer-events: none;
  background: radial-gradient(circle, var(--accento) 0%%, transparent 68%%); }
.carta .faccia { width: 76px; height: 76px; object-fit: cover; object-position: top;
  filter: drop-shadow(0 6px 10px rgba(0,0,0,.55)); z-index: 1; }
.carta .faccia.vuota { display: flex; align-items: center; justify-content: center;
  font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 1.6rem;
  color: var(--accento); background: var(--fondo2); border: 1px solid var(--linea); }
.carta .chi { flex: 1; min-width: 0; z-index: 1; }
.carta .ruolo { font-size: .6rem; letter-spacing: .16em; color: var(--accento);
  text-transform: uppercase; }
.carta .nome { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 1.85rem;
  line-height: 1.02; text-transform: uppercase; color: var(--testo);
  /* il nome del giocatore in battuta non si tronca mai: "MAR..." non serve a
     niente quando devi decidere se rilanciare. Si stringe finche' ci sta, e a
     capo ci va solo fra una parola e l'altra — mai spezzando un cognome. */
  overflow-wrap: normal; word-break: keep-all; hyphens: none; }
.carta .nome.lungo { font-size: 1.42rem; }
.carta .nome.lunghissimo { font-size: 1.12rem; line-height: 1.08; }
.carta .squadra { font-size: .74rem; color: var(--tenue); margin-top: .1rem; }
.carta .pillole { margin-top: .34rem; display: flex; flex-wrap: wrap; gap: .22rem; }
.carta .prezzone { text-align: right; z-index: 1; padding-left: .6rem; }
.carta .prezzone b { display: block; font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif;
  font-size: 3.1rem; line-height: .92; color: var(--arancio);
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 22px color-mix(in srgb, var(--arancio) 45%%, transparent); }
.carta .prezzone span { font-size: .58rem; letter-spacing: .14em;
  text-transform: uppercase; color: var(--fioco); }

/* ---------------------------------------------------------- righello */
.righello { margin: .7rem 0 .2rem; }
.righello .pista { position: relative; height: 8px; background: var(--fondo2);
  border: 1px solid var(--linea); }
.righello .fatto { position: absolute; left: 0; top: 0; bottom: 0;
  background: color-mix(in srgb, var(--arancio) 70%%, transparent); }
.righello .tacca { position: absolute; top: -4px; width: 2px; height: 16px; }
.righello .tacca.mia { background: var(--ciano); }
.righello .tacca.loro { background: var(--rosso); }
.righello .etichette { display: flex; justify-content: space-between;
  margin-top: .35rem; font-size: .64rem; text-transform: uppercase;
  letter-spacing: .06em; color: var(--fioco); }
.righello .etichette b { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif;
  font-size: .92rem; color: var(--testo); margin-left: .25rem; }
.righello .etichette .mia b { color: var(--ciano); }
.righello .etichette .loro b { color: var(--rosso); }

/* -------------------------------------------------------------- banco */
/* il pannello del giocatore in battuta resta agganciato in alto mentre a
   sinistra scorri il listone: e' li' che si guarda quando parte un rilancio */
.st-key-banco { position: sticky; top: 5.4rem; background: var(--fondo2);
  border: 1px solid var(--linea); padding: .85rem .9rem 1rem; }
.st-key-banco .stExpander { border: 0; }
.st-key-banco [data-testid="stExpander"] summary { font-size: .78rem;
  text-transform: uppercase; letter-spacing: .08em; color: var(--tenue); }

.perche { margin: .55rem 0 .2rem; display: flex; flex-direction: column;
  gap: .22rem; font-size: .78rem; line-height: 1.35; }
.perche span { padding-left: .8rem; position: relative; color: var(--tenue); }
.perche span::before { position: absolute; left: 0; top: 0; font-weight: 700; }
.perche .si::before { content: '+'; color: var(--verde); }
.perche .no::before { content: '-'; color: var(--rosso); }

.sottonome { display: block; font-size: .73rem; color: var(--fioco);
  line-height: 1.25; margin-top: .1rem; max-width: 30ch; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }

.stretti { display: flex; gap: 6px; margin: .3rem 0 .7rem; }
.stretti .stretto { flex: 1 1 0; min-width: 0; background: var(--sup);
  border: 1px solid var(--linea); border-top: 2px solid var(--linea2);
  padding: .42rem .5rem .5rem; }
.stretti .stretto.ciano { border-top-color: var(--ciano); }
.stretti .stretto.verde { border-top-color: var(--verde); }
.stretti .stretto.rosso { border-top-color: var(--rosso); }
.stretti .stretto.ambra { border-top-color: var(--ambra); }
.stretti .et { display: block; font-size: .6rem; letter-spacing: .09em;
  text-transform: uppercase; color: var(--fioco); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.stretti .val { font-family: 'Saira Condensed', Bahnschrift, sans-serif;
  font-size: 1.5rem; font-weight: 700; line-height: 1.05; color: var(--testo);
  font-variant-numeric: tabular-nums; }
.stretti .sub { display: block; font-size: .62rem; color: var(--fioco);
  line-height: 1.25; }

.spiega { border-left: 2px solid var(--linea2); padding: .1rem 0 .1rem .7rem;
  margin: .5rem 0 1.4rem; }
.spiega p { margin: 0 0 .45rem; font-size: .84rem; line-height: 1.5;
  color: var(--tenue); }
.spiega p.rischio { color: var(--fioco); font-size: .8rem; margin-bottom: 0; }
.spiega p.rischio b { color: var(--attenzione); }

/* -------------------------------------------------- cartellini e vuoti */
.cart { display: inline-flex; align-items: center; gap: 2px; }
.cart i { display: inline-block; width: 7px; height: 10px; border-radius: 1px; }
.cart i.g { background: #F2C14E; }
.cart i.r { background: var(--rosso); }
.cart i.niente { background: transparent; border: 1px dashed var(--linea2);
  opacity: .8; }
.cart em { font-style: normal; font-size: .64rem; color: var(--fioco);
  margin-left: .22rem; letter-spacing: .04em; }
.vuoto { padding: 1.1rem 1.2rem; border: 1px dashed var(--linea2);
  color: var(--tenue); background: var(--sup); }
.vuoto b { display: block; font-family: 'Saira Condensed', Bahnschrift, sans-serif;
  text-transform: uppercase; letter-spacing: .08em; font-size: .92rem;
  color: var(--testo); margin-bottom: .2rem; }
.vuoto span { font-size: .82rem; line-height: 1.45; }

.dorf-banda { text-wrap: balance; }
.dorf-nota, .spiega p { text-wrap: pretty; }
.dorf-banda .conta { float: right; font-family: 'Inter', sans-serif;
  font-size: .7rem; letter-spacing: .04em; color: var(--fioco);
  text-transform: none; font-weight: 500; }

/* --------------------------------------------- classifiche e stemmi */
.posto { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; font-size: 1rem;
  color: var(--fioco); font-variant-numeric: tabular-nums; }
tr:first-child .posto { color: var(--arancio); }
.titoletto { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif; text-transform: uppercase;
  letter-spacing: .1em; font-size: .78rem; color: var(--tenue);
  margin: .5rem 0 .3rem; }
.stemma, .stemma-grande { display: inline-block; background-repeat: no-repeat;
  background-position: center; background-size: contain; }
.stemma { width: 18px; height: 18px; vertical-align: -4px; margin-right: .34rem; }
.stemma-grande { width: 30px; height: 30px; vertical-align: -8px;
  margin-right: .5rem; }

/* ------------------------------------------------------- rifiniture */
footer, #MainMenu, header[data-testid="stHeader"] { visibility: hidden; }
hr { border-color: var(--linea); }
div[data-testid="stTabs"] button { font-family: 'Saira Condensed', Bahnschrift, 'Bahnschrift SemiCondensed', 'Segoe UI Semibold', 'Arial Narrow', sans-serif;
  text-transform: uppercase; letter-spacing: .09em; }
/* ============================================================= LA PELLE */
:root {
  /* raggi: uno per gli oggetti piccoli, uno per i pannelli, uno per i giganti */
  --r1: 10px; --r2: 16px; --r3: 22px;
  /* il vetro: sfondo, sfocatura e luce sul bordo */
  --vetro1: color-mix(in srgb, var(--sup) 72%%, transparent);
  --vetro2: color-mix(in srgb, var(--sup2) 66%%, transparent);
  --luce: inset 0 1px 0 color-mix(in srgb, white 9%%, transparent);
  --luce-forte: inset 0 1px 0 color-mix(in srgb, white 16%%, transparent);
  /* profondita' a tre livelli: appoggiato, sollevato, in primo piano */
  --q1: 0 1px 2px rgba(0,0,0,.18), 0 2px 8px -4px rgba(0,0,0,.30);
  --q2: 0 2px 4px rgba(0,0,0,.22), 0 12px 28px -12px rgba(0,0,0,.45);
  --q3: 0 4px 8px rgba(0,0,0,.26), 0 28px 60px -24px rgba(0,0,0,.60);
  --accento-caldo: linear-gradient(135deg, var(--arancio), var(--ambra) 92%%);
}
:root[data-tema="chiaro"], .chiaro {
  --luce: inset 0 1px 0 color-mix(in srgb, white 70%%, transparent);
  --luce-forte: inset 0 1px 0 white;
  --q1: 0 1px 2px rgba(16,24,32,.05), 0 2px 8px -4px rgba(16,24,32,.10);
  --q2: 0 2px 4px rgba(16,24,32,.06), 0 12px 28px -12px rgba(16,24,32,.16);
  --q3: 0 4px 8px rgba(16,24,32,.07), 0 28px 60px -24px rgba(16,24,32,.22);
}

/* Niente piu' angoli tagliati: la diagonale sopravvive solo come accento
   grafico, non come forma degli oggetti. */
.dorf-tile, .pill, .stretti .stretto, .dorf-nota, .vuoto, .carta,
.stButton > button, .dorf-wrap, .spiega, .dorf-scheda, .dorf-prezzo {
  clip-path: none !important;
}

/* ---- superfici: vetro, luce in cima, ombra sotto ---- */
.dorf-tile, .stretti .stretto {
  background: var(--vetro1);
  backdrop-filter: blur(14px) saturate(1.25);
  border: 1px solid color-mix(in srgb, var(--linea2) 60%%, transparent);
  border-radius: var(--r2); corner-shape: squircle;
  box-shadow: var(--q1), var(--luce);
  padding: .85rem 1rem .95rem;
  container-type: inline-size;
  transition: box-shadow var(--t-breve) var(--curva),
              transform var(--t-breve) var(--curva);
}
.dorf-tile:hover { box-shadow: var(--q2), var(--luce-forte); transform: translateY(-1px); }
/* la barra di colore in cima non e' piu' incollata all'angolo: segue la curva */
.dorf-tile::before {
  inset: 0 0 auto 0; height: 3px; border-radius: var(--r2) var(--r2) 0 0;
  opacity: .9;
}

.dorf-wrap {
  background: var(--vetro2);
  backdrop-filter: blur(10px);
  border: 1px solid color-mix(in srgb, var(--linea2) 55%%, transparent);
  border-radius: var(--r2); corner-shape: squircle; overflow: hidden;
  box-shadow: var(--q1), var(--luce);
}
.carta {
  border-radius: var(--r3); corner-shape: squircle;
  background: var(--vetro1);
  backdrop-filter: blur(18px) saturate(1.3);
  border: 1px solid color-mix(in srgb, var(--accento) 30%%, transparent);
  border-left: 3px solid var(--accento);
  box-shadow: var(--q2), var(--luce);
}
.dorf-nota, .vuoto, .spiega {
  border-radius: var(--r1); corner-shape: squircle;
}
.dorf-nota {
  background: var(--vetro2); backdrop-filter: blur(8px);
  border: 1px solid color-mix(in srgb, var(--linea2) 50%%, transparent);
  border-left: 3px solid var(--linea2);
  box-shadow: var(--q1);
}
.dorf-nota.ok { border-left-color: var(--verde); }
.dorf-nota.allarme { border-left-color: var(--rosso); }

/* ---- le pastiglie diventano pastiglie ---- */
.pill {
  border-radius: 999px; padding: .16rem .58rem .2rem;
  box-shadow: 0 1px 2px rgba(0,0,0,.16);
  letter-spacing: .06em;
}
.pill.vuota { border-radius: 999px; box-shadow: none;
  border-color: color-mix(in srgb, var(--linea2) 70%%, transparent); }

/* ---- i comandi ---- */
.stButton > button {
  border-radius: var(--r1) !important; corner-shape: squircle;
  box-shadow: var(--q1), var(--luce);
  padding-top: .34rem; padding-bottom: .34rem;
}
.stButton > button[kind="primary"] {
  background: var(--accento-caldo) !important; border-color: transparent !important;
  color: #0B0F13 !important; box-shadow: var(--q2),
    0 0 0 1px color-mix(in srgb, var(--arancio) 40%%, transparent);
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.06); }
div[data-testid="stSelectbox"] div[role="group"],
div[data-testid="stMultiSelect"] div[role="group"],
.stTextInput input, .stNumberInput input {
  border-radius: var(--r1) !important; corner-shape: squircle;
  background: var(--vetro2) !important;
  backdrop-filter: blur(6px);
  box-shadow: var(--luce);
}
.st-key-plancia [data-testid="stButtonGroup"] button {
  border-radius: 999px !important; corner-shape: squircle;
}

/* ---- la plancia: il vetro piu' spesso di tutti, perche' sta sopra tutto ---- */
.st-key-plancia {
  background: color-mix(in srgb, var(--fondo2) 76%%, transparent);
  backdrop-filter: blur(22px) saturate(1.5);
  border-bottom: 1px solid color-mix(in srgb, var(--linea2) 60%%, transparent);
  box-shadow: var(--luce);
}

/* ---- il banco: il pannello che conta, sollevato dal resto ---- */
.st-key-banco {
  border-radius: var(--r3); corner-shape: squircle;
  background: var(--vetro1);
  backdrop-filter: blur(16px) saturate(1.3);
  border: 1px solid color-mix(in srgb, var(--linea2) 55%%, transparent);
  box-shadow: var(--q3), var(--luce);
  padding: .9rem .95rem 1rem;
}

/* ---- i numeri grandi: piu' grandi, e con la luce dentro ---- */
.dorf-tile .val {
  font-size: 2.5rem; letter-spacing: -.018em;
  background: linear-gradient(175deg, var(--testo) 40%%,
              color-mix(in srgb, var(--testo) 62%%, transparent));
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.dorf-tile.ciano .val, .dorf-tile.verde .val, .dorf-tile.rosso .val,
.dorf-tile.ambra .val { -webkit-text-fill-color: currentColor; }
.dorf-tile.ciano .val { color: var(--info); }
.dorf-tile.verde .val { color: var(--su); }
.dorf-tile.rosso .val { color: var(--giu); }
.dorf-tile.ambra .val { color: var(--attenzione); }
.stato b { font-size: 1.34rem; }

/* ---- la tabella respira ---- */
table.dorf thead th {
  background: color-mix(in srgb, var(--sup3) 82%%, transparent);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 -1px 0 color-mix(in srgb, var(--arancio) 55%%, transparent);
  border-bottom: 0;
}
table.dorf tbody td {
  border-bottom: 1px solid color-mix(in srgb, var(--linea) 55%%, transparent);
  padding-top: .56rem; padding-bottom: .56rem;
}
table.dorf tbody tr:hover {
  background: color-mix(in srgb, var(--arancio) 7%%, transparent);
}
table.dorf td.big { font-size: 1.42rem; }

/* ---- le bande di sezione: meno riga, piu' titolo ---- */
.dorf-banda {
  background: transparent; border: 0; padding: 0 0 .3rem;
  border-bottom: 1px solid color-mix(in srgb, var(--linea2) 45%%, transparent);
  font-size: 1.02rem; letter-spacing: .1em; color: var(--testo);
  margin: 1.9rem 0 .9rem; position: relative;
}
.dorf-banda::after {
  content: ''; position: absolute; left: 0; bottom: -1px; width: 54px; height: 2px;
  background: var(--accento-caldo); border-radius: 2px;
}

/* ---- lo sfondo prende aria e colore ---- */
.stApp {
  background:
    radial-gradient(1100px 620px at 8%% -10%%,
      color-mix(in srgb, var(--arancio) 13%%, transparent), transparent 60%%),
    radial-gradient(900px 560px at 98%% 2%%,
      color-mix(in srgb, var(--ciano) 10%%, transparent), transparent 58%%),
    radial-gradient(1000px 700px at 50%% 108%%,
      color-mix(in srgb, var(--viola) 9%%, transparent), transparent 62%%),
    linear-gradient(180deg, var(--fondo2) 0%%, var(--fondo) 52%%);
  background-attachment: fixed;
}
.block-container { padding-top: 1.7rem; }

/* ---- il campo: erba piu' vera, meno cartone ---- */
.campo {
  border-radius: var(--r3); corner-shape: squircle;
  box-shadow: var(--q2), var(--luce);
}

/* I tre riquadri del banco stanno in poco piu' di trecento pixel: li' il
   respiro dei riquadri grandi tronca le parole, e un'etichetta tagliata a meta'
   e' peggio di un'etichetta piccola. */
.stretti { gap: 7px; }
.stretti .stretto { padding: .48rem .52rem .55rem; border-radius: var(--r1); }
.stretti .et { font-size: .55rem; letter-spacing: .05em; }
.stretti .val { font-size: 1.42rem; }
.stretti .sub { font-size: .58rem; line-height: 1.3; }

/* i comandi non devono mai perdere una lettera */
.stButton > button {
  padding-left: .74rem !important; padding-right: .74rem !important;
  white-space: nowrap;
}
.stButton > button p { white-space: nowrap; }

/* ---- ogni riga porta il colore del suo ruolo ---- */
/* Con dodici colonne di numeri, capire a colpo d'occhio se stai guardando un
   difensore o un attaccante costa un attimo di troppo. Un filo di colore sul
   bordo sinistro lo dice prima che tu abbia letto la pastiglia. */
table.dorf tbody td:first-child { border-left: 3px solid transparent; }
table.dorf tbody tr:has(.pill.ruolo-P) td:first-child { border-left-color:
  color-mix(in srgb, var(--ciano) 75%%, transparent); }
table.dorf tbody tr:has(.pill.ruolo-D) td:first-child { border-left-color:
  color-mix(in srgb, var(--viola) 75%%, transparent); }
table.dorf tbody tr:has(.pill.ruolo-C) td:first-child { border-left-color:
  color-mix(in srgb, var(--arancio) 75%%, transparent); }
table.dorf tbody tr:has(.pill.ruolo-A) td:first-child { border-left-color:
  color-mix(in srgb, var(--rosso) 75%%, transparent); }

/* la pastiglia del ruolo diventa un gettone tondo */
.pill.ruolo-P, .pill.ruolo-D, .pill.ruolo-C, .pill.ruolo-A {
  width: 22px; height: 22px; padding: 0; justify-content: center;
  border-radius: 999px; font-size: .72rem; letter-spacing: 0;
}

/* ---- le barre dentro le celle prendono luce ---- */
.cella-barra i {
  height: 3px; border-radius: 2px;
  background: linear-gradient(90deg, var(--arancio), var(--ambra));
  box-shadow: 0 0 8px -2px var(--arancio);
}

/* ---- il ritratto nella carta si stacca dal fondo ---- */
.carta .faccia {
  filter: drop-shadow(0 8px 14px rgba(0,0,0,.6));
}
.carta .alone { opacity: .22; }

/* Chi ha chiesto meno movimento tiene il vetro ma non il sollevamento. */
@media (prefers-reduced-motion: reduce) {
  .dorf-tile:hover { transform: none; }
}

</style>
"""


# --------------------------------------------------------- mattoncini
def pillola(testo, colore, vuota=False):
    """La pastiglia. Quando contiene una lettera sola di ruolo si porta dietro
    una classe in piu': serve alla riga della tabella per tingere il proprio
    bordo del colore del reparto, che si legge prima ancora della pastiglia."""
    if vuota:
        return '<span class="pill vuota">%s</span>' % e(testo)
    ruolo = (' ruolo-%s' % testo) if testo in RUOLO_COLORE else ''
    return ('<span class="pill%s" style="background:%s">%s</span>'
            % (ruolo, colore, e(testo)))


def numero(valore):
    """Un numero che ci arriva davanti agli occhi invece di essere gia' li'.

    Vale solo per gli interi, e solo dove il numero e' il contenuto — i crediti
    che restano, il prezzo massimo, quanti ne sono stati venduti. Su una
    fantamedia con due decimali sarebbe un vezzo; su "quanto posso spendere" e'
    la cifra che stai guardando mentre qualcuno rilancia.

    Il conteggio e' fatto in CSS: la variabile --fine dice dove arrivare, e
    l'animazione ci porta il contatore. Riparte da sola solo quando il numero
    cambia davvero, perche' e' allora che Streamlit ricostruisce quel pezzo di
    pagina — se premi un tasto nella ricerca i numeri restano fermi.
    """
    try:
        intero = int(valore)
    except (TypeError, ValueError):
        return e(valore)
    if abs(intero) > 9999 or str(valore).strip() != str(intero):
        return e(valore)
    return '<span class="cifra" style="--fine:%d"></span>' % intero


def riquadri(voci):
    """voci: lista di (etichetta, valore, sottotitolo, variante)."""
    parti = []
    for et, val, sub, var in voci:
        parti.append(
            '<div class="dorf-tile %s"><span class="et">%s</span>'
            '<div class="val">%s</div><span class="sub">%s</span></div>'
            % (var, e(et), numero(val), e(sub)))
    return '<div class="dorf-tiles">%s</div>' % ''.join(parti)


def riquadri_stretti(voci):
    """Gli stessi riquadri, ma per una colonna stretta.

    Nel banco dell'asta lo spazio orizzontale e' quello che e': i riquadri
    normali chiedono centocinquanta pixel a testa e si impilano uno sotto
    l'altro, allungando la colonna fino a mandare fuori schermo il tasto
    Assegna. Qui stanno affiancati sempre, a costo di un numero piu' piccolo.
    """
    parti = []
    for et, val, sub, var in voci:
        parti.append('<div class="stretto %s"><span class="et">%s</span>'
                     '<div class="val">%s</div><span class="sub">%s</span></div>'
                     % (var, e(et), numero(val), e(sub)))
    return '<div class="stretti">%s</div>' % ''.join(parti)


def banda(testo, contatore=None):
    """L'intestazione di sezione, con la possibilita' di dire quanti sono.

    Sapere che le occasioni sono tre e non quaranta cambia se ci vai a guardare
    oppure no, e lo si vuole sapere prima di aprire, non dopo."""
    conta = ('<span class="conta">%s</span>' % e(contatore)
             if contatore is not None else '')
    return '<div class="dorf-banda">%s%s</div>' % (e(testo), conta)


def nota(testo, variante=''):
    return '<div class="dorf-nota %s">%s</div>' % (variante, testo)


def tabella(intestazioni, righe, alta=False, attributi=None):
    """attributi: una lista lunga quanto le righe, con l'HTML da appendere al
    <tr> — serve a marcare le righe che si sono appena mosse."""
    th = ''.join('<th class="%s">%s</th>' % ('sep' if 'sep' in cl else '', e(t))
                 for t, cl in intestazioni)
    corpo = []
    for n, r in enumerate(righe):
        celle = ''.join('<td class="%s">%s</td>' % (intestazioni[i][1], c)
                        for i, c in enumerate(r))
        extra = (attributi[n] if attributi and n < len(attributi) else '')
        corpo.append('<tr%s>%s</tr>' % ((' ' + extra) if extra else '', celle))
    return ('<div class="dorf-wrap%s"><table class="dorf"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>'
            % (' alta' if alta else '', th, ''.join(corpo)))


def con_barra(valore, quota, colore=None):
    """Un numero con sotto la barra che dice quanto vale rispetto al massimo
    della sua colonna: la tabella si legge con la coda dell'occhio."""
    q = max(0.0, min(1.0, quota))
    stile = 'width:%.0f%%' % (q * 100)
    if colore:
        stile += ';background:%s' % colore
    return '<span class="cella-barra">%s<i style="%s"></i></span>' % (e(valore), stile)


def stemma(sigla, grande=False, dato=None):
    """Lo stemma della squadra: una classe, non un'immagine.

    L'immagine vera sta nel foglio di stile, definita una volta sola per tutte e
    venti le squadre (risorse.foglio_stemmi). Qui esce solo il riferimento, che
    pesa tre byte invece di quattordicimila: in una tabella da duecentocinquanta
    righe la differenza fra tre megabyte e mezzo e centoventi kilobyte.

    `dato` resta accettato per non rompere i vecchi richiami, ma non serve piu'.
    """
    if not sigla:
        return ''
    return '<i class="%s sq-%s" title="%s"></i>' % (
        'stemma-grande' if grande else 'stemma', e(sigla), e(sigla))


def scarto(v):
    if v is None or v == '':
        return ''
    n = int(v)
    if n > 0:
        return '<span class="su">+%d</span>' % n
    if n < 0:
        return '<span class="giu">%d</span>' % n
    return '0'


# ------------------------------------------------------ grafica dei dati
def curva(valori, larghezza=440, altezza=90, riferimento=1.0, etichette=None):
    """L'andamento dell'asta: come si e' mosso quello che la lega paga.

    La linea tratteggiata e' il riferimento — i miei prezzi consigliati — e la
    curva e' quanto la lega ci sta pagando sopra o sotto. Sopra la linea si
    strapaga, sotto e' il momento di comprare.
    """
    v = [x for x in valori if x is not None]
    if len(v) < 2:
        return ('<div class="vuoto"><b>Ancora niente da mostrare</b><span>La curva '
                'dei prezzi compare dopo qualche giocatore battuto.</span></div>')
    lo = min(min(v), riferimento * 0.9)
    hi = max(max(v), riferimento * 1.1)
    campo = (hi - lo) or 1.0
    passo = (larghezza - 12) / float(len(v) - 1)

    def y(x):
        return altezza - 10 - (x - lo) / campo * (altezza - 26)

    punti = ' '.join('%.1f,%.1f' % (6 + i * passo, y(x)) for i, x in enumerate(v))
    area = '6,%.1f %s %.1f,%.1f' % (altezza - 10, punti,
                                    6 + (len(v) - 1) * passo, altezza - 10)
    colore = VERDE if v[-1] <= riferimento else ROSSO
    testa = ''
    if etichette:
        testa = ('<text x="6" y="11" font-size="9" fill="var(--fioco)">%s</text>'
                 '<text x="%d" y="11" font-size="9" fill="var(--fioco)" '
                 'text-anchor="end">%s</text>' % (e(etichette[0]), larghezza - 6,
                                                  e(etichettapiu(etichette))))
    return ('<svg viewBox="0 0 %d %d" width="100%%" height="%d" '
            'preserveAspectRatio="none" style="display:block">'
            '<polygon points="%s" fill="%s" opacity=".10"/>'
            '<line x1="6" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--linea2)" '
            'stroke-dasharray="3 3" stroke-width="1"/>'
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="2" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
            '<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>%s</svg>'
            % (larghezza, altezza, altezza, area, colore,
               y(riferimento), larghezza - 6, y(riferimento),
               punti, colore, 6 + (len(v) - 1) * passo, y(v[-1]), colore, testa))


def etichettapiu(etichette):
    return etichette[1] if len(etichette) > 1 else ''


def linea_forma(valori, larghezza=78, altezza=22):
    """La linea delle ultime giornate: sopra il 6 verde, sotto rosso."""
    v = [x for x in valori if x is not None]
    if len(v) < 2:
        return '<span style="color:var(--fioco);font-size:.72rem">—</span>'
    lo, hi = min(min(v), 5.0), max(max(v), 7.5)
    passo = larghezza / float(len(v) - 1)
    punti = ' '.join('%.1f,%.1f' % (i * passo,
                                    altezza - (x - lo) / (hi - lo) * (altezza - 3) - 1.5)
                     for i, x in enumerate(v))
    y6 = altezza - (6.0 - lo) / (hi - lo) * (altezza - 3) - 1.5
    colore = VERDE if v[-1] >= 6 else ROSSO
    return ('<svg width="%d" height="%d" style="vertical-align:middle">'
            '<line x1="0" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--linea2)" '
            'stroke-dasharray="2 2" stroke-width="1"/>'
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="1.7" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
            '<circle cx="%.1f" cy="%.1f" r="2.3" fill="%s"/></svg>'
            % (larghezza, altezza, y6, larghezza, y6, punti, colore,
               (len(v) - 1) * passo,
               altezza - (v[-1] - lo) / (hi - lo) * (altezza - 3) - 1.5, colore))


def radar(assi, lato=168):
    """Il profilo del giocatore su cinque assi, da 0 a 1. Serve a vedere la forma
    di un giocatore in un colpo d'occhio: due che hanno la stessa fantamedia
    disegnano quasi sempre figure diverse."""
    import math
    n = len(assi)
    c = lato / 2.0
    r = c - 30
    anelli = ''
    for q in (0.25, 0.5, 0.75, 1.0):
        p = ' '.join('%.1f,%.1f' % (c + r * q * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
                                    c + r * q * math.sin(-math.pi / 2 + i * 2 * math.pi / n))
                     for i in range(n))
        anelli += ('<polygon points="%s" fill="none" stroke="var(--linea)" '
                   'stroke-width="1"/>' % p)
    punti, etichette = [], ''
    for i, (nome, val) in enumerate(assi):
        a = -math.pi / 2 + i * 2 * math.pi / n
        v = max(0.04, min(1.0, val))
        punti.append('%.1f,%.1f' % (c + r * v * math.cos(a), c + r * v * math.sin(a)))
        ex, ey = c + (r + 15) * math.cos(a), c + (r + 15) * math.sin(a) + 3
        anc = 'middle' if abs(math.cos(a)) < .3 else ('start' if math.cos(a) > 0 else 'end')
        etichette += ('<text x="%.1f" y="%.1f" text-anchor="%s" fill="var(--fioco)" '
                      'font-size="8.5" font-family="Saira Condensed,sans-serif" '
                      'letter-spacing=".08em">%s</text>' % (ex, ey, anc, e(nome.upper())))
    return ('<svg width="%d" height="%d">%s'
            '<polygon points="%s" fill="rgba(255,106,0,.24)" stroke="%s" '
            'stroke-width="1.8"/>%s</svg>'
            % (lato, lato, anelli, ' '.join(punti), ARANCIO, etichette))


def anello(quota, testo='', lato=104):
    """Ciambella per il budget: quanto e' andato e quanto resta."""
    import math
    q = max(0.0, min(1.0, quota))
    r = lato / 2.0 - 9
    circ = 2 * math.pi * r
    return ('<svg width="%d" height="%d" style="transform:rotate(-90deg)">'
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="var(--sup3)" '
            'stroke-width="9"/>'
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" '
            'stroke-width="9" stroke-dasharray="%.1f %.1f" stroke-linecap="butt"/>'
            '</svg><div style="margin-top:-%dpx;text-align:center;'
            'font-family:Saira Condensed,sans-serif;font-size:1.35rem;font-weight:700;'
            'color:var(--testo)">%s</div>'
            % (lato, lato, lato / 2.0, lato / 2.0, r, lato / 2.0, lato / 2.0, r,
               ARANCIO, circ * q, circ, int(lato / 2 + 12), e(testo)))


RIGHE_CAMPO = (
    '<svg class="righe" viewBox="0 0 100 150" preserveAspectRatio="none">'
    '<g fill="none" stroke="rgba(255,255,255,.42)" stroke-width=".55"'
    ' vector-effect="non-scaling-stroke">'
    '<rect x="1.6" y="1.6" width="96.8" height="146.8"/>'
    '<line x1="1.6" y1="75" x2="98.4" y2="75"/>'
    '<circle cx="50" cy="75" r="13"/>'
    '<rect x="23" y="126" width="54" height="22.4"/>'
    '<rect x="37" y="140" width="26" height="8.4"/>'
    '<path d="M35 126 A 16 12 0 0 0 65 126"/>'
    '<rect x="23" y="1.6" width="54" height="22.4"/>'
    '<rect x="37" y="1.6" width="26" height="8.4"/>'
    '<path d="M35 24 A 16 12 0 0 1 65 24"/>'
    '<path d="M1.6 6 A 5 4 0 0 0 6 1.6"/>'
    '<path d="M94 1.6 A 5 4 0 0 0 98.4 6"/>'
    '<path d="M1.6 144 A 5 4 0 0 1 6 148.4"/>'
    '<path d="M94 148.4 A 5 4 0 0 1 98.4 144"/>'
    '</g>'
    '<circle cx="50" cy="75" r="1" fill="rgba(255,255,255,.5)"/>'
    '<circle cx="50" cy="134" r="1" fill="rgba(255,255,255,.5)"/>'
    '<circle cx="50" cy="16" r="1" fill="rgba(255,255,255,.5)"/>'
    '</svg>')


def campo(form, foto=None):
    """La formazione su un campo vero: righe di gioco disegnate a norma, e ogni
    giocatore col suo ritratto dentro un anello del colore del ruolo. Con le facce
    la formazione si legge in un secondo; con i soli cognomi no.

    `foto` e' una funzione che dall'id del giocatore restituisce l'immagine gia'
    pronta da mettere nello sfondo, oppure None: in quel caso disegno le iniziali.
    """
    classi = {'P': 'por', 'D': 'dif', 'C': '', 'A': 'att'}
    linee = []
    for ru in ('P', 'D', 'C', 'A'):
        uomini = []
        for q, prezzo in form[ru]:
            img = foto(q['id']) if foto else None
            if img:
                dentro = ''
                stile = ' style="background-image:url(%s)"' % img
            else:
                dentro = e(''.join(x[0] for x in q['nome'].split()[:2]).upper())
                stile = ''
            mio = ' mio' if not str(prezzo).isdigit() else ''
            uomini.append(
                '<div class="dorf-uomo %s%s"><div class="foto"%s>%s</div>'
                '<div class="nm">%s</div><div class="pz">%s</div></div>'
                % (classi[ru], mio, stile, dentro, e(q['nome']), e(prezzo)))
        if uomini:
            linee.append('<div class="dorf-linea">%s</div>' % ''.join(uomini))
    return '<div class="dorf-campo">%s%s</div>' % (RIGHE_CAMPO, ''.join(linee))


def carta(p, ritratto=None, stemma_dato=None, prezzo=None, etichetta='max da pagare',
          note=(), colore=None):
    """La carta del calciatore: faccia, nome, e il numero che conta.

    E' l'oggetto che ricompare ovunque — in asta, nella rosa, nei consigli — cosi'
    invece di sei impaginazioni diverse ce n'e' una sola da imparare. Il numero
    grande non e' la quotazione ne' la fantamedia: e' il massimo che pagherei, che
    e' l'unica cosa che serve sapere mentre il banditore conta.
    """
    accento = colore or RUOLO_COLORE.get(p['R'], ARANCIO)
    faccia = ('<img class="faccia" src="%s" alt="">' % ritratto if ritratto
              else '<div class="faccia vuota">%s</div>'
                   % e((p['nome'] or '?')[:2].upper()))
    pillole = ''.join(pillola(t, c) for t, c in note)
    numero = ''
    if prezzo is not None:
        numero = ('<div class="prezzone"><b>%d</b><span>%s</span></div>'
                  % (prezzo, e(etichetta)))
    return (
        '<div class="carta" style="--accento:%s">'
        '<div class="alone"></div>'
        '%s'
        '<div class="chi">'
        '<div class="ruolo">%s</div>'
        '<div class="nome %s">%s</div>'
        '<div class="squadra">%s%s</div>'
        '<div class="pillole">%s</div>'
        '</div>%s</div>'
        % (accento, faccia, e(p['R']),
           'lunghissimo' if len(p['nome']) > 13 else
           'lungo' if len(p['nome']) > 9 else '', e(p['nome']),
           stemma(p['squadra'], dato=stemma_dato), e(p['squadra']),
           pillole, numero))


def righello(offerta, tetto, rivale, nome_rivale, massimo):
    """Fin dove puoi spingerti tu, e fin dove possono spingersi loro.

    Una barra sola con tre segni: quanto e' stato offerto adesso, il tuo tetto, e
    il muro del rivale piu' ricco. Il senso e' rispondere in un colpo d'occhio
    alla domanda che uno si fa all'asta — se rilancio, quello puo' seguirmi? —
    invece di andare a cercarla in un'altra pagina.
    """
    scala = float(max(massimo, tetto, rivale, offerta, 1))

    def dove(x):
        return max(0.0, min(100.0, 100.0 * x / scala))

    return (
        '<div class="righello">'
        '<div class="pista">'
        '<i class="fatto" style="width:%.1f%%"></i>'
        '<i class="tacca mia" style="left:%.1f%%"></i>'
        '<i class="tacca loro" style="left:%.1f%%"></i>'
        '</div>'
        '<div class="etichette">'
        '<span>offerta <b>%d</b></span>'
        '<span class="mia">il tuo tetto <b>%d</b></span>'
        '<span class="loro">%s arriva a <b>%d</b></span>'
        '</div></div>'
        % (dove(offerta), dove(tetto), dove(rivale), offerta, tetto,
           e(nome_rivale or 'il rivale'), rivale))


def cartellini(amm, esp=0, sagome=3):
    """I cartellini disegnati invece che scritti.

    Un numero lo devi leggere, dei rettangoli li conti con l'occhio. E quando non
    ce n'e' nemmeno uno restano tre sagome vuote, perche' essere corretti e' un
    pregio e un pregio va visto: una cella vuota sembra un dato mancante.
    """
    amm, esp = int(amm or 0), int(esp or 0)
    if not amm and not esp:
        return ('<span class="cart">%s<em>mai</em></span>'
                % ('<i class="niente"></i>' * sagome))
    pezzi = []
    if amm > 12:
        pezzi.append('<i class="g"></i><em>&times;%d</em>' % amm)
    else:
        pezzi.append('<i class="g"></i>' * amm)
    pezzi.append('<i class="r"></i>' * min(esp, 4))
    if esp > 4:
        pezzi.append('<em>&times;%d</em>' % esp)
    return '<span class="cart">%s</span>' % ''.join(pezzi)


def vuoto(titolo, testo=''):
    """Lo spazio vuoto che dice perche' e' vuoto.

    Alla terza giornata i diffidati sono zero e gli espulsi pure: senza una riga
    che lo spieghi, tre punti dell'app sembrano rotti invece che vuoti."""
    return ('<div class="vuoto"><b>%s</b>%s</div>'
            % (e(titolo), '<span>%s</span>' % e(testo) if testo else ''))


def panchina(voci):
    return ('<div class="dorf-panca">%s</div>'
            % ''.join('<span class="voce"><b>%s</b> %s · %s</span>'
                      % (e(q['nome']), e(q['squadra']), e(prezzo))
                      for q, prezzo in voci))


def testata(titolo, dettagli):
    return ('<div class="dorf-testata"><div class="t">%s</div>'
            '<div class="d">%s</div></div>' % (e(titolo), dettagli))


# il foglio pronto all'uso, tema scuro: app.py puo' comunque chiedere l'altro
CSS = foglio(True)
