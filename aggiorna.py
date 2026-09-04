# -*- coding: utf-8 -*-
"""Aggiornamento completo: scarica da fantacalcio.it, rielabora, ricalcola.

Lo lancia da solo Windows tutti i giorni (vedi installa_aggiornamento.ps1),
ma puoi lanciarlo a mano quando vuoi:  python aggiorna.py
"""
import datetime
import io
import os
import subprocess
import sys

import radice

BASE = radice.cartella()
LOG = os.path.join(BASE, 'dati', 'aggiornamento.log')


def registra(testo):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write('%s  %s\n' % (datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'), testo))
    try:
        print(testo)
    except (UnicodeEncodeError, ValueError, OSError):
        # console Windows con codepage stretta, oppure nessuna console sotto
        # pythonw: sul file il log e' gia' scritto, qui non deve morire niente
        try:
            print(testo.encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass


class Raccolta(io.StringIO):
    """Un foglio dove far scrivere i passi quando girano qui dentro.

    I moduli cominciano con sys.stdout.reconfigure(): una StringIO normale quel
    metodo non ce l'ha e morirebbero sulla prima riga."""

    def reconfigure(self, **_):
        pass


def passo_interno(modulo):
    """Il passo eseguito dentro questo processo, senza lanciarne un altro.

    Nell'eseguibile portatile non c'e' nessun python.exe da chiamare: i moduli
    sono qui dentro, quindi li importo e chiamo la loro main(), raccogliendo
    quello che stampano per riversarlo nel log come se fosse un figlio."""
    import contextlib
    import importlib
    import traceback

    foglio = Raccolta()
    try:
        with contextlib.redirect_stdout(foglio), contextlib.redirect_stderr(foglio):
            esito = importlib.import_module(modulo[:-3]).main()
    except Exception:
        esito = 1
        foglio.write(traceback.format_exc())
    for riga in foglio.getvalue().splitlines():
        registra('    ' + riga)
    if esito:
        registra('    %s e\' fallito (codice %s)' % (modulo, esito))
    return not esito


def passo(nome, modulo):
    registra('--- %s' % nome)
    if radice.portatile():
        return passo_interno(modulo)
    # impongo UTF-8 al processo figlio: senza, su Windows scrive nella codepage
    # locale e i nomi accentati arrivano storpiati
    ambiente = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    r = subprocess.run([sys.executable, os.path.join(BASE, modulo)],
                       cwd=BASE, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=ambiente)
    for riga in (r.stdout or '').splitlines():
        registra('    ' + riga)
    if r.returncode != 0:
        for riga in (r.stderr or '').splitlines()[-15:]:
            registra('    ! ' + riga)
        registra('    %s e\' fallito (codice %d)' % (modulo, r.returncode))
    return r.returncode == 0


def main():
    registra('=== aggiornamento avviato')
    ok = True
    ok &= passo('scarico le pagine', 'fanta_scarica.py')
    ok &= passo('scarico le schede giocatore nuove', 'fanta_schede.py')
    ok &= passo('rileggo i dati', 'fanta_parse.py')
    ok &= passo('leggo le gerarchie dei rigoristi', 'fanta_rigoristi.py')
    ok &= passo('prendo i gol attesi', 'fanta_understat.py')
    ok &= passo('leggo di chi parlano le redazioni', 'fanta_redazioni.py')
    ok &= passo('scarico i ritratti mancanti', 'fanta_campioncini.py')
    ok &= passo('scarico gli stemmi delle squadre', 'fanta_loghi.py')
    ok &= passo('ricalcolo valutazioni e prezzi', 'fanta_modello.py')
    registra('=== aggiornamento %s' % ('completato' if ok else 'completato con errori'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
