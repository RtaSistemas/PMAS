/* PMAS — Frontend App */

// ---------------------------------------------------------------------------
// i18n — translation tables live in lang/pt.js and lang/en.js
// ---------------------------------------------------------------------------
const _LANG = { pt: window._LANG_PT || {}, en: window._LANG_EN || {} };
let _locale = localStorage.getItem('pmas_lang') || 'pt';
function _t(key) { return (_LANG[_locale] || _LANG.pt)[key] || key; }
function _applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = _t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = _t(el.dataset.i18nPh); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = _t(el.dataset.i18nTitle); });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', _t(el.dataset.i18nAria)); });
}

// ---------------------------------------------------------------------------
// EVM glossary — terms and tooltip behaviour live in evm-glossary.js
// ---------------------------------------------------------------------------
const _EVM_TERMS = window._EVM_TERMS || {};

// ---------------------------------------------------------------------------
// Multi-currency display (UI-only conversion, no backend calls)
// ---------------------------------------------------------------------------
let _currencyFactor = 1;
let _currencySymbol = 'R$';

function _fmtCost(rawValue, decimals = 2) {
  if (rawValue == null) return '—';
  const v = rawValue * _currencyFactor;
  return `${_currencySymbol} ${v.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

function _applyConversion(factor, symbol) {
  _currencyFactor = factor > 0 ? factor : 1;
  _currencySymbol = symbol || 'R$';
}

function _onCurrencyChange() {
  const factor = parseFloat(document.getElementById('currencyFactor').value);
  const symbol = document.getElementById('currencySymbol').value.trim();
  _applyConversion(factor, symbol);
  _renderActiveTab();
}

document.getElementById('currencyFactor').addEventListener('change', _onCurrencyChange);
document.getElementById('currencySymbol').addEventListener('change', _onCurrencyChange);

// ---------------------------------------------------------------------------
// Modal utilities — focus trap + Escape + aria
// ---------------------------------------------------------------------------
function openModal(modalId, triggerEl, firstFocusSelector) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal._triggerEl = triggerEl || document.activeElement;
  modal.hidden = false;
  const firstFocusable = firstFocusSelector
    ? modal.querySelector(firstFocusSelector)
    : modal.querySelector('input:not([disabled]), select:not([disabled]), button:not([disabled])');
  requestAnimationFrame(() => firstFocusable?.focus());
  modal._trapHandler = e => {
    if (e.key !== 'Tab') return;
    const focusable = [...modal.querySelectorAll(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )];
    if (!focusable.length) return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (e.shiftKey) { if (document.activeElement === first) { e.preventDefault(); last.focus(); } }
    else            { if (document.activeElement === last)  { e.preventDefault(); first.focus(); } }
  };
  modal._escHandler = e => { if (e.key === 'Escape') closeModal(modalId); };
  modal.addEventListener('keydown', modal._trapHandler);
  document.addEventListener('keydown', modal._escHandler);
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.hidden = true;
  if (modal._trapHandler) modal.removeEventListener('keydown', modal._trapHandler);
  if (modal._escHandler)  document.removeEventListener('keydown', modal._escHandler);
  modal._triggerEl?.focus();
}

// Single delegated handler — any button/link with data-modal-close="<id>" closes that modal
document.addEventListener('click', e => {
  const btn = e.target.closest('[data-modal-close]');
  if (btn) closeModal(btn.dataset.modalClose);
});

function confirmDialog(message, onConfirm, danger = true) {
  document.getElementById('confirmModalMsg').textContent = message;
  const btn = document.getElementById('confirmModalOk');
  btn.className = `btn ${danger ? 'btn-danger' : 'btn-primary'}`;
  const handler = () => {
    closeModal('confirmModal');
    onConfirm();
    btn.removeEventListener('click', handler);
  };
  btn.addEventListener('click', handler);
  openModal('confirmModal', document.activeElement, '#confirmModalOk');
}

// ---------------------------------------------------------------------------
// Table sort
// ---------------------------------------------------------------------------
const _tableSortState = {};

function _sortData(data, key, type, dir) {
  return [...data].sort((a, b) => {
    let va = a[key], vb = b[key];
    if (type === 'num')        { va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }
    else if (type === 'date')  { va = va ? +new Date(va) : 0; vb = vb ? +new Date(vb) : 0; }
    else { va = (va ?? '').toString().toLowerCase(); vb = (vb ?? '').toString().toLowerCase(); }
    return dir * (va < vb ? -1 : va > vb ? 1 : 0);
  });
}

function _applySort(tableId, data) {
  const st = _tableSortState[tableId];
  return st?.col ? _sortData(data, st.col, st.type, st.dir) : data;
}

function _makeSortable(tableId, colDefs, getDataFn, renderFn) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const ths = table.querySelectorAll('thead th');
  _tableSortState[tableId] = { col: null, type: null, dir: 1 };
  ths.forEach((th, i) => {
    const def = colDefs[i];
    if (!def) return;
    th.classList.add('sortable');
    th.setAttribute('role', 'columnheader');
    th.setAttribute('aria-sort', 'none');
    th.setAttribute('tabindex', '0');
    const _sortHandler = () => {
      const st = _tableSortState[tableId];
      if (st.col === def.key) { st.dir *= -1; }
      else { st.col = def.key; st.type = def.type; st.dir = 1; }
      ths.forEach(t => { t.classList.remove('sort-asc', 'sort-desc'); t.removeAttribute('aria-sort'); });
      th.classList.add(st.dir === 1 ? 'sort-asc' : 'sort-desc');
      th.setAttribute('aria-sort', st.dir === 1 ? 'ascending' : 'descending');
      renderFn(_applySort(tableId, getDataFn()));
    };
    th.addEventListener('click', _sortHandler);
    th.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _sortHandler(); } });
  });
}

// ---------------------------------------------------------------------------
// Theme-aware helpers
// ---------------------------------------------------------------------------
function _cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function _echartsTip(extra = {}) {
  return Object.assign({
    backgroundColor: _cssVar('--card'),
    borderColor:     _cssVar('--border'),
    textStyle:       { color: _cssVar('--text') },
  }, extra);
}

// ---------------------------------------------------------------------------
// Top-level tab navigation
// ---------------------------------------------------------------------------
const tabBtns     = document.querySelectorAll('.tab-btn');
const tabSections = document.querySelectorAll('.tab-section');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
    tabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;

    if (btn.dataset.tab === 'dashboard') _renderActiveTab();
    if (btn.dataset.tab === 'projects') loadProjectsTable();
    if (btn.dataset.tab === 'cycles')   loadCyclesTable();
    if (btn.dataset.tab === 'team')     loadTeamTab();
    if (btn.dataset.tab === 'my')       _initMyArea();
    if (btn.dataset.tab === 'admin')  { loadUsersTable(); loadAuditLog(); loadRulesList(); _loadThemeEditor(); loadAdminAlerts(); }
  });
});

// ---------------------------------------------------------------------------
// Analytics sub-tab navigation + ECharts instance registry
// ---------------------------------------------------------------------------

// Chart instance registry — keyed by DOM element id
const _charts = {};

// Which chart IDs belong to each sub-tab (to dispose on leave)
const CHARTS_PER_TAB = {
  effort:     ['effortChart', 'trendsChart', 'pepCpiChart', 'costCompositionChart', 'collabInlineTimelineChart', 'collabCalendarChart'],
  portfolio:  ['treemapChart', 'bulletChart', 'scatterChart'],
  forecast:   ['forecastChart', 'burnUpChart', 'whatIfBurnUpChart', 'mcHistogramChart', 'velocitySparklineChart'],
};

function _disposeTabCharts(tabId) {
  (CHARTS_PER_TAB[tabId] || []).forEach(id => {
    if (_charts[id] && !_charts[id].isDisposed()) {
      _charts[id].dispose();
    }
    delete _charts[id];
  });
}

function _getOrCreateChart(id) {
  if (!_charts[id] || _charts[id].isDisposed()) {
    _charts[id] = echarts.init(document.getElementById(id), 'pmas', { renderer: 'svg' });
    _charts[id].setOption({ aria: { enabled: true } });
  }
  return _charts[id];
}


// ResizeObserver — resize all live charts when container changes
const _ro = new ResizeObserver(() => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.resize(); } catch (_) {} });
});
_ro.observe(document.querySelector('main'));

// Print hooks — hide toolbox icons before printing (SVG renderer embeds them
// as <path> elements inside <svg>, so @media print CSS cannot target them).
// Restore immediately after the print dialog closes.
window.addEventListener('beforeprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: false } }); } catch (_) {} });
});
window.addEventListener('afterprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: true  } }); } catch (_) {} });
});

// Sub-tab state
let _activeATab = 'effort';
let _stackMode  = true;   // true = stacked, false = grouped
let _evmMode    = false;  // false = hours, true = R$
let _pepCpiMode = false;  // false = hidden, true = per-PEP CPI panel visible
let _portfolioTimelineMode = false;  // false = aggregated treemap, true = cycle timeline

const atabBtns     = document.querySelectorAll('.atab-btn');
const atabSections = document.querySelectorAll('.atab-section');

atabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    _disposeTabCharts(_activeATab);
    atabBtns.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
    atabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
    _activeATab = btn.dataset.atab;
    document.getElementById(`atab-${_activeATab}`).hidden = false;
    if (_activeATab === 'forecast') _populateForecastPepSelect();
    _renderActiveTab();
  });
});

document.getElementById('evmToggleBtn').addEventListener('click', () => {
  _evmMode = !_evmMode;
  document.getElementById('evmToggleBtn').textContent = _evmMode ? _t('btn.view_cost') : _t('btn.view_hours');
  _renderPortfolioTab();
});

document.getElementById('timelineToggleBtn').addEventListener('click', () => {
  _portfolioTimelineMode = !_portfolioTimelineMode;
  document.getElementById('timelineToggleBtn').textContent =
    _portfolioTimelineMode ? _t('btn.timeline_off') : _t('btn.timeline_on');
  document.getElementById('timelineToggleBtn').classList.toggle('btn-primary', _portfolioTimelineMode);
  document.getElementById('timelineToggleBtn').classList.toggle('btn-secondary', !_portfolioTimelineMode);
  _renderPortfolioTab();
});

document.getElementById('cpiToggleBtn').addEventListener('click', () => {
  _pepCpiMode = !_pepCpiMode;
  document.getElementById('cpiToggleBtn').textContent =
    _pepCpiMode ? _t('btn.hide_cpi') : _t('btn.view_cpi');
  if (_activeATab === 'effort') _renderActiveTab();
});

document.getElementById('exportCsvBtn').addEventListener('click', () => {
  if (!_lastEffortData.length) { notify(_t('msg.load_before_export'), 'info'); return; }
  const header = `${_t('allocation.collaborator')},${_t('ch.normal_h')},${_t('ch.extra_h')},${_t('ch.standby_h')},${_t('allocation.total')}`;
  const rows = _lastEffortData.map(d => {
    const total = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
    return `"${d.collaborator.replace(/"/g, '""')}",${d.normal_hours.toFixed(1)},${d.extra_hours.toFixed(1)},${d.standby_hours.toFixed(1)},${total}`;
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'esforco-equipe.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('runwayExportBtn').addEventListener('click', () => {
  if (!_lastRunwayData.length) { notify(_t('msg.load_before_export'), 'info'); return; }
  const header = _t('runway.csv.header');
  const rows = _lastRunwayData.map(d => {
    const risk = { ok: 'OK', warning: _t('risk.warning'), critical: _t('risk.critical'), overrun: _t('runway.overrun'), no_budget: _t('runway.no_budget') }[d.risk] || d.risk;
    return [
      `"${d.pep_wbs}"`, `"${d.name || ''}"`,
      d.budget_hours != null ? d.budget_hours.toFixed(1) : '',
      d.consumed_hours.toFixed(1),
      d.pct_consumed  != null ? d.pct_consumed.toFixed(1)  : '',
      d.avg_hours_per_cycle != null ? d.avg_hours_per_cycle.toFixed(1) : '',
      d.cycles_to_complete != null ? d.cycles_to_complete.toFixed(1) : '',
      `"${d.estimated_completion_cycle || ''}"`,
      d.cpi != null ? d.cpi.toFixed(2) : '',
      `"${risk}"`,
    ].join(',');
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'runway-portfolio.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('stackToggleBtn').addEventListener('click', () => {
  _stackMode = !_stackMode;
  document.getElementById('stackToggleBtn').textContent =
    _stackMode ? _t('btn.stacked') : _t('btn.grouped');
  const ch = _charts['effortChart'];
  if (ch && !ch.isDisposed()) {
    ch.setOption(_buildEffortSeriesOnly(_stackMode), false);
  }
});

