/* FantAiuto Web — SPA statica per GitHub Pages.
 * I dati sono una fotografia locale prodotta dal motore Python originale.
 * La gestione dell'asta vive nel browser e viene salvata in IndexedDB.
 */

const ROLE_LABELS = { P: 'Portieri', D: 'Difensori', C: 'Centrocampisti', A: 'Attaccanti' };
const ROLE_ORDER = ['P', 'D', 'C', 'A'];
const PAGE_LABELS = {
  home: 'Plancia', auction: 'Asta', advice: 'Consigli', teams: 'Squadre',
  squad: 'Rosa', lineup: 'Formazione', injuries: 'Infermeria', stats: 'Statistiche',
  ask: 'Chiedimi', settings: 'Opzioni'
};
const DB_NAME = 'fantaiuto-web';
const DB_VERSION = 1;
const DB_STORE = 'app';
const STATE_KEY = 'state';

let DATA = null;
let state = null;
let dbPromise = null;
let marketCache = null;
let ui = {
  page: 'home',
  detailId: null,
  askText: '',
  askAnswer: '',
  showCount: 60,
  toast: '',
  filters: { role: '', team: '', risk: '', query: '', sort: 'max' }
};

const $ = (selector, root = document) => root.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));
const clone = (value) => JSON.parse(JSON.stringify(value));
const money = (value) => `${Math.round(Number(value) || 0)} cr`;
const number = (value, digits = 0) => Number(value || 0).toLocaleString('it-IT', {
  minimumFractionDigits: digits, maximumFractionDigits: digits
});
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

function player(id) {
  return DATA.giocatori.find((item) => String(item.id) === String(id));
}

function adviceFor(id) {
  return (DATA.consigli && DATA.consigli[String(id)]) || {};
}

function defaultState(config) {
  const squads = [];
  for (let i = 0; i < config.squadre; i += 1) {
    squads.push(i === 0 ? 'La mia squadra' : `Squadra ${i + 1}`);
  }
  return {
    version: 1,
    theme: 'dark',
    config: clone(config),
    asta: { squadre: squads, mia: 0, acquisti: {} },
    updatedAt: new Date().toISOString()
  };
}

function normalizeState(raw, config) {
  const base = defaultState(config);
  const saved = raw && typeof raw === 'object' ? raw : {};
  const savedConfig = saved.config || {};
  const mergedConfig = {
    ...base.config,
    ...savedConfig,
    slot: { ...base.config.slot, ...(savedConfig.slot || {}) },
    quote: { ...base.config.quote, ...(savedConfig.quote || {}) }
  };
  const savedAsta = saved.asta || {};
  let squads = Array.isArray(savedAsta.squadre) ? savedAsta.squadre.map(String) : base.asta.squadre;
  const required = Math.max(Number(mergedConfig.squadre) || 10, squads.length || 0);
  while (squads.length < required) squads.push(squads.length ? `Squadra ${squads.length + 1}` : 'La mia squadra');
  const purchases = {};
  const rawPurchases = savedAsta.acquisti || {};
  Object.entries(rawPurchases).forEach(([id, value]) => {
    if (!value || !Number.isFinite(Number(value.prezzo))) return;
    purchases[String(id)] = {
      squadra: Math.max(0, Number(value.squadra) || 0),
      prezzo: Math.max(1, Math.round(Number(value.prezzo)))
    };
  });
  const mia = clamp(Number(savedAsta.mia) || 0, 0, Math.max(0, squads.length - 1));
  return {
    version: 1,
    theme: saved.theme === 'light' ? 'light' : 'dark',
    config: mergedConfig,
    asta: { squadre: squads, mia, acquisti: purchases },
    updatedAt: saved.updatedAt || new Date().toISOString()
  };
}

function requestToPromise(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function openDatabase() {
  if (!window.indexedDB) return Promise.reject(new Error('IndexedDB non disponibile'));
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(DB_STORE)) request.result.createObjectStore(DB_STORE);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  return dbPromise;
}

async function loadSavedState() {
  try {
    const db = await openDatabase();
    const transaction = db.transaction(DB_STORE, 'readonly');
    return await requestToPromise(transaction.objectStore(DB_STORE).get(STATE_KEY));
  } catch (error) {
    try { return JSON.parse(localStorage.getItem('fantaiuto-state') || 'null'); } catch (_) { return null; }
  }
}

async function saveState() {
  state.updatedAt = new Date().toISOString();
  try {
    const db = await openDatabase();
    const transaction = db.transaction(DB_STORE, 'readwrite');
    await requestToPromise(transaction.objectStore(DB_STORE).put(state, STATE_KEY));
  } catch (error) {
    try { localStorage.setItem('fantaiuto-state', JSON.stringify(state)); } catch (_) { /* storage pieno */ }
  }
}

function notify(message) {
  ui.toast = message;
  render();
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => { ui.toast = ''; render(); }, 3000);
}

async function commit(mutator) {
  mutator(state);
  marketCache = null;
  await saveState();
  render();
}

function roleBadge(p) {
  return `<span class="role-badge role-${esc(p.R)}">${esc(p.R)}</span>`;
}

function tag(text, style = '') {
  return `<span class="tag ${style}">${esc(text)}</span>`;
}

function purchasedEntry(id) {
  return state.asta.acquisti[String(id)] || null;
}

function purchasedIds() {
  return new Set(Object.keys(state.asta.acquisti));
}

function teamSpent(team) {
  return Object.values(state.asta.acquisti)
    .filter((value) => Number(value.squadra) === Number(team))
    .reduce((sum, value) => sum + Number(value.prezzo || 0), 0);
}

function teamPlayers(team) {
  return Object.entries(state.asta.acquisti)
    .filter(([, value]) => Number(value.squadra) === Number(team))
    .map(([id, value]) => ({ p: player(id), price: Number(value.prezzo) }))
    .filter((entry) => entry.p);
}

function teamMissing(team) {
  return Object.values(state.config.slot).reduce((sum, slots) => sum + Number(slots), 0) - teamPlayers(team).length;
}

function teamOfferCap(team) {
  const remaining = Number(state.config.crediti) - teamSpent(team);
  return Math.max(0, remaining - Math.max(0, teamMissing(team) - 1));
}

function leagueSummary() {
  const mine = teamPlayers(state.asta.mia);
  const spent = mine.reduce((sum, entry) => sum + entry.price, 0);
  const totalSlots = Object.values(state.config.slot).reduce((sum, value) => sum + Number(value), 0);
  return {
    mine,
    spent,
    remaining: Number(state.config.crediti) - spent,
    missing: totalSlots - mine.length,
    cap: teamOfferCap(state.asta.mia),
    sold: Object.keys(state.asta.acquisti).length,
    slots: totalSlots
  };
}

