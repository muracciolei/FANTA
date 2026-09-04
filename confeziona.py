# -*- coding: utf-8 -*-
"""Mette insieme la cartella portatile e la posa sul Desktop.

PyInstaller produce l'eseguibile e le sue librerie; qui si aggiunge tutto il
resto — i dati, i ritratti, gli stemmi, il manuale — e si confeziona il tutto in
una cartella che funziona ovunque la si copi, chiavetta compresa.

L'eseguibile da solo non basta e non e' un difetto: dentro ci sta il programma,
fuori ci stanno i dati, perche' i dati cambiano ogni ora e quello che cambia non
puo' vivere dentro un file che non si puo' riscrivere. Sul Desktop, oltre alla
cartella, resta un collegamento: si clicca quello.
"""
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
NOME = 'FantAiuto Portatile'

ISTRUZIONI = """FANTAIUTO — VERSIONE PORTATILE
===============================

Per aprirlo: doppio clic su FantAiuto.exe (o sul collegamento che trovi
sul Desktop).

Non serve Python, non serve installare niente. Questa cartella funziona
anche copiata su una chiavetta e aperta su un altro computer Windows.

COSA C'E' DENTRO
  FantAiuto.exe     il programma
  _internal\\        le sue librerie: non toccarla, non spostarla
  dati\\             quotazioni, statistiche, ritratti, e la tua asta
  LEGGIMI.md        il manuale completo

DUE COSE DA SAPERE

1. La cartella va tenuta insieme. L'eseguibile da solo non parte: cerca
   dati\\ e _internal\\ accanto a se'. Se vuoi spostarlo, sposta tutta la
   cartella.

2. Questa copia ha i suoi dati, separati da quelli del programma
   installato. Gli acquisti che segni qui non compaiono la' e viceversa:
   all'asta usane una sola, o ti ritrovi due verita' diverse.

AGGIORNARE I DATI
  Dal programma: il menu con i tre puntini in alto a destra, "Aggiorna
  adesso". Ci vuole circa un minuto e serve la connessione.

  La versione installata si aggiorna da sola ogni ora; questa no, perche'
  puo' stare su una chiavetta scollegata. Prima dell'asta, aggiornala a
  mano.
"""


def copia_dati(dentro):
    """I dati: tutto tranne i registri, che sono cronaca del computer di qui."""
    sorgente = os.path.join(BASE, 'dati')
    dest = os.path.join(dentro, 'dati')
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(sorgente, dest,
                    ignore=shutil.ignore_patterns('*.log', 'andamento.json',
                                                  '*.bak'))
    return dest


def azzera_asta(dentro):
    """La copia portatile parte da un'asta vuota: e' una postazione nuova."""
    import json
    perc = os.path.join(dentro, 'dati', 'asta.json')
    try:
        with open(perc, encoding='utf-8') as f:
            a = json.load(f)
    except (OSError, ValueError):
        a = {'squadre': [], 'mia': 0, 'acquisti': {}}
    a['acquisti'] = {}
    with open(perc, 'w', encoding='utf-8') as f:
        json.dump(a, f, ensure_ascii=False)


def collegamento(destinazione):
    """Il collegamento sul Desktop, con l'icona del programma."""
    ps = (
        "$s = (New-Object -COM WScript.Shell).CreateShortcut('%s');"
        "$s.TargetPath = '%s';"
        "$s.WorkingDirectory = '%s';"
        "$s.IconLocation = '%s';"
        "$s.Description = 'FantAiuto, versione portatile';"
        "$s.Save()"
    ) % (os.path.join(DESKTOP, 'FantAiuto.lnk'),
         os.path.join(destinazione, 'FantAiuto.exe'),
         destinazione,
         os.path.join(destinazione, 'FantAiuto.exe'))
    import subprocess
    return subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                          capture_output=True, text=True).returncode == 0


def collauda(cartella, attesa=75):
    """Lo lancio e guardo se si apre davvero, prima di consegnarlo.

    Un eseguibile che non parte e' peggio di nessun eseguibile: sembra pronto e
    ti pianta in asso la sera che serve. Qui si aspetta che compaia la finestra
    col titolo giusto — non che il processo esista, perche' un processo puo'
    esistere e stare morendo.
    """
    import ctypes
    import subprocess
    import time

    exe = os.path.join(cartella, 'FantAiuto.exe')
    p = subprocess.Popen([exe], cwd=cartella)
    trovata = False
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        if ctypes.windll.user32.FindWindowW(None, 'FantAiuto'):
            trovata = True
            break
        if p.poll() is not None:
            break
        time.sleep(1.0)

    if trovata:
        h = ctypes.windll.user32.FindWindowW(None, 'FantAiuto')
        ctypes.windll.user32.PostMessageW(h, 0x0010, 0, 0)   # WM_CLOSE
        time.sleep(3)
    try:
        p.terminate()
    except OSError:
        pass
    registro = os.path.join(cartella, 'dati', 'finestra.log')
    if os.path.exists(registro):
        with open(registro, encoding='utf-8', errors='replace') as f:
            coda = f.read()[-260:]
        print('  la finestra nativa ha avuto problemi, e si e aperto il browser:')
        for riga in coda.splitlines()[-4:]:
            print('     %s' % riga)
    return trovata


def peso(cartella):
    tot = 0
    for radice, _, file in os.walk(cartella):
        for f in file:
            try:
                tot += os.path.getsize(os.path.join(radice, f))
            except OSError:
                pass
    return tot / (1024.0 * 1024.0)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print('uso: python confeziona.py <cartella prodotta da PyInstaller>')
        return 1
    prodotto = sys.argv[1]
    if not os.path.exists(os.path.join(prodotto, 'FantAiuto.exe')):
        print('non trovo FantAiuto.exe in %s' % prodotto)
        return 1

    destinazione = os.path.join(DESKTOP, NOME)
    if os.path.exists(destinazione):
        shutil.rmtree(destinazione)
    print('copio il programma...')
    shutil.copytree(prodotto, destinazione)

    print('copio i dati...')
    copia_dati(destinazione)
    azzera_asta(destinazione)

    shutil.copy2(os.path.join(BASE, 'LEGGIMI.md'), destinazione)
    with open(os.path.join(destinazione, 'LEGGIMI PRIMA.txt'), 'w',
              encoding='utf-8') as f:
        f.write(ISTRUZIONI)

    print('collaudo: lo apro per vedere se parte...')
    if not collauda(destinazione):
        print()
        print('NON PARTE: non lo lascio sul Desktop in questo stato.')
        print('la cartella resta in %s per capire cosa manca' % destinazione)
        return 2
    print('  si apre correttamente')

    fatto = collegamento(destinazione)
    print()
    print('pronto: %s' % destinazione)
    print('peso: %.0f MB' % peso(destinazione))
    print('collegamento sul Desktop: %s' % ('sì' if fatto else 'non riuscito'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