// ---------------------------------------------------------------------------
// Auth helpers + fetch wrappers + notify + login
// ---------------------------------------------------------------------------
function _authHeaders(extra = {}) {
  const token = sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

function _getTokenPayload() {
  const token = sessionStorage.getItem('access_token');
  if (!token) return null;
  try { return JSON.parse(atob(token.split('.')[1])); } catch (_) { return null; }
}

function _isAdmin() {
  const p = _getTokenPayload();
  return p ? p.role === 'admin' : false;
}

function _handleUnauthorized() {
  sessionStorage.removeItem('access_token');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
}

function _friendlyError(e) {
  if (!e) return _t('msg.err_generic');
  const s = e.status ?? e.statusCode;
  if (s === 401 || s === 403) return _t('err.unauthorized');
  if (s === 404)              return _t('err.not_found');
  if (s === 409)              return _t('err.conflict');
  if (s === 422) {
    const detail = e.message;
    if (detail && typeof detail === 'string' && detail.length < 200 && !detail.includes('traceback')) return detail;
    return _t('err.validation');
  }
  if (s === 429)              return _t('err.rate_limit');
  if (s != null && s >= 500)  return _t('err.server');
  return e.message || _t('msg.err_generic');
}

function _apiError(status, detail, statusText) {
  const err = new Error(detail ?? statusText);
  err.status = status;
  return err;
}

async function apiFetch(url) {
  const res = await fetch(url, { headers: _authHeaders() });
  if (res.status === 401) { _handleUnauthorized(); throw _apiError(401, 'Sessão expirada. Faça login novamente.'); }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw _apiError(res.status, j.detail, res.statusText);
  }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: _authHeaders({ 'Content-Type': 'application/json' }),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { _handleUnauthorized(); throw _apiError(401, 'Sessão expirada. Faça login novamente.'); }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw _apiError(res.status, j.detail, res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

const _notifQueue = [];
let _notifShowing = false;

function notify(msg, type = 'info') {
  _notifQueue.push({ msg, type });
  if (!_notifShowing) _processNotifQueue();
}

function _processNotifQueue() {
  if (!_notifQueue.length) { _notifShowing = false; return; }
  _notifShowing = true;
  const { msg, type } = _notifQueue.shift();
  const el = document.getElementById('notification');
  const textEl = document.getElementById('notificationText');
  textEl.textContent = msg;
  el.className = type;
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => {
    el.hidden = true;
    setTimeout(_processNotifQueue, 150);
  }, type === 'error' ? 12000 : 5000);
}

document.getElementById('notificationClose').addEventListener('click', () => {
  const el = document.getElementById('notification');
  clearTimeout(el._timer);
  el.hidden = true;
  _notifShowing = false;
  setTimeout(_processNotifQueue, 150);
});

window.addEventListener('unhandledrejection', e => {
  notify(_friendlyError(e.reason), 'error');
  console.error('[unhandled]', e.reason);
});

function fmt(h) {
  return Number(h).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  });
}

