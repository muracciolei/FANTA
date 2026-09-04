# -*- coding: utf-8 -*-
"""La pagina "Chiedimi": le domande dell'asta, scritte come vengono.

Il resto del programma risponde a domande che ho previsto io, mettendole in
tabelle e in pagine. Qui la domanda la fai tu, con le tue parole, mentre il
banditore sta contando. La risposta arriva con i numeri di quel secondo li':
i crediti che ti restano davvero, i prezzi ricalibrati sui rilanci di stasera,
fin dove puo' spingersi chi ti sta rilanciando contro.

L'ordine della pagina segue quello che succede a un'asta: prima il campo dove
scrivere, subito sotto la risposta, e sotto ancora le domande di prima — perche'
capita spesso di volere di nuovo sotto gli occhi quello che avevi chiesto due
giocatori fa.
"""
import streamlit as st

import consulente as C
import mercato as MK
import strategia as S
import tema as T

MEMORIA = 6          # quante domande tengo sotto la risposta


def _html(x):
    st.markdown(x, unsafe_allow_html=True)


def contesto(d, asta, andamento=None):
    """Tutto quello che serve per rispondere, calcolato adesso.

    Ricalcolo a ogni domanda invece di tenerlo in cache: costa qualche decimo di
    secondo e mi assicura che, se nel frattempo hai segnato un acquisto, la
    risposta ne tenga conto. All'asta un prezzo vecchio di tre minuti e' un
    prezzo sbagliato.
    """
    cfg, giocatori = d['config'], d['giocatori']
    cal = MK.calibrazione(giocatori, asta)
    prezzi = MK.prezzi_live(giocatori, cfg, asta, cal)
    scar = MK.scarsita(giocatori, cfg, asta)
    massimi, tetto = MK.prezzi_massimi(giocatori, cfg, asta, prezzi, scar)
    attesi = MK.prezzi_attesi(giocatori, cfg, asta, prezzi)
    return {
        'd': d, 'asta': asta, 'cfg': cfg,
        'massimi': massimi, 'prezzi': prezzi, 'scar': scar, 'cal': cal,
        'attesi': attesi, 'temperatura': MK.temperatura(giocatori, cfg, asta),
        'andamento': andamento or [],
        'tetto': tetto,
        'per_id': {p['id']: p for p in giocatori},
        'sit': S.situazione(d, asta, cfg, MK.miei(asta)),
        'offerta_massima': lambda i: MK.offerta_massima(asta, cfg, i),
    }


def _chiedi(testo):
    """Metto la domanda in coda e faccio ridisegnare la pagina."""
    st.session_state['chiedimi_domanda'] = testo
    st.session_state['chiedimi_nuova'] = True


def pagina(d, asta):
    cfg = d['config']
    ctx = contesto(d, asta, MK.leggi_andamento())
    sit = ctx['sit']

    _html(T.riquadri([
        ('Crediti', sit['residuo'], 'te ne restano', 'ciano'),
        ('Puoi arrivare a', ctx['offerta_massima'](asta['mia']),
         'su un solo giocatore', 'verde'),
        ('Caselle', '%d/%d' % (sum(sit['ho'].values()), sum(cfg['slot'].values())),
         'riempite', ''),
        ('Sul mercato', len(d['giocatori']) - len(asta['acquisti']),
         'calciatori ancora liberi', ''),
    ]))

    with st.form('chiedimi', clear_on_submit=False):
        riga = st.columns([9, 2], vertical_alignment='bottom')
        testo = riga[0].text_input(
            'Chiedimi', key='chiedimi_testo',
            placeholder='quanto vale Dimarco? · posso arrivare a 90 su Lautaro? · '
                        'cosa mi manca? · chi resta in difesa?')
        inviato = riga[1].form_submit_button('Chiedi', type='primary',
                                             use_container_width=True)
    if inviato and testo.strip():
        _chiedi(testo.strip())

    # le domande pronte: all'asta non hai tempo di scrivere
    _html('<div class="titoletto">oppure chiedimi al volo</div>')
    scorciatoie = [
        ('Come sto messo?', 'come sto messo'),
        ('Cosa mi manca?', 'cosa mi manca'),
        ('Occasioni adesso', 'occasioni adesso'),
        ('Chi può rilanciarmi?', 'chi puo rilanciarmi'),
        ('Chi resta in difesa?', 'chi resta in difesa'),
        ('Chi resta in attacco?', 'chi resta in attacco'),
    ]
    colonne = st.columns(len(scorciatoie))
    for col, (etichetta, domanda) in zip(colonne, scorciatoie):
        if col.button(etichetta, key='sc_%s' % domanda.replace(' ', '_'),
                      use_container_width=True):
            _chiedi(domanda)

    storico = st.session_state.setdefault('chiedimi_storico', [])
    if st.session_state.pop('chiedimi_nuova', False):
        domanda = st.session_state.get('chiedimi_domanda', '')
        risposta = C.rispondi(domanda, ctx)
        storico.insert(0, {'domanda': domanda, 'risposta': risposta})
        del storico[MEMORIA:]

    if not storico:
        _html(T.vuoto(
            'Non mi hai ancora chiesto niente',
            'Scrivi un nome e ti dico quanto pagarlo. Scrivi un nome e una cifra '
            'e ti dico se quella cifra sta in piedi e cosa ti resta dopo. Scrivi '
            'due nomi e ti dico quale dei due prenderei.'))
        _html(C.risposta_aiuto(ctx)['corpo'])
        return

    prima = storico[0]
    _html(T.banda(prima['risposta']['titolo'], prima['domanda']))
    _html(prima['risposta']['corpo'])

    if len(storico) > 1:
        _html(T.banda('Le domande di prima', '%d' % (len(storico) - 1)))
        for voce in storico[1:]:
            with st.expander('%s  —  %s' % (voce['domanda'],
                                            voce['risposta']['titolo'])):
                _html(voce['risposta']['corpo'])
        if st.button('Svuota le domande'):
            st.session_state['chiedimi_storico'] = []
            st.rerun()

    _html(T.nota(
        'Le risposte escono dal motore di calcolo del programma, non da un '
        'modello che scrive frasi: i numeri sono quelli veri di adesso, '
        'ricalcolati sugli acquisti che hai segnato. In cambio capisco solo le '
        'domande che ho previsto — e quando non capisco te lo dico, invece di '
        'inventare un prezzo mentre stai per rilanciare.'))
