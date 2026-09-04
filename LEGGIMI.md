# FantAiuto

Assistente per l'asta e per la formazione del fantacalcio, con i dati ufficiali di
fantacalcio.it aggiornati da soli **ogni ora**.

Impostato per la tua lega: **10 squadre, 500 crediti, Classic, con modificatore di
difesa**, rose da 3 portieri, 8 difensori, 8 centrocampisti, 6 attaccanti.

---

## Come si usa

**FantAiuto è un programma installato**: lo trovi nel menu Start e sul Desktop.
Si apre in una finestra sua, senza browser e senza terminale.

- Reinstallare o aggiornare l'installazione: `installa.ps1` (tasto destro, *Esegui con PowerShell*)
- Disinstallare: Impostazioni di Windows › App installate › FantAiuto, oppure `disinstalla.ps1`
- Aprirlo senza scorciatoia: `pythonw avvia.py`
- Vederlo nel browser per fare prove: `python -m streamlit run app.py`

### Le pagine

| Pagina | A cosa serve |
|---|---|
| **Asta** | Il cuore. Cerca e filtra i 590 calciatori, apri la scheda, segna chi viene venduto. I prezzi si ricalcolano a ogni acquisto in base a quanti crediti e quanti giocatori validi restano davvero sul tavolo. |
| **Chiedimi** | Le domande dell'asta scritte come vengono: *quanto vale Dimarco*, *posso arrivare a 90 su Lautaro*, *a quanto finirà*, *cosa mi manca*, *come sta andando l'asta*. Risponde coi numeri di quel secondo. |
| **Consigli** | Il ragionamento: sei rose che farei con i crediti che ti restano, disegnate su un campo, le alternative a ogni fascia di prezzo reparto per reparto, i blocchi difensivi per il modificatore, le occasioni, i rigoristi, chi non salta mai, le scommesse, di chi parlano le redazioni e gli avvisi. Si ricalcola a ogni acquisto. |
| **Le squadre** | Tutte e 10 le squadre della lega: quanto ha speso ognuna, quanto le resta, fin dove può rilanciare, che rosa sta costruendo. |
| **La mia rosa** | Cosa hai comprato, quanto hai speso rispetto al consiglio, dove sei scoperto. |
| **Formazione** | Chi schierare nella prossima giornata. Per ogni modulo provo tutte le combinazioni di portiere e difensori e tengo quella che rende di più **modificatore compreso**, poi ti dico quale dei sette moduli conviene e di quanti punti. Avversario, campo, probabili formazioni, infortuni e diffidati già incrociati. |
| **Infermeria** | Chi è fuori e per quanto, con la nota della redazione. In cima quelli della tua rosa. |
| **Statistiche** | Quattro stagioni, diciassette classifiche, i cartellini di ogni calciatore, la scomposizione della fantamedia, le squadre e il tabellone completo. |
| **Impostazioni** | Numero di squadre, crediti, modificatore, squadre impegnate nelle coppe, slot, quote di budget per reparto. Salvi e ricalcola tutto. |

Le tabelle non sono ordinabili cliccando l'intestazione: usa il menu **Ordina per**
(prezzo consigliato, valore atteso, occasioni rispetto al mercato, partite attese...).

### Assegnare un giocatore, in asta

Subito sotto la tabella c'è una riga sola:

**Calciatore ▾ · A quale squadra ▾ · Prezzo · ASSEGNA**

La squadra proposta è sempre la tua (quella con la stella), quindi comprare per te è
scegliere il nome, scrivere il prezzo e premere il tasto arancione. Per segnare
l'acquisto di un avversario cambi solo il menu di mezzo. Se il giocatore era già
assegnato l'app te lo dice e riassegnarlo lo sposta; c'è anche un tasto **Libera** per
correggere un errore.

Segna anche gli acquisti degli altri: è così che i prezzi restano sensati man mano che
il mercato si svuota, ed è così che la pagina *Le squadre* sa quanto ti possono
rilanciare.

### La pagina "Le squadre"

In cima, **i nomi**: dieci caselle dove scrivere come si chiamano i tuoi avversari, più
il menu che dice quale delle dieci sei tu. Premi *Salva i nomi* e li ritrovi ovunque,
a partire dal menu a tendina dell'asta.

Poi una riga per squadra con crediti spesi, residui, **offerta massima** e la rosa
divisa per ruolo. L'offerta massima è quanto quella squadra può davvero mettere su un
singolo giocatore tenendosi un credito per ogni slot che le resta da riempire: è il
numero che ti dice fin dove possono spingersi.

Sotto, una scheda per squadra: cosa ha comprato e a che prezzo, con il confronto
rispetto al prezzo consigliato, e i comandi per aggiungere o togliere giocatori.

---

## La versione portatile

Sul Desktop c'è **FantAiuto Portatile**, una copia che funziona senza Python e senza
installare niente — anche copiata su una chiavetta e aperta su un altro computer
Windows. Il collegamento `FantAiuto` sul Desktop punta lì.

**Perché è una cartella e non un solo file.** Dentro l'eseguibile ci sta il programma;
fuori ci stanno i dati, perché i dati cambiano ogni ora e quello che cambia non può
vivere dentro un file che non si può riscrivere. Si può fare anche un `.exe` unico da
un file solo, ma dovrebbe scompattarsi da capo a ogni avvio: dieci secondi di attesa
ogni volta, che la sera dell'asta sono dieci di troppo.

