# -*- mode: python ; coding: utf-8 -*-
"""Ricetta per costruire FantAiuto.exe, la versione portatile.

Si costruisce con:  python -m PyInstaller portatile.spec

Tre cose non ovvie, tutte necessarie perche' funzioni:

- **app.py viaggia come file, non come modulo.** Streamlit non importa la pagina,
  la *esegue leggendola dal disco*, quindi il sorgente deve esistere davvero dentro
  il pacchetto. Lo aggiungo ai dati e lo cerco poi con radice.codice().
- **app.py e' anche un import nascosto.** PyInstaller analizza solo i sorgenti che
  gli passi: dichiarandolo import nascosto legge le sue dipendenze e si porta
  dietro tema, strategia, giudizio e tutto il resto.
- **pyarrow e altair restano fuori.** Servono ai grafici e alle tabelle di
  Streamlit, che qui non uso: tutte le tabelle e tutti i grafici del programma
  sono HTML e SVG scritti a mano. Sono trecento mega risparmiati.
"""
import os

from PyInstaller.utils.hooks import collect_all, copy_metadata

BASE = os.path.abspath(os.getcwd())

datas, binaries, nascosti = [], [], []
for pacchetto in ('streamlit', 'webview', 'clr_loader', 'pythonnet'):
    d, b, n = collect_all(pacchetto)
    datas += d
    binaries += b
    nascosti += n

# Streamlit si legge la versione dai metadati del pacchetto: senza, non parte
for pacchetto in ('streamlit', 'pywebview'):
    try:
        datas += copy_metadata(pacchetto)
    except Exception:
        pass

datas += [(os.path.join(BASE, 'app.py'), '.')]

# Tutti i moduli del programma. app.py viene eseguito da Streamlit come file,
# non importato, quindi PyInstaller non ne vede le dipendenze da solo: le
# dichiaro qui una per una. Se ne aggiungi uno e ti scordi questa riga,
# l'eseguibile parte e poi muore alla prima pagina che lo usa.
# clr e' il ponte verso .NET che pywebview usa per aprire la finestra nativa.
# E' un modulo di tre righe che nessuno importa esplicitamente, quindi
# PyInstaller non lo vede: senza, l'eseguibile parte, accende il motore e poi
# muore in silenzio perche' la finestra non riesce a nascere.
nascosti += ['clr', 'pythonnet', 'clr_loader']
nascosti += ['app', 'aggiorna', 'radice', 'risorse', 'tema', 'strategia',
             'giudizio', 'statistiche', 'mercato', 'consulente',
             'pag_chiedimi', 'pag_statistiche',
             'fanta_modello', 'fanta_parse', 'fanta_scarica', 'fanta_schede',
             'fanta_sosfanta', 'fanta_fantapazz', 'fanta_rigoristi',
             'fanta_redazioni', 'fanta_campioncini', 'fanta_loghi',
             'fanta_understat']

analisi = Analysis(
    ['avvia.py'],
    pathex=[BASE],
    binaries=binaries,
    datas=datas,
    hiddenimports=nascosti,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pyarrow', 'altair', 'matplotlib', 'tkinter', 'IPython',
              'jupyter', 'notebook', 'pytest', 'PIL.ImageQt', 'PyQt5', 'PySide6'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analisi.pure)

exe = EXE(
    pyz,
    analisi.scripts,
    [],
    exclude_binaries=True,
    name='FantAiuto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE, 'FantAiuto.ico'),
)

coll = COLLECT(
    exe,
    analisi.binaries,
    analisi.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FantAiuto',
)