// ---------------------------------------------------------------------------
// Login form
// ---------------------------------------------------------------------------
document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errEl    = document.getElementById('loginError');
  errEl.textContent = '';
  try {
    const res = await fetch('/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      errEl.textContent = j.detail ?? _t('msg.invalid_credentials');
      return;
    }
    const { access_token } = await res.json();
    sessionStorage.setItem('access_token', access_token);
    sessionStorage.setItem('username', username);
    document.getElementById('loginOverlay').setAttribute('hidden', '');
    document.getElementById('appShell').removeAttribute('hidden');
    _bootApp();
  } catch (_) {
    errEl.textContent = _t('msg.connection_error');
  }
});

function _logout() {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('username');
  sessionStorage.removeItem('role');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
}

document.getElementById('logoutBtn').addEventListener('click', _logout);

function _checkTokenExpiry() {
  const p = _getTokenPayload();
  if (!p?.exp) return;
  const minsLeft = (p.exp - Date.now() / 1000) / 60;
  if (minsLeft <= 0) { _logout(); return; }
  if (minsLeft < 10) notify(_t('auth.session_expiring_soon'), 'warning');
}


// ---------------------------------------------------------------------------
// User preferences — populated at login, used by layout + color pickers
// ---------------------------------------------------------------------------
let _userPrefs = null;

