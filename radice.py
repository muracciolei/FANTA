# -*- coding: utf-8 -*-
"""Dove stanno i dati.

Quando il programma gira dai sorgenti i dati sono nella cartella del programma, e
non c'e' niente da decidere. Quando invece gira dentro l'eseguibile portatile il
codice sta compresso dentro l'exe — in una cartella temporanea che Windows puo'
cancellare — mentre i dati devono stare fuori, accanto all'eseguibile, altrimenti
ogni aggiornamento e ogni acquisto segnato all'asta sparirebbero alla chiusura.

Un modulo di due righe, ma e' l'unico posto in cui questa differenza viene decisa:
tutti gli altri chiedono qui e non si preoccupano di come sono stati avviati.
"""
import os
import sys


def cartella():
    """La cartella dei dati: accanto all'eseguibile, o quella dei sorgenti."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def portatile():
    """True se stiamo girando dentro l'eseguibile e non dai sorgenti."""
    return bool(getattr(sys, 'frozen', False))


def codice():
    """Dove stanno i sorgenti: dentro l'eseguibile e' la cartella temporanea in
    cui PyInstaller li scompatta, altrimenti e' la cartella del programma."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def senza_console():
    """Sotto pythonw o dentro l'eseguibile senza finestra nera lo standard output
    non esiste: chi stampa deve avere qualcosa dove scrivere, o muore."""
    if sys.stdout is None or sys.stderr is None:
        buco = open(os.devnull, 'w', encoding='utf-8')
        if sys.stdout is None:
            sys.stdout = buco
        if sys.stderr is None:
            sys.stderr = buco