function calibration() {
  let allPaid = 0;
  let allExpected = 0;
  const role = {};
  Object.entries(state.asta.acquisti).forEach(([id, entry]) => {
    const p = player(id);
    if (!p) return;
    const expected = Math.max(1, Number(p.prezzo_prudente || p.prezzo || p.prezzo_mercato || 1));
    const item = role[p.R] || (role[p.R] = { paid: 0, expected: 0, count: 0 });
    item.paid += Number(entry.prezzo || 0);
    item.expected += expected;
    item.count += 1;
    allPaid += Number(entry.prezzo || 0);
    allExpected += expected;
  });
  const league = allExpected ? (allPaid / allExpected * 0.75 + 1 * 0.25) : 1;
  const roles = {};
  ROLE_ORDER.forEach((r) => {
    const item = role[r];
    const direct = item && item.expected ? item.paid / item.expected : league;
    roles[r] = direct * ((item ? item.count : 0) / ((item ? item.count : 0) + 4)) + league * (4 / ((item ? item.count : 0) + 4));
  });
  return { league, roles };
}

function liveMarket() {
  if (marketCache) return marketCache;
  const sold = purchasedIds();
  const cfg = state.config;
  const totalCredits = Number(cfg.squadre) * Number(cfg.crediti);
  const spent = Object.values(state.asta.acquisti).reduce((sum, value) => sum + Number(value.prezzo || 0), 0);
  const totalSlots = Number(cfg.squadre) * Object.values(cfg.slot).reduce((sum, value) => sum + Number(value), 0);
  const slotsRemaining = Math.max(1, totalSlots - sold.size);
  const availableCredits = Math.max(1, totalCredits - spent);
  const startPerSlot = Number(cfg.crediti) / Object.values(cfg.slot).reduce((sum, value) => sum + Number(value), 0);
  const temperature = (availableCredits / slotsRemaining) / Math.max(.1, startPerSlot);
  const cal = calibration();
  const reports = {};
  const factors = {};

  ROLE_ORDER.forEach((role) => {
    const free = DATA.giocatori.filter((p) => p.R === role && !sold.has(String(p.id)))
      .sort((a, b) => (Number(b.valore) || 0) - (Number(a.valore) || 0));
    const purchasedRole = DATA.giocatori.filter((p) => p.R === role && sold.has(String(p.id))).length;
    const roleSlots = Math.max(0, Number(cfg.squadre) * Number(cfg.slot[role]) - purchasedRole);
    const substitute = free.length ? Number(free[Math.min(roleSlots, free.length - 1)].valore || 0) : 0;
    const values = free.map((p) => Math.max(0, Number(p.valore || 0) - substitute));
    const totalValue = values.reduce((sum, value) => sum + value, 0);
    const weight = Number(cfg.quote[role] || 0) * totalValue * (cal.roles[role] || 1);
    reports[role] = { free, roleSlots, values, totalValue, weight };
    free.forEach((p, index) => { factors[String(p.id)] = { role, value: values[index] }; });
  });

  const totalWeight = Object.values(reports).reduce((sum, report) => sum + report.weight, 0) || 1;
  const equi = {};
  const max = {};
  const scarcity = {};
  ROLE_ORDER.forEach((role) => {
    const report = reports[role];
    const budget = availableCredits * report.weight / totalWeight;
    const allocable = Math.max(0, budget - report.roleSlots);
    const weightedValue = report.values.reduce((sum, value, index) => {
      const p = report.free[index];
      const slotFactor = (p.slot ? 1 + Math.max(-.15, Math.min(.25, (cal.roles[role] || 1) - 1)) : 1);
      return sum + value * slotFactor;
    }, 0) || 1;
    const supplyBySlot = {};
    report.free.forEach((p) => { const key = p.slot || 'none'; supplyBySlot[key] = (supplyBySlot[key] || 0) + 1; });
    const demandBySlot = {};
    for (let team = 0; team < state.asta.squadre.length; team += 1) {
      const players = teamPlayers(team);
      const counts = players.filter((entry) => entry.p.R === role).reduce((out, entry) => {
        const key = entry.p.slot || 'none'; out[key] = (out[key] || 0) + 1; return out;
      }, {});
      for (let slot = 1; slot <= Number(cfg.slot[role]); slot += 1) {
        const key = String(slot);
        if (!(counts[key] || 0)) demandBySlot[key] = (demandBySlot[key] || 0) + 1;
      }
      if (players.filter((entry) => entry.p.R === role).length < Number(cfg.slot[role])) {
        demandBySlot.none = (demandBySlot.none || 0) + 1;
      }
    }
    report.free.forEach((p, index) => {
      const key = String(p.slot || 'none');
      const ratio = Math.min(2.5, Math.max(.4, (demandBySlot[key] || 0) / Math.max(1, supplyBySlot[key] || 0)));
      scarcity[String(p.id)] = ratio;
      const value = report.values[index];
      const model = value <= 0 ? 1 : 1 + allocable * value / weightedValue;
      equi[String(p.id)] = Math.max(1, Math.round(.6 * model + .4 * Number(p.prezzo_mercato || p.prezzo || 1)));
      const shortagePremium = Math.min(.6, Math.max(-.15, .5 * (ratio - 1)));
      max[String(p.id)] = Math.max(1, Math.min(teamOfferCap(state.asta.mia), Math.round(equi[String(p.id)] * (1 + shortagePremium))));
    });
  });

  marketCache = { equi, max, scarcity, temperature, cal };
  return marketCache;
}

function expected(p) {
  const value = adviceFor(p.id).atteso;
  return Number.isFinite(Number(value)) ? Number(value) : Number(p.fm_att || 0);
}

function pageHeading(eyebrow, title, text = '', action = '') {
  return `<div class="page-heading"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1>${text ? `<p class="lede">${esc(text)}</p>` : ''}</div>${action}</div>`;
}

function renderHeader() {
  const summary = leagueSummary();
  const navPages = ['home', 'auction', 'advice', 'teams', 'squad', 'lineup', 'injuries', 'stats', 'ask', 'settings'];
  return `<header class="topbar"><div class="topbar-inner">
    <a class="brand" href="#" data-page="home"><span class="brand-mark">F</span><span class="brand-copy">FantAiuto<small>${number(DATA.prossima_giornata)}ª giornata</small></span></a>
    <nav class="main-nav" aria-label="Navigazione principale">${navPages.map((page) => `<button class="nav-button ${ui.page === page ? 'active' : ''}" data-page="${page}">${esc(PAGE_LABELS[page])}</button>`).join('')}</nav>
    <div class="header-actions"><button class="icon-button" title="Cambia tema" aria-label="Cambia tema" data-action="theme">${state.theme === 'dark' ? '☼' : '☾'}</button><button class="icon-button" title="Esporta dati" aria-label="Esporta dati" data-action="export">⇩</button></div>
  </div></header>
  <div class="dashboard-strip">
    <div class="metric"><small>Crediti</small><strong>${number(summary.remaining)}</strong><em>rimasti a te</em></div>
    <div class="metric"><small>Puoi offrire</small><strong>${number(summary.cap)}</strong><em>tetto reale</em></div>
    <div class="metric"><small>Rosa</small><strong>${summary.mine.length}/${summary.slots}</strong><em>slot riempiti</em></div>
    <div class="metric"><small>Venduti</small><strong>${summary.sold}</strong><em>in tutta la lega</em></div>
  </div>`;
}

function renderBottomNav() {
  const pages = [['home', '⌂'], ['auction', '⚡'], ['squad', '♙'], ['lineup', '♢'], ['settings', '⋯']];
  return `<nav class="bottom-nav" aria-label="Navigazione rapida">${pages.map(([page, icon]) => `<button class="${ui.page === page ? 'active' : ''}" data-page="${page}"><span>${icon}</span>${esc(PAGE_LABELS[page])}</button>`).join('')}</nav>`;
}