**Due cose da sapere.** La cartella va tenuta insieme: l'eseguibile cerca `dati\` e
`_internal\` accanto a sé. E questa copia ha i **suoi** dati, separati da quelli del
programma installato: gli acquisti che segni in una non compaiono nell'altra. All'asta
usane una sola, o ti ritrovi due verità diverse.

**L'aggiornamento**, dentro l'eseguibile, funziona in modo diverso: non potendo
chiamare un `python.exe` che lì non esiste, il programma richiama sé stesso con un
argomento ed esegue i passaggi uno dentro l'altro. Il pulsante nel menu dei tre puntini
fa esattamente questo. La versione installata si aggiorna da sola ogni ora, la
portatile no — può stare su una chiavetta scollegata — quindi prima dell'asta
aggiornala a mano.

**Come si ricostruisce**, se un giorno servisse:

```
python -m PyInstaller portatile.spec --noconfirm
python confeziona.py dist/FantAiuto
```

Il secondo comando copia i dati, azzera l'asta, scrive le istruzioni, **prova ad
aprirlo** e solo se la finestra compare lo lascia sul Desktop col suo collegamento. Un
eseguibile che non parte è peggio di nessun eseguibile: sembra pronto e ti pianta in
asso la sera che serve.

---

## L'aggiornamento automatico

È già installato: **ogni ora, cinque minuti dopo l'ora piena**, Windows riscarica
tutto e ricalcola. Non è pignoleria: le probabili formazioni e l'infermeria cambiano
durante la giornata, un ballottaggio può ribaltarsi la mattina della partita, e nel
giorno dell'asta un dato vecchio di ventiquattro ore è semplicemente un dato sbagliato.

Il PC dev'essere acceso: se in quel momento è spento il giro salta e riprende al
successivo. Puoi sempre forzarlo con il pulsante **Aggiorna i dati adesso** nell'app,
oppure con `python aggiorna.py`. Le pagine che non cambiano più restano in cache, quindi
un giro costa una manciata di secondi e poche centinaia di kilobyte.

Cosa scarica: quotazioni e listone, statistiche di quattro stagioni, i voti di ogni
giornata già giocata, le schede di tutti i calciatori, il calendario, e da SosFanta le
probabili formazioni con l'infermeria.

### Da dove vengono i dati

| Cosa | Fonte |
|---|---|
| Listone e ruoli | fantacalcio.it — è il listone ufficiale dell'asta |
| **Prezzo di mercato** | **due fonti: FVM di fantacalcio.it + quotazione di Fantapazz** |
| Statistiche 2023/24 → 2026/27 | fantacalcio.it |
| Voti giornata per giornata | fantacalcio.it |
| Schede giocatore (età, storico presenze) | fantacalcio.it |
| Calendario | fantacalcio.it |
| **Probabili formazioni** | **SosFanta** |
| **Ballottaggi** | **SosFanta** |
| **Infortunati e indisponibili** | **SosFanta**, integrata con fantacalcio.it |
| **Gol attesi (xG), minuti veri, xGChain** | **Understat** |
| **Consenso delle redazioni** | **titoli e sommari delle rubriche di consigli di SosFanta e fantacalcio.it** |

SosFanta dà tre cose che l'altra fonte non ha, e sono proprio quelle che servivano:
la **percentuale di titolarità** di ogni giocatore, i **ballottaggi** con le rispettive
quote, e la **giornata di rientro** attesa per chi è fuori. Il rientro in particolare
sostituisce una stima che prima ricavavo a naso dal testo della notizia.

Nella pagina Infermeria il rientro è mostrato in tre modi: la **giornata** indicata dalla
redazione, **quanti turni mancano** da qui, e la **data** di quella giornata presa dal
calendario. Quando la redazione non si sbilancia resta un trattino: preferisco non
inventarla.

- Log: `dati/aggiornamento.log`
- Diradarlo: `.\installa_aggiornamento.ps1 -OgniOre 3`
- Toglierlo: `.\installa_aggiornamento.ps1 -Rimuovi`

---

## Lo stile

L'app è stata rifatta. Non ridipinta: rifatta nel modo in cui è organizzata, perché il
problema non era il colore.

**Via la barra laterale, arriva la plancia.** Prima la navigazione, il tema e il pulsante
di aggiornamento stavano in una colonna a sinistra, e i numeri che contano davvero —
quanti crediti ti restano, fin dove puoi spingerti — stavano in fondo alla pagina. Due
difetti seri. Il primo è che dentro la finestra di FantAiuto, se chiudevi la barra
laterale, non c'era più modo di riaprirla. Il secondo è che all'asta nessuno scorre: se un
numero non è sullo schermo mentre il banditore conta, quel numero non esiste.

Adesso in cima c'è una fascia sola che non si muove mai, con dentro tutto: il marchio, le
otto sezioni, e quattro numeri sempre accesi — **crediti**, **fin dove puoi arrivare**,
**slot riempiti**, **giocatori venduti** in tutta la lega. Il tema chiaro e
l'aggiornamento manuale sono finiti sotto il bottone con i tre puntini: si usano una volta
al mese, non meritavano spazio permanente.

**Il banco.** La pagina Asta è divisa in due: a sinistra il listone che scorre, a destra
il banco, agganciato in alto. Il banco è il giocatore in battuta, e mostra quattro cose in
quest'ordine: chi è, quanto pagherei io, quanto stai per offrire, e fin dove può spingersi
il rivale più ricco. Quest'ultima è la risposta alla domanda che uno si fa davvero mentre
rilancia — *se salgo, quello mi segue?* — e prima stava in un'altra pagina.

**La carta.** Il giocatore non è più una riga di tabella: è una carta con il ritratto
ritagliato, l'alone del colore del suo ruolo, il cognome in condensato e il **massimo da
pagare** in arancione alto tre centimetri. È lo stesso oggetto ovunque compaia, così ce
n'è uno solo da imparare invece di sei impaginazioni diverse.

**Gli stemmi.** Le venti squadre hanno il loro stemma accanto alla sigla, nel listone,
nella rosa, nelle rose degli avversari e nella formazione. Su seicento righe la differenza
si sente: una riga con lo stemma si riconosce prima di una riga con tre lettere.

**Il movimento, poco.** Le carte si accendono in due decimi di secondo, i riquadri
scivolano dentro sfalsati, le barre si allungano invece di saltare. Nient'altro. Chi ha
chiesto al sistema operativo di ridurre le animazioni non ne vede nessuna.

Resta l'identità di sempre: arancione che comanda, grafite, angoli tagliati invece che
stondati, il colore che dice qualcosa e non decora mai. Sotto, una griglia tecnica appena
percettibile dà profondità senza farsi notare.

### Quattro difetti trovati misurando, non guardando

Il ridisegno l'ho fatto valutare da nove revisori con tre lenti diverse — fattibilità
tecnica, uso sotto pressione, ambizione visiva — e la parte più utile non sono stati i
complimenti ma i quattro difetti che nessuno vedeva a occhio.

**La tabella pesava tre megabyte e mezzo.** Gli stemmi che avevo appena aggiunto finivano
dentro *ogni cella* come immagine incorporata: 14.147 byte per riga, per 250 righe, e
Streamlit ricostruiva tutto a ogni lettera digitata nel campo di ricerca. Ora le venti
immagini sono definite una volta sola nel foglio di stile e le celle le richiamano per
nome. Misurato: da 3,54 MB a 310 KB.

**La pastiglia più importante era illeggibile.** Lo slot 1 — il titolarissimo, quello che
in asta si guarda più di ogni altra cosa — era blu notte con sopra testo nero: 1,68 di
contrasto, sotto qualunque soglia. Lo slot 3 stava a 2,75. Ora la scala degli slot parte da
13,50 e non scende mai sotto 5. E i colori usati come *inchiostro* (verde, rosso, ambra)
sono diventati quattro token separati che cambiano fra tema chiaro e scuro: prima in tema
chiaro il verde faceva 2,06 su bianco, cioè non si leggeva.

**I menù a tendina restavano bianchi nel tema scuro** e non capivo perché. Il foglio di
stile parlava a un attributo che Streamlit 1.63 non genera più: contati sulla pagina viva,
zero elementi. Tre regole morte da mesi. Ora usano il nodo giusto e sono scuri come il
resto.

**Due comandi cancellavano senza chiedere.** *Cancella gli acquisti* azzerava l'asta di
tutta la lega al primo clic, su un file che non ha un annulla; e nella pagina Le squadre
bastava cambiare il menu *Togli* — anche solo con la rotellina del mouse — perché
l'acquisto sparisse. Adesso il primo chiede conferma dicendoti quanti acquisti stai per
perdere, il secondo vuole che tu prema Conferma.

I controlli in `prove.py` ora misurano da soli il contrasto di tutte le tinte in tutti e
due i temi: se un colore torna sotto soglia, lo dicono prima che lo veda tu.

**Caratteri**: Saira Condensed per i titoli e i numeri grandi, Inter per il testo, con le
cifre a larghezza fissa così le colonne restano allineate. Arrivano da Google, ma se
all'asta la rete non c'è la pagina non si sfascia: sotto ci sono **Bahnschrift** e **Segoe
UI**, che Windows ha già installate, e il condensato resta condensato.

### La pelle: vetro, blu notte, angoli morbidi

Il primo vestito era netto e tecnico: angoli tagliati in diagonale, grigio ferro,
superfici tutte sullo stesso piano. Funzionava, ma era il gusto di dieci anni fa.
Adesso il linguaggio è un altro, e sta in tre decisioni.

**Gli angoli si arrotondano, ma non come sempre.** Al posto del taglio diagonale c'è
lo *squircle* — il quadrato-cerchio che Apple usa da quindici anni e che i browser
sanno finalmente disegnare da soli con `corner-shape`. La curvatura non parte di
scatto come in un angolo tondo normale: accelera. È la differenza fra un oggetto
stampato e un oggetto fabbricato, e si sente anche senza saperla riconoscere.

**Le superfici diventano vetro.** Non solo perché è la moda di quest'anno: questa app
ha molti pannelli sovrapposti — il banco sopra il listone, la plancia sopra tutto — e
il vetro dice a colpo d'occhio cosa sta sopra cosa. Sfondo semitrasparente, sfocatura
di quello che passa sotto, una linea di luce sul bordo alto. La profondità ha tre
livelli dichiarati: appoggiato, sollevato, in primo piano. Il banco è in primo piano
perché è lì che decidi.

**Il fondo passa dal grigio al blu notte.** Il grigio è neutro e non dice niente; su
un fondo bluastro l'arancione — che gli sta all'opposto sulla ruota dei colori — si
accende invece di spegnersi, e i verdi e i rossi dei dati si staccano di più senza
doverli fare più violenti.

E una cosa piccola che cambia la lettura più di tutte: **ogni riga porta il colore del
suo ruolo** su un filo verticale a sinistra, e la pastiglia del ruolo è diventata un
gettone tondo. Con dodici colonne di numeri, capire se stai guardando un difensore o
un attaccante costava un attimo di troppo.

Il tema chiaro non è un ripiego: ha le sue ombre, le sue luci e la sua punta di
azzurro, ed è controllato dagli stessi collaudi sul contrasto.

### Il movimento

Le tendenze del 2026 dicono tutte la stessa cosa, e per una volta hanno ragione: il
movimento è tornato a essere una **strategia, non una decorazione**. Interfacce calme,
micro-interazioni al posto degli effetti da fiera, e il rispetto di chi chiede meno
animazioni.

Qui il criterio è ancora più stretto, perché questa app si usa mentre il banditore
conta: **il movimento deve far capire cosa è cambiato, e sparire**. Tre durate sole,
una curva sola, dichiarate una volta in cima al foglio di stile.

| | Quando |
|---|---|
| **110 ms** | la risposta al tocco: un bottone che cede sotto il dito |
| **190 ms** | qualcosa che compare |
| **320 ms** | uno stato che cambia |

**Il prezzo che si muove è la cosa che conta.** Quando qualcuno strapaga un difensore,
tre secondi dopo i prezzi degli altri difensori sono cambiati — ma su una tabella da
duecentocinquanta righe non se ne accorge nessuno. Adesso le celle si accendono del
colore della direzione, verde in su e rosso in giù, con la freccia dello scarto accanto
al prezzo, e si spengono da sole in due secondi. Si vede con la coda dell'occhio mentre
si guarda altrove, che è esattamente come si guarda un'asta.

**I numeri salgono invece di apparire.** I crediti che restano, quanto puoi arrivare a
offrire, il prezzo massimo: ci arrivano davanti contando. È tutto CSS — `@property`
rende animabile una variabile intera e `counter()` la stampa — quindi non c'è
javascript che possa incantarsi. E riparte solo quando il numero cambia davvero: se
digiti nel campo di ricerca, i numeri restano fermi.

**Le righe si rivelano entrando nella vista**, con le animazioni legate allo
scorrimento (`animation-timeline: view()`). È l'unico effetto qui dentro che esiste
per il piacere di guardarlo, ed è tarato per non farsi notare: parte già quasi opaco
e finisce prima che l'occhio ci arrivi sopra.

**La plancia si stacca dalla pagina solo quando c'è qualcosa sopra di lei.** Ferma in
cima è parte del foglio; appena scorri, si alza di un millimetro con la sua ombra.

**Mentre il programma ricalcola**, una linea sottile scorre in cima allo schermo, al
posto della rotellina in un angolo che non guardava nessuno.

E due cose che si notano solo se mancano: **chi naviga da tastiera** vede sempre dove
si trova, con un contorno arancione che compare solo col tabulatore e mai col mouse; e
**chi ha chiesto al sistema di ridurre le animazioni** non ne vede nemmeno una — i
prezzi mossi restano colorati in modo fisso, i numeri sono già scritti al loro posto.

Il collaudo automatico controlla che tutto questo non si rompa in silenzio: che le
durate siano dichiarate una volta sola, che il blocco per chi non vuole animazioni
spenga davvero tutto, e che un numero decimale non finisca per sbaglio dentro un
contatore.

### La grafica dei dati

La novità che conta più dell'estetica: dentro le tabelle i numeri non sono più solo
cifre.

- Sotto il **prezzo massimo** c'è la barra che dice quanto pesa rispetto al più caro in
  lista; sotto la **fantamedia** e le **partite attese** lo stesso, in ciano e in verde.
  Una tabella così si legge con la coda dell'occhio invece di doverla studiare.
- La colonna **Forma** disegna l'andamento delle ultime giornate, con la linea del 6
  tratteggiata come riferimento: verde se l'ultimo voto è sopra, rosso se sotto.
- Nella scheda di ogni giocatore c'è il **profilo a cinque assi** — quanto rende, quanto
  gioca, quanto è solido nel voto, quanto pesa nel gioco della sua squadra, quanto è
  affidabile — confrontato con la media del suo ruolo. Due giocatori con la stessa
  fantamedia disegnano quasi sempre figure diverse, ed è lì che si vede chi ti serve
  davvero.

Tutto è disegnato in SVG dentro il programma: nessuna libreria di grafici, nessuna
immagine da scaricare, e funziona identico in tema chiaro e scuro.

Sta in `tema.py`: palette, foglio di stile e i mattoncini (riquadri, pastiglie, tabelle,
campo, radar, linee). Se vuoi cambiare i colori, le costanti in cima a quel file sono
l'unico posto da toccare.

---

## Come nascono i numeri

**FM attesa** — la fantamedia prevista. Media delle stagioni pesata sia per recenza sia
per partite giocate, **stagione in corso compresa**: il suo peso cresce con le giornate
giocate (10% alla seconda, 26% alla quinta, oltre il 50% dalla decima in poi) e il resto
si ridistribuisce sulle annate passate mantenendone le proporzioni. Alla terza giornata
due partite non dicono niente e comanda lo storico; a dicembre è il contrario. Le partite
della stagione in corso vengono riportate al passo di un'annata intera, altrimenti a
settembre risulterebbero tutti panchinari.

Fino alla versione precedente lo storico era 60/28/12 sulle tre annate passate, poi riportata
un po' verso la media del ruolo quando le partite alle spalle sono poche. Serve a non
farsi ingannare da un 8,5 costruito su quattro partite.

**PV attese** — le partite a voto previste. Parte dallo storico con gli stessi pesi, poi
toglie le giornate di stop che mancano al rientro (SosFanta dice in quale giornata è
atteso) e corregge per la probabilità di titolarità della settimana. La correzione resta
contenuta, perché quella percentuale vale per una giornata sola mentre lo storico parla
di un'intera stagione; per i portieri invece pesa molto, perché lì la gerarchia è quasi
assoluta.
Una stagione passata in Serie A conta con le partite realmente giocate anche se sono
zero — chi è stato fuori un anno viene penalizzato — mentre una stagione all'estero o in
Serie B viene ignorata.

**Valore** — `(FM attesa − fantamedia media del ruolo) × PV attese`: i fantapunti che ti
fa guadagnare in una stagione rispetto a un giocatore qualunque del suo ruolo. È questo
il metro dell'asta, non la fantamedia secca: tiene insieme quanto è forte e quanto gioca,
e non premia il mediano che c'è sempre ma non porta bonus.
### Il modificatore di difesa, come funziona davvero

Nella tua lega schieri portiere più almeno quattro difensori, ma nella media entrano
**solo il portiere e i tre difensori col voto migliore**, e da 6,00 in su si sale di un
punto ogni 0,25. Due conseguenze che quasi nessun tool prezza:

**Un modulo a tre dietro rinuncia al modificatore per intero.** Non è un dettaglio: sono
uno o due punti a giornata buttati. La scelta del modulo, sia nelle rose che propongo sia
nella pagina Formazione, ora mette il modificatore nel conto — ed è il motivo per cui le
proposte escono tutte con quattro o cinque difensori.

**Il quarto difensore non vale niente per il modificatore.** Se hai già portiere e tre
difensori da voto alto, il quinto acquisto in difesa alza la media di zero, perché nella
media non ci entra. Il valore di un difensore quindi *non è un numero assoluto*: dipende
da chi hai già. Il programma lo calcola sulla **tua** rosa e lo rifà a ogni acquisto —
Akanji vale +1,1 fantapunti se ti migliora il terzo posto del blocco, e +0,0 se non lo
migliora. Lo trovi scritto nella scheda di ogni portiere e difensore.

Per la valutazione uso la versione smussata della tabella invece dei gradini: dove finirà
davvero la media del blocco non si sa, e il valore atteso di una scala di gradini vista da
lontano è la retta che li unisce. Ma i due estremi restano: sotto il 6 non prendi niente,
sopra il 7 non prendi di più, e sono proprio i punti dove una formula lineare sbaglierebbe.

**Il secondo portiere non è un riempitivo.** Col modificatore, se il titolare salta due
giornate e schieri un portiere qualunque il blocco crolla. Nelle rose che propongo il
secondo portiere è il vice della stessa squadra del tuo titolare — entra lui quando
l'altro non c'è — oppure un altro titolare vero, e costa pochi crediti.

**La formazione della settimana la scelgo provando tutte le combinazioni.** Mettere in
fila i difensori per fantamedia attesa e prendere i primi quattro è la cosa sbagliata da
fare: il modificatore guarda il *voto*, non il fantavoto, e guarda solo i tre voti più
alti. Un difensore da 6,30 di media voto che non segna mai può valere più di uno che ogni
tanto la butta dentro ma prende 5,5. Quindi nella pagina Formazione, per ogni modulo,
provo ogni portiere schierabile per ogni combinazione di difensori — qualche centinaio di
conti, un battito di ciglia — e tengo quella che massimizza *fantapunti dell'undici più
modificatore*. Poi confronto i sette moduli fra loro e ti dico quale rende di più, con la
differenza in punti rispetto agli altri. In tabella trovi la colonna **MV**, la previsione
sul voto secco, e in azzurro i quattro che formano il blocco.

Un effetto che si vede subito: col modificatore acceso il quarto difensore si paga da
solo, e il 3-4-3 che senza modificatore era il modulo migliore diventa il peggiore.

**Solo numeri** — il valore convertito in crediti: si toglie il livello del giocatore che
in quel ruolo prenderesti comunque a 1 credito, e si spalma il budget della lega sul
resto secondo le quote per reparto.

**Mercato** — la media di **due stime indipendenti**: il FVM ufficiale di
fantacalcio.it e la quotazione di mercato di Fantapazz. Le trovi anche separate, nelle
colonne *Fcalcio* e *Fpazz*, e nella scheda del giocatore ti segnalo quando divergono
molto: lì di solito c'è qualcosa da capire.

Ogni fonte usa una scala sua, e nessuna delle due è calibrata sui crediti veri: sommando
il FVM dei 250 giocatori che verranno effettivamente comprati viene il 118% del budget
della lega, con Fantapazz il 95%. Le riporto entrambe al 100%, così smettono di essere
un indice astratto e diventano *quanto quel giocatore costerà davvero nella tua asta* —
confrontabile con i miei prezzi e con quello che vedi battere sul tavolo.

(SosFanta ha una pagina quotazioni, ma ripubblica il listone ufficiale di Leghe
Fantacalcio: come terza fonte non aggiungerebbe niente di nuovo.)

**Max da pagare** — il numero che conta, e l'unico prezzo che trovi in tabella.
È il valore equo del giocatore più un premio di scarsità, tagliato da quello che ti
puoi davvero permettere.

Il premio di scarsità nasce dal rapporto fra quanti giocatori restano in quella fascia
e quante squadre la stanno ancora cercando. All'inizio dell'asta ogni fascia ha dieci
giocatori e dieci squadre che li vogliono: il rapporto vale 1 e non c'è premio. Quando
una fascia si svuota più in fretta di quanto cali la domanda, il premio sale — ed è
esattamente quando conviene pagare qualcosa in più, perché dopo non c'è più. La colonna
*Scorte* te lo dice a parole.

Il taglio finale è la tua borsa: i crediti che ti restano meno uno per ogni slot che
dovrai ancora riempire. Se il tetto che vedi è quello, l'app te lo scrive.

Le quotazioni delle singole fonti non stanno più in tabella: le trovi nella scheda del
giocatore, insieme a tutto il resto che serve per capire quel numero.

**Comparatore** — sotto la scheda, chi vale come lui: i pari-fascia più vicini per
valore atteso, con i già venduti e il prezzo che hanno spuntato. È la domanda vera
dell'asta — *se Paz N. è andato a 70, McTominay quanto vale?* — e la risposta si vede
subito, perché il tetto di tutti i pari-fascia si muove insieme.

**Slot** — la fascia che il giocatore occupa nel suo ruolo. Con 10 squadre i primi 10
attaccanti sono lo slot **A1**, cioè il centravanti titolare di ogni fantallenatore; i
successivi 10 sono A2, e così via fino ad A6. Chi resta fuori dai 60 è *fuori rosa*:
qualcuno non lo comprerà nessuno. L'ordinamento è per prezzo di mercato, perché è così
che l'asta li metterà in fila davvero. Nella pagina Asta c'è anche il filtro per slot:
"mostrami i difensori di terza fascia ancora liberi" è una domanda che in asta ti fai
di continuo.

### Le statistiche, cartellini compresi

Ammonizioni ed espulsioni ora ci sono per ogni calciatore, su tutte e quattro le stagioni:
**2625 gialli e 121 rossi** dal 2023/24 a oggi, e per la stagione in corso anche **giornata
per giornata**. Non sono lì per completezza, servono a rispondere a tre domande diverse.

**Quanto è falloso davvero.** Il totale dei gialli premia chi ha giocato di più: dodici
ammonizioni in trentacinque partite sono un difensore normale, otto in dodici partite sono
un problema. Quindi il numero che uso ovunque è **gialli per partita giocata**, pesato
sulle stagioni come tutto il resto (quella in corso conta di più, le vecchie scendono), e
confrontato con gli altri dello stesso ruolo: essere il più falloso dei difensori vuol dire
un'altra cosa che esserlo fra gli attaccanti.

**Quante giornate rischia di perdere.** In Serie A la quinta ammonizione fa saltare una
giornata, e un rosso ne costa una, a volte due. Dalla frequenza storica ricavo le giornate
di squalifica attese per la stagione: Wesley ne rischia 3,3, Zaccagni 2,3, Dimarco 0,5.
Questa stima non viene sottratta dalle presenze attese, e c'è un motivo: le assenze del
passato — squalifiche comprese — sono già dentro il conteggio delle partite saltate.
Toglierle di nuovo sarebbe contarle due volte. È un'informazione, non una penalità
nascosta.

**Quanto gli costano in fantapunti.** Mezzo punto per giallo e uno per rosso sembrano
niente. Su un difensore da dieci gialli l'anno sono cinque fantapunti buttati più una o due
giornate di squalifica: vale quanto un gol e mezzo di un attaccante.

#### Da dove viene la fantamedia

C'era una domanda a cui dovevo rispondere prima di poter usare i cartellini: la fantamedia
pubblicata dalla fonte li conta già, oppure no? Se li contasse e io li sottraessi ancora,
gli stessi giocatori verrebbero puniti due volte.

L'ho verificato invece di fidarmi. Ho preso i 625 giocatori con almeno cinque presenze in
due stagioni e ho fatto una regressione di `(fantamedia − media voto) × presenze` sui
bonus e i malus. I coefficienti che sono usciti:

| | coefficiente trovato | regolamento |
|---|---|---|
| Gol | +2,89 | +3 |
| Assist | +1,01 | +1 |
| Rigore parato | +2,98 | +3 |
| Gol subito | −1,00 | −1 |
| Ammonizione | −0,49 | −0,5 |
| Espulsione | −1,09 | −1 |

È il regolamento del fantacalcio, ritrovato dai numeri. Quindi sì: **i cartellini sono già
dentro la fantamedia**, e nel modello non vanno tolti un'altra volta.

Il sottoprodotto è la parte più interessante: sapendo i pesi posso **scomporre la
fantamedia di chiunque** e dire da dove arrivano i suoi punti. La ricostruzione coincide
con il valore dichiarato (scarto mediano 0,00 su 318 giocatori, massimo 0,20), quindi non è
una stima, è una scomposizione esatta:

- **Pongracic** — voto 5,84, nessun bonus, −0,17 di ammonizioni: fantamedia 5,67. Non è
  sfortuna, sono dodici gialli.
- **Dimarco** — voto 6,60, +0,60 dai gol, +0,49 dagli assist, −0,04 di cartellini: 7,64.
- **Svilar** — voto 6,26, −0,82 di gol subiti: 5,44. Per un portiere il malus è il mestiere.

#### Il cartellino era lì e nessuno lo vedeva

Per avere i cartellini di giornata sono dovuto andare a cercarli dove non sembravano
esserci. Nella pagina dei voti, fantacalcio.it pubblica otto bonus per giocatore — gol,
assist, autoreti, rigori — e i cartellini non sono fra quelli. Il fantavoto che stampa non
li conta nemmeno: il malus lo applica la lega al momento del calcolo.

Il cartellino però c'è: non è un dato, è una **classe CSS attaccata al voto**. Un ammonito
ha `class="player-grade yellow-card"` invece di `class="player-grade "`.

Questa scoperta ne ha portata dietro una peggiore. Il programma cercava la classe esatta,
quindi le righe degli ammoniti non gli somigliavano e le buttava via: **32 giocatori su 319
per ogni giornata**, il dieci per cento del campionato, sempre gli stessi, sempre gli
ammoniti. Sparivano dai voti di giornata, dalla colonna Forma e da qualunque media
calcolata sulla stagione in corso, e nessuno se ne accorgeva perché mancavano in silenzio.

Ora la classe viene letta invece che pretesa. I voti letti per giornata sono passati da 287
a 319, e in cambio ho il cartellino partita per partita. La controprova che sia giusto:
sommando i gialli giornata per giornata e confrontandoli con il totale dichiarato nelle
statistiche di stagione, **tornano per tutti e 592 i calciatori**.

#### Un errore che ho trovato mentre lavoravo

I fantavoti alti erano sbagliati. Il sito a volte scrive i voti senza virgola — "55" per
5,5 — e il programma li rimetteva in scala dividendo per dieci tutto ciò che superava il
10. Peccato che un fantavoto sopra il 10 sia legittimo: Malen alla prima giornata ha fatto
tre gol e ha preso 17,5, che diventava 1,75. Le partite migliori della stagione risultavano
le peggiori.

Ora la soglia è 30, non 10: sotto quel valore nessuna cifra scritta senza virgola è
ambigua. Trentacinque fantavoti della stagione in corso erano sbagliati e ora sono giusti,
e con loro la colonna Forma e tutte le classifiche di giornata.

---

### Il mio giudizio

Sotto ogni scheda c'è un riquadro arancione con un verdetto in due parole e le ragioni
scritte per esteso. Non è la fantamedia riscritta: è quello che i numeri grezzi non
dicono, su sei dimensioni.

**Quanto pesa nel gioco della sua squadra.** La fetta di gol e assist del club che passa
dai suoi piedi. Chi fa il 25% dei bonus è il riferimento offensivo; chi ne fa il 4% ha
avuto una buona annata di voti, che è un'altra cosa e si ripete meno.

**Quanto dipende dai rigori.** Non li deduco più dall'anno scorso: leggo la **gerarchia
dichiarata a mercato chiuso** da fantacalcio.it — primo, secondo e terzo rigorista squadra
per squadra, più i battitori di calci piazzati — dove ogni nome porta con sé l'id del
giocatore, quindi nessun abbinamento per nome e nessun rischio di sbagliare persona.

Poi tolgo dalla fantamedia i rigori del passato e ci rimetto quelli attesi dalla gerarchia
di oggi. Il risultato: Ramos, Beto, Cutrone e Calò guadagnano un quarto di fantamedia
perché sono i rigoristi designati e non ne avevano mai tirato uno; Nkunku ne perde più di
mezza perché li tirava e oggi nel Milan non è nell'ordine. Sapere che uno è il **secondo**
rigorista non è un dettaglio da poco: vale se il primo si ferma, ed è il genere di cosa
che all'asta nessuno prezza.

**Quanto è voto e quanto è bonus.** Due giocatori da 7,00 di fantamedia possono essere
opposti: uno prende 6,5 di voto e poco bonus, l'altro 5,9 e vive di gol. Il primo lo
schieri sempre, il secondo ti fa vincere tre giornate e perdere le altre venti. Nella
tua lega, col modificatore, la parte di voto vale doppio.

**Dove gioca davvero.** Il ruolo Mantra distingue il centrale dal terzino, il mediano
dal trequartista — mondi diversi per potenziale di bonus, che il ruolo Classic appiattisce
in una lettera sola. Un trequartista schierato fra i centrocampisti prende bonus da
attaccante al prezzo di un centrocampista, ed è una delle asimmetrie più sfruttabili
dell'asta.

**In che squadra ha fatto quei numeri, e in che squadra gioca adesso.** Quindici gol in
una squadra che ne produce cento non valgono quindici gol in una che ne produce settanta.

**Cosa ne dicono le redazioni.** Leggo titoli e sommari delle rubriche di consigli e asta
di SosFanta e fantacalcio.it — 447 brani all'ultimo giro, 113 giocatori nominati — e conto
chi viene citato e con che parole (*sottovalutati, scommesse, occasioni* da una parte;
*attenzione, trappole, rischio* dall'altra). Non è un parere di merito: è un termometro.
I nomi molto citati all'asta si pagano sopra il loro valore, e saperlo prima serve a non
rincorrerli. Dove due giocatori condividono il cognome — i due Thuram — la citazione conta
solo se il testo porta anche l'iniziale: attribuire un consiglio al fratello sbagliato
sarebbe peggio che non contarlo.

Di queste sei, **due correggono davvero il valore atteso**: il cambio di contesto e il
rischio rigori dopo un trasferimento. Sono le uniche informazioni che lo storico non
contiene già, e quindi le uniche che possono spostare un prezzo senza contare due volte
la stessa cosa. Chi non ha cambiato squadra ha uno scostamento esattamente zero. Le altre
quattro restano giudizio, e come tale te le racconto invece di nasconderle in un numero.

### La pagina Consigli

Non è un elenco ordinato per prezzo, è una strategia, e tiene insieme quattro cose che
all'asta vanno decise nello stesso momento.

**Tre rose che farei.** Non tre varianti della stessa idea: tre modi diversi di
spendere gli stessi crediti, **affiancati** per poterli confrontare a colpo d'occhio.
Ognuna è disegnata su un **campo da gioco vero**: righe tracciate a norma (aree di
rigore, aree piccole, dischetti, cerchio di centrocampo, archi d'angolo), e ogni
giocatore con il suo **ritratto** dentro un anello del colore del ruolo — ciano il
portiere, viola i difensori, arancione il centrocampo, rosso l'attacco — con il nome e il
prezzo massimo che pagherei. Sotto, il resto della rosa in panchina. Con le facce una
formazione si legge in un secondo; con i soli cognomi no.

I ritratti sono i campioncini ufficiali di fantacalcio.it, scaricati una volta sola in
`dati/campioncini/` (sei mega in tutto). Li tengo in locale invece di richiamarli dal
sito a ogni schermata perché all'asta la connessione è l'ultima cosa di cui fidarsi; chi
non ha il ritratto mostra le iniziali.

Il modulo non lo impongo: lo detta la rosa. Non ha senso schierare un 3-4-3 a chi ha
cinque difensori buoni e due attaccanti, quindi per ogni proposta provo tutti i moduli e
tengo quello che valorizza di più i giocatori che ha.

Le tre proposte vengono scelte perché **si assomiglino il meno possibile**: costruisco
una ventina di squadre e poi scarto quelle che condividono più del settanta per cento dei
nomi con una già scelta. Proporti tre volte la stessa rosa con due cambi non servirebbe.
Il titolo di ciascuna te ne dice il carattere — *Corazzata dietro*, *Peso in attacco*,
*Centrocampo che fa i bonus*, *Equilibrata* — e quando due proposte hanno lo stesso
carattere le distinguo col big su cui sono costruite.

Ogni rosa parte dallo stesso principio: la squadra che rende di più con i crediti che ti
restano, non la lista dei più forti. Prima assicuro i titolari veri di ogni reparto — quelli che
giocano almeno ventidue partite — scegliendoli in *un'unica classifica* per resa sul
credito invece che reparto per reparto, perché altrimenti il primo della fila si mangia
il budget degli altri.

Poi c'è un problema che quasi tutti i tool hanno e che ho dovuto risolvere: un algoritmo
che sceglie sempre il miglior rapporto valore/prezzo **non compra mai un top**, perché
ogni acquisto costoso peggiora quel rapporto anche quando è esattamente il giocatore che
fa la differenza. Quindi non costruisco una rosa sola: ne costruisco una ventina, ognuna
ancorata a un big diverso o a una coppia di big, le valuto tutte su una stagione intera
e tengo la migliore. Il punteggio non è la somma dei venticinque — ogni giornata ne
schieri undici, quindi contano i titolari; la panchina pesa un quarto e chi non gioca
mai quasi niente, con una penalità per i reparti senza abbastanza giocatori veri.

**Reparto per reparto.** Per ogni ruolo i migliori disponibili divisi in tre fasce di
spesa, otto nomi per fascia. Serve a non restare fermi quando il nome che volevi vola
via: sotto ogni top c'è quasi sempre qualcuno che rende l'ottanta per cento a un terzo
del prezzo.

**Occasioni, rigoristi, chi non salta mai.** Tre liste separate, perché all'asta sono
tre domande diverse. Le occasioni sono quelli su cui il mio tetto sta sopra il prezzo di
mercato. I rigoristi sono il bonus più prevedibile che esista, con la segnalazione di chi
ha cambiato squadra e quindi la designazione da riconquistare. "Chi non salta mai" sono
i trenta o più partite a voto previste: in un campionato da trentotto giornate la
presenza è il bonus più sottovalutato che c'è.

**Il blocco difensivo.** La tua lega usa il modificatore, e lì contano le medie voto,
non i bonus. Ti mostro quali squadre offrono ancora un portiere e tre difensori che
prendono voti alti, quanto costa il blocco e che media porta: costruire il reparto
attorno a un solo club è il modo più diretto di alzare quel modificatore.

**Le scommesse.** Un giocatore economico non è automaticamente un affare: il portiere
del Lecce costa poco perché vale poco. Cerco altro — chi rende molto rispetto a quello
che chiede *e* ha una ragione concreta per farlo: l'età, i rigori, un posto da titolare
appena conquistato pur essendo di bassa fascia. I portieri restano fuori: lì non ci sono
sorprese, o giochi o no.

**Gli avvisi.** Le cose di cui, se non te le dice nessuno, ti accorgi troppo tardi: i
crediti che non bastano più, un reparto che sta finendo mentre ti mancano slot, un ruolo
che la lega sta pagando troppo (lascia correre) o troppo poco (spingi), troppi giocatori
fragili in rosa.

Su cosa ragiona: listone e statistiche di quattro stagioni da fantacalcio.it, probabili
formazioni e infermeria da SosFanta, quotazioni da fantacalcio.it e Fantapazz, più i
prezzi reali che stai battendo in questa asta. Quello che **non** fa è leggere gli
articoli di consigli usciti stamattina: il ragionamento è costruito sui numeri, non
sulle opinioni delle redazioni.

### I prezzi si ricalibrano su quello che succede in asta

Ogni volta che segni un acquisto, il programma confronta il prezzo pagato con quello che
aveva consigliato, e aggiorna tutto. Guarda tre livelli — l'intera lega, il singolo
ruolo, il singolo slot — perché un'asta non si scalda in modo uniforme: capita che volino
i primi attaccanti e restino fermi i terzi portieri. Con pochi acquisti alle spalle il
dato è rumoroso, quindi ogni livello viene tirato verso quello più generale finché i
numeri non bastano.

Il risultato è che i crediti rimasti vengono ridistribuiti in base a due cose: quanto
valore è ancora sul mercato in ogni reparto, e quanto quel reparto sta effettivamente
costando. Se la lega brucia 1800 crediti sui primi dieci attaccanti, tutti i prezzi
scendono perché c'è meno cassa in giro, ma gli attaccanti scendono meno degli altri
perché è lì che i soldi continuano ad andare. In cima alla pagina Asta trovi la riga che
te lo dice: *"la lega sta pagando +20%, attaccanti +35%"*.

**Consiglio** — media pesata: 60% numeri, 40% mercato. Il mercato conosce cose che le
statistiche non vedono (gerarchie, mercato estivo, voci di spogliatoio), e quando i due
sono molto distanti vale la pena capire perché. Sui 258 giocatori che contano davvero le
due stime vanno d'accordo (correlazione 0,90): sono gli scarti grossi la parte
interessante.

**Rischio** — quanto è probabile che salti giornate. Nasce dallo storico giornata per
giornata delle ultime due stagioni: un blocco di assenze consecutive conta come probabile
infortunio solo se il giocatore stava giocando prima e torna a giocare dopo (è quella la
firma di uno stop); un blocco a inizio o fine stagione di uno che comunque gioca poco è
semplicemente panchina. Poi si aggiunge mezza giornata per ogni anno oltre i 30.
Basso sotto 3 giornate perse attese, Medio da 3 a 8, Alto oltre. *Ignoto* vuol dire che
non c'è storico in Serie A.

**Atteso** (pagina Formazione) — la fantamedia prevista per quella singola partita:
fantamedia storica corretta per la forza dell'avversario, per il fattore campo e per la
percentuale di titolarità di SosFanta. Chi rischia di non prendere voto vale meno a
prescindere da quanto è bravo, e la percentuale è il modo onesto di metterli in fila.
Non è una previsione del voto, è un ordinamento di chi conviene schierare.

La fantamedia della fonte usa il punteggio standard: gol +3, assist +1, ammonizione −0,5,
espulsione −1; per i portieri rigore parato +3 e gol subito −1. L'ho verificato sui dati.

---

### Le coppe europee e i diffidati

**Le coppe.** Chi gioca in Europa gioca tre partite in otto giorni, e in campionato
ruota: i titolarissimi saltano qualche giornata in più, le riserve ne giocano qualcuna in
più. Lo storico non se ne accorge quando una squadra le coppe le ha appena conquistate o
appena perse. Una pagina da cui leggere l'elenco in modo affidabile non c'è — ci ho
provato — quindi te lo chiedo direttamente: in **Impostazioni → Coppe europee** spunti le
squadre impegnate, ti propongo un'ipotesi già pronta basata sulla differenza reti
dell'anno scorso, e tu la correggi. Da lì i perni di quelle squadre perdono il 6% delle
presenze attese e le alternative ne guadagnano l'8%, con tutto quello che segue sul
valore e sul prezzo.

**I diffidati.** Un diffidato gioca, ma al primo giallo salta la giornata dopo: non è
un'assenza, è un rischio da sapere *prima* di schierarlo, soprattutto sotto un turno
infrasettimanale. Nella pagina Formazione compare come pillola accanto al giocatore e
come avviso sotto l'undici. Alla terza giornata la lista è vuota, ed è giusto così: per
essere in diffida servono quattro gialli.

---

## La pagina Chiedimi

Una premessa, perché è l'unica cosa che conta per fidarsene: **lì dentro non c'è
nessuna intelligenza artificiale**. Non c'è un modello linguistico, non c'è una
connessione a un servizio che pensa. C'è un interprete che riconosce le domande che
si fanno davvero a un'asta e risponde usando il motore di calcolo del programma.

La differenza si sente in due modi opposti. In male: se scrivi una domanda che non ho
previsto, non improvviso — te lo dico e ti mostro cosa so fare. In bene: quando
rispondo, i numeri sono veri. Non sono un riassunto plausibile di quello che di solito
si dice sui difensori: sono il prezzo ricalcolato sui rilanci di stasera, i tuoi
crediti residui, gli slot che ti restano, e fin dove può spingersi la squadra seduta
di fronte a te.

Quello che capisce:

| Scrivi | Ti dice |
|---|---|
| **un nome** — *Dimarco*, *quanto vale Lautaro Martinez* | il massimo che pagherei oggi, perché, e chi te lo può portare via |
| **un nome e una cifra** — *posso arrivare a 90 su Thuram?*, *Kean a 45* | se quella cifra sta in piedi e, soprattutto, **cosa ti resta dopo** |
| **due nomi** — *Dimarco o Bastoni?* | il confronto, con la ragione della scelta |
| **come sto messo** | crediti, caselle, dove sei scoperto, il rivale più ricco |
| **cosa mi manca** | i buchi in rosa e chi li riempie, reparto per reparto |
| **un ruolo e un budget** — *difensore da 20* | i migliori entro quella cifra, in ordine di valore |
| **chi resta in attacco** | le scorte del reparto, per capire se conviene aspettare |
| **chi può rilanciarmi** | ogni squadra: crediti, tetto su un singolo giocatore, cosa le manca |
| **come sta andando l'asta** | la temperatura del mercato, la curva dei prezzi dal primo acquisto, reparto per reparto |
| **occasioni** | chi oggi vale più di quanto costerà |

La risposta più utile è la seconda. A *«Thuram a 118»*, con 120 crediti in cassa e 21
caselle da riempire, non risponde «sì»: risponde che dopo averlo pagato ti
resterebbero 2 crediti per 20 caselle, che te ne serve almeno uno a testa, e che
quindi il tuo tetto vero su quel giocatore è 100. È il conto che all'asta non fa in
tempo a fare nessuno.

**I nomi.** Nel listone Lautaro Martinez si chiama «Martinez L.» e Nico Paz «Paz N.»:
chi li cercasse per nome proprio non li troverebbe mai. Adesso il programma si porta
dietro anche il nome per esteso di tutti e 592 i calciatori, preso dalle schede che
già scaricava. E siccome in Serie A ci sono due Thuram, due Martinez e due Lautaro,
quando la parola che hai scritto è di più di uno **chiedo quale**, invece di scegliere
io e darti il prezzo dell'altro. Se uno dei due si chiama esattamente come hai scritto
— «Thuram» è Marcus, Khephren nel listone è «Thuram K.» — non ti chiedo niente.

---

## Le sei rose

Non sono sei varianti della stessa idea: sono **sei convinzioni diverse** su come si
vince una lega, e ognuna costruisce la rosa per servire la sua.

| | L'idea | Cosa costa |
|---|---|---|
| **La migliore che riesco a fare** | nessun vincolo: a ogni acquisto il giocatore che rende di più per credito speso | — |
| **Corazzata dietro** | il modificatore premia le medie voto, e il difensore medio è molto più scarso dell'attaccante medio | 5 punti |
| **Centrocampo che fa i bonus** | trequartisti e ali prendono bonus da attaccante al prezzo di un centrocampista | 43 punti |
| **Nessun big, tutti titolari** | niente sopra i 45 crediti, in cambio undici che giocano sempre | 44 punti |
| **Due fuoriclasse e via** | due nomi da prima fascia, il resto con quel che avanza | 56 punti |
| **Peso in attacco** | un centravanti da venti gol non lo sostituisci con niente | 64 punti |

La colonna di destra è la cosa che rende utile il confronto: **quanto costa preferire
un'idea**, in fantapunti su una stagione intera. Sotto ogni campo c'è anche il
rischio scritto per esteso — cosa va storto se quell'idea non funziona.

**Come sono costruite.** Ogni strategia riceve una divisione diversa del budget fra i
reparti, e poi lavora in due tempi: prima **copre**, comprando in ogni ruolo i
giocatori che rendono di più per credito speso, e solo dopo **migliora**, spendendo
quello che le è avanzato per sostituire i suoi elementi più deboli con i migliori che
può permettersi.

L'ordine conta più di quanto sembri. Il primo tentativo comprava subito i più cari nei
reparti privilegiati, e produceva rose che valevano un quarto delle altre: la borsa si
svuotava su due nomi e il reparto restava pieno di gente che non gioca. È lo stesso
errore che si fa all'asta vera quando ci si innamora del primo big che passa.

---

## Il prezzo che si muove mentre l'asta va avanti

Ogni volta che segni un acquisto — tuo o di un avversario — tutti i prezzi si rifanno
da zero. Non è un modo di dire: sono quattro conti diversi che girano insieme.

**1. Quanto vale.** I crediti ancora vivi nella lega vengono ridistribuiti fra i
reparti in proporzione al valore rimasto sul mercato e a quanto la lega sta pagando
quel reparto. Se gli attaccanti buoni finiscono, quei soldi migrano su difesa e
centrocampo e i prezzi lì salgono da soli.

**2. A quanto verrà battuto.** Questa è la novità che cambia il modo di giocare
l'asta. In un'asta al rialzo **il prezzo non lo fa chi vince: lo fa il secondo** —
paghi un credito più di quanto era disposto a mettere l'ultimo che si è ritirato.
Quindi per ogni giocatore guardo chi lo vuole ancora (chi ha una casella libera in
quel ruolo), quanti crediti ha davvero in mano, e quanto è disposto a spingersi: chi
ha il doppio dei crediti per casella paga di più, ed è quello che si vede a ogni asta.
Da lì escono due numeri che prima non c'erano:

| | Cosa dice |
|---|---|
| **Finirà a** | il prezzo di aggiudicazione previsto, cioè dove si fermerà l'asta |
| **Per batterli** | quanto devi mettere **tu** per portartelo via |

Se il tuo massimo è 118 e per batterli bastano 70, la mossa giusta non è rilanciare
fino a 118: è prenderlo a 72 e tenersi i 46 crediti, che valgono un centrocampista.
Il programma te lo dice in chiaro: *«Non serve arrivare a 118. Per batterli bastano
70: sono 48 crediti che restano tuoi.»*

**3. Chi si è mosso.** Appena segni un'aggiudicazione compare la riga di chi è
salito e chi è sceso. Provato: se qualcuno paga Dimarco 207 quando ne vale 138,
Bastoni passa da 35 a 40, Bremer da 39 a 44, Akanji da 32 a 36 — e nello stesso
momento Lautaro scende di 5, Thuram di 4, Hojlund di 3, perché quei crediti sono
finiti in difesa e non ci sono più per l'attacco.

**4. Da dove era partito.** Nella scheda di ogni giocatore c'è quanto valeva prima
che l'asta cominciasse e quanto vale adesso, con la ragione: la lega sta pagando quel
ruolo sopra i consigli, la sua fascia si sta svuotando, o nella lega sono rimasti più
(o meno) crediti per casella di quanti ne servano.

**La temperatura.** Il numero che riassume tutto è *quanti crediti restano in tutta
la lega per ogni casella ancora da riempire*. Da voi parte da 20 — cinquecento crediti
diviso venticinque slot. Sopra, i portafogli sono più pieni di quello che resta da
comprare e si strapaga; sotto, i soldi sono finiti prima dei giocatori ed è il momento
delle occasioni. Chiedi *«come sta andando l'asta»* e trovi la curva di come si è
mossa la lega dal primo colpo di martello a adesso.

**Una cautela onesta.** Il prezzo di aggiudicazione presume che i tuoi avversari
valutino i giocatori come li valuta il mercato. Se alla tua asta c'è quello che si
innamora di un nome e ci butta 150 crediti, nessun modello lo prevede — ma il
programma ti dirà comunque, un secondo dopo, che ha pagato 80 più del dovuto e dove è
rimasto scoperto. E finché i giocatori battuti sono meno di cinque, non ti dice niente
sul mercato: con quattro dati qualunque percentuale è rumore, e preferisco scriverlo
che darti un consiglio inventato.

---

## I gol attesi: fortuna o merito

Tutte le altre fonti dicono **cos'è successo** — cinque gol, due assist, sette
ammonizioni. Nessuna dice quanto sia ripetibile, e all'asta è la domanda che conta.

Gli *expected goals* rispondono a questo: ogni tiro vale una frazione di gol secondo
la posizione, l'angolo, la pressione, e la somma è quanti gol un giocatore *avrebbe
segnato* con un realizzatore nella media. Chi sta molto sopra il suo xG ha avuto una
settimana fortunata — e la fortuna non si compra a centoventi crediti.

Alla terza giornata i numeri parlano già:

| | Gol su azione | Gol costruiti | |
|---|---|---|---|
| Calhanoglu | 2 | 0,09 | due gol da fuori area: non si ripeteranno |
| Malen | 5 | 3,80 | sta rendendo sopra le sue occasioni |
| Gonçalo Ramos | 1 | 2,27 | tira bene e non la butta dentro: è in credito |
| Lautaro | 0 | 1,13 | zero gol ma occasioni vere, lo stavi valutando su tre partite storte |

**La correzione è prudente, e per tre motivi espliciti.** Conta solo i gol su azione,
perché i rigori li pesa già la gerarchia dei rigoristi e toglierli due volte
punirebbe chi non li tira. Cresce coi minuti giocati: su centoventi minuti lo scarto
è rumore, su cinque partite piene è un dato. E corregge poco più della metà dello
scarto, perché certi attaccanti stanno stabilmente sopra il loro xG semplicemente
perché calciano meglio degli altri — è un merito, non un colpo di fortuna. Infine
vale solo per la quota di fantamedia che viene da questa stagione: alla terza
giornata pesa il 15%, e la correzione con lei.

**Con una sola eccezione, la più importante.** Per chi non ha storico in Serie A la
fantamedia non viene dalle stagioni passate — non ne ha — ma dai giocatori con
quotazione simile, che è poco più di un'ipotesi. Lì quello che sta facendo *adesso* è
l'unica cosa vera che sappiamo, e pesa quasi tutto: è il motivo per cui Gonçalo Ramos
è salito da 105 a 113 crediti. Era la parte più debole del modello, ed è quella dove
il dato nuovo serve di più.

**Altre due cose che arrivano da lì.** I **minuti veri**: prima chi entrava
all'ottantottesimo contava come chi giocava novanta minuti. E l'**xGChain**, quanto
un giocatore partecipa alle azioni che finiscono in gol anche senza segnare né
servire l'assist — la misura di quanto pesa nel gioco della squadra, che prima
approssimavo con i soli bonus. Dimarco 0,91 ogni novanta minuti, Barella 1,32,
Mancini 1,27: sono i giocatori attraverso cui passa il gioco, e adesso il programma
lo dice.

**L'abbinamento fra le due fonti** è la parte fragile: lì si chiama "Lautaro
Martínez", nel listone è "Martinez L.". Funziona solo perché il programma si porta
dietro il nome per esteso di tutti i 592 calciatori. Su 370 giocatori ne abbina 361,
e ogni abbinamento dedotto deve superare una controprova: un pezzo di **cognome** —
non il nome proprio — deve ritrovarsi nel nome per esteso. È così che "Kevin Omoruyi"
non è finito su "Kevin Carlos", che sono due persone diverse. Chi non passa la prova
resta senza xG: meglio un dato mancante che il dato di un altro.

---

## Il modificatore: quanto costa davvero

La sezione dei blocchi difensivi non mette più in fila le squadre. Portiere e tre
difensori dello stesso club era una bella tabella e un consiglio inutile: all'asta
quattro giocatori della stessa squadra non li prendi quasi mai, o te li soffiano o
costano il doppio perché tutti hanno avuto la stessa idea.

Adesso trovi **lo stesso reparto comprato a quattro prezzi diversi**, pescando in
tutto il mercato rimasto. E il confronto dice una cosa che vale l'intera sezione:

| | Costo | Media voto | A giornata | In stagione |
|---|---|---|---|---|
| Con poco | 34 | 6,12 | +1,0 | 37 punti |
| Spesa media | 70 | 6,18 | +1,2 | 45 punti |
| Investimento | 107 | 6,24 | +1,5 | 55 punti |
| Senza badare a spese | 168 | 6,27 | +1,6 | 60 punti |

**Centotrentaquattro crediti separano il primo blocco dall'ultimo, e comprano 23 punti
in una stagione**: 0,17 punti per credito. Un attaccante da cinquanta crediti in più
ne rende fra 0,3 e 0,5. Il modificatore non è mai una scommessa sbagliata, ma non è
nemmeno un pozzo senza fondo: oltre una certa spesa i decimi di media si pagano cari,
e quei crediti fanno più danno altrove.

Il blocco è portiere più **tre** difensori perché nel modificatore contano solo i tre
voti migliori. Il quarto va schierato lo stesso, ma in quella media non entra: per
quel posto conviene chi porta bonus.

## Le scommesse, reparto per reparto

In una rosa da venticinque, i giocatori che decidono il campionato sono cinque o sei.
Gli altri diciannove sono il problema che tutti sottovalutano: le ultime caselle si
riempiono a fine asta, di fretta, con quello che avanza — ed è lì che si perdono i
punti, non sul top pagato dieci crediti di troppo.

La sezione adesso risponde a tre domande insieme: **quante** caselle di basso costo ti
restano in ogni reparto, **chi** ci metterei, e **quanti crediti tenere da parte**
perché non ti tocchi prendere il primo che passa. In cima trovi il totale — oggi 113
crediti su 500 — e poi tre elenchi separati per difesa, centrocampo e attacco.

**Quanto sia "poco" lo decide il reparto.** Diciotto crediti sono tanti per un
difensore e pochi per un attaccante, dove il listino parte più in alto: con un tetto
unico gli attaccanti da scommessa erano sempre uno o due. Adesso il tetto viene dai
prezzi veri di quel ruolo, e ogni reparto ha almeno tre nomi.

E ognuno ha una **ragione concreta** accanto, non un generico "costa poco": l'età, i
rigori che tira, un posto da titolare appena conquistato, il fatto che arrivi da fuori
e il mercato non sappia ancora quanto vale, o che le redazioni lo stiano indicando.

---

## Cosa il modello non sa

- **Non prevede gli infortuni.** Il rischio dice quanto spesso uno è stato indisponibile
  in passato, non chi si farà male. E la distinzione tra infortunio e panchina è dedotta
  dalla forma delle assenze, non dichiarata dalla fonte: su un giocatore che alterna
  può sbagliare.
- **Non conosce le gerarchie se non attraverso le probabili formazioni**, che valgono per
  una giornata sola. Un titolare che ha appena perso il posto lo scopre con settimane di
  ritardo.
- **I prezzi consigliati e la fantamedia attesa sono calcolati qui**, non presi da Algo
  Fantacalcio: quello è un tool a pagamento e i suoi numeri stanno dentro l'app, dietro
  l'abbonamento. Il metodo di questo programma è scritto per intero qui sopra, il loro no.
- **Gli xG coprono solo chi ha già giocato quest'anno** (361 su 592): chi non ha
  ancora messo piede in campo non ha tirato, e quindi non ha gol attesi.
- **Sui 181 giocatori senza storico in Serie A** (segnati *Ignoto*) il valore è stimato
  dai giocatori simili per quotazione: è la parte più debole di tutto il modello.
- **La pagina Chiedimi capisce solo le domande che ho previsto.** Non è un modello
  linguistico: fuori da quell'elenco dice «non ho capito» invece di inventare.
- **Le coppe europee gliele devi dire tu**, in Impostazioni: non esiste una fonte da cui
  leggerle in modo affidabile e preferisco chiedertelo che indovinare.
- **Non sa nulla di cambi di allenatore, moduli nuovi, o del fatto che una neopromossa è
  più dura della precedente.** Alle neopromosse assegna d'ufficio un attacco un po' sotto
  la media e una difesa un po' sopra.

---

## I file

```
avvia.py                      apre il programma nella sua finestra
app.py                        l'interfaccia: plancia, asta, consigli, rosa, formazione
  pag_statistiche.py          la pagina delle statistiche, cresciuta a parte
  risorse.py                  ritratti e stemmi, letti una volta e tenuti in memoria