async function _loadPreferences() {
  try {
    _userPrefs = await apiFetch('/api/my/preferences');
  } catch {
    _userPrefs = { dashboard: { grid_cols: 2, charts: [] } };
  }
}

// ---------------------------------------------------------------------------
// Theme loader (public endpoint — no auth required)
// ---------------------------------------------------------------------------
const _DENSITY_MAP = {
  compact:  { spacing: '0.45rem', fontSize: '0.78rem' },
  normal:   { spacing: '0.875rem', fontSize: '0.875rem' },
  relaxed:  { spacing: '1.35rem', fontSize: '1rem' },
};

function _getPalette() {
  return window._CHART_PALETTE || ['#4f8ef7','#e94560','#2ecc71','#f39c12','#9b59b6','#1abc9c'];
}

function _resolveSeriesColor(chartId, seriesName, fallbackIndex) {
  const prefs = window._userPrefs?.dashboard?.charts?.find(c => c.id === chartId);
  const custom = prefs?.options?.series_colors?.[seriesName];
  if (custom) return custom;
  const palette = _getPalette();
  return palette[fallbackIndex % palette.length] || '#4f8ef7';
}

async function _loadTheme() {
  try {
    const t = await fetch('/api/theme').then(r => r.json());
    const root = document.documentElement;

    const primary   = t.color_primary    || '#4f8ef7';
    const bg        = t.color_background || '#1a1a2e';
    const surface   = t.color_surface    || '#16213e';
    const accent    = t.color_accent     || '#e94560';
    const success   = t.color_success    || '#2ecc71';
    const warning   = t.color_warning    || '#f39c12';
    const danger    = t.color_danger     || '#e74c3c';
    const text      = t.color_text       || '#e0e0e0';
    const textMuted = t.color_text_muted || '#8892a4';

    // Standard --color-* vars (new CSS)
    root.style.setProperty('--color-primary',    primary);
    root.style.setProperty('--color-background', bg);
    root.style.setProperty('--color-surface',    surface);
    root.style.setProperty('--color-accent',     accent);
    root.style.setProperty('--color-success',    success);
    root.style.setProperty('--color-warning',    warning);
    root.style.setProperty('--color-danger',     danger);
    root.style.setProperty('--color-text',       text);
    root.style.setProperty('--color-text-muted', textMuted);

    // --theme-* aliases (gradient bar, tooltips)
    root.style.setProperty('--theme-primary',    primary);
    root.style.setProperty('--theme-bg',         bg);
    root.style.setProperty('--theme-surface',    surface);
    root.style.setProperty('--theme-accent',     accent);
    root.style.setProperty('--theme-success',    success);
    root.style.setProperty('--theme-warning',    warning);
    root.style.setProperty('--theme-danger',     danger);
    root.style.setProperty('--theme-text',       text);
    root.style.setProperty('--theme-text-muted', textMuted);

    // Original legacy vars — the ones the existing stylesheet actually uses
    // (--bg 3×, --surface 8×, --card 8×, --text 12×, --primary 10×, etc.)
    root.style.setProperty('--bg',        bg);
    root.style.setProperty('--surface',   surface);
    root.style.setProperty('--card',      surface);
    root.style.setProperty('--card-alt',  bg);
    root.style.setProperty('--text',      text);
    root.style.setProperty('--text-2',    textMuted);
    root.style.setProperty('--text-3',    textMuted);
    root.style.setProperty('--primary',   primary);
    root.style.setProperty('--primary-d', primary);
    root.style.setProperty('--primary-g', `linear-gradient(135deg, ${primary} 0%, ${accent} 100%)`);
    root.style.setProperty('--green',     success);
    root.style.setProperty('--amber',     warning);
    root.style.setProperty('--red',       danger);
    root.style.setProperty('--cyan',      accent);

    // Extended optional tokens — override defaults when present
    if (t.color_card)      root.style.setProperty('--card',     t.color_card);
    if (t.color_border)    root.style.setProperty('--border',   t.color_border);
    if (t.color_text_hint) root.style.setProperty('--text-3',   t.color_text_hint);
    if (t.color_violet)    root.style.setProperty('--violet',   t.color_violet);
    if (t.border_radius) {
      const _radMap = { sharp: '2px',  normal: '8px',  rounded: '16px' };
      const _lgMap  = { sharp: '4px',  normal: '12px', rounded: '24px' };
      root.style.setProperty('--radius',    _radMap[t.border_radius] || '8px');
      root.style.setProperty('--radius-lg', _lgMap[t.border_radius]  || '12px');
    }

    // Density
    const density = _DENSITY_MAP[t.density] || _DENSITY_MAP.normal;
    root.style.setProperty('--density-spacing',   density.spacing);
    root.style.setProperty('--density-font-size', density.fontSize);

    // Font family
    if (t.font_family) root.style.setProperty('--font-family', t.font_family);

    // Chart palette
    window._CHART_PALETTE = t.chart_palette?.length ? t.chart_palette : undefined;

    // Register pmas echarts theme from CSS tokens
    if (window.echarts) {
      echarts.registerTheme('pmas', {
        backgroundColor: 'transparent',
        textStyle: { color: _cssVar('--text-1') },
        axisLabel: { color: _cssVar('--text-2') },
        splitLine: { lineStyle: { color: _cssVar('--border') } },
      });
    }

    // App name
    const appName = t.app_name || 'PMAS';
    document.title = `${appName} — Dashboard`;
    document.querySelectorAll('[data-app-name]').forEach(el => { el.textContent = appName; });

    // Logo
    if (t.logo_url) {
      document.querySelectorAll('[data-app-logo]').forEach(el => { el.src = escHtml(t.logo_url); });
      const box = document.getElementById('headerLogoBox');
      if (box) box.innerHTML = `<img src="${escHtml(t.logo_url)}" class="header-logo-img" alt="Logo" data-app-logo />`;
    }
  } catch (_) { /* silently ignore — not critical */ }
}


