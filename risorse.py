# -*- coding: utf-8 -*-
"""Le immagini: ritratti dei calciatori e stemmi delle squadre.

Stanno qui e non dentro app.py perche' le usano piu' pagine, e non dentro tema.py
perche' quello disegna e basta: non deve sapere dove sono i file.

Tutto viene letto dal disco e incorporato nella pagina come base64. In asta la
connessione e' l'ultima cosa di cui fidarsi, e seicento ritratti che si caricano
uno alla volta da un sito esterno sono seicento occasioni di vedere un rettangolo
vuoto proprio mentre serve riconoscere un nome.
"""
import base64
import os

import streamlit as st

import radice

DATI = os.path.join(radice.cartella(), 'dati')


@st.cache_data(show_spinner=False, max_entries=800)
def ritratto(pid):
    """Il campioncino del giocatore, pronto per lo sfondo di un elemento.

    I file vuoti sono i buchi segnati dallo scaricatore: quel giocatore un
    ritratto non ce l'ha, e chi disegna ripiega sulle iniziali."""
    f = os.path.join(DATI, 'campioncini', '%s.png' % pid)
    try:
        if os.path.getsize(f) < 200:
            return None
        with open(f, 'rb') as fp:
            return 'data:image/png;base64,' + base64.b64encode(fp.read()).decode()
    except OSError:
        return None


@st.cache_data(show_spinner=False, max_entries=40)
def stemma(sigla):
    """Lo stemma della squadra in base64, o None se manca."""
    f = os.path.join(DATI, 'loghi', '%s.png' % sigla)
    try:
        with open(f, 'rb') as fp:
            return base64.b64encode(fp.read()).decode()
    except OSError:
        return None


@st.cache_data(show_spinner=False)
def foglio_stemmi():
    """Le venti immagini definite UNA volta, come classi CSS.

    Il modo ingenuo — incorporare il PNG dentro ogni cella della colonna Sq —
    costa quattordicimila byte per riga: su un listone da duecentocinquanta
    calciatori sono tre megabyte e mezzo di HTML, che Streamlit ricostruisce e
    rispedisce a ogni tasto premuto nel campo di ricerca. Definite qui una volta
    sola pesano duecentottanta kilobyte in tutto, e le celle diventano tre byte
    di classe.
    """
    regole = []
    for f in sorted(os.listdir(os.path.join(DATI, 'loghi'))):
        if not f.endswith('.png'):
            continue
        dato = stemma(f[:-4])
        if dato:
            regole.append('.sq-%s{background-image:url(data:image/png;base64,%s)}'
                          % (f[:-4], dato))
    return '<style>%s</style>' % ''.join(regole)
