# -*- coding: utf-8 -*-
"""Il livello di giudizio: quello che i numeri grezzi non dicono.

Una fantamedia e' un riassunto, e come tutti i riassunti nasconde le ragioni. Due
attaccanti da 7.00 possono essere cose opposte: uno che prende 6.5 di voto e segna
poco, e uno che prende 5.9 e vive di gol e rigori. Il primo lo schieri sempre, il
secondo ti fa vincere tre giornate e perdere le altre venti.

Qui provo a guardare le ragioni, su sei dimensioni che il calcolo di FM x PV non
puo' vedere:

1. **quanto pesa nel gioco della sua squadra** — la fetta di gol e assist del club
   che passa dai suoi piedi. Un giocatore che fa il 30% dei bonus della squadra e'
   il riferimento; uno al 5% e' un passeggero che ha avuto una buona annata;
2. **quanto del suo rendimento dipende dai rigori** — perche' i rigori cambiano
   piede da un anno all'altro, e chi ne ha vissuto rischia di dimezzarsi;
3. **quanto e' voto e quanto e' bonus** — la parte di voto e' ripetibile, la parte
   di bonus e' volatile. Nelle leghe col modificatore la prima vale doppio;
4. **dove gioca davvero** — il ruolo Mantra dice se un difensore e' un centrale o
   un esterno, se un centrocampista e' un mediano o un trequartista. Sono mondi
   diversi per potenziale di bonus, e il ruolo Classic li appiattisce;
5. **in che squadra li ha fatti, quei numeri, e in che squadra gioca adesso** —
   quindici gol in una squadra che ne segna sessanta non valgono quindici gol in
   una che ne segna trentacinque;
6. **cosa ne dicono le redazioni** — non per fidarmi, ma perche' i nomi molto
   citati all'asta si pagano di piu', e saperlo prima serve.

Di queste, due correggono davvero il valore atteso — il cambio di contesto e il
rischio rigori dopo un trasferimento — perche' sono le uniche informazioni che lo
storico non contiene gia'. Le altre restano giudizio, e come tale te le racconto.
"""
import re

RUOLI = ['P', 'D', 'C', 'A']

# quanto e' avanzato un giocatore secondo il ruolo Mantra, da 0 (portiere) a 1
# (punta): serve a distinguere il centrale dal terzino e il mediano dal trequartista
AVANZAMENTO = {'POR': 0.0, 'DC': 0.15, 'DD': 0.30, 'DS': 0.30, 'E': 0.45,
               'M': 0.40, 'C': 0.55, 'W': 0.75, 'T': 0.80, 'A': 0.90, 'PC': 1.0}
NOME_MANTRA = {'POR': 'portiere', 'DC': 'difensore centrale', 'DD': 'terzino destro',
               'DS': 'terzino sinistro', 'E': 'esterno', 'M': 'mediano',
               'C': 'centrocampista centrale', 'W': 'ala', 'T': 'trequartista',
               'A': 'attaccante', 'PC': 'punta centrale'}


def produzione_squadre(stats25):
    """Gol e assist prodotti da ogni squadra la scorsa stagione, piu' i gol subiti:
    e' il denominatore con cui misurare quanto pesa un singolo giocatore."""
    fatti, subiti, presenze_por = {}, {}, {}
    for r in stats25.values():
        sq = r.get('squadra')
        if not sq:
            continue
        fatti[sq] = fatti.get(sq, 0) + (r.get('gol') or 0) + (r.get('ass') or 0)
        if r['R'] == 'P':
            subiti[sq] = subiti.get(sq, 0) + (r.get('gs') or 0)
            presenze_por[sq] = presenze_por.get(sq, 0) + (r.get('pv') or 0)
    for sq in list(subiti):
        subiti[sq] = subiti[sq] / max(1.0, presenze_por.get(sq, 1))
    return fatti, subiti


