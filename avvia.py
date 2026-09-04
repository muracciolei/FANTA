# -*- coding: utf-8 -*-
"""Avvia FantAiuto come programma con la sua finestra.

Fa tre cose: accende il motore Streamlit su una porta libera senza aprire nessuna
finestra nera, aspetta che risponda, e poi mostra tutto dentro una finestra sua,
senza barra degli indirizzi ne' altra roba del browser. Quando chiudi la finestra
il motore viene spento.

Va lanciato con pythonw.exe (le scorciatoie create dall'installazione lo fanno gia').
"""
import os
import socket
import subprocess
import sys
import time

import radice

BASE = radice.cartella()
TITOLO = 'FantAiuto'
ATTESA_MAX = 90          # secondi prima di arrendersi
SENZA_CONSOLE = 0x08000000  # CREATE_NO_WINDOW


def porta_libera():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def risponde(porta):
    with socket.socket() as s:
        s.settimeout(0.4)
        try:
            s.connect(('127.0.0.1', porta))
            return True
        except OSError:
            return False


def interprete():
    """Quando gira sotto pythonw.exe uso quello, cosi' nemmeno il motore apre
    finestre nere."""
    exe = sys.executable
    senza = os.path.join(os.path.dirname(exe), 'pythonw.exe')
    return senza if os.path.exists(senza) else exe


def accendi_motore(porta):
    if radice.portatile():
        # nell'eseguibile non c'e' nessun python da chiamare: richiamo me stesso
        # con un argomento, e il ramo --motore accende Streamlit da dentro
        comando = [sys.executable, '--motore', str(porta)]
    else:
        comando = [
            interprete(), '-m', 'streamlit', 'run', os.path.join(BASE, 'app.py'),
            '--server.port', str(porta),
            '--server.headless', 'true',
            '--server.address', '127.0.0.1',
            '--browser.gatherUsageStats', 'false',
            '--global.developmentMode', 'false',
        ]
    creazione = SENZA_CONSOLE if os.name == 'nt' else 0
    return subprocess.Popen(comando, cwd=BASE, creationflags=creazione,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def motore(porta):
    """Streamlit acceso dentro questo stesso processo, senza riga di comando.

    E' quello che fa `streamlit run` quando lo lanci dal terminale, ma chiamato a
    mano: nell'eseguibile il comando `streamlit` non esiste, esiste solo il codice.
    """
    radice.senza_console()
    registro = os.path.join(BASE, 'dati', 'motore.log')
    try:
        os.makedirs(os.path.dirname(registro), exist_ok=True)
        sys.stdout = sys.stderr = open(registro, 'a', encoding='utf-8', errors='replace')
    except OSError:
        pass
    os.chdir(BASE)

    from streamlit import config as configurazione
    from streamlit.web import bootstrap

    script = os.path.join(radice.codice(), 'app.py')
    opzioni = {
        'server_port': porta,
        'server_headless': True,
        'server_address': '127.0.0.1',
        'server_fileWatcherType': 'none',   # dentro un bundle non c'e' niente da sorvegliare
        'browser_gatherUsageStats': False,
        'global_developmentMode': False,
    }
    configurazione._main_script_path = script
    bootstrap.load_config_options(flag_options=opzioni)
    bootstrap.run(script, False, [], opzioni)
    return 0


def finestra(porta):
    """La finestra vera se pywebview parte, il browser se non ce la fa.

    Prima qui si catturava il solo ImportError, e non bastava: dentro
    l'eseguibile portatile il modulo si importava benissimo ed era la
    *creazione* della finestra a fallire, per un pezzo del ponte verso .NET che
    non era stato impacchettato. Il programma moriva in silenzio, con il motore
    gia' acceso e nessun messaggio. Adesso qualunque cosa vada storta finisce
    scritta nel registro e l'app si apre nel browser: un'app che si apre nel
    posto sbagliato e' sempre meglio di un'app che non si apre.
    """
    try:
        import webview
        webview.create_window(
            TITOLO, 'http://127.0.0.1:%d' % porta,
            width=1480, height=940, min_size=(1024, 680),
            background_color='#FFFFFF', text_select=True)
        webview.start()
        return True
    except Exception as err:
        import traceback
        try:
            with open(os.path.join(BASE, 'dati', 'finestra.log'), 'a',
                      encoding='utf-8') as f:
                f.write(traceback.format_exc())
        except OSError:
            pass
        import webbrowser
        webbrowser.open('http://127.0.0.1:%d' % porta)
        return False


def errore(testo):
    """Se qualcosa va storto lo dico in una finestrella, non in un terminale che
    con pythonw nessuno vedrebbe."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, testo, TITOLO, 0x10)
    except Exception:
        sys.stderr.write(testo + '\n')


def main():
    # due scorciatoie usate solo dall'eseguibile: il motore che si accende in un
    # processo suo, e l'aggiornamento dei dati chiesto dal pulsante nell'app
    if '--motore' in sys.argv:
        return motore(int(sys.argv[sys.argv.index('--motore') + 1]))
    if '--aggiorna' in sys.argv:
        radice.senza_console()
        import aggiorna
        return aggiorna.main()

    if not os.path.exists(os.path.join(BASE, 'dati', 'valutazioni.json')):
        errore('Mancano i dati.\n\nLa cartella "dati" deve stare accanto a '
               'FantAiuto: se hai spostato l\'eseguibile da solo, riportalo '
               'nella sua cartella.'
               if radice.portatile() else
               'Mancano i dati.\n\nLancia una volta l\'aggiornamento '
               '(aggiorna.py) e poi riapri FantAiuto.')
        return 1

    porta = porta_libera()
    processo = accendi_motore(porta)

    scadenza = time.time() + ATTESA_MAX
    while time.time() < scadenza:
        if risponde(porta):
            break
        if processo.poll() is not None:
            errore('Il motore non e\' partito.\n\nProva a lanciare a mano:\n'
                   'python -m streamlit run app.py')
            return 1
        time.sleep(0.25)
    else:
        processo.terminate()
        errore('FantAiuto non ha risposto entro %d secondi.' % ATTESA_MAX)
        return 1

    try:
        if not finestra(porta):
            errore('FantAiuto e\' aperto nel browser.\n\nQuando hai finito chiudi '
                   'questa finestrella: serve a spegnere il motore.')
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=8)
        except subprocess.TimeoutExpired:
            processo.kill()
    return 0


if __name__ == '__main__':
    sys.exit(main())