function _bootApp() {
  if (_isAdmin()) document.getElementById('adminTabBtn').removeAttribute('hidden');
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  _loadTheme();
  _loadPreferences().then(() => _applyLayoutPreferences());
  _updateHeaderUser();
  _restoreFilterDates();
  if (_getTokenPayload()?.must_change) _showDefaultPasswordBanner();
  loadDashboardCycles().then(() => {
    if (!_allCycles.length && _isAdmin()) _showOnboardingBanner();
    _restoreFilterSelections();
  });
  loadSemaphore();
  loadGlobalConfig();
  _refreshTabBadges();
  _renderActiveTab();
  _initNotifications();
  _checkTokenExpiry();
  setInterval(_checkTokenExpiry, 5 * 60 * 1000);
}

function _showDefaultPasswordBanner() {
  if (document.getElementById('defaultPassBanner')) return;
  const banner = document.createElement('div');
  banner.id = 'defaultPassBanner';
  banner.style.cssText = [
    'display:flex;align-items:center;gap:1rem;flex-wrap:wrap',
    'margin:1rem 1.5rem 0',
    'padding:.75rem 1rem',
    'border-radius:6px',
    'border:1px solid var(--red)',
    'background:rgba(var(--red-rgb,220,38,38),0.08)',
    'color:var(--text)',
  ].join(';');
  banner.innerHTML = `
    <span style="font-size:1.2rem">⚠️</span>
    <span style="flex:1;font-size:.9rem">
      <b style="color:var(--red)">${_t('sec.default_pass.title')}</b><br>
      <span style="color:var(--text-2)">${_t('sec.default_pass.body')}</span>
    </span>
    <button class="btn btn-sm" id="defaultPassCta"
      style="background:var(--red);color:var(--text-inv,#fff);border:none;white-space:nowrap">
      ${_t('sec.default_pass.cta')}
    </button>
  `;
  document.getElementById('appShell')?.prepend(banner);
  document.getElementById('defaultPassCta')?.addEventListener('click', () => {
    document.querySelector('[data-tab="admin"]')?.click();
    setTimeout(() => document.getElementById('usersTable')?.scrollIntoView({ behavior: 'smooth' }), 200);
  });
}