function renderHome() {
  const summary = leagueSummary();
  const market = liveMarket();
  const top = [...DATA.giocatori].filter((p) => !purchasedEntry(p.id)).sort((a, b) => (market.max[b.id] || 0) - (market.max[a.id] || 0)).slice(0, 6);
  const date = DATA.aggiornato || 'non disponibile';
  return `${pageHeading('Plancia', 'Decidi in fretta.', `Il mercato si muove mentre l'asta va avanti. I dati sono aggiornati al ${date}.`, '<button class="button" data-page="auction">Apri l’asta</button>')}
    <div class="grid grid-2">
      <section class="card hero-card"><div class="eyebrow">Il banco</div><h2>Quanto puoi spingerti oggi?</h2><p class="lede">Hai ancora <strong class="accent">${money(summary.cap)}</strong> su un singolo giocatore, tenendo un credito per ogni slot che ti manca.</p><button class="button" data-page="auction">Vai al listone →</button></section>
      <section class="card pad"><div class="card-header"><div><div class="eyebrow">Mercato</div><h2>Segnali di oggi</h2></div>${tag(market.temperature > 1.12 ? 'mercato caldo' : market.temperature < .88 ? 'mercato freddo' : 'in equilibrio', market.temperature > 1.12 ? 'red-tag' : market.temperature < .88 ? 'green-tag' : 'amber-tag')}</div><p class="lede">${market.temperature > 1.12 ? 'La lega sta spendendo più del previsto: conserva margine.' : market.temperature < .88 ? 'Il mercato è sotto la partenza: cerca valore.' : 'Prezzi vicini alla distribuzione iniziale.'}</p><div class="detail-stats"><div class="detail-stat"><small>Per casella</small><strong>${money(market.temperature * Number(state.config.crediti) / Object.values(state.config.slot).reduce((a, b) => a + Number(b), 0))}</strong></div><div class="detail-stat"><small>Giocatori</small><strong>${DATA.giocatori.length}</strong></div><div class="detail-stat"><small>Prossima</small><strong>${DATA.prossima_giornata}ª</strong></div></div></section>
    </div>
    <section class="card pad" style="margin-top:14px"><div class="card-header"><div><div class="eyebrow">Pronti al banco</div><h2>I sei nomi più costosi</h2></div><button class="button-secondary small" data-page="auction">Vedi tutti</button></div><div class="grid grid-3">${top.map((p) => renderMiniPlayer(p, market)).join('')}</div></section>
    <div class="grid grid-3" style="margin-top:14px"><section class="card stat-card"><small>Valore atteso</small><strong>${number(Math.round(Math.max(...DATA.giocatori.map((p) => Number(p.valore) || 0))))}</strong><p>Il motore confronta ogni giocatore con il sostituto del suo ruolo.</p></section><section class="card stat-card"><small>Modificatore</small><strong>${state.config.modificatore_difesa ? 'Attivo' : 'Spento'}</strong><p>Il valore dei difensori si adatta alla tua rosa.</p></section><section class="card stat-card"><small>Persistenza</small><strong>Locale</strong><p>Acquisti e impostazioni restano sul tuo iPhone tramite IndexedDB.</p></section></div>`;
}

function renderMiniPlayer(p, market) {
  const max = market.max[p.id] || p.prezzo || 1;
  return `<button class="player-card" data-action="detail" data-id="${esc(p.id)}" style="text-align:left"><span>${roleBadge(p)}</span><span class="player-main"><span class="player-name">${esc(p.nome)}</span><span class="player-meta"><span>${esc(p.squadra)}</span><span>${esc(p.verdetto || 'Analisi')}</span></span></span><span class="player-numbers"><strong>${money(max)}</strong><small>tetto</small></span><span class="button-secondary small">Apri</span></button>`;
}

function renderAuction() {
  const market = liveMarket();
  const filters = ui.filters;
  let list = DATA.giocatori.filter((p) => {
    if (filters.role && p.R !== filters.role) return false;
    if (filters.team && p.squadra !== filters.team) return false;
    if (filters.risk && p.rischio !== filters.risk) return false;
    if (filters.query && !`${p.nome} ${p.nome_completo || ''} ${p.squadra}`.toLowerCase().includes(filters.query.toLowerCase())) return false;
    return true;
  });
  const sorts = {
    max: (p) => -(market.max[p.id] || 0),
    value: (p) => -(Number(p.valore) || 0),
    price: (p) => -(Number(p.prezzo_mercato) || 0),
    expected: (p) => -expected(p),
    risk: (p) => ({ Basso: 0, Medio: 1, Alto: 2, Ignoto: 3 }[p.rischio] ?? 4)
  };
  list.sort((a, b) => sorts[filters.sort](a) - sorts[filters.sort](b));
  const visible = list.slice(0, ui.showCount);
  const selected = player(ui.detailId) || (visible.length ? visible[0] : null);
  const teams = [...new Set(DATA.giocatori.map((p) => p.squadra))].sort();
  const detail = selected ? renderPlayerDetail(selected, market) : '<div class="empty">Nessun giocatore corrisponde ai filtri.</div>';
  return `${pageHeading('Asta', 'Il listone, adesso.', 'Cerca un nome, apri la scheda e registra ogni acquisto: il tetto degli altri cambia subito.', '')}
    <form class="toolbar" data-action="filter-form">
      <div class="field"><label for="player-search">Cerca</label><input id="player-search" name="query" value="${esc(filters.query)}" placeholder="Nome o squadra…" autocomplete="off"></div>
      <div class="field compact"><label for="role-filter">Ruolo</label><select id="role-filter" name="role" data-filter="role"><option value="">Tutti</option>${ROLE_ORDER.map((r) => `<option value="${r}" ${filters.role === r ? 'selected' : ''}>${ROLE_LABELS[r]}</option>`).join('')}</select></div>
      <div class="field compact"><label for="team-filter">Squadra</label><select id="team-filter" name="team" data-filter="team"><option value="">Tutte</option>${teams.map((team) => `<option value="${esc(team)}" ${filters.team === team ? 'selected' : ''}>${esc(team)}</option>`).join('')}</select></div>
      <div class="field compact"><label for="risk-filter">Rischio</label><select id="risk-filter" name="risk" data-filter="risk"><option value="">Tutti</option>${['Basso', 'Medio', 'Alto', 'Ignoto'].map((risk) => `<option value="${risk}" ${filters.risk === risk ? 'selected' : ''}>${risk}</option>`).join('')}</select></div>
      <div class="field compact"><label for="sort-filter">Ordina</label><select id="sort-filter" name="sort" data-filter="sort"><option value="max" ${filters.sort === 'max' ? 'selected' : ''}>Tetto da pagare</option><option value="value" ${filters.sort === 'value' ? 'selected' : ''}>Valore atteso</option><option value="price" ${filters.sort === 'price' ? 'selected' : ''}>Mercato</option><option value="expected" ${filters.sort === 'expected' ? 'selected' : ''}>FM giornata</option><option value="risk" ${filters.sort === 'risk' ? 'selected' : ''}>Rischio</option></select></div>
      <button class="button" type="submit">Filtra</button>
    </form>
    <div class="auction-layout"><section><div class="card-header"><div class="muted">${list.length} giocatori · ${Object.keys(state.asta.acquisti).length} già venduti</div><div class="faint">Tocca una scheda per aprirla</div></div><div class="auction-list">${visible.length ? visible.map((p) => renderAuctionPlayer(p, market)).join('') : '<div class="empty">Nessun calciatore con questi filtri.</div>'}</div>${list.length > visible.length ? `<button class="button-secondary full" style="margin-top:12px" data-action="show-more">Mostra altri ${Math.min(60, list.length - visible.length)}</button>` : ''}<p class="source-note">Prezzi elaborati dal dataset locale. L’aggiornamento automatico richiede una nuova pubblicazione su GitHub Pages.</p></section><aside class="sticky-card">${detail}</aside></div>`;
}

function renderAuctionPlayer(p, market) {
  const sold = purchasedEntry(p.id);
  const max = market.max[p.id] || p.prezzo || 1;
  const adv = adviceFor(p.id);
  const riskClass = p.rischio === 'Alto' ? 'red' : p.rischio === 'Medio' ? 'amber' : p.rischio === 'Basso' ? 'green' : 'faint';
  return `<article class="player-card ${sold ? 'sold' : ''}"><button aria-label="Apri ${esc(p.nome)}" data-action="detail" data-id="${esc(p.id)}">${roleBadge(p)}</button><button class="player-main" style="border:0;background:transparent;color:inherit;text-align:left;padding:0" data-action="detail" data-id="${esc(p.id)}"><span class="player-name">${esc(p.nome)}${sold ? ` <span class="faint">· venduto a ${esc(state.asta.squadre[sold.squadra] || 'squadra')}</span>` : ''}</span><span class="player-meta"><span>${esc(p.squadra)}</span><span>${esc(p.verdetto || 'Analisi')}</span>${adv.titolare_previsto ? '<span class="green">probabile titolare</span>' : ''}</span></button><span class="player-numbers"><strong>${sold ? money(sold.prezzo) : money(max)}</strong><small>${sold ? 'pagato' : 'tetto'}</small></span><button class="button-secondary small" data-action="detail" data-id="${esc(p.id)}">Apri</button><span class="risk ${riskClass}">${esc(p.rischio || 'Ignoto')}</span></article>`;
}

function renderPlayerDetail(p, market) {
  const sold = purchasedEntry(p.id);
  const max = market.max[p.id] || p.prezzo || 1;
  const price = sold ? sold.prezzo : max;
  const adv = adviceFor(p.id);
  const reasons = [...(p.motivi_pro || []), ...(p.motivi_contro || [])].slice(0, 4);
  const defaultTeam = sold ? Number(sold.squadra) : Number(state.asta.mia);
  return `<section class="card player-detail"><div class="detail-top"><div><div class="eyebrow">${esc(ROLE_LABELS[p.R])} · ${esc(p.squadra)}</div><h2 class="detail-name">${esc(p.nome)}</h2><div class="detail-team">${esc(p.nome_completo || p.nome)} · ${esc(p.verdetto || 'Analisi')}</div></div>${roleBadge(p)}</div><div class="price-hero"><div><small>${sold ? 'Prezzo pagato' : 'Quanto pagherei oggi'}</small><strong>${money(price)}</strong></div><div class="faint">mercato ${money(p.prezzo_mercato)}</div></div><div class="detail-stats"><div class="detail-stat"><small>FM attesa</small><strong>${number(p.fm_att, 2)}</strong></div><div class="detail-stat"><small>Presenze attese</small><strong>${number(p.pv_proiettate, 0)}</strong></div><div class="detail-stat"><small>Max personale</small><strong>${money(state.asta.acquisti[p.id] ? teamOfferCap(sold.squadra) : max)}</strong></div></div><div class="player-meta">${tag(p.rischio || 'Ignoto', p.rischio === 'Alto' ? 'red-tag' : p.rischio === 'Medio' ? 'amber-tag' : 'green-tag')}${p.rigorista ? tag('rigorista', 'amber-tag') : ''}${p.diffidato ? tag('diffidato', 'amber-tag') : ''}${p.slot ? tag(`slot ${p.slot}`, 'accent-tag') : ''}</div>${reasons.length ? `<ul class="reason-list">${reasons.map((reason) => `<li>${esc(reason)}</li>`).join('')}</ul>` : '<p class="section-note">Nessuna ragione aggiuntiva disponibile.</p>'}<div class="assign-box"><div class="eyebrow">Registro asta</div>${sold ? `<p class="section-note">Attualmente assegnato a <strong>${esc(state.asta.squadre[sold.squadra])}</strong> per ${money(sold.prezzo)}.</p>` : '<p class="section-note">Segna qui il prezzo reale battuto.</p>'}<form data-action="assign" data-id="${esc(p.id)}"><div class="assign-grid"><div class="field"><label>Squadra</label><select name="team">${state.asta.squadre.map((team, index) => `<option value="${index}" ${defaultTeam === index ? 'selected' : ''}>${index === state.asta.mia ? '★ ' : ''}${esc(team)}</option>`).join('')}</select></div><div class="field"><label>Prezzo</label><input name="price" type="number" min="1" max="${Number(state.config.crediti)}" value="${Math.max(1, Math.round(price))}"></div></div><div class="button-row"><button class="button" type="submit">${sold ? 'Aggiorna acquisto' : 'Assegna giocatore'}</button>${sold ? `<button class="button-danger" type="button" data-action="release" data-id="${esc(p.id)}">Libera</button>` : ''}</div></form></div><div class="button-row" style="margin-top:15px"><button class="button-secondary small" data-action="page" data-page="stats">Apri statistiche</button></div></section>`;
}

function renderAdvice() {
  const market = liveMarket();
  const free = DATA.giocatori.filter((p) => !purchasedEntry(p.id));
  const opportunities = [...free].sort((a, b) => ((Number(b.valore) || 0) / Math.max(1, market.max[b.id] || b.prezzo || 1)) - ((Number(a.valore) || 0) / Math.max(1, market.max[a.id] || a.prezzo || 1))).slice(0, 12);
  const reliable = [...free].filter((p) => p.rischio === 'Basso').sort((a, b) => (Number(b.valore) || 0) - (Number(a.valore) || 0)).slice(0, 12);
  const warnings = [...free].filter((p) => p.rischio === 'Alto').sort((a, b) => (Number(a.valore) || 0) - (Number(b.valore) || 0)).slice(0, 12);
  return `${pageHeading('Consigli', 'Dove mettere i crediti.', 'Tre liste pratiche: rendimento, solidità e rischi. Il prezzo è quello stimato per lo stato attuale dell’asta.', '')}<div class="grid grid-3"><section class="card pad"><div class="card-header"><div><div class="eyebrow">Opportunità</div><h2>Valore / tetto</h2></div>${tag('da guardare', 'green-tag')}</div>${renderRankList(opportunities, market, (p) => `${number((Number(p.valore) || 0) / Math.max(1, market.max[p.id] || 1), 2)}x`)}</section><section class="card pad"><div class="card-header"><div><div class="eyebrow">Solidi</div><h2>Rischio basso</h2></div>${tag('continuità', 'cyan-tag')}</div>${renderRankList(reliable, market, (p) => money(market.max[p.id] || p.prezzo))}</section><section class="card pad"><div class="card-header"><div><div class="eyebrow">Attenzione</div><h2>Rischio alto</h2></div>${tag('prudenza', 'red-tag')}</div>${renderRankList(warnings, market, (p) => money(market.max[p.id] || p.prezzo))}</section></div><section class="card pad" style="margin-top:14px"><div class="card-header"><div><div class="eyebrow">Ragioni</div><h2>Come leggere il consiglio</h2></div></div><p class="help-box">Il tetto combina rendimento atteso, sostituti ancora disponibili, temperatura del mercato e portafoglio della tua squadra. Aprendo ogni giocatore trovi le ragioni generate dal motore.</p></section>`;
}

function renderRankList(list, market, value) {
  if (!list.length) return '<div class="empty">Nessun dato disponibile.</div>';
  return `<div class="rank-list">${list.map((p, index) => `<button class="rank-row" style="border:0;background:transparent;color:inherit;width:100%;text-align:left" data-action="detail" data-id="${esc(p.id)}"><span class="rank-number">${index + 1}</span><span><strong>${esc(p.nome)}</strong><small>${esc(p.squadra)} · ${esc(p.verdetto || 'analisi')}</small></span><span class="rank-value">${esc(value(p))}</span></button>`).join('')}</div>`;
}

function renderTeams() {
  const teamCount = state.asta.squadre.length;
  const total = Number(state.config.crediti);
  const totalSlots = Object.values(state.config.slot).reduce((sum, value) => sum + Number(value), 0);
  return `${pageHeading('La lega', 'Tutti i portafogli.', 'Dai un nome alle squadre e registra anche gli acquisti degli avversari: il tetto che vedi è quello reale.', '')}<section class="card pad"><form data-action="save-teams"><div class="grid grid-2">${state.asta.squadre.map((team, index) => `<div class="field"><label for="team-${index}">Squadra ${index + 1}${index === state.asta.mia ? ' · tu' : ''}</label><input id="team-${index}" name="team-${index}" value="${esc(team)}" maxlength="30"></div>`).join('')}</div><div class="field" style="max-width:360px;margin-top:14px"><label for="my-team">La mia squadra</label><select id="my-team" name="my-team">${state.asta.squadre.map((team, index) => `<option value="${index}" ${index === state.asta.mia ? 'selected' : ''}>${esc(team)}</option>`).join('')}</select></div><button class="button" style="margin-top:14px" type="submit">Salva nomi</button></form></section><div class="team-grid" style="margin-top:14px">${state.asta.squadre.map((team, index) => renderTeamCard(team, index, total, totalSlots)).join('')}</div>`;
}

function renderTeamCard(team, index, total, totalSlots) {
  const entries = teamPlayers(index);
  const spent = teamSpent(index);
  const roleCounts = ROLE_ORDER.map((role) => entries.filter((entry) => entry.p.R === role).length);
  return `<section class="card team-card ${index === state.asta.mia ? 'mine' : ''}"><div class="team-head"><div><h3>${index === state.asta.mia ? '★ ' : ''}${esc(team)}</h3><div class="team-money">${money(spent)} spesi · ${money(total - spent)} residui</div></div><span class="tag ${index === state.asta.mia ? 'accent-tag' : ''}">${money(teamOfferCap(index))} max</span></div><div class="progress"><span style="width:${clamp(entries.length / Math.max(1, totalSlots) * 100, 0, 100)}%"></span></div><div class="role-counts">${roleCounts.map((count, roleIndex) => `<div class="role-count"><small>${ROLE_ORDER[roleIndex]}</small><strong>${count}/${state.config.slot[ROLE_ORDER[roleIndex]]}</strong></div>`).join('')}</div>${entries.length ? `<div class="team-players">${entries.sort((a, b) => b.price - a.price).slice(0, 8).map((entry) => `<button class="team-player" style="border:0;background:transparent;color:inherit;text-align:left;width:100%;padding:0" data-action="detail" data-id="${esc(entry.p.id)}"><span><strong>${esc(entry.p.nome)}</strong> · ${esc(entry.p.R)}</span><span>${money(entry.price)}</span></button>`).join('')}${entries.length > 8 ? `<span class="faint">+ ${entries.length - 8} altri</span>` : ''}</div>` : '<p class="section-note">Nessun acquisto.</p>'}</section>`;
}

function renderSquad() {
  const summary = leagueSummary();
  const byRole = ROLE_ORDER.map((role) => [role, summary.mine.filter((entry) => entry.p.R === role)]);
  const missing = ROLE_ORDER.map((role) => `${ROLE_LABELS[role]}: ${Math.max(0, Number(state.config.slot[role]) - (byRole.find(([key]) => key === role)[1].length))}`).join(' · ');
  return `${pageHeading('La mia rosa', state.asta.squadre[state.asta.mia], `${summary.mine.length} giocatori, ${money(summary.spent)} spesi. Ti mancano ${summary.missing} slot.`, '<button class="button-secondary" data-page="teams">Gestisci lega</button>')}<div class="grid grid-4">${[['Valore rosa', summary.mine.reduce((sum, entry) => sum + Number(entry.p.valore || 0), 0).toFixed(0), 'punti attesi'], ['Crediti', summary.remaining, 'ancora disponibili'], ['Offerta max', summary.cap, 'su un giocatore'], ['Scoperti', summary.missing, missing]].map(([label, value, sub]) => `<section class="card stat-card"><small>${esc(label)}</small><strong>${typeof value === 'number' ? number(value) : value}</strong><p>${esc(sub)}</p></section>`).join('')}</div><div class="grid grid-2" style="margin-top:14px">${byRole.map(([role, entries]) => `<section class="card pad"><div class="card-header"><div><div class="eyebrow">${esc(ROLE_LABELS[role])}</div><h2>${entries.length}/${state.config.slot[role]}</h2></div>${tag(entries.length >= state.config.slot[role] ? 'completo' : 'da riempire', entries.length >= state.config.slot[role] ? 'green-tag' : 'amber-tag')}</div>${entries.length ? `<div class="rank-list">${entries.sort((a, b) => Number(b.p.valore || 0) - Number(a.p.valore || 0)).map((entry) => `<button class="rank-row" style="border:0;background:transparent;color:inherit;width:100%;text-align:left" data-action="detail" data-id="${esc(entry.p.id)}"><span>${roleBadge(entry.p)}</span><span><strong>${esc(entry.p.nome)}</strong><small>${esc(entry.p.verdetto || '')} · FM ${number(entry.p.fm_att, 2)}</small></span><span class="rank-value">${money(entry.price)}</span></button>`).join('')}</div>` : '<div class="empty">Ancora nessuno in questo reparto.</div>'}</section>`).join('')}</div>`;
}

const FORMATIONS = [{ name: '3-4-3', D: 3, C: 4, A: 3 }, { name: '3-5-2', D: 3, C: 5, A: 2 }, { name: '4-3-3', D: 4, C: 3, A: 3 }, { name: '4-4-2', D: 4, C: 4, A: 2 }, { name: '4-5-1', D: 4, C: 5, A: 1 }, { name: '5-3-2', D: 5, C: 3, A: 2 }, { name: '5-4-1', D: 5, C: 4, A: 1 }];

function formationFor(entries, shape) {
  const selected = {};
  const keeper = entries.filter((entry) => entry.p.R === 'P').sort((a, b) => expected(b.p) - expected(a.p))[0];
  if (keeper) selected.P = [keeper];
  ROLE_ORDER.slice(1).forEach((role) => {
    selected[role] = entries.filter((entry) => entry.p.R === role).sort((a, b) => expected(b.p) - expected(a.p)).slice(0, shape[role]);
  });
  const flat = ROLE_ORDER.flatMap((role) => selected[role] || []);
  const defenders = selected.D || [];
  const allMvs = selected.P && selected.P[0] ? [Number(selected.P[0].p.mv_att || 0), ...defenders.map((entry) => Number(entry.p.mv_att || 0))] : [];
  const modifier = state.config.modificatore_difesa && defenders.length >= 4 ? Math.max(0, Math.min(5, ((allMvs[0] + defenders.sort((a, b) => Number(b.p.mv_att || 0) - Number(a.p.mv_att || 0)).slice(0, 3).reduce((sum, entry) => sum + Number(entry.p.mv_att || 0), 0)) / 4 - 5.875) / .25)) : 0;
  return { selected, flat, points: flat.reduce((sum, entry) => sum + expected(entry.p), 0) + modifier, modifier };
}

function renderFormationPitch(formation) {
  return `<div class="pitch">${['A', 'C', 'D', 'P'].map((role) => `<div class="pitch-row">${(formation.selected[role] || []).map((entry) => `<div class="pitch-player"><i>${esc(role)}</i>${esc(entry.p.nome)}</div>`).join('')}</div>`).join('')}</div>`;
}

function renderLineup() {
  const entries = teamPlayers(state.asta.mia);
  const formations = FORMATIONS.map((shape) => ({ shape, result: formationFor(entries, shape) })).sort((a, b) => b.result.points - a.result.points);
  const best = formations[0];
  return `${pageHeading('Formazione', `La prossima: ${DATA.prossima_giornata}ª.`, 'Il modulo migliore viene scelto sui giocatori della tua rosa, con il modificatore incluso quando possibile.', '')}${!entries.length ? '<div class="empty">Prima registra qualche acquisto nella pagina Asta.</div>' : `<section class="card pad" style="margin-bottom:14px"><div class="card-header"><div><div class="eyebrow">Scelta consigliata</div><h2>${best.shape.name}</h2><p class="muted">${number(best.result.points, 2)} punti attesi${best.result.modifier ? ` · +${number(best.result.modifier, 2)} modificatore` : ''}</p></div>${tag('migliore tra i disponibili', 'accent-tag')}</div>${renderFormationPitch(best.result)}<p class="source-note">Le probabilità, gli avversari e le indisponibilità arrivano dall’ultimo dataset pubblicato.</p></section><div class="lineup-grid">${formations.map(({ shape, result }) => `<section class="card lineup-card ${shape === best.shape ? 'best' : ''}"><h3><span>${shape.name}</span><span class="accent">${number(result.points, 1)}</span></h3>${renderFormationPitch(result)}<div class="substitution">${result.flat.length < 11 ? `Mancano ${11 - result.flat.length} titolari` : result.modifier ? `Modificatore +${number(result.modifier, 1)}` : 'Senza modificatore'}</div></section>`).join('')}</div>`}`;
}

function renderInjuries() {
  const mine = new Set(teamPlayers(state.asta.mia).map((entry) => String(entry.p.id)));
  const rows = [...(DATA.indisponibili || [])].sort((a, b) => {
    const am = mine.has(String((DATA.giocatori.find((p) => p.nome === a.nome && p.squadra === a.squadra) || {}).id));
    const bm = mine.has(String((DATA.giocatori.find((p) => p.nome === b.nome && p.squadra === b.squadra) || {}).id));
    return Number(bm) - Number(am);
  });
  return `${pageHeading('Infermeria', 'Chi rischia il voto.', 'Gli indisponibili della fonte dati, con la tua rosa in cima quando il nome è riconosciuto.', '')}<section class="card pad"><div class="table-wrap"><table><thead><tr><th>Calciatore</th><th>Squadra</th><th>Stato</th><th>Rientro</th><th>Nota</th></tr></thead><tbody>${rows.map((row) => { const p = DATA.giocatori.find((candidate) => candidate.nome === row.nome && candidate.squadra === row.squadra); const isMine = p && mine.has(String(p.id)); return `<tr>${isMine ? '<td class="accent">★ ' : '<td>'}${esc(row.nome)}</td><td>${esc(row.squadra)}</td><td>${tag(row.tipo || 'Indisponibile', row.tipo === 'Squalificato' ? 'red-tag' : 'amber-tag')}</td><td>${esc(row.rientro ? `${row.rientro}ª giornata` : '—')}</td><td class="muted">${esc(row.nota || '—')}</td></tr>`; }).join('')}</tbody></table></div><p class="source-note">${rows.length} segnalazioni nel dataset del ${esc(DATA.aggiornato || 'giorno di aggiornamento')}.</p></section>`;
}

function renderStats() {
  const last = DATA.giocatori.filter((p) => p.storico && p.storico['2025-26']);
  const byFm = [...last].sort((a, b) => Number(b.storico['2025-26'].fm || 0) - Number(a.storico['2025-26'].fm || 0)).slice(0, 12);
  const byGoals = [...last].sort((a, b) => Number(b.storico['2025-26'].gol || 0) - Number(a.storico['2025-26'].gol || 0)).slice(0, 12);
  const byApps = [...last].sort((a, b) => Number(b.storico['2025-26'].pv || 0) - Number(a.storico['2025-26'].pv || 0)).slice(0, 12);
  const totalGoals = last.reduce((sum, p) => sum + Number(p.storico['2025-26'].gol || 0), 0);
  return `${pageHeading('Statistiche', 'Il contesto prima del nome.', 'Quattro stagioni nel dataset locale, con classifiche rapide e dettaglio giocatore dal listone.', '')}<div class="grid grid-4"><section class="card stat-card"><small>Giocatori storici</small><strong>${last.length}</strong><p>con dati 2025/26</p></section><section class="card stat-card"><small>Gol registrati</small><strong>${number(totalGoals)}</strong><p>nell’ultima stagione completa</p></section><section class="card stat-card"><small>Giornate</small><strong>${number(DATA.giornate_giocate)}</strong><p>giocate nel dataset corrente</p></section><section class="card stat-card"><small>Fonti prezzo</small><strong>${number(Object.keys(DATA.fonti_prezzo || {}).length)}</strong><p>mercato indipendente</p></section></div><div class="grid grid-3" style="margin-top:14px"><section class="card pad"><div class="eyebrow">Rendimento</div><h2>Fantamedia</h2>${renderHistoryRank(byFm, (p) => Number(p.storico['2025-26'].fm || 0))}</section><section class="card pad"><div class="eyebrow">Bonus</div><h2>Gol</h2>${renderHistoryRank(byGoals, (p) => Number(p.storico['2025-26'].gol || 0), 0)}</section><section class="card pad"><div class="eyebrow">Continuità</div><h2>Presenze</h2>${renderHistoryRank(byApps, (p) => Number(p.storico['2025-26'].pv || 0), 0)}</section></div>`;
}

function renderHistoryRank(list, value, digits = 1) {
  return `<div class="rank-list">${list.map((p, index) => `<button class="rank-row" style="border:0;background:transparent;color:inherit;width:100%;text-align:left" data-action="detail" data-id="${esc(p.id)}"><span class="rank-number">${index + 1}</span><span><strong>${esc(p.nome)}</strong><small>${esc(p.squadra)} · ${esc(ROLE_LABELS[p.R])}</small></span><span class="rank-value">${number(value(p), digits)}</span></button>`).join('')}</div>`;
}

function renderAsk() {
  const answer = ui.askAnswer ? `<section class="card pad" style="margin-top:14px"><div class="eyebrow">Risposta</div><div class="help-box" style="margin-top:8px">${ui.askAnswer}</div></section>` : '';
  return `${pageHeading('Chiedimi', 'Parla come all’asta.', 'Le risposte sono calcolate nel browser sui dati e sugli acquisti di questa copia.', '')}<form class="card pad" data-action="ask"><div class="field"><label for="ask-input">La tua domanda</label><input id="ask-input" name="question" value="${esc(ui.askText)}" placeholder="Quanto vale Lautaro? Cosa mi manca?" autocomplete="off"></div><button class="button" style="margin-top:12px" type="submit">Rispondi</button></form>${answer}`;
}

function answerQuestion(question) {
  const text = question.toLowerCase();
  const summary = leagueSummary();
  if (text.includes('manca') || text.includes('scopert')) {
    const counts = ROLE_ORDER.map((role) => [role, summary.mine.filter((entry) => entry.p.R === role).length]);
    return `Ti mancano <strong>${summary.missing} slot</strong>: ${counts.map(([role, count]) => `${ROLE_LABELS[role]} ${Math.max(0, Number(state.config.slot[role]) - count)}`).join(', ')}. Hai ancora <strong>${money(summary.cap)}</strong> di offerta massima.`;
  }
  const tokens = text.split(/[^a-zà-ÿ0-9]+/i).filter((token) => token.length >= 3);
  const found = DATA.giocatori.find((p) => tokens.some((token) => p.nome.toLowerCase().includes(token) || String(p.nome_completo || '').toLowerCase().includes(token)));
  if (found) {
    const market = liveMarket();
    const sold = purchasedEntry(found.id);
    if (text.includes('vendut') && sold) return `<strong>${esc(found.nome)}</strong> è assegnato a <strong>${esc(state.asta.squadre[sold.squadra])}</strong> per <strong>${money(sold.prezzo)}</strong>.`;
    return `<strong>${esc(found.nome)}</strong> è un ${ROLE_LABELS[found.R].toLowerCase()} da <strong>${money(market.max[found.id] || found.prezzo)}</strong>. FM attesa ${number(found.fm_att, 2)}, ${number(found.pv_proiettate, 0)} presenze attese. ${esc(found.verdetto || '')}.`;
  }
  if (text.includes('asta') || text.includes('mercato')) {
    const market = liveMarket();
    return `Il mercato è ${market.temperature > 1.12 ? '<strong>caldo</strong>' : market.temperature < .88 ? '<strong>freddo</strong>' : '<strong>in equilibrio</strong>'}. Nella lega sono stati venduti ${Object.keys(state.asta.acquisti).length} giocatori.`;
  }
  return 'Posso aiutarti con un nome, un prezzo, la tua rosa o il mercato. Prova: “Quanto vale Lautaro?” oppure “Cosa mi manca?”.';
}

function renderSettings() {
  const cfg = state.config;
  const quoteSum = ROLE_ORDER.reduce((sum, role) => sum + Number(cfg.quote[role] || 0), 0);
  const usedTeams = Object.values(state.asta.acquisti).some((entry) => Number(entry.squadra) >= Number(cfg.squadre));
  return `${pageHeading('Opzioni', 'La tua lega.', 'Queste impostazioni e l’asta vengono salvate solo su questo dispositivo.', '')}<div class="settings-grid"><section class="settings-group"><div class="eyebrow">Configurazione</div><h3>Parametri principali</h3><form data-action="save-settings"><div class="settings-fields"><div class="field"><label>Squadre</label><input name="squadre" type="number" min="2" max="20" value="${Number(cfg.squadre)}"></div><div class="field"><label>Crediti</label><input name="crediti" type="number" min="100" max="2000" step="10" value="${Number(cfg.crediti)}"></div></div><label class="status-pill" style="margin-top:14px"><input name="modificatore" type="checkbox" ${cfg.modificatore_difesa ? 'checked' : ''} style="width:auto;min-height:0"> Modificatore di difesa</label><h3 style="margin-top:20px">Slot per ruolo</h3><div class="settings-fields">${ROLE_ORDER.map((role) => `<div class="field"><label>${ROLE_LABELS[role]}</label><input name="slot-${role}" type="number" min="1" max="15" value="${Number(cfg.slot[role])}"></div>`).join('')}</div><h3 style="margin-top:20px">Quote budget</h3><div class="settings-fields">${ROLE_ORDER.map((role) => `<div class="field"><label>${ROLE_LABELS[role]}</label><input name="quote-${role}" type="number" min="0" max="1" step="0.01" value="${Number(cfg.quote[role]).toFixed(2)}"></div>`).join('')}</div>${Math.abs(quoteSum - 1) > .005 ? `<div class="warning">Le quote attuali sommano a ${(quoteSum * 100).toFixed(0)}%. Devono sommare a 100%.</div>` : ''}<button class="button" style="margin-top:17px" type="submit">Salva e applica</button></form></section><section class="settings-group"><div class="eyebrow">Dati locali</div><h3>Backup e reset</h3><p class="help-box">IndexedDB conserva nomi, acquisti, tema e configurazione sul dispositivo. Esporta un backup prima di cambiare telefono o browser.</p><div class="settings-actions"><button class="button-secondary" data-action="export">Esporta backup</button><button class="button-secondary" data-action="import">Importa backup</button><input id="import-file" type="file" accept="application/json" hidden></div><div class="warning" style="margin-top:24px">${usedTeams ? 'La configurazione attuale contiene acquisti in squadre oltre il numero impostato: sistemali prima di ridurre la lega.' : 'Il dataset è statico: per nuovi dati serve pubblicare una nuova versione del sito.'}</div><button class="button-danger" style="margin-top:15px" data-action="reset">Azzera tutti gli acquisti</button></section></div>`;
}

function renderPage() {
  switch (ui.page) {
    case 'auction': return renderAuction();
    case 'advice': return renderAdvice();
    case 'teams': return renderTeams();
    case 'squad': return renderSquad();
    case 'lineup': return renderLineup();
    case 'injuries': return renderInjuries();
    case 'stats': return renderStats();
    case 'ask': return renderAsk();
    case 'settings': return renderSettings();
    default: return renderHome();
  }
}

function render() {
  if (!DATA || !state) return;
  marketCache = null;
  document.documentElement.dataset.theme = state.theme;
  const root = $('#app');
  root.innerHTML = `<div class="app-shell">${renderHeader()}<main class="content">${renderPage()}</main>${renderBottomNav()}${ui.toast ? `<div class="toast" role="status">${esc(ui.toast)}</div>` : ''}</div>`;
}

function setPage(page) {
  if (!PAGE_LABELS[page]) return;
  ui.page = page;
  ui.detailId = null;
  ui.showCount = 60;
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function handleAssign(form) {
  const id = String(form.dataset.id);
  const p = player(id);
  const formData = new FormData(form);
  const team = Number(formData.get('team'));
  const price = Math.round(Number(formData.get('price')));
  if (!p || !Number.isInteger(team) || team < 0 || team >= state.asta.squadre.length || !Number.isFinite(price) || price < 1 || price > Number(state.config.crediti)) {
    notify('Controlla squadra e prezzo.'); return;
  }
  const old = purchasedEntry(id);
  const targetEntries = teamPlayers(team).filter((entry) => String(entry.p.id) !== id);
  const roleLimit = Number(state.config.slot[p.R] || 0);
  if (targetEntries.filter((entry) => entry.p.R === p.R).length >= roleLimit) {
    notify(`La squadra ha già tutti gli slot ${ROLE_LABELS[p.R].toLowerCase()} pieni.`); return;
  }
  const targetSpent = targetEntries.reduce((sum, entry) => sum + entry.price, 0) + price;
  if (targetSpent > Number(state.config.crediti)) {
    notify('Questa squadra non ha abbastanza crediti.'); return;
  }
  await commit((current) => { current.asta.acquisti[id] = { squadra: team, prezzo: price }; });
  ui.detailId = id;
  notify(old ? 'Acquisto aggiornato.' : 'Giocatore assegnato.');
}

async function handleSettings(form) {
  const fd = new FormData(form);
  const next = clone(state.config);
  next.squadre = clamp(Math.round(Number(fd.get('squadre'))), 2, 20);
  next.crediti = clamp(Math.round(Number(fd.get('crediti'))), 100, 2000);
  next.modificatore_difesa = fd.get('modificatore') === 'on';
  ROLE_ORDER.forEach((role) => {
    next.slot[role] = clamp(Math.round(Number(fd.get(`slot-${role}`))), 1, 15);
    next.quote[role] = clamp(Number(fd.get(`quote-${role}`)), 0, 1);
  });
  const quoteSum = ROLE_ORDER.reduce((sum, role) => sum + next.quote[role], 0);
  if (Math.abs(quoteSum - 1) > .005) { notify('Le quote devono sommare a 100%.'); return; }
  const overTeam = Object.values(state.asta.acquisti).some((entry) => Number(entry.squadra) >= next.squadre);
  if (overTeam) { notify('Non puoi ridurre le squadre finché esistono acquisti nelle squadre rimosse.'); return; }
  const overSlot = Object.entries(state.asta.acquisti).some(([id, entry]) => {
    const p = player(id); if (!p) return false;
    return teamPlayers(entry.squadra).filter((other) => other.p.R === p.R).length > next.slot[p.R];
  });
  if (overSlot) { notify('I nuovi slot lascerebbero un reparto sovraffollato.'); return; }
  await commit((current) => {
    current.config = next;
    current.asta.squadre = current.asta.squadre.slice(0, next.squadre);
    while (current.asta.squadre.length < next.squadre) current.asta.squadre.push(`Squadra ${current.asta.squadre.length + 1}`);
  });
  notify('Impostazioni salvate.');
}

async function handleImport(file) {
  if (!file) return;
  try {
    const imported = JSON.parse(await file.text());
    state = normalizeState(imported, DATA.config);
    await saveState();
    render();
    notify('Backup importato.');
  } catch (error) { notify('Il backup non è valido.'); }
}

function exportState() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = `fantaiuto-backup-${new Date().toISOString().slice(0, 10)}.json`;
  link.click(); URL.revokeObjectURL(url);
}

document.addEventListener('click', async (event) => {
  const pageTarget = event.target.closest('[data-page]');
  if (pageTarget) { event.preventDefault(); setPage(pageTarget.dataset.page); return; }
  const actionTarget = event.target.closest('[data-action]');
  if (!actionTarget) return;
  const action = actionTarget.dataset.action;
  if (action === 'detail') { ui.detailId = String(actionTarget.dataset.id); render(); return; }
  if (action === 'show-more') { ui.showCount += 60; render(); return; }
  if (action === 'theme') { await commit((current) => { current.theme = current.theme === 'dark' ? 'light' : 'dark'; }); return; }
  if (action === 'export') { exportState(); return; }
  if (action === 'import') { $('#import-file')?.click(); return; }
  if (action === 'release') {
    if (!window.confirm('Liberare questo acquisto?')) return;
    await commit((current) => { delete current.asta.acquisti[String(actionTarget.dataset.id)]; });
    notify('Acquisto liberato.'); return;
  }
  if (action === 'reset') {
    if (!window.confirm('Cancellare tutti gli acquisti della lega?')) return;
    await commit((current) => { current.asta.acquisti = {}; });
    notify('Asta azzerata.');
  }
});

document.addEventListener('change', (event) => {
  const filter = event.target.closest('[data-filter]');
  if (filter) { ui.filters[filter.dataset.filter] = filter.value; ui.showCount = 60; render(); return; }
  if (event.target.id === 'import-file') handleImport(event.target.files[0]);
});

document.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target.closest('form[data-action]');
  if (!form) return;
  const action = form.dataset.action;
  if (action === 'filter-form') {
    const fd = new FormData(form);
    ['query', 'role', 'team', 'risk', 'sort'].forEach((key) => { ui.filters[key] = String(fd.get(key) || ''); });
    ui.showCount = 60; render(); return;
  }
  if (action === 'assign') { await handleAssign(form); return; }
  if (action === 'save-teams') {
    const fd = new FormData(form);
    await commit((current) => {
      current.asta.squadre = current.asta.squadre.map((team, index) => String(fd.get(`team-${index}`) || `Squadra ${index + 1}`).trim() || `Squadra ${index + 1}`);
      current.asta.mia = Number(fd.get('my-team')) || 0;
    });
    notify('Nomi salvati.'); return;
  }
  if (action === 'ask') {
    const question = String(new FormData(form).get('question') || '').trim();
    ui.askText = question; ui.askAnswer = answerQuestion(question); render(); return;
  }
  if (action === 'save-settings') { await handleSettings(form); }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && ui.detailId) { ui.detailId = null; render(); }
});

async function boot() {
  try {
    const response = await fetch('./dati/valutazioni.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    DATA = await response.json();
    state = normalizeState(await loadSavedState(), DATA.config);
    await saveState();
    render();
  } catch (error) {
    $('#app').innerHTML = `<div class="error-screen"><div class="brand-mark">!</div><h2>Impossibile caricare FantAiuto</h2><p class="muted">${esc(error.message)}. Pubblica la cartella tramite GitHub Pages o un server web locale: non aprire direttamente il file HTML.</p></div>`;
  }
}

boot();