def analizza(d, base_fm, base_mv, redazioni=None):
    stats25 = d['stats']['2025-26']
    fatti, subiti = produzione_squadre(stats25)
    media_fatti = (sum(fatti.values()) / len(fatti)) if fatti else 60.0
    media_subiti = (sum(subiti.values()) / len(subiti)) if subiti else 1.3
    citazioni = (redazioni or {}).get('giocatori', {})

    for p in d['listone']:
        r25 = p['storico'].get('2025-26') or {}
        p['valore_base'] = p['valore']
        motivi, cautele = [], []

        # ---- 1. quanto pesa nel gioco della squadra
        suoi = (r25.get('gol') or 0) + (r25.get('ass') or 0)
        totale = fatti.get(r25.get('squadra'), 0)
        p['peso_squadra'] = (suoi / totale) if totale >= 8 else None
        if p['peso_squadra'] is not None and p['R'] != 'P':
            q = p['peso_squadra']
            if q >= 0.22:
                motivi.append('il %d%% dei bonus del suo club passava da lui: '
                              'e\' il riferimento offensivo, non un comprimario'
                              % round(q * 100))
            elif q <= 0.05 and suoi >= 1:
                cautele.append('pesava solo il %d%% dei bonus della squadra: '
                               'la buona fantamedia veniva piu\' dal voto che dal gioco'
                               % round(q * 100))

        # ---- 2. i rigori: conta chi li tira adesso, non chi li tirava
        gol = r25.get('gol') or 0
        rig = r25.get('rig_seg') or 0
        p['quota_rigori'] = (rig / gol) if gol >= 3 else None
        ordine = (p.get('rigorista') or {}).get('ordine')
        if ordine == 1:
            motivi.append("è il rigorista designato della sua squadra, ed è il bonus "
                          "più prevedibile che esista al fanta")
        elif ordine == 2:
            motivi.append("secondo rigorista: oggi non tira, ma se il primo si ferma "
                          "eredita il bonus più facile del campionato")
        elif ordine == 3:
            motivi.append('terzo nella gerarchia dei rigori della sua squadra')
        if (p.get('piazzati') or {}).get('ordine') == 1:
            motivi.append('batte lui le punizioni e i corner')
        if not ordine and rig >= 2:
            cautele.append("l'anno scorso ha segnato %d rigori ma oggi non è nella "
                           "gerarchia della sua squadra: quei gol non tornano"
                           % int(rig))
        elif p['quota_rigori'] is not None and p['quota_rigori'] >= 0.34 and ordine != 1:
            cautele.append("%d dei suoi %d gol erano rigori e non è più il primo "
                           "rigorista" % (int(rig), int(gol)))

        # ---- 3. quanto e' voto e quanto e' bonus
        # attenzione al segno: per un portiere la fantamedia sta SOTTO il voto,
        # perche' i gol subiti sono un malus. Qui il differenziale puo' essere
        # negativo e va trattato come tale, non azzerato
        differenza = p['fm_att'] - p['mv_att']
        bonus = max(0.0, differenza)
        p['bonus_partita'] = differenza
        p['solidita'] = p['mv_att'] - base_mv[p['R']]
        if p['R'] in ('P', 'D'):
            if p['solidita'] >= 0.18:
                motivi.append('media voto %.2f, sopra la media del ruolo: con il '
                              'modificatore di difesa e\' oro' % p['mv_att'])
        else:
            if bonus >= 0.9 and p['solidita'] <= -0.05:
                cautele.append('vive di bonus (%.2f a partita) su un voto sotto la '
                               'media: nelle giornate storte ti lascia a piedi' % bonus)
            elif bonus >= 0.6 and p['solidita'] > 0:
                motivi.append('unisce voto alto e %.2f di bonus a partita: '
                              'e\' la combinazione che regge tutta la stagione' % bonus)

        # ---- 4. dove gioca davvero
        av = [AVANZAMENTO.get(x) for x in (p.get('RM') or []) if x in AVANZAMENTO]
        p['avanzamento'] = max(av) if av else None
        p['posizione'] = ', '.join(NOME_MANTRA.get(x, x) for x in (p.get('RM') or []))
        if p['R'] == 'D' and p['avanzamento'] and p['avanzamento'] >= 0.30:
            motivi.append('gioca da %s, non da centrale: nel ruolo di difensore e\' '
                          'la posizione che porta i bonus' % p['posizione'])
        if p['R'] == 'C' and p['avanzamento'] and p['avanzamento'] >= 0.75:
            motivi.append('e\' un %s schierato fra i centrocampisti: prende bonus '
                          'da attaccante al prezzo di un centrocampista' % p['posizione'])
        if p['R'] == 'C' and p['avanzamento'] and p['avanzamento'] <= 0.40:
            cautele.append('e\' un %s: prende voti ma raramente bonus'
                           % p['posizione'])

        # ---- 5. il contesto e' cambiato?
        vecchia = r25.get('squadra')
        cambio = bool(vecchia and vecchia != p['squadra'])
        p['cambio_squadra'] = cambio
        fattore = 1.0
        if cambio and p['R'] in ('C', 'A'):
            va, na = fatti.get(vecchia), fatti.get(p['squadra'])
            if va and na:
                fattore = min(1.30, max(0.75, na / float(va)))
                if fattore <= 0.88:
                    cautele.append('quei numeri li ha fatti in una squadra che '
                                   'produceva %d bonus, adesso ne e\' in una da %d: '
                                   'meno treni passano' % (va, na))
                elif fattore >= 1.15:
                    motivi.append('passa da una squadra da %d bonus a una da %d: '
                                  'stesso giocatore, piu\' occasioni' % (va, na))
        elif cambio and p['R'] in ('P', 'D'):
            vs, ns = subiti.get(vecchia), subiti.get(p['squadra'])
            if vs and ns:
                fattore = min(1.25, max(0.80, vs / float(ns)))
                if fattore <= 0.90:
                    cautele.append('la sua nuova difesa subisce piu\' gol della '
                                   'precedente (%.1f contro %.1f a partita)' % (ns, vs))

        # il rischio rigori non lo stimo piu' a naso: la gerarchia vera e'
        # gia' entrata nella fantamedia attesa, qui non serve altro
        rischio_rig = 0.0

        # ---- il valore, corretto solo per cio' che lo storico non sapeva.
        # Se il giocatore non ha cambiato squadra il fattore vale 1 e non si muove
        # nulla: il giudizio interviene solo dove ha qualcosa da dire.
        if differenza >= 0:
            corretta = differenza * fattore
        elif p['R'] in ('P', 'D') and fattore:
            # malus da gol subiti: una difesa peggiore lo fa crescere, non calare
            corretta = differenza / fattore
        else:
            corretta = differenza
        fm_corretta = p['mv_att'] + corretta - rischio_rig
        p['fm_giudizio'] = fm_corretta
        p['valore'] = ((fm_corretta - base_fm[p['R']]) * p['pv_proiettate']
                       + p.get('valore_modificatore', 0.0))
        p['scarto_giudizio'] = p['valore'] - p['valore_base']

        # ---- 6. cosa ne dicono le redazioni
        c = citazioni.get(p['id'])
        p['redazioni'] = c
        if c:
            if c['pro'] >= 2:
                motivi.append('indicato come occasione da %d articoli di consigli'
                              % c['pro'])
            if c['contro'] >= 2:
                cautele.append('%d articoli lo mettono fra i nomi su cui stare '
                               'attenti' % c['contro'])
            if c['citazioni'] >= 5 and c['pro'] < 2:
                cautele.append('nome molto chiacchierato (%d citazioni): all\'asta '
                               'i nomi caldi si pagano sopra il loro valore'
                               % c['citazioni'])

        v = p.get('xg') or {}
        if v.get('partite') and v['minuti'] >= 150:
            if v['scarto_azione'] <= -1.0:
                motivi.append("sta costruendo più di quanto segna (%.1f gol "
                              "attesi contro %d fatti): il rendimento dovrebbe "
                              "salire da solo"
                              % (v['npxg'], v['gol_su_azione']))
            elif v['scarto_azione'] >= 1.2:
                cautele.append("ha segnato %.1f gol più di quanti ne costruisce: "
                               "sta rendendo sopra le sue possibilità"
                               % v['scarto_azione'])
            if (v.get('xgchain90') or 0) >= 0.75 and p['R'] in ('C', 'D'):
                motivi.append('partecipa a molte azioni da gol della sua squadra '
                              '(%.2f di xGChain ogni novanta minuti)'
                              % v['xgchain90'])
        if p.get('coppe'):
            motivi.append("la sua squadra gioca le coppe: piu' turnover in "
                          "campionato per i titolari, piu' spazio per le riserve")
        if p.get('diffidato'):
            cautele.append('diffidato: al prossimo giallo salta una giornata')
        p['motivi_pro'] = motivi
        p['motivi_contro'] = cautele
        p['verdetto'] = verdetto(p)