function _showOnboardingBanner() {
  if (document.getElementById('onboardingBanner')) return;
  const banner = document.createElement('div');
  banner.id = 'onboardingBanner';
  banner.className = 'card';
  banner.style.cssText = 'margin:1.5rem;padding:1.5rem;border:1px solid var(--primary);background:rgba(14,165,233,0.05)';
  banner.innerHTML = `
    <h2 style="margin:0 0 1rem;font-size:1.1rem;color:var(--primary)">${_t('onboard.title')}</h2>
    <ol style="margin:0 0 1.25rem;padding-left:1.4rem;display:flex;flex-direction:column;gap:.4rem;color:var(--text-2)">
      <li>${_t('onboard.step1')}</li>
      <li>${_t('onboard.step2')}</li>
      <li>${_t('onboard.step3')}</li>
    </ol>
    <button class="btn btn-primary btn-sm" id="onboardingCta">${_t('onboard.cta')}</button>
  `;
  const dashPanel = document.getElementById('tab-dashboard');
  if (dashPanel) dashPanel.prepend(banner);
  document.getElementById('onboardingCta')?.addEventListener('click', () => {
    banner.remove();
    document.querySelector('[data-tab="projects"]')?.click();
  });
}


document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return;
  if (!sessionStorage.getItem('access_token')) return;
  const tab = document.querySelector('.tab-btn.active')?.dataset.tab;
  if (tab === 'cycles')   loadCyclesTable();
  if (tab === 'projects') loadProjectsTable();
});

if (sessionStorage.getItem('access_token')) {
  document.getElementById('loginOverlay').setAttribute('hidden', '');
  document.getElementById('appShell').removeAttribute('hidden');
  _bootApp();
}