aggiorna.py                   scarica + rielabora + ricalcola (lo lancia Windows ogni ora)
  fanta_scarica.py            scarica le pagine di fantacalcio.it
  fanta_schede.py             scarica le schede giocatore (età, storico presenze)
  fanta_sosfanta.py           legge le probabili e l'infermeria di SosFanta
  fanta_fantapazz.py          legge il listone e le quotazioni di Fantapazz
  fanta_redazioni.py          conta di chi parlano le rubriche di consigli
  fanta_campioncini.py        scarica i ritratti dei calciatori
  fanta_loghi.py              scarica gli stemmi delle venti squadre
  fanta_rigoristi.py          le gerarchie di rigori e calci piazzati
giudizio.py                   il livello di giudizio: le ragioni dietro i numeri
strategia.py                  il ragionamento d'asta: piano, blocchi, scommesse, avvisi
statistiche.py                classifiche, cartellini, scomposizione della fantamedia
  fanta_parse.py              trasforma l'HTML in dati/dataset.json
  fanta_modello.py            valutazioni, prezzi, rischio, consigli
tema.py                       lo stile: palette, CSS e mattoncini HTML
radice.py                     dove stanno i dati (sorgenti o eseguibile portatile)
prove.py                      i controlli: `python prove.py` dice se qualcosa si e' rotto
crea_icona.py                 genera FantAiuto.ico (gia' fatto, serve solo se la cambi)
portatile.spec                la ricetta per costruire l'eseguibile portatile
installa.ps1                  installa il programma e le scorciatoie
disinstalla.ps1               lo toglie del tutto
installa_aggiornamento.ps1    installa o rimuove il solo aggiornamento automatico
dati/
  html/       pagine scaricate      campioncini/  ritratti dei calciatori
  loghi/      stemmi delle squadre  schede.json   schede giocatore
  dataset.json   tutto il grezzo    valutazioni.json  il risultato dei calcoli
  config.json    le tue impostazioni
  asta.json      squadre della lega e tutti gli acquisti  <- l'unico file da salvare
  aggiornamento.log
```