def verdetto(p):
    """Una riga sola, quella che diresti a un amico che ti chiede "lo prendo?"."""
    if p.get('stato_attuale') and (p.get('giornate_stop_ora') or 0) >= 5:
        return 'Aspetta'
    pro, contro = len(p['motivi_pro']), len(p['motivi_contro'])
    forte = p['valore'] > 0 and p['pv_proiettate'] >= 24
    if p['stima']:
        return 'Incognita'
    if forte and pro >= 2 and contro == 0:
        return 'Da prendere'
    if p['scarto_giudizio'] <= -8 or contro >= pro + 2:
        return 'Occhio'
    if p['valore'] <= 0:
        return 'Solo a un credito'
    if pro > contro:
        return 'Buon affare'
    return 'Al prezzo giusto'


def racconta(p):
    """Il giudizio in prosa, come lo direi a voce."""
    pezzi = []
    if p['motivi_pro']:
        pezzi.append('A favore: ' + '; '.join(p['motivi_pro']) + '.')
    if p['motivi_contro']:
        pezzi.append('Contro: ' + '; '.join(p['motivi_contro']) + '.')
    if abs(p.get('scarto_giudizio') or 0) >= 4:
        verso = 'alza' if p['scarto_giudizio'] > 0 else 'abbassa'
        pezzi.append('Messo tutto insieme, il mio giudizio %s la sua valutazione di '
                     '%d fantapunti rispetto al puro storico.'
                     % (verso, abs(round(p['scarto_giudizio']))))
    return ' '.join(pezzi)
