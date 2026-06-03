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

function _fmtCost(rawValue) {
  const v = rawValue * _currencyFactor;
  return `${_currencySymbol} ${v.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
    th.addEventListener('click', () => {
      const st = _tableSortState[tableId];
      if (st.col === def.key) { st.dir *= -1; }
      else { st.col = def.key; st.type = def.type; st.dir = 1; }
      ths.forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(st.dir === 1 ? 'sort-asc' : 'sort-desc');
      renderFn(_applySort(tableId, getDataFn()));
    });
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
    if (btn.dataset.tab === 'projects') { loadCyclesTable(); loadProjectsTable(); }
    if (btn.dataset.tab === 'team')     loadTeamTab();
    if (btn.dataset.tab === 'my')       _initMyArea();
    if (btn.dataset.tab === 'admin')  { loadUsersTable(); loadAuditLog(); loadRulesList(); _loadThemeEditor(); }
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
    _charts[id] = echarts.init(document.getElementById(id), 'dark', { renderer: 'svg' });
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
// Dashboard — DOM refs and multi-selects
// ---------------------------------------------------------------------------
const loadBtn  = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const _msRegistry = [];
function _createMS(el, placeholder, onChange) {
  const ms = new MultiSelect(el, placeholder, onChange);
  _msRegistry.push(ms);
  return ms;
}

const cycleMs        = _createMS(document.getElementById('cycleMs'),        _t('ms.cycle_ph'),    onCycleChange);
const pepMs          = _createMS(document.getElementById('pepMs'),           _t('ms.pep_ph'),      onPepChange);
const pepDescMs      = _createMS(document.getElementById('pepDescMs'),       _t('ms.pep_desc_ph'), onPepDescChange);
const collaboratorMs = _createMS(document.getElementById('collaboratorMs'),  _t('ms.collab_ph'),   onCollabChange);

let pepDataCache = {};

async function onCycleChange()    { await Promise.all([refreshPeps(), refreshCollaborators()]); }
async function onPepChange()      { refreshPepDescriptions(); await refreshCollaborators(); }
async function onPepDescChange()  { await refreshCollaborators(); }
async function onCollabChange()   { await refreshPeps(); }

// ---------------------------------------------------------------------------
// Filter cascade helpers
// ---------------------------------------------------------------------------
async function loadDashboardCycles() {
  try {
    const filters = await apiFetch('/api/v2/filters');
    const cycles = filters.cycles;
    const peps   = filters.peps;
    const collabs = filters.collaborators;

    _allCycles = cycles;
    cycleMs.setItems(cycles.map(c => ({ value: c.id, label: c.name })));

    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();

    collaboratorMs.setItems(collabs.map(c => ({ value: c.id, label: c.name })), true);
  } catch (e) { notify(`${_t('msg.err_load_filters')}: ${e.message}`, 'error'); }
}

async function refreshPeps() {
  try {
    const filters = await apiFetch('/api/v2/filters');
    const peps = filters.peps;
    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();
  } catch (e) { console.warn('refreshPeps:', e); notify(`${_t('msg.err_update_pep_filter')}: ${e.message}`, 'warning'); }
}

function refreshPepDescriptions() {
  const selected = pepMs.getValues();
  const descs = [...new Set(selected.flatMap(code => pepDataCache[code] || []))];
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  try {
    const filters = await apiFetch('/api/v2/filters');
    collaboratorMs.setItems(filters.collaborators.map(c => ({ value: c.id, label: c.name })), true);
  } catch (e) { console.warn('refreshCollaborators:', e); notify(`${_t('msg.err_update_collab_filter')}: ${e.message}`, 'warning'); }
}

// ---------------------------------------------------------------------------
// Upload result panel
// ---------------------------------------------------------------------------
function _showIngestResult(json, filename) {
  const panel   = document.getElementById('ingestResultPanel');
  const summary = document.getElementById('ingestResultSummary');
  const details = document.getElementById('ingestResultDetails');

  const chip = (label, val, color) =>
    val > 0 ? `<span style="background:${color}22;color:${color};border:1px solid ${color}44;border-radius:.3rem;padding:.1rem .5rem;font-size:.78rem;white-space:nowrap">${label}: <strong>${val}</strong></span>` : '';

  summary.innerHTML =
    `<span style="font-weight:600;color:#e2e8f0">${escHtml(filename)}</span>` +
    chip('Inseridos',   json.records_inserted,         '#2ecc71') +
    chip('Ignorados',   json.records_skipped,           _cssVar('--text-3')) +
    chip('Quarentena',  json.quarantine_records_added,  _cssVar('--red')) +
    chip('Avisos',      json.warning_count,             _cssVar('--amber')) +
    chip('Infos',       json.info_count,                '#60a5fa');

  let html = '';
  if (json.warnings?.length) {
    html += `<details open style="padding:.6rem 1rem;border-bottom:1px solid ${_cssVar('--surface')}">
      <summary style="cursor:pointer;color:${_cssVar('--amber')};font-weight:600;font-size:.8rem;list-style:none">⚠ ${json.warnings.length} aviso(s)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.warnings.map(w => `<li style="color:#fcd34d;font-size:.79rem">${escHtml(w)}</li>`).join('')}
      </ul></details>`;
  }
  if (json.infos?.length) {
    html += `<details open style="padding:.6rem 1rem">
      <summary style="cursor:pointer;color:#60a5fa;font-weight:600;font-size:.8rem;list-style:none">ℹ ${json.infos.length} informação(ões)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.infos.map(i => `<li style="color:#93c5fd;font-size:.79rem">${escHtml(i)}</li>`).join('')}
      </ul></details>`;
  }
  details.innerHTML = html || `<p style="padding:.6rem 1rem;color:#475569;font-size:.8rem;margin:0">${_t('msg.no_warnings_infos')}</p>`;
  panel.hidden = false;
  clearTimeout(panel._dismissTimer);
  panel._dismissTimer = setTimeout(() => { panel.hidden = true; }, 6000);
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
// Language toggle
document.getElementById('langToggleBtn').addEventListener('click', () => {
  _locale = _locale === 'pt' ? 'en' : 'pt';
  localStorage.setItem('pmas_lang', _locale);
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  cycleMs.setPlaceholder(_t('ms.cycle_ph'));
  pepMs.setPlaceholder(_t('ms.pep_ph'));
  pepDescMs.setPlaceholder(_t('ms.pep_desc_ph'));
  collaboratorMs.setPlaceholder(_t('ms.collab_ph'));
  // Re-render dynamic content for active tab
  const tab = document.querySelector('.tab-btn.active')?.dataset.tab;
  if (tab === 'cycles')   _renderCyclesTable(_allCycles);
  if (tab === 'projects') _renderProjectsTable(_allProjects);
  if (tab === 'team')     loadTeamTab();
  if (tab === 'dashboard') _renderActiveTab();
  if (tab === 'admin')    { loadUsersTable(); loadAuditLog(); loadRulesList(); _loadThemeEditor(); }
  if (tab === 'my')       _initMyArea();
});

// ---------------------------------------------------------------------------
// Load button
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', () => { _saveFilters(); _renderActiveTab(); });

clearBtn.addEventListener('click', () => {
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  try { localStorage.removeItem('pmas_filters_v1'); } catch (_) {}
  pepDataCache = {};
  _evmMode = false;
  document.getElementById('evmToggleBtn').textContent = _t('btn.view_hours');
  _pepCpiMode = false;
  document.getElementById('cpiToggleBtn').textContent = _t('btn.view_cpi');
  document.getElementById('pepCpiPanel').hidden = true;
  _showEmpty('pepCpiEmpty', false);
  document.getElementById('scatterPanel').hidden = true;
  _showEmpty('scatterEmpty', false);
  _disposeTabCharts('effort');
  _disposeTabCharts('portfolio');
  document.getElementById('allocationMatrix').innerHTML = '';
  _showEmpty('allocationEmpty', false);
  _disposeTabCharts('forecast');
  document.getElementById('forecastKpis').hidden = true;
  document.getElementById('forecastKpis').innerHTML = '';
  _showEmpty('forecastEmpty', true);
  document.getElementById('effortStats').innerHTML = '';
  document.getElementById('portfolioStats').innerHTML = '';
  document.getElementById('bulletPanel').hidden  = true;
  document.getElementById('runwayTable').hidden = true;
  document.getElementById('runwayEmpty').hidden = true;
  document.getElementById('concentrationPanel').hidden = true;
  document.getElementById('concentrationGrid').innerHTML = '';
  _showEmpty('effortEmpty',    false);
  _showEmpty('portfolioEmpty', false);
  _showEmpty('trendsEmpty',    false);
});

// ---------------------------------------------------------------------------
// Date filter shortcuts
// ---------------------------------------------------------------------------
(function () {
  function _isoDate(d) {
    return d.toISOString().slice(0, 10);
  }
  function _applyDates(from, to) {
    document.getElementById('dateFromInput').value = _isoDate(from);
    document.getElementById('dateToInput').value   = _isoDate(to);
    loadBtn.click();
  }
  document.getElementById('shortcutLastMonth')?.addEventListener('click', () => {
    const now = new Date();
    _applyDates(
      new Date(now.getFullYear(), now.getMonth() - 1, 1),
      new Date(now.getFullYear(), now.getMonth(), 0)
    );
  });
  document.getElementById('shortcutLastQuarter')?.addEventListener('click', () => {
    const now = new Date();
    const q = Math.floor(now.getMonth() / 3);
    const prevQ = q === 0 ? 3 : q - 1;
    const prevQYear = q === 0 ? now.getFullYear() - 1 : now.getFullYear();
    _applyDates(
      new Date(prevQYear, prevQ * 3, 1),
      new Date(prevQYear, prevQ * 3 + 3, 0)
    );
  });
  document.getElementById('shortcutThisYear')?.addEventListener('click', () => {
    const y = new Date().getFullYear();
    _applyDates(new Date(y, 0, 1), new Date(y, 11, 31));
  });
})();

// ---------------------------------------------------------------------------
// Analytics — render dispatcher
// ---------------------------------------------------------------------------
async function _renderActiveTab() {
  const btn = document.getElementById('loadBtn');
  if (btn) { btn.disabled = true; btn.setAttribute('aria-busy', 'true'); }
  try {
    if (_activeATab === 'effort')    await _renderEffortTab();
    if (_activeATab === 'portfolio') await _renderPortfolioTab();
    if (_activeATab === 'forecast')  await _renderForecastTab();
  } finally {
    if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
  }
}

function _showEmpty(id, show) {
  const el = document.getElementById(id);
  if (el) el.hidden = !show;
}

// ---------------------------------------------------------------------------
// Esforço da Equipe
// ---------------------------------------------------------------------------
let _lastEffortData = [];
let _lastRunwayData = [];
let _selectedCollaborator = null;
let _calYear  = new Date().getFullYear();
let _calMonth = new Date().getMonth() + 1; // 1-12

async function _renderEffortTab() {
  _closeCollabDetail();
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  cycleIds.forEach(id => p.append('cycle_id', id));
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  _setChartLoading(['effortChart'], true);
  try {
    const data = await apiFetch(`/api/v2/effort?${p}`);
    _setChartLoading(['effortChart'], false);
    _lastEffortData = data;
    const bva = [];

    // Stats row
    document.getElementById('effortStats').innerHTML = '';
    document.getElementById('effortStats').appendChild(_buildStatsRow(data, bva));

    // Title
    document.getElementById('effortTitle').textContent = _buildEffortTitle(cycleIds, pepCodes);

    if (data.length === 0) {
      _showEmpty('effortEmpty', true);
      _disposeTabCharts('effort');
      return;
    }
    _showEmpty('effortEmpty', false);

    // Sort ascending — ECharts horizontal bar renders bottom-to-top,
    // so low→high puts the highest contributor at the visual top.
    const sortedData = [...data].sort((a, b) =>
      (a.normal_hours + a.extra_hours + a.standby_hours) -
      (b.normal_hours + b.extra_hours + b.standby_hours)
    );
    const h = calcHeight(sortedData.length);
    document.getElementById('effortChart').style.height = `${h}px`;
    const ch = _getOrCreateChart('effortChart');
    ch.setOption(_buildHoursBarOption({
      data:        sortedData,
      categoryKey: 'collaborator',
      orientation: 'horizontal',
      stacked:     _stackMode,
      showTotal:   true,
      richLabel:   true,
      maxItems:    40,
      toolboxName: 'PMAS-Esforco',
    }), true);
    ch.resize();
    ch.off('click');
    ch.on('click', async (params) => {
      if (params && params.name) {
        if (_selectedCollaborator === params.name) {
          _closeCollabDetail();
        } else {
          await _openCollabDetail(params.name);
        }
      }
    });

    // Trends + CPI charts — full filter passthrough with cycle window logic
    await _renderTrendsCharts(pepCodes, pepDescs, collabIds, cycleIds, dateFrom, dateTo);

  } catch (err) {
    _setChartLoading(['effortChart'], false);
    notify(`${_t('msg.err_generic')}: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Portfolio Runway panel
// ---------------------------------------------------------------------------
function _riskColor(risk) {
  const colors = {
    ok:       'var(--green,   #10d98a)',
    warning:  'var(--amber,   #d9b273)',
    critical: 'var(--red,     #c56d76)',
    overrun:  'var(--red,     #c56d76)',
    no_budget:'var(--text-3,  #818998)',
  };
  return colors[risk] || colors.no_budget;
}

function _renderRunwayPanel(runway) {
  _lastRunwayData = runway;
  const table     = document.getElementById('runwayTable');
  const empty     = document.getElementById('runwayEmpty');
  const exportBtn = document.getElementById('runwayExportBtn');

  // Update column headers for current mode
  const plannedTh = document.getElementById('runwayPlannedTh');
  if (plannedTh) plannedTh.textContent = _evmMode ? _t('runway.th.planned_r') : _t('runway.th.planned');
  const avgTh = document.getElementById('runwayAvgTh');
  if (avgTh) avgTh.textContent = _evmMode ? _t('runway.th.avg_r') : _t('runway.th.avg');

  const withBudget = runway
    .filter(r => _evmMode ? r.budget_cost != null : r.budget_hours != null)
    .map(r => Object.assign({}, r, {
      _sortPlanned: _evmMode ? (r.budget_cost||0)         : (r.budget_hours||0),
      _sortAvg:     _evmMode ? (r.avg_cost_per_cycle||0)  : (r.avg_hours_per_cycle||0),
    }));
  if (exportBtn) exportBtn.hidden = !runway.length;
  if (!withBudget.length) {
    table.hidden = true;
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  table.hidden = false;
  _drawRunwayRows(_applySort('runwayTable', withBudget));
}

function _drawRunwayRows(data) {
  const tbody = document.getElementById('runwayBody');
  tbody.innerHTML = '';
  data.forEach(item => {
    const rawPct = _evmMode ? item.pct_consumed_cost : item.pct_consumed;
    const pct    = rawPct != null ? Math.min(rawPct, 100) : 0;

    const color = _riskColor(_evmMode ? item.cost_risk : item.risk);

    const absLabel = _evmMode
      ? `R$ ${item.actual_cost.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
      : `${item.consumed_hours.toFixed(1)}h`;
    const pctLabel = rawPct != null ? `${rawPct.toFixed(1)}% (${absLabel})` : '—';
    const bar = `<div style="background:#1e293b;border-radius:3px;height:6px;width:120px">` +
      `<div style="height:6px;border-radius:3px;background:${color};width:${pct}%"></div></div>` +
      `<span style="font-size:.75rem;color:#94a3b8;margin-left:.4rem">${pctLabel}</span>`;

    let cyclesCell;
    let completionCell;
    if (item.is_closed) {
      const closedTag = `<span style="color:var(--green,#5ad388);font-weight:600">${_t('runway.closed')}</span>`;
      cyclesCell    = closedTag;
      completionCell = closedTag;
    } else {
      cyclesCell = '—';
      if (item.risk === 'overrun') {
        cyclesCell = `<span style="color:var(--red,#c56d76);font-weight:600">${_t('runway.overrun')}</span>`;
      } else if (item.cycles_to_complete != null) {
        cyclesCell = item.cycles_to_complete.toFixed(1);
      }
      completionCell = escHtml(item.estimated_completion_cycle || '—');
    }

    let spiCell = '—';
    if (item.spi != null) {
      const spiColor = _EVM_COLOR_CSS[item.spi_color] || _EVM_COLOR_CSS.success;
      spiCell = `<span style="color:${spiColor};font-weight:600">${item.spi.toFixed(2)}</span>`;
    }

    const statusMap = {
      on_track:    { label: _t('runway.status.on_track')    || 'No prazo',     color: 'var(--primary,#4f8ef7)' },
      at_risk:     { label: _t('runway.status.at_risk')     || 'Atenção',      color: 'var(--amber,#d9b273)' },
      behind:      { label: _t('runway.status.behind')      || 'Atrasado',     color: 'var(--red,#c56d76)' },
      no_baseline: { label: _t('runway.status.no_baseline') || 'Sem baseline', color: '#475569' },
    };
    const st = statusMap[item.schedule_status] || statusMap.no_baseline;
    const statusCell = `<span style="font-size:.78rem;font-weight:600;color:${st.color}">${st.label}</span>`;

    let cpiCell = '—';
    if (item.cpi != null) {
      const cpiColor = _EVM_COLOR_CSS[item.cpi_color] || _EVM_COLOR_CSS.success;
      cpiCell = `<span style="color:${cpiColor};font-weight:600">${item.cpi.toFixed(2)}</span>`;
    }

    const rowBg = (item.risk === 'critical' || item.risk === 'overrun')
      ? 'background:rgba(197,109,118,.07)'
      : '';

    const tr = document.createElement('tr');
    tr.style.cssText = rowBg;
    tr.innerHTML = `
      <td style="font-family:monospace;font-size:.82rem">${escHtml(item.pep_wbs)}</td>
      <td style="font-size:.82rem;color:#94a3b8">${escHtml(item.name || '—')}</td>
      <td style="text-align:right">${_evmMode
        ? (item.budget_cost != null ? `R$ ${item.budget_cost.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}` : '—')
        : (item.budget_hours != null ? item.budget_hours.toFixed(1) : '—')}</td>
      <td style="white-space:nowrap">${bar}</td>
      <td style="text-align:right">${_evmMode
        ? (item.avg_cost_per_cycle  != null ? `R$ ${item.avg_cost_per_cycle.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}` : '—')
        : (item.avg_hours_per_cycle != null ? item.avg_hours_per_cycle.toFixed(1) : '—')}</td>
      <td style="text-align:right">${cpiCell}</td>
      <td style="text-align:right">${cyclesCell}</td>
      <td style="font-size:.82rem">${completionCell}</td>
      <td style="text-align:right">${spiCell}</td>
      <td>${statusCell}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------------------
// Concentration Risk panel
// ---------------------------------------------------------------------------
function _renderConcentrationPanel(concentration) {
  const panel = document.getElementById('concentrationPanel');
  const empty = document.getElementById('concentrationEmpty');
  const grid  = document.getElementById('concentrationGrid');
  grid.innerHTML = '';

  // Update subtitle to reflect current mode
  const noteEl = document.getElementById('concentrationNote');
  if (noteEl) noteEl.textContent = _evmMode ? _t('conc.note_cost') : _t('conc.note');

  if (!concentration || !concentration.length) {
    panel.hidden = false;
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  panel.hidden = false;

  concentration.forEach(item => {
    // In cost mode re-sort contributors by cost share so bars reflect correct order
    const contribs = _evmMode
      ? [...item.top_contributors].sort((a, b) => b.pct_cost - a.pct_cost)
      : item.top_contributors;

    const top1val  = contribs.length > 0 ? (_evmMode ? contribs[0].pct_cost : contribs[0].pct) : 0;
    const riskSrc  = _evmMode ? item.risk_cost : item.risk;
    const riskKey  = riskSrc === 'high' ? 'critical' : riskSrc === 'medium' ? 'warning' : 'ok';
    const dotColor = _riskColor(riskKey);

    const barsHtml = contribs.map(c => {
      const pct      = _evmMode ? c.pct_cost : c.pct;
      const barWidth = top1val > 0 ? Math.round(pct / top1val * 100) : 0;
      const cName    = c.is_other
        ? `${_t('concentration.others')} (${c.others_count})`
        : c.name;
      return `<div style="display:flex;align-items:center;gap:.35rem;min-width:0">` +
        `<span style="font-size:.78rem;color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100px" title="${escHtml(cName)}">${escHtml(cName)}</span>` +
        `<div style="flex:1;min-width:40px;max-width:80px;background:#1e293b;border-radius:2px;height:8px">` +
          `<div style="height:8px;border-radius:2px;background:${dotColor};width:${barWidth}%"></div>` +
        `</div>` +
        `<span style="font-size:.75rem;color:#94a3b8;white-space:nowrap">${pct.toFixed(0)}%</span>` +
        `</div>`;
    }).join('');

    const totalDisplay = _evmMode
      ? `R$ ${item.total_cost.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
      : `${item.total_hours.toFixed(0)}h`;

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:1rem;padding:.4rem .5rem;border-radius:.35rem;background:#0e2038';
    row.innerHTML = `
      <div style="min-width:14px;display:flex;align-items:center"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;flex-shrink:0;background:${dotColor}"></span></div>
      <div style="min-width:130px">
        <div style="font-family:monospace;font-size:.8rem;color:#e2e8f0">${escHtml(item.pep_wbs)}</div>
        <div style="font-size:.72rem;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:130px" title="${escHtml(item.name || '')}">${escHtml(item.name || '')}</div>
      </div>
      <div style="display:flex;gap:.75rem;flex-wrap:wrap;flex:1">${barsHtml}</div>
      <div style="font-size:.72rem;color:#475569;white-space:nowrap">${totalDisplay}</div>
    `;
    grid.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// Saúde do Portfólio
// ---------------------------------------------------------------------------
async function _renderPortfolioTab() {
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  // Single params object shared by all four portfolio charts
  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  _setChartLoading(['treemapChart'], true);
  try {
    const [health, trends, runway, concentration] = await Promise.all([
      apiFetch(`/api/v2/portfolio?${p}`),
      apiFetch(`/api/v2/trends?${p}`).catch(() => []),
      apiFetch(`/api/v2/runway?${p}`).catch(() => []),
      apiFetch(`/api/v2/concentration?${p}`).catch(() => []),
    ]);
    _setChartLoading(['treemapChart'], false);

    // Stats row — rendered before the empty-state guard so it clears on no data
    const statsEl = document.getElementById('portfolioStats');
    statsEl.innerHTML = '';
    if (health.length > 0) {
      statsEl.appendChild(_buildPortfolioStatsRow(health, trends));
    }

    // Runway panel — always rendered (shows empty state if no budgeted PEPs)
    _renderRunwayPanel(runway);

    // Concentration panel
    _renderConcentrationPanel(concentration);

    if (!health.length) {
      _showEmpty('portfolioEmpty', true);
      _disposeTabCharts('portfolio');
      document.getElementById('bulletPanel').hidden = true;
      return;
    }
    _showEmpty('portfolioEmpty', false);

    // Update treemap title
    document.getElementById('portfolioTreemapTitle').textContent =
      _evmMode ? _t('portfolio.treemap_r') : _t('portfolio.treemap_h');

    // Treemap — dynamic height: 220px for ≤4 PEPs, +55px per extra PEP, cap 440px
    document.getElementById('treemapChart').style.height =
      (health.length <= 4 ? 220 : Math.min(440, 220 + (health.length - 4) * 55)) + 'px';
    const tm = _getOrCreateChart('treemapChart');
    tm.setOption(_buildTreemapOption(health, _evmMode), true);
    tm.resize();

    // Bullet chart — in hours mode use budget_hours, in R$ mode use budget_cost
    const withBudget = _evmMode
      ? health.filter(d => d.budget_cost != null)
      : health.filter(d => d.budget_hours != null);
    if (withBudget.length > 0) {
      document.getElementById('bulletPanel').hidden = false;
      document.getElementById('bulletChart').style.height =
        `${Math.max(220, withBudget.length * 60 + 80)}px`;
      const bc = _getOrCreateChart('bulletChart');
      bc.setOption(_buildBulletOption(withBudget, _evmMode), true);
      bc.resize();
    } else {
      document.getElementById('bulletPanel').hidden = true;
    }

    // EVM Quadrant (CPI × SPI) — uses runway data already fetched above
    const quadrantItems = runway.filter(r => r.cpi != null && r.spi != null);
    if (quadrantItems.length >= 1) {
      _showEmpty('scatterEmpty', false);
      document.getElementById('scatterPanel').hidden = false;
      document.getElementById('scatterChart').style.height = '380px';
      const sc = _getOrCreateChart('scatterChart');
      sc.setOption(_buildEvmQuadrantOption(quadrantItems), true);
      sc.resize();
    } else {
      _showEmpty('scatterEmpty', quadrantItems.length === 0);
      document.getElementById('scatterPanel').hidden = true;
      if (_charts['scatterChart'] && !_charts['scatterChart'].isDisposed()) {
        _charts['scatterChart'].dispose();
        delete _charts['scatterChart'];
      }
    }

    // Allocation matrix — last item in portfolio
    await _renderAllocationTab();

  } catch (err) {
    _setChartLoading(['treemapChart'], false);
    notify(`${_t('msg.err_generic')}: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Cost Composition by Hour Type chart
// ---------------------------------------------------------------------------
function _renderCostCompositionChart(trends) {
  const panel = document.getElementById('costCompositionPanel');
  const emptyEl = document.getElementById('costCompositionEmpty');

  const filtered = (trends || []).filter(t =>
    (t.normal_cost || 0) + (t.extra_cost || 0) + (t.standby_cost || 0) > 0
  );

  if (!filtered.length) {
    panel.hidden = false;
    emptyEl.hidden = false;
    if (_charts['costCompositionChart'] && !_charts['costCompositionChart'].isDisposed()) {
      _charts['costCompositionChart'].dispose();
      delete _charts['costCompositionChart'];
    }
    document.getElementById('costCompositionChart').style.visibility = 'hidden';
    return;
  }

  panel.hidden = false;
  emptyEl.hidden = true;
  document.getElementById('costCompositionChart').style.visibility = '';

  const sym = document.getElementById('currencySymbol')?.value || 'R$';
  const factor = parseFloat(document.getElementById('currencyFactor')?.value) || 1;

  const categories = filtered.map(t => t.cycle_name);
  const normalData  = filtered.map(t => +((t.normal_cost  || 0) * factor).toFixed(2));
  const extraData   = filtered.map(t => +((t.extra_cost   || 0) * factor).toFixed(2));
  const standbyData = filtered.map(t => +((t.standby_cost || 0) * factor).toFixed(2));

  const pal = _getPalette();
  const cc = _getOrCreateChart('costCompositionChart');
  cc.setOption({
    ..._chartDefaults(),
    legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ..._chartDefaults().tooltip,
      formatter(params) {
        const total = params.reduce((s, p) => s + (p.value || 0), 0);
        let html = `<b>${params[0].axisValue}</b><br/>`;
        params.forEach(p => {
          const pct = total > 0 ? (p.value / total * 100).toFixed(1) : '0.0';
          html += `${p.marker}${p.seriesName}: ${sym} ${p.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (${pct}%)<br/>`;
        });
        html += `<b>Total: ${sym} ${total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</b>`;
        return html;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: categories, axisLabel: { color: '#94a3b8', fontSize: 11, rotate: categories.length > 8 ? 30 : 0 } },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${sym} ${v.toLocaleString('pt-BR')}` } },
    series: [
      { name: _t('trends.normal'),  type: 'bar', stack: 'cost', data: normalData,  itemStyle: { color: pal[0] } },
      { name: _t('trends.extra'),   type: 'bar', stack: 'cost', data: extraData,   itemStyle: { color: pal[1] } },
      { name: _t('trends.standby'), type: 'bar', stack: 'cost', data: standbyData, itemStyle: { color: pal[2] } },
    ],
  }, true);
  cc.resize();
}

// ---------------------------------------------------------------------------
// Compute date window for Queima/IDP when cycles are selected.
// Returns {dateFrom, dateTo} covering selected cycles ±1 neighbor.
// If no cycles selected, returns the manually entered date range unchanged.
// ---------------------------------------------------------------------------
function _computeTrendsWindow(cycleIds, dateFrom, dateTo) {
  if (!cycleIds.length) return { dateFrom, dateTo };

  const sorted = [..._allCycles]
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));

  if (!sorted.length) return { dateFrom, dateTo };

  const indices = cycleIds
    .map(id => sorted.findIndex(c => String(c.id) === String(id)))
    .filter(i => i >= 0);

  if (!indices.length) return { dateFrom, dateTo };

  const minIdx = Math.min(...indices);
  const maxIdx = Math.max(...indices);
  const prevIdx = Math.max(0, minIdx - 1);
  const nextIdx = Math.min(sorted.length - 1, maxIdx + 1);

  return {
    dateFrom: sorted[prevIdx].start_date,
    dateTo:   sorted[nextIdx].end_date,
  };
}

// ---------------------------------------------------------------------------
// Skeleton / shimmer loading state for chart containers
// ---------------------------------------------------------------------------
function _setChartLoading(ids, on) {
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.toggleAttribute('data-chart-loading', on);
  });
}

// ---------------------------------------------------------------------------
// Filter persistence — dateFrom / dateTo saved across sessions
// ---------------------------------------------------------------------------
function _saveFilters() {
  try {
    localStorage.setItem('pmas_filters_v1', JSON.stringify({
      dateFrom: document.getElementById('dateFromInput').value,
      dateTo:   document.getElementById('dateToInput').value,
    }));
  } catch (_) {}
}
function _restoreFilterDates() {
  try {
    const s = JSON.parse(localStorage.getItem('pmas_filters_v1') || 'null');
    if (!s) return;
    if (s.dateFrom) document.getElementById('dateFromInput').value = s.dateFrom;
    if (s.dateTo)   document.getElementById('dateToInput').value   = s.dateTo;
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Trends + CPI helper — called from _renderEffortTab
// ---------------------------------------------------------------------------
async function _renderTrendsCharts(pepCodes, pepDescs, collabIds, cycleIds, dateFrom, dateTo) {
  const { dateFrom: wFrom, dateTo: wTo } = _computeTrendsWindow(cycleIds, dateFrom, dateTo);

  const p = new URLSearchParams();
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (wFrom) p.set('date_from', wFrom);
  if (wTo)   p.set('date_to',   wTo);

  _setChartLoading(['trendsChart'], true);
  try {
    const trends = await apiFetch(`/api/v2/trends?${p}`);
    _setChartLoading(['trendsChart'], false);

    if (!trends.length) {
      _showEmpty('trendsEmpty', true);
      if (_charts['trendsChart'] && !_charts['trendsChart'].isDisposed()) {
        _charts['trendsChart'].dispose(); delete _charts['trendsChart'];
      }
      document.getElementById('costCompositionPanel').hidden = true;
      if (_charts['costCompositionChart'] && !_charts['costCompositionChart'].isDisposed()) {
        _charts['costCompositionChart'].dispose(); delete _charts['costCompositionChart'];
      }
      return;
    }
    _showEmpty('trendsEmpty', false);

    // Trends chart with moving average overlay
    const trendsOpt = _buildHoursBarOption({
      data:        trends,
      categoryKey: 'cycle_name',
      orientation: 'vertical',
      stacked:     true,
      showTotal:   true,
      richLabel:   false,
      maxItems:    40,
      toolboxName: 'PMAS-Queima',
    });
    const tc = _getOrCreateChart('trendsChart');
    tc.setOption(trendsOpt, true);
    tc.resize();

    // Cost Composition chart — G3
    _renderCostCompositionChart(trends);

    // Per-PEP CPI panel (toggle-controlled)
    if (!_pepCpiMode) {
      document.getElementById('pepCpiPanel').hidden = true;
      return;
    }
    // When no specific cycles are selected, use all active (non-quarantine) cycles
    const effectiveCycleIds = cycleIds.length > 0
      ? cycleIds
      : (_allCycles || []).filter(c => c.is_active).map(c => c.id);

    if (!effectiveCycleIds.length) {
      _showEmpty('pepCpiEmpty', true);
      document.getElementById('pepCpiPanel').hidden = false;
      return;
    }
    try {
      const cycleStartMap = {};
      const cycleNameMap  = {};
      (_allCycles || []).forEach(c => { cycleStartMap[c.id] = c.start_date; cycleNameMap[c.id] = c.name; });

      // Sort cycles chronologically so cumulative accumulation is correct
      const sortedCycleIds = [...effectiveCycleIds].sort((a, b) => {
        const aD = cycleStartMap[a] ?? '';
        const bD = cycleStartMap[b] ?? '';
        return aD < bD ? -1 : aD > bD ? 1 : 0;
      });

      // Get PEP list: use filter selection or fall back to single portfolio call
      let pepWbsList;
      if (pepCodes.length > 0) {
        pepWbsList = [...pepCodes];
      } else {
        try {
          const listP = new URLSearchParams();
          pepDescs.forEach(d   => listP.append('pep_description', d));
          collabIds.forEach(id => listP.append('collaborator_id', id));
          if (dateFrom) listP.set('date_from', dateFrom);
          if (dateTo)   listP.set('date_to',   dateTo);
          const listItems = await apiFetch(`/api/v2/portfolio?${listP}`);
          pepWbsList = [...new Set(listItems.map(i => i.pep_wbs).filter(Boolean))];
        } catch (_) { pepWbsList = []; }
      }

      if (!pepWbsList.length) {
        _showEmpty('pepCpiEmpty', true);
        document.getElementById('pepCpiPanel').hidden = false;
        return;
      }

      // Fetch forecast per PEP — uses baseline-aware budget for correct EV/CPI
      const fcParams = new URLSearchParams();
      if (dateFrom) fcParams.set('date_from', dateFrom);
      if (dateTo)   fcParams.set('date_to',   dateTo);

      const selectedCycleNames = new Set(effectiveCycleIds.map(id => cycleNameMap[id]).filter(Boolean));

      const fcAll = await Promise.all(
        pepWbsList.map(wbs =>
          apiFetch(`/api/v2/forecast?pep_wbs=${encodeURIComponent(wbs)}&${fcParams}`).catch(() => null)
        )
      );

      // Build pepMap + spiMapByPep from forecast history
      // CPI = cumulative_ev_cost / cumulative_cost (server-computed, baseline-aware)
      const pepMap = {};
      const spiMapByPep = {};

      fcAll.forEach((fc, i) => {
        if (!fc?.history?.length) return;
        const wbs = pepWbsList[i];
        const points = [];
        const spiMap = {};
        fc.history.forEach(h => {
          // Honour cycle filter when active
          if (cycleIds.length > 0 && !selectedCycleNames.has(h.cycle_name)) return;
          if (h.cumulative_cost > 0 && h.cumulative_ev_cost != null) {
            points.push({ cycleName: h.cycle_name, cpi: +(h.cumulative_ev_cost / h.cumulative_cost).toFixed(3) });
          }
          if (h.spi_cumulative != null) spiMap[h.cycle_name] = h.spi_cumulative;
        });
        if (!points.length) return;
        pepMap[wbs] = { desc: fc.pep_description || fc.name || wbs, points };
        spiMapByPep[wbs] = spiMap;
      });

      const peps = Object.entries(pepMap);
      const allCycleNames = sortedCycleIds.map(id => cycleNameMap[id] ?? `Cycle ${id}`);

      if (!peps.length) {
        _showEmpty('pepCpiEmpty', true);
        document.getElementById('pepCpiPanel').hidden = false;
        if (_charts['pepCpiChart'] && !_charts['pepCpiChart'].isDisposed()) {
          _charts['pepCpiChart'].dispose(); delete _charts['pepCpiChart'];
        }
        return;
      }

      _showEmpty('pepCpiEmpty', false);
      document.getElementById('pepCpiPanel').hidden = false;
      const pcc = _getOrCreateChart('pepCpiChart');
      pcc.setOption(_buildPepCpiOption(peps, allCycleNames, spiMapByPep), true);
      pcc.resize();
    } catch (err) {
      notify(`${_t('msg.err_cpi_pep')}: ${err.message}`, 'error');
    }
  } catch (err) {
    _setChartLoading(['trendsChart'], false);
    notify(`${_t('msg.err_load_trends')}: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Alocação — Matriz Colaborador × Projeto
// ---------------------------------------------------------------------------


let _lastAllocData  = null;
let _allocSortCol   = '__total__';
let _allocSortDir   = -1;

async function _renderAllocationTab() {
  const btn = document.getElementById('loadBtn');
  if (btn) { btn.disabled = true; btn.setAttribute('aria-busy', 'true'); }
  try {
    const cycleIds  = cycleMs.getValues();
    const collabIds = collaboratorMs.getValues();
    const pepCodes  = pepMs.getValues();
    const pepDescs  = pepDescMs.getValues();
    const dateFrom  = document.getElementById('dateFromInput').value;
    const dateTo    = document.getElementById('dateToInput').value;

    const p = new URLSearchParams();
    cycleIds.forEach(id  => p.append('cycle_id', id));
    collabIds.forEach(id => p.append('collaborator_id', id));
    pepCodes.forEach(c   => p.append('pep_wbs', c));
    pepDescs.forEach(d   => p.append('pep_description', d));
    if (dateFrom) p.set('date_from', dateFrom);
    if (dateTo)   p.set('date_to', dateTo);

    const data = await apiFetch(`/api/v2/allocation?${p}`);
    _lastAllocData = data;
    _allocSortCol  = '__total__';
    _allocSortDir  = -1;
    _drawAllocMatrix();
  } catch (err) {
    notify(`${_t('msg.err_generic')}: ${err.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
  }
}

function _drawAllocMatrix() {
  const data     = _lastAllocData;
  const emptyEl  = document.getElementById('allocationEmpty');
  const matrixEl = document.getElementById('allocationMatrix');

  if (!data || !data.length) {
    _showEmpty('allocationEmpty', true);
    matrixEl.innerHTML = '';
    return;
  }
  _showEmpty('allocationEmpty', false);

  const pepLabels = {};
  data.forEach(d => {
    if (d.pep_wbs) pepLabels[d.pep_wbs] = d.pep_description || d.pep_wbs;
  });

  const collabTotals = {};
  const pepTotals    = {};
  const matrix       = {};

  data.forEach(d => {
    const pep = d.pep_wbs || '__none__';
    const val = _evmMode ? d.total_cost : d.total_hours;
    if (!matrix[d.collaborator]) matrix[d.collaborator] = {};
    matrix[d.collaborator][pep] = (matrix[d.collaborator][pep] || 0) + val;
    collabTotals[d.collaborator] = (collabTotals[d.collaborator] || 0) + val;
    pepTotals[pep] = (pepTotals[pep] || 0) + val;
  });

  const sortedPeps = Object.keys(pepTotals).sort((a, b) => pepTotals[b] - pepTotals[a]);
  const grandTotal = Object.values(collabTotals).reduce((a, b) => a + b, 0);
  const maxVal     = Math.max(...Object.values(collabTotals));

  const sortedCollabs = Object.keys(collabTotals).sort((a, b) => {
    const d = _allocSortDir;
    if (_allocSortCol === '__name__')  return d * (a < b ? -1 : a > b ? 1 : 0);
    if (_allocSortCol === '__total__') return d * (collabTotals[a] - collabTotals[b]);
    const va = matrix[a]?.[_allocSortCol] || 0;
    const vb = matrix[b]?.[_allocSortCol] || 0;
    return d * (va - vb);
  });

  const fmt = v => _evmMode
    ? `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
    : `${v.toFixed(1)}h`;

  const cellBg = v => {
    if (!v) return '';
    const ratio = v / maxVal;
    const a = (0.08 + ratio * 0.72).toFixed(2);
    return `background:rgba(14,165,233,${a})`;
  };

  const thCls = key => {
    if (_allocSortCol !== key) return 'sortable';
    return `sortable ${_allocSortDir > 0 ? 'sort-asc' : 'sort-desc'}`;
  };

  let html = '<table class="alloc-matrix data-table"><thead><tr>';
  html += `<th class="${thCls('__name__')}" data-sort-key="__name__">${_t('allocation.collaborator')}</th>`;
  sortedPeps.forEach(pep => {
    const desc  = pep === '__none__' ? '(sem PEP)' : (pepLabels[pep] || pep);
    const headerContent = pep === '__none__'
      ? escHtml(desc)
      : `${escHtml(pep)}<br><span class="alloc-th-desc">${escHtml(desc)}</span>`;
    html += `<th class="${thCls(pep)}" data-sort-key="${pep}" title="${escHtml(pep + ' · ' + desc)}">${headerContent}</th>`;
  });
  html += `<th class="${thCls('__total__')}" data-sort-key="__total__">${_t('allocation.total')}</th></tr></thead><tbody>`;

  sortedCollabs.forEach(collab => {
    html += `<tr><td class="alloc-name">${escHtml(collab)}</td>`;
    sortedPeps.forEach(pep => {
      const v = matrix[collab]?.[pep] || 0;
      html += v
        ? `<td style="${cellBg(v)}">${fmt(v)}</td>`
        : `<td class="alloc-zero">—</td>`;
    });
    html += `<td class="alloc-total">${fmt(collabTotals[collab] || 0)}</td></tr>`;
  });

  html += `<tr class="alloc-footer"><td>${_t('allocation.total')}</td>`;
  sortedPeps.forEach(pep => {
    html += `<td>${fmt(pepTotals[pep] || 0)}</td>`;
  });
  html += `<td class="alloc-total">${fmt(grandTotal)}</td></tr>`;
  html += '</tbody></table>';

  matrixEl.innerHTML = html;

  matrixEl.querySelector('thead').addEventListener('click', e => {
    const th = e.target.closest('th[data-sort-key]');
    if (!th) return;
    const key = th.dataset.sortKey;
    if (_allocSortCol === key) { _allocSortDir *= -1; }
    else { _allocSortCol = key; _allocSortDir = -1; }
    _drawAllocMatrix();
  });
}

// ---------------------------------------------------------------------------
// Previsão de Conclusão (EVM)
// ---------------------------------------------------------------------------

async function _populateForecastPepSelect() {
  const sel = document.getElementById('forecastPepSelect');
  const current = sel.value;
  try {
    const filters = await apiFetch('/api/v2/filters');
    const peps = filters.peps;
    sel.innerHTML = `<option value="">${_t('forecast.select_pep')}</option>` +
      peps.map(p => `<option value="${escHtml(p.code)}">${escHtml(p.code)}${p.descriptions[0] ? ' — ' + escHtml(p.descriptions[0]) : ''}</option>`).join('');
    if (peps.some(p => p.code === current)) sel.value = current;
  } catch (_) { /* non-critical */ }
}

document.getElementById('forecastPepSelect').addEventListener('change', () => {
  if (_activeATab === 'forecast') _renderForecastTab();
});

function _buildForecastKpis(fc) {
  const fmtH = h => `${(+h).toFixed(1)}h`;
  const fmtR = v => _fmtCost(v);

  const pctH = fc.budget_hours
    ? `${Math.min(fc.consumed_hours / fc.budget_hours * 100, 999).toFixed(1)}%`
    : '—';
  const overH = fc.budget_hours != null && fc.consumed_hours > fc.budget_hours;

  const pctC = fc.budget_cost && fc.actual_cost != null
    ? `${Math.min(fc.actual_cost / fc.budget_cost * 100, 999).toFixed(1)}%`
    : '—';
  const overC = fc.budget_cost != null && fc.actual_cost != null && fc.actual_cost > fc.budget_cost;

  const spiVal  = fc.spi  != null ? (+fc.spi).toFixed(2)  : '—';
  const spiCls  = _EVM_COLOR_CARD[fc.spi_color]  || 'neutral';
  const svFmt   = fc.sv   != null ? (fc.sv  >= 0 ? '+' : '') + fmtR(fc.sv)  : '—';
  const svCls   = _EVM_COLOR_CARD[fc.sv_color] || 'neutral';

  const cpiVal  = fc.cpi  != null ? (+fc.cpi).toFixed(2)  : '—';
  const cpiCls  = _EVM_COLOR_CARD[fc.cpi_color]  || 'neutral';
  const cvFmt   = fc.cv   != null ? (fc.cv  >= 0 ? '+' : '') + fmtR(fc.cv)  : '—';
  const cvCls   = _EVM_COLOR_CARD[fc.cv_color] || 'neutral';
  const tcpiVal = fc.tcpi != null ? (+fc.tcpi).toFixed(2) : '—';
  const tcpiCls = _EVM_COLOR_CARD[fc.tcpi_color] || 'neutral';
  const vacFmt  = fc.vac  != null ? (fc.vac >= 0 ? '+' : '') + fmtR(fc.vac) : '—';
  const vacCls  = _EVM_COLOR_CARD[fc.vac_color]  || (fc.vac  == null ? 'neutral' : fc.vac >= 0 ? 'green' : 'red');

  // EAC sublabel: method · schedule divergence (>5%) · uncertainty range
  const eacMethodLabel = fc.eac_method === 'cpi_spi' ? 'CPI+SPI' : fc.eac_method === 'cpi' ? 'CPI' : null;
  const eacSchedulePart = (fc.eac_schedule != null && fc.eac != null && Math.abs(fc.eac_schedule - fc.eac) / fc.eac > 0.05)
    ? `agenda: ${fmtR(fc.eac_schedule)}`
    : null;
  const eacRangePart = (fc.eac_low != null && fc.eac_high != null)
    ? `${fmtR(fc.eac_low)} — ${fmtR(fc.eac_high)}`
    : null;
  const eacSublbl = [eacMethodLabel, eacSchedulePart, eacRangePart].filter(Boolean).join(' · ') || null;

  // Completion cycle range sublabel (R-12)
  const completionRangeSublbl = (fc.est_cycles_optimistic != null && fc.est_cycles_pessimistic != null)
    ? `+${fc.est_cycles_optimistic} a +${fc.est_cycles_pessimistic} ciclos`
    : null;

  const completionVal = fc.is_closed && fc.completed_on
    ? _fmtDateBR(fc.completed_on)
    : (fc.estimated_completion_cycle
      || (fc.estimated_cycles_to_complete != null ? `+${fc.estimated_cycles_to_complete} ciclos` : '—'));
  const completionLbl = fc.is_closed ? _t('forecast.completed_on') : _t('forecast.completion');

  const row1 = [
    { val: fmtH(fc.consumed_hours),                                                    lbl: _t('forecast.consumed'),          cls: 'blue'                    },
    { val: fc.remaining_hours != null ? fmtH(Math.max(0, fc.remaining_hours)) : '—',  lbl: _t('forecast.remaining'),         cls: overH ? 'red' : 'neutral' },
    { val: pctH,                                                                        lbl: _t('forecast.utilization_hours'), cls: overH ? 'red' : 'green'   },
    { val: spiVal,                                                                      lbl: 'SPI',  cls: spiCls,  evm: 'SPI',  sublbl: fc.spi_label  || null },
    { val: svFmt,                                                                       lbl: 'SV',   cls: svCls,   evm: 'SV',   sublbl: fc.sv_label  || null },
    { val: escHtml(String(completionVal)),                                              lbl: completionLbl, cls: 'violet', sublbl: completionRangeSublbl      },
    { val: tcpiVal,                                                                     lbl: 'TCPI', cls: tcpiCls, evm: 'TCPI', sublbl: fc.tcpi_label || null },
  ].map(_mkStatCard).join('');

  const row2 = [
    { val: fc.actual_cost != null ? fmtR(fc.actual_cost) : '—',                        lbl: 'AC',                            cls: 'blue',    evm: 'AC'      },
    { val: fc.remaining_cost != null ? fmtR(Math.max(0, fc.remaining_cost)) : '—',    lbl: 'ETC',                           cls: 'neutral', evm: 'ETC'     },
    { val: pctC,                                                                        lbl: _t('forecast.utilization_cost'), cls: overC ? 'red' : 'green'   },
    { val: cpiVal,                                                                      lbl: 'CPI',  cls: cpiCls,  evm: 'CPI',  sublbl: fc.cpi_label  || null },
    { val: cvFmt,                                                                       lbl: 'CV',   cls: cvCls,   evm: 'CV',   sublbl: fc.cv_label  || null },
    { val: fc.eac != null ? fmtR(fc.eac) : '—',                                        lbl: 'EAC',  cls: 'neutral', evm: 'EAC', sublbl: eacSublbl           },
    { val: vacFmt,                                                                      lbl: 'VAC',  cls: vacCls,  evm: 'VAC',  sublbl: fc.vac_label  || null },
  ].map(_mkStatCard).join('');

  // F3 — Earned Schedule row (only when ES data is available)
  const esRow = (fc.es != null || fc.spi_t != null || fc.sv_t != null || fc.ieac_t != null) ? (() => {
    const esVal    = fc.es    != null ? (+fc.es).toFixed(2)    : '—';
    const spiTVal  = fc.spi_t != null ? (+fc.spi_t).toFixed(2) : '—';
    const spiTCls  = fc.spi_t == null ? 'neutral' : fc.spi_t >= 1 ? 'green' : fc.spi_t >= 0.8 ? 'amber' : 'red';
    const svTFmt   = fc.sv_t  != null ? (fc.sv_t >= 0 ? '+' : '') + (+fc.sv_t).toFixed(2) + ' ciclos' : '—';
    const svTCls   = fc.sv_t  == null ? 'neutral' : fc.sv_t >= 0 ? 'green' : 'red';
    const ieacTVal = fc.ieac_t != null ? (+fc.ieac_t).toFixed(1) + ' ciclos' : '—';
    const atVal    = fc.actual_time_cycles != null ? fc.actual_time_cycles + ' ciclos' : '—';
    const pdVal    = fc.planned_duration_cycles != null ? fc.planned_duration_cycles + ' ciclos' : '—';
    const cards = [
      { val: esVal,    lbl: 'ES',      cls: 'blue',    evm: 'ES',    sublbl: `${_t('forecast.es.at')} ${atVal}` },
      { val: spiTVal,  lbl: 'SPI(t)',  cls: spiTCls,   evm: 'SPIt'  },
      { val: svTFmt,   lbl: 'SV(t)',   cls: svTCls,    evm: 'SVt'   },
      { val: ieacTVal, lbl: 'IEAC(t)', cls: 'neutral', evm: 'IEACt', sublbl: `${_t('forecast.pd')} ${pdVal}` },
    ].map(_mkStatCard).join('');
    return `<div class="stats-row">${cards}</div>`;
  })() : '';

  return `<div class="stats-row">${row1}</div><div class="stats-row">${row2}</div>${esRow}`;
}

// _buildForecastOption — moved to charts/forecast.js

function _forecastInfoStat(lbl, val) {
  return `<div style="display:flex;flex-direction:column;gap:.15rem">
    <span style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;letter-spacing:.04em">${escHtml(lbl)}</span>
    <span style="font-size:.88rem;font-weight:600;color:var(--text)">${val}</span>
  </div>`;
}

function _renderForecastProjectInfo(fc, proj) {
  const el = document.getElementById('forecastProjectInfo');
  if (!el) return;

  const hh = fc.health_hours || 'no_budget';
  const hc = fc.health_cost  || 'no_budget';
  const semColor = _healthToSemColor(hh, hc);
  const semLabel  = _t(`sem.${semColor}`);

  const budgetParts = [];
  if (fc.budget_hours != null) budgetParts.push(`${fc.budget_hours.toFixed(1)}h`);
  if (fc.budget_cost  != null) budgetParts.push(_fmtCost(fc.budget_cost));
  const budgetStr = budgetParts.length ? budgetParts.join(' / ') : _t('forecast.info.no_budget');

  const dotHtml = `<span class="sem-dot ${semColor}" style="display:inline-block;vertical-align:middle;margin-right:.35rem"></span>`;

  let baselineStr;
  if (fc.using_baseline && fc.baseline_locked_at) {
    const dt = _fmtDateShort(fc.baseline_locked_at);
    const lbl = fc.baseline_label ? ` — ${escHtml(fc.baseline_label)}` : '';
    baselineStr = `📍 ${_t('baseline.active')}${lbl} · ${_t('baseline.locked_at')} ${dt}`;
  } else if (!fc.using_baseline && fc.budget_cost != null) {
    baselineStr = `⚠️ ${_t('baseline.warning')}`;
  } else {
    baselineStr = escHtml(_t('forecast.info.baseline_none'));
  }

  const dateChips = [];
  if (fc.start_date)       dateChips.push(`▸ ${_t('forecast.info.start')}: ${_fmtDateBR(fc.start_date)}`);
  if (fc.planned_end_date) dateChips.push(`→ ${_t('forecast.info.planned_end')}: ${_fmtDateBR(fc.planned_end_date)}`);
  if (fc.completed_on)     dateChips.push(`✓ ${_t('forecast.info.completed')}: ${_fmtDateBR(fc.completed_on)}`);

  el.innerHTML =
    _forecastInfoStat(_t('forecast.info.project'),
      escHtml(proj?.name || _t('forecast.info.no_name'))) +
    _forecastInfoStat(_t('forecast.info.manager'),
      escHtml(proj?.manager || _t('forecast.info.no_manager'))) +
    _forecastInfoStat(_t('forecast.info.budget'), budgetStr) +
    (dateChips.length ? _forecastInfoStat(_t('projects.th.dates'), escHtml(dateChips.join('  '))) : '') +
    _forecastInfoStat(_t('forecast.info.status'), `${dotHtml}${escHtml(semLabel)}`) +
    _forecastInfoStat(_t('forecast.info.baseline'), baselineStr);
  el.hidden = false;
}

// _buildBurnUpOption — moved to charts/forecast.js

async function _renderForecastTab() {
  await _populateForecastPepSelect();
  const pep      = document.getElementById('forecastPepSelect').value;
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;

  const kpisEl  = document.getElementById('forecastKpis');
  const emptyEl = document.getElementById('forecastEmpty');

  const infoEl = document.getElementById('forecastProjectInfo');

  if (!pep) {
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    if (infoEl) infoEl.hidden = true;
    document.getElementById('forecastAllocCard').hidden = true;
    document.getElementById('forecastAllocCostCard').hidden = true;
    _disposeTabCharts('forecast');
    return;
  }

  const p = new URLSearchParams({ pep_wbs: pep });
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  _setChartLoading(['forecastChart', 'burnUpChart'], true);
  try {
    const [fc, projects] = await Promise.all([
      apiFetch(`/api/v2/forecast?${p}`),
      apiFetch('/api/projects'),
    ]);
    _setChartLoading(['forecastChart', 'burnUpChart'], false);
    const proj = projects.find(pr => pr.pep_wbs === pep) || null;
    _showEmpty('forecastEmpty', false);
    kpisEl.hidden = false;
    kpisEl.innerHTML = _buildForecastKpis(fc);
    _renderForecastProjectInfo(fc, proj);
    const badge = document.getElementById('forecastPhysicalBadge');
    if (badge) {
      badge.hidden = !fc.uses_physical_pct;
      const span = badge.querySelector('span');
      if (span && fc.last_physical_pct != null) {
        span.title = _t('forecast.physical_badge_title');
        span.textContent = `${_t('forecast.physical_badge')} — ${(fc.last_physical_pct * 100).toFixed(0)}%`;
      }
    }
    _currentForecastPep = pep;
    _fcAvgVelocity = fc.avg_hours_per_cycle || null;
    if (proj) _loadForecastSimulation(proj.id);
    else { document.getElementById('whatIfCard').hidden = true; document.getElementById('monteCarloCard').hidden = true; }
    try {
      const chart = _getOrCreateChart('forecastChart');
      chart.setOption(_buildForecastOption(fc), true);
      chart.resize();
    } catch (_) { /* chart lib may not be loaded in offline envs */ }
    _renderVelocitySparkline(fc);
    _renderBurnUpChart(fc);
    await _renderForecastAllocTable(pep, dateFrom, dateTo);
    await _renderForecastAllocCostTable(pep, dateFrom, dateTo);
  } catch (err) {
    _setChartLoading(['forecastChart', 'burnUpChart'], false);
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    if (infoEl) infoEl.hidden = true;
    document.getElementById('burnUpCard').hidden = true;
    document.getElementById('forecastAllocCard').hidden = true;
    document.getElementById('forecastAllocCostCard').hidden = true;
    _disposeTabCharts('forecast');
    if (!err.message?.includes('404')) notify(`${_t('msg.err_generic')}: ${err.message}`, 'error');
  }
}

function _renderVelocitySparkline(fc) {
  const el = document.getElementById('velocitySparklineChart');
  if (!el) return;
  const history = (fc.history || []).filter(h => h.period_hours > 0);
  if (history.length < 2) { el.hidden = true; return; }
  el.hidden = false;

  const labels = history.map(h => h.cycle_name);
  const vals   = history.map(h => h.period_hours);
  const last3  = vals.slice(-3);
  const avg3   = last3.reduce((s, v) => s + v, 0) / last3.length;

  const chart = _getOrCreateChart('velocitySparklineChart');
  chart.setOption({
    grid: { top: 18, bottom: 28, left: 40, right: 12 },
    tooltip: { trigger: 'axis', formatter: p => `${p[0].name}<br/>${p[0].value.toFixed(1)} h` },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 9, interval: 'auto' } },
    yAxis: { type: 'value', axisLabel: { fontSize: 9, formatter: v => v + 'h' } },
    series: [
      {
        type: 'bar', data: vals, name: _t('sim.velocity_base'),
        itemStyle: { color: 'var(--color-neutral, #6b7280)' },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: 'var(--color-danger, #ef4444)', width: 1.5, type: 'dashed' },
          label: { formatter: `${_t('forecast.avg3')}: {c}h`, fontSize: 9 },
          data: [{ yAxis: +avg3.toFixed(1) }],
        },
      },
    ],
  }, true);
  chart.resize();
}

function _renderBurnUpChart(fc) {
  const card = document.getElementById('burnUpCard');
  const history = fc.history || [];
  const hasEV = history.some(h => h.cumulative_ev_cost != null);
  if (!hasEV) {
    card.hidden = true;
    if (_charts['burnUpChart'] && !_charts['burnUpChart'].isDisposed()) {
      _charts['burnUpChart'].dispose();
      delete _charts['burnUpChart'];
    }
    return;
  }
  card.hidden = false;
  try {
    const chart = _getOrCreateChart('burnUpChart');
    chart.setOption(_buildBurnUpOption(fc), true);
    chart.resize();
  } catch (_) {}
}

// ── F11: What-If + F4: Monte Carlo ───────────────────────────────────────────

let _simProjectId = null;
let _fcAvgVelocity = null;

async function _loadForecastSimulation(projectId) {
  _simProjectId = projectId;
  const wiCard = document.getElementById('whatIfCard');
  const mcCard = document.getElementById('monteCarloCard');
  if (!wiCard || !mcCard) return;
  wiCard.hidden = false;
  mcCard.hidden = false;
  // reset result areas
  document.getElementById('whatIfResult').innerHTML = '';
  document.getElementById('mcResult').innerHTML = `<span class="hint">${_t('loading')}</span>`;
  // B4: show base velocity hint so user knows what 1× means
  const hint = document.getElementById('whatIfVelocityHint');
  if (hint) {
    hint.textContent = _fcAvgVelocity != null
      ? `${_t('sim.velocity_base')} ${_fcAvgVelocity.toFixed(1)} h/ciclo`
      : '';
  }
  // auto-load monte carlo
  _runMonteCarlo();
}

async function _runWhatIf() {
  if (!_simProjectId) return;
  const mult  = parseFloat(document.getElementById('whatIfMultiplier').value)  || 1.0;
  const extra = parseFloat(document.getElementById('whatIfExtraHours').value)   || 0.0;
  const btn   = document.getElementById('whatIfRunBtn');
  btn.disabled = true;
  const burnEl = document.getElementById('whatIfBurnUpChart');
  try {
    const r = await apiFetchJSON(`/api/v2/projects/${_simProjectId}/simulate`, 'POST', {
      velocity_multiplier: mult, extra_hours_per_cycle: extra,
    });
    const el = document.getElementById('whatIfResult');
    const ctc = r.cycles_to_complete != null ? `${r.cycles_to_complete} ciclos` : '—';
    const eac = r.projected_eac_cost != null ? _fmtCost(r.projected_eac_cost) : '—';
    const cards = [
      { val: `${r.avg_velocity.toFixed(1)}h`, lbl: _t('sim.avg_velocity'),      cls: 'neutral', evm: 'SimAvgVel'  },
      { val: `${r.sim_velocity.toFixed(1)}h`, lbl: _t('sim.sim_velocity'),      cls: 'blue',    evm: 'SimVelocity'},
      { val: ctc,                              lbl: _t('sim.cycles_to_complete'), cls: 'violet',  evm: 'SimCycles'  },
      { val: eac,                              lbl: _t('sim.projected_eac'),      cls: 'neutral', evm: 'SimEAC'     },
    ].map(_mkStatCard).join('');
    el.innerHTML = `<div class="stats-row" style="margin-top:.5rem">${cards}</div>`;

    // Burn-up projection chart
    if (burnEl && r.burn_up_projected?.length) {
      const projected = [r.consumed_hours, ...r.burn_up_projected];
      const cats = ['Atual', ...r.burn_up_projected.map((_, i) => `C+${i + 1}`)];
      const budget = r.budget_hours;
      burnEl.hidden = false;
      const wc = _getOrCreateChart('whatIfBurnUpChart');
      wc.setOption({
        ..._chartDefaults(),
        grid: { top: 36, right: '4%', bottom: 32, left: '2%', containLabel: true },
        legend: {
          data: [_t('sim.burnup.projected'), ...(budget != null ? [_t('sim.burnup.budget')] : [])],
          top: 4, left: 'center',
          textStyle: { color: _cssVar('--text'), fontSize: 11 },
          itemGap: 20, itemWidth: 14, itemHeight: 8,
        },
        tooltip: { trigger: 'axis', ..._chartDefaults().tooltip,
          formatter: params => {
            let html = `<b>${params[0]?.axisValue}</b><br>`;
            params.forEach(p => p.value != null && (html += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br>`));
            return html;
          },
        },
        xAxis: { type: 'category', data: cats,
          axisLabel: { color: _cssVar('--text-3'), fontSize: 10 }, axisTick: { show: false } },
        yAxis: { type: 'value', name: 'h',
          nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          axisLabel: { color: _cssVar('--text-3'), fontSize: 10, formatter: v => `${v}h` },
          splitLine: { lineStyle: { color: _cssVar('--surface') } } },
        series: [
          { name: _t('sim.burnup.projected'), type: 'line', data: projected,
            lineStyle: { color: _cssVar('--primary'), width: 2.5 },
            itemStyle: { color: _cssVar('--primary') },
            symbol: 'circle', symbolSize: 5, connectNulls: true,
            areaStyle: { color: (_cssVar('--primary') || '#6366f1') + '22' },
          },
          ...(budget != null ? [{
            name: _t('sim.burnup.budget'), type: 'line', data: cats.map(() => budget),
            symbol: 'none', lineStyle: { color: _cssVar('--amber'), width: 1.5, type: 'dashed' },
            itemStyle: { color: _cssVar('--amber') },
          }] : []),
        ],
      }, true);
      wc.resize();
    } else if (burnEl) {
      burnEl.hidden = true;
    }
  } catch (e) {
    document.getElementById('whatIfResult').innerHTML = `<p class="hint" style="color:var(--error-text)">${_t('msg.err_generic')}</p>`;
    if (burnEl) burnEl.hidden = true;
  } finally {
    btn.disabled = false;
  }
}

async function _runMonteCarlo() {
  if (!_simProjectId) return;
  const el    = document.getElementById('mcResult');
  const histEl = document.getElementById('mcHistogram');
  el.innerHTML = `<span class="hint">${_t('loading')}</span>`;
  if (histEl) histEl.hidden = true;
  try {
    const r = await apiFetch(`/api/v2/projects/${_simProjectId}/monte-carlo?iterations=1000`);
    if (r.error === 'insufficient_data') {
      el.innerHTML = `<p class="hint">${_t('mc.insufficient_data')}</p>`;
      return;
    }
    const mcCards = [
      { val: `${r.p10 ?? '—'} ciclos`,                   lbl: `P10 ${_t('mc.optimistic')}`, cls: 'green',   evm: 'MCP10'     },
      { val: `${r.p50 ?? '—'} ciclos`,                   lbl: `P50 ${_t('mc.median')}`,     cls: 'blue',    evm: 'MCP50'     },
      { val: `${r.p90 ?? '—'} ciclos`,                   lbl: `P90 ${_t('mc.pessimistic')}`,cls: 'red',     evm: 'MCP90'     },
      { val: `${r.mean_velocity?.toFixed(1) ?? '—'}h`,   lbl: _t('mc.mean_velocity'),        cls: 'neutral', evm: 'MCMeanVel' },
    ].map(_mkStatCard).join('');
    el.innerHTML = `<div class="stats-row" style="margin-top:.5rem">${mcCards}</div>`;

    // Histogram
    if (histEl && r.histogram?.length) {
      histEl.hidden = false;
      const hc = _getOrCreateChart('mcHistogramChart');
      const cats  = r.histogram.map(b => String(b.cycle));
      const freqs = r.histogram.map(b => b.count);
      hc.setOption({
        ..._chartDefaults(),
        grid: { top: 36, right: '4%', bottom: 40, left: '2%', containLabel: true },
        legend: { show: false },
        tooltip: { trigger: 'axis', ..._chartDefaults().tooltip,
          formatter: params => `<b>${params[0].axisValue} ${_t('sim.cycles_to_complete')}</b><br>${params[0].marker}${_t('mc.histogram.frequency')}: <b>${params[0].value}</b>`,
        },
        xAxis: { type: 'category', data: cats,
          name: _t('sim.cycles_to_complete'), nameLocation: 'middle', nameGap: 28,
          nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          axisLabel: { color: _cssVar('--text-3'), fontSize: 10 },
          axisTick: { alignWithLabel: true },
        },
        yAxis: { type: 'value', name: _t('mc.histogram.frequency'),
          nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          axisLabel: { color: _cssVar('--text-3'), fontSize: 10 },
          splitLine: { lineStyle: { color: _cssVar('--surface') } },
        },
        series: [{
          type: 'bar', data: freqs, barMaxWidth: 36,
          itemStyle: { color: _cssVar('--primary') },
          markLine: {
            symbol: 'none',
            lineStyle: { type: 'dashed', width: 1.5 },
            label: { fontSize: 10 },
            data: [
              ...(r.p10 != null ? [{ xAxis: String(r.p10), lineStyle: { color: _cssVar('--green') }, label: { formatter: 'P10', color: _cssVar('--green') } }] : []),
              ...(r.p50 != null ? [{ xAxis: String(r.p50), lineStyle: { color: _cssVar('--primary') }, label: { formatter: 'P50', color: _cssVar('--primary') } }] : []),
              ...(r.p90 != null ? [{ xAxis: String(r.p90), lineStyle: { color: _cssVar('--red') }, label: { formatter: 'P90', color: _cssVar('--red') } }] : []),
            ],
          },
        }],
      }, true);
      hc.resize();
    }
  } catch (e) {
    el.innerHTML = `<p class="hint" style="color:var(--error-text)">${_t('msg.err_generic')}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Forecast allocation table (hours heatmap per collaborator, single PEP)
// ---------------------------------------------------------------------------

let _filterExpanded = true;
document.getElementById('filterToggle').addEventListener('click', () => {
  _filterExpanded = !_filterExpanded;
  document.getElementById('filterBody').style.display = _filterExpanded ? '' : 'none';
  document.getElementById('filterChevron').style.transform = _filterExpanded ? '' : 'rotate(-90deg)';
});

let _forecastAllocExpanded = true;
document.getElementById('forecastAllocToggle').addEventListener('click', () => {
  _forecastAllocExpanded = !_forecastAllocExpanded;
  document.getElementById('forecastAllocBody').style.display = _forecastAllocExpanded ? '' : 'none';
  const ch = document.getElementById('forecastAllocChevron');
  ch.style.transform = _forecastAllocExpanded ? '' : 'rotate(-90deg)';
});

let _forecastAllocCostExpanded = true;
document.getElementById('forecastAllocCostToggle').addEventListener('click', () => {
  _forecastAllocCostExpanded = !_forecastAllocCostExpanded;
  document.getElementById('forecastAllocCostBody').style.display = _forecastAllocCostExpanded ? '' : 'none';
  const ch = document.getElementById('forecastAllocCostChevron');
  ch.style.transform = _forecastAllocCostExpanded ? '' : 'rotate(-90deg)';
});

async function _renderForecastAllocTable(pep, dateFrom, dateTo) {
  const card = document.getElementById('forecastAllocCard');
  const tbl  = document.getElementById('forecastAllocTable');
  if (!pep) { card.hidden = true; return; }

  try {
    const p = new URLSearchParams({ pep_wbs: pep });
    if (dateFrom) p.set('date_from', dateFrom);
    if (dateTo)   p.set('date_to',   dateTo);
    const data = await apiFetch(`/api/v2/allocation?${p}`);

    if (!data.length) { card.hidden = true; return; }
    card.hidden = false;

    // Aggregate per collaborator (multiple pep_description rows possible for same pep_wbs)
    const byCollab = {};
    data.forEach(d => {
      if (!byCollab[d.collaborator]) byCollab[d.collaborator] = { normal: 0, extra: 0, standby: 0, total: 0 };
      byCollab[d.collaborator].normal  += d.normal_hours  || 0;
      byCollab[d.collaborator].extra   += d.extra_hours   || 0;
      byCollab[d.collaborator].standby += d.standby_hours || 0;
      byCollab[d.collaborator].total   += d.total_hours   || 0;
    });

    const collabs = Object.entries(byCollab).sort((a, b) => b[1].total - a[1].total);

    // Independent max per column for meaningful per-type heatmap
    const maxNormal  = Math.max(...collabs.map(([, v]) => v.normal),  0.001);
    const maxExtra   = Math.max(...collabs.map(([, v]) => v.extra),   0.001);
    const maxStandby = Math.max(...collabs.map(([, v]) => v.standby), 0.001);

    const heat = (v, max) => {
      if (!v) return '';
      const a = (0.08 + (v / max) * 0.72).toFixed(2);
      return `style="background:rgba(14,165,233,${a})"`;
    };
    const fmt = v => v > 0 ? `${v.toFixed(1)}h` : '—';

    const totNormal  = collabs.reduce((s, [, v]) => s + v.normal,  0);
    const totExtra   = collabs.reduce((s, [, v]) => s + v.extra,   0);
    const totStandby = collabs.reduce((s, [, v]) => s + v.standby, 0);
    const totTotal   = collabs.reduce((s, [, v]) => s + v.total,   0);

    let html = `<table class="data-table alloc-matrix" style="width:100%"><thead><tr>
      <th>${_t('forecast.alloc.collaborator')}</th>
      <th>${_t('forecast.alloc.normal')}</th>
      <th>${_t('forecast.alloc.extra')}</th>
      <th>${_t('forecast.alloc.standby')}</th>
      <th class="alloc-total">${_t('forecast.alloc.total')}</th>
    </tr></thead><tbody>`;

    collabs.forEach(([name, v]) => {
      html += `<tr>
        <td class="alloc-name">${escHtml(name)}</td>
        <td ${heat(v.normal,  maxNormal)}>${fmt(v.normal)}</td>
        <td ${heat(v.extra,   maxExtra)}>${fmt(v.extra)}</td>
        <td ${heat(v.standby, maxStandby)}>${fmt(v.standby)}</td>
        <td class="alloc-total">${fmt(v.total)}</td>
      </tr>`;
    });

    html += `<tr class="alloc-footer">
      <td>${_t('forecast.alloc.total')}</td>
      <td>${fmt(totNormal)}</td>
      <td>${fmt(totExtra)}</td>
      <td>${fmt(totStandby)}</td>
      <td class="alloc-total">${fmt(totTotal)}</td>
    </tr></tbody></table>`;

    tbl.innerHTML = html;
  } catch (_) {
    card.hidden = true;
  }
}

async function _renderForecastAllocCostTable(pep, dateFrom, dateTo) {
  const card = document.getElementById('forecastAllocCostCard');
  const tbl  = document.getElementById('forecastAllocCostTable');
  if (!pep) { card.hidden = true; return; }

  try {
    const p = new URLSearchParams({ pep_wbs: pep });
    if (dateFrom) p.set('date_from', dateFrom);
    if (dateTo)   p.set('date_to',   dateTo);
    const data = await apiFetch(`/api/v2/allocation?${p}`);

    if (!data.length) { card.hidden = true; return; }
    card.hidden = false;

    const byCollab = {};
    data.forEach(d => {
      if (!byCollab[d.collaborator]) byCollab[d.collaborator] = { normal: 0, extra: 0, standby: 0, total: 0 };
      byCollab[d.collaborator].normal  += d.normal_cost  || 0;
      byCollab[d.collaborator].extra   += d.extra_cost   || 0;
      byCollab[d.collaborator].standby += d.standby_cost || 0;
      byCollab[d.collaborator].total   += d.total_cost   || 0;
    });

    const collabs = Object.entries(byCollab).sort((a, b) => b[1].total - a[1].total);

    const maxNormal  = Math.max(...collabs.map(([, v]) => v.normal),  0.001);
    const maxExtra   = Math.max(...collabs.map(([, v]) => v.extra),   0.001);
    const maxStandby = Math.max(...collabs.map(([, v]) => v.standby), 0.001);

    const heat = (v, max) => {
      if (!v) return '';
      const a = (0.08 + (v / max) * 0.72).toFixed(2);
      return `style="background:rgba(14,165,233,${a})"`;
    };
    const fmt = v => v > 0 ? _fmtCost(v) : '—';

    const totNormal  = collabs.reduce((s, [, v]) => s + v.normal,  0);
    const totExtra   = collabs.reduce((s, [, v]) => s + v.extra,   0);
    const totStandby = collabs.reduce((s, [, v]) => s + v.standby, 0);
    const totTotal   = collabs.reduce((s, [, v]) => s + v.total,   0);

    let html = `<table class="data-table alloc-matrix" style="width:100%"><thead><tr>
      <th>${_t('forecast.alloc.collaborator')}</th>
      <th>${_t('forecast.alloc_cost.normal')}</th>
      <th>${_t('forecast.alloc_cost.extra')}</th>
      <th>${_t('forecast.alloc_cost.standby')}</th>
      <th class="alloc-total">${_t('forecast.alloc_cost.total')}</th>
    </tr></thead><tbody>`;

    collabs.forEach(([name, v]) => {
      html += `<tr>
        <td class="alloc-name">${escHtml(name)}</td>
        <td ${heat(v.normal,  maxNormal)}>${fmt(v.normal)}</td>
        <td ${heat(v.extra,   maxExtra)}>${fmt(v.extra)}</td>
        <td ${heat(v.standby, maxStandby)}>${fmt(v.standby)}</td>
        <td class="alloc-total">${fmt(v.total)}</td>
      </tr>`;
    });

    html += `<tr class="alloc-footer">
      <td>${_t('forecast.alloc_cost.total')}</td>
      <td>${fmt(totNormal)}</td>
      <td>${fmt(totExtra)}</td>
      <td>${fmt(totStandby)}</td>
      <td class="alloc-total">${fmt(totTotal)}</td>
    </tr></tbody></table>`;

    tbl.innerHTML = html;
  } catch (_) {
    card.hidden = true;
  }
}

// ---------------------------------------------------------------------------
// Plan management (ProjectCyclePlan)
// ---------------------------------------------------------------------------
let _currentForecastPep = null;
let _planProjectId = null;

async function _renderPlanTable() {
  const tbody = document.getElementById('planBody');
  if (!_planProjectId) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.panel.select_hint')}</td></tr>`;
    return;
  }
  try {
    const plans = await apiFetch(`/api/projects/${_planProjectId}/plans`);
    if (!plans.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.no_plans')}</td></tr>`;
      return;
    }
    tbody.innerHTML = plans.map(pl => {
      const costStr = pl.planned_cost != null
        ? pl.planned_cost.toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2})
        : '<span style="color:var(--text-3)">—</span>';
      const physStr = pl.physical_pct != null
        ? `<span style="color:var(--color-accent);font-weight:600">${(pl.physical_pct * 100).toFixed(0)}%</span>`
        : '<span style="color:var(--text-3)">—</span>';
      return `<tr>
        <td>${escHtml(pl.cycle_name)}</td>
        <td style="text-align:right">${(+pl.planned_hours).toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1})}</td>
        <td style="text-align:right">${costStr}</td>
        <td style="text-align:right">${physStr}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-secondary btn-sm" onclick="editPlan(${pl.cycle_id}, ${escHtml(JSON.stringify(pl.cycle_name))}, ${pl.planned_hours}, ${pl.planned_cost ?? 'null'})" style="margin-right:.25rem">${_t('btn.edit')}</button>
          <button class="btn btn-danger btn-sm" onclick="deletePlan(${pl.cycle_id})">${_t('btn.delete')}</button>
        </td>
      </tr>`;
    }).join('');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

function deletePlan(cycle_id) {
  if (!_planProjectId) return;
  confirmDialog(_t('confirm.remove_baseline'), async () => {
    try {
      await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${cycle_id}`, 'DELETE');
      await _renderPlanTable();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

let _editPlanCycleId = null;

function editPlan(cycle_id, cycle_name, planned_hours, planned_cost) {
  _editPlanCycleId = cycle_id;
  document.getElementById('editPlanCycleName').textContent = cycle_name;
  document.getElementById('editPlanHours').value = planned_hours;
  document.getElementById('editPlanCost').value  = planned_cost != null ? planned_cost : '';
  document.getElementById('editPlanError').textContent = '';
  openModal('editPlanModal');
}

document.getElementById('editPlanModalClose').addEventListener('click', () => closeModal('editPlanModal'));
document.getElementById('editPlanCancelBtn').addEventListener('click', () => closeModal('editPlanModal'));

document.getElementById('editPlanSaveBtn').addEventListener('click', async () => {
  if (!_planProjectId || !_editPlanCycleId) return;
  const errEl = document.getElementById('editPlanError');
  const hours = parseFloat(document.getElementById('editPlanHours').value);
  const rawCost = document.getElementById('editPlanCost').value.trim();
  const cost = rawCost === '' ? null : parseFloat(rawCost);
  if (isNaN(hours) || hours < 0) { errEl.textContent = _t('msg.valid_hours'); return; }
  if (cost !== null && (isNaN(cost) || cost < 0)) { errEl.textContent = 'Custo inválido.'; return; }
  try {
    await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${_editPlanCycleId}`, 'PUT',
      { cycle_id: _editPlanCycleId, planned_hours: hours, planned_cost: cost });
    closeModal('editPlanModal');
    await _renderPlanTable();
  } catch (e) { errEl.textContent = `${_t('msg.err_generic')}: ${e.message}`; }
});

let _addPlanAvailableCycles = [];

function _addPlanRow(available) {
  const container = document.getElementById('addPlanRows');
  const wrapper = document.createElement('div');
  wrapper.style.cssText = 'display:flex;flex-direction:column;gap:.3rem;padding:.5rem;border:1px solid var(--border);border-radius:.4rem';

  const topRow = document.createElement('div');
  topRow.style.cssText = 'display:flex;gap:.5rem;align-items:center';
  const sel = document.createElement('select');
  sel.className = 'form-select';
  sel.style.cssText = 'flex:1;height:2rem;font-size:.82rem';
  sel.innerHTML = `<option value="">— ${_t('plan.select_cycle')} —</option>` +
    available.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  const rm = document.createElement('button');
  rm.type = 'button';
  rm.className = 'btn btn-secondary btn-sm';
  rm.textContent = '✕';
  rm.onclick = () => wrapper.remove();
  topRow.append(sel, rm);

  const bottomRow = document.createElement('div');
  bottomRow.style.cssText = 'display:flex;gap:.5rem';
  const inpH = document.createElement('input');
  inpH.type = 'number'; inpH.min = '0'; inpH.step = '0.5';
  inpH.placeholder = _t('plan.th.hours');
  inpH.style.cssText = 'flex:1;height:2rem;font-size:.82rem';
  const inpC = document.createElement('input');
  inpC.type = 'number'; inpC.min = '0'; inpC.step = '0.01';
  inpC.placeholder = _t('plan.th.cost') + ' (opcional)';
  inpC.style.cssText = 'flex:1;height:2rem;font-size:.82rem';
  bottomRow.append(inpH, inpC);

  wrapper.append(topRow, bottomRow);
  container.appendChild(wrapper);
}

document.getElementById('addPlanRowBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const [allCycles, existingPlans] = await Promise.all([
      apiFetch('/api/cycles?include_archived=false'),
      apiFetch(`/api/projects/${_planProjectId}/plans`),
    ]);
    const plannedCycleIds = new Set(existingPlans.map(p => p.cycle_id));
    _addPlanAvailableCycles = allCycles.filter(c => !plannedCycleIds.has(c.id));
    if (!_addPlanAvailableCycles.length) { notify(_t('msg.all_baseline_set'), 'info'); return; }
    document.getElementById('addPlanRows').innerHTML = '';
    document.getElementById('addPlanError').textContent = '';
    _addPlanRow(_addPlanAvailableCycles);
    openModal('addPlanModal');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
});

// ---------------------------------------------------------------------------
// Physical Progress modal
// ---------------------------------------------------------------------------
document.getElementById('physicalProgressBtn').addEventListener('click', async () => {
  if (!_planProjectId) { notify(_t('msg.err_generic'), 'info'); return; }
  try {
    const plans = await apiFetch(`/api/projects/${_planProjectId}/plans`);
    if (!plans.length) { notify(_t('plan.no_plans'), 'info'); return; }
    const tbody = document.getElementById('physicalProgressBody');
    tbody.innerHTML = plans.map(pl => {
      const pctVal = pl.physical_pct != null ? (pl.physical_pct * 100).toFixed(0) : '';
      const noteVal = escHtml(pl.physical_note || '');
      const hStr = (+pl.planned_hours).toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1}) + 'h';
      const cStr = pl.planned_cost != null
        ? ' / R$ ' + pl.planned_cost.toLocaleString('pt-BR', {minimumFractionDigits:2})
        : '';
      return `<tr data-cycle-id="${pl.cycle_id}">
        <td>${escHtml(pl.cycle_name)}</td>
        <td style="text-align:right;white-space:nowrap">${hStr}${cStr}</td>
        <td style="text-align:right">
          <input type="number" min="0" max="100" step="1" value="${pctVal}"
            class="form-input input-sm" style="width:6rem;text-align:right"
            placeholder="—" data-field="pct" />
        </td>
        <td>
          <input type="text" value="${noteVal}" class="form-input input-sm"
            style="width:100%" placeholder="..." data-field="note" />
        </td>
        <td>
          <button type="button" class="btn btn-secondary btn-sm" data-clear="${pl.cycle_id}"
            title="${_t('plan.physical.clear')}">✕</button>
        </td>
      </tr>`;
    }).join('');
    tbody.querySelectorAll('[data-clear]').forEach(btn => {
      btn.addEventListener('click', () => {
        const row = btn.closest('tr');
        row.querySelector('[data-field="pct"]').value  = '';
        row.querySelector('[data-field="note"]').value = '';
      });
    });
    document.getElementById('physicalProgressError').textContent = '';
    openModal('physicalProgressModal');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
});

document.getElementById('physicalProgressModalClose').addEventListener('click', () => closeModal('physicalProgressModal'));
document.getElementById('physicalProgressCancelBtn').addEventListener('click', () => closeModal('physicalProgressModal'));

document.getElementById('physicalProgressSaveBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  const errEl = document.getElementById('physicalProgressError');
  errEl.textContent = '';
  const rows = document.getElementById('physicalProgressBody').querySelectorAll('tr[data-cycle-id]');
  const payload = [];
  for (const row of rows) {
    const cycleId = parseInt(row.dataset.cycleId);
    const rawPct  = row.querySelector('[data-field="pct"]').value.trim();
    const note    = row.querySelector('[data-field="note"]').value.trim() || null;
    let pct = null;
    if (rawPct !== '') {
      pct = parseFloat(rawPct);
      if (isNaN(pct) || pct < 0 || pct > 100) {
        errEl.textContent = `% inválido na linha "${row.cells[0].textContent}". Use valores entre 0 e 100.`;
        return;
      }
      pct = pct / 100;
    }
    payload.push({ cycle_id: cycleId, physical_pct: pct, physical_note: note });
  }
  try {
    await apiFetchJSON(`/api/projects/${_planProjectId}/plans/physical-progress`, 'PATCH', payload);
    closeModal('physicalProgressModal');
    await _renderPlanTable();
    notify(_t('msg.layout_saved'), 'success');
  } catch (e) { errEl.textContent = `${_t('msg.err_generic')}: ${e.message}`; }
});

document.getElementById('addPlanAddRowBtn').addEventListener('click', () => {
  _addPlanRow(_addPlanAvailableCycles);
});

function _closeAddPlanModal() {
  closeModal('addPlanModal');
}
document.getElementById('addPlanModalClose').addEventListener('click', _closeAddPlanModal);
document.getElementById('addPlanCancelBtn').addEventListener('click', _closeAddPlanModal);

document.getElementById('addPlanSaveBtn').addEventListener('click', async () => {
  const wrappers = document.getElementById('addPlanRows').querySelectorAll(':scope > div');
  const errEl = document.getElementById('addPlanError');
  errEl.textContent = '';
  const entries = [];
  const seenIds = new Set();
  for (const wrapper of wrappers) {
    const sel   = wrapper.querySelector('select');
    const inpH  = wrapper.querySelectorAll('input')[0];
    const inpC  = wrapper.querySelectorAll('input')[1];
    const cycleId = parseInt(sel.value);
    const hours   = parseFloat(inpH.value);
    const rawC    = inpC.value.trim();
    const cost    = rawC === '' ? null : parseFloat(rawC);
    if (!cycleId) { errEl.textContent = _t('msg.select_cycle_all'); return; }
    if (seenIds.has(cycleId)) { errEl.textContent = _t('msg.duplicate_cycle'); return; }
    if (isNaN(hours) || hours < 0) { errEl.textContent = _t('msg.valid_hours'); return; }
    if (cost !== null && (isNaN(cost) || cost < 0)) { errEl.textContent = 'Custo inválido.'; return; }
    seenIds.add(cycleId);
    entries.push({ cycle_id: cycleId, planned_hours: hours, planned_cost: cost });
  }
  if (!entries.length) { _closeAddPlanModal(); return; }
  try {
    await Promise.all(entries.map(e =>
      apiFetchJSON(`/api/projects/${_planProjectId}/plans/${e.cycle_id}`, 'PUT',
        { cycle_id: e.cycle_id, planned_hours: e.planned_hours, planned_cost: e.planned_cost })
    ));
    _closeAddPlanModal();
    await _renderPlanTable();
  } catch (e) { errEl.textContent = `${_t('msg.err_generic')}: ${e.message}`; }
});

document.getElementById('exportPlanBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const res = await fetch(`/api/projects/${_planProjectId}/plans/export`, {
      headers: _authHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const disp = res.headers.get('Content-Disposition') || '';
    const match = disp.match(/filename="([^"]+)"/);
    const fname = match ? match[1] : 'baseline.csv';
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: fname }).click();
    URL.revokeObjectURL(url);
  } catch (e) { notify(`${_t('msg.err_export')}: ${e.message}`, 'error'); }
});

document.getElementById('importPlanFile').addEventListener('change', async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = '';
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/plans/import', {
      method: 'POST',
      headers: _authHeaders(),
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = _t('msg.baseline_imported').replace('{n}', data.created).replace('{m}', data.updated) +
      (data.errors.length ? ` — ${data.errors.length} ${_t('msg.errors_n')}` : '');
    notify(msg, data.errors.length ? 'warning' : 'success');
    await _renderPlanTable();
  } catch (e) { notify(`Erro ao importar: ${e.message}`, 'error'); }
});

// ---------------------------------------------------------------------------
// Chart option builders — moved to charts/effort.js, charts/portfolio.js,
// and charts/forecast.js. Stubs kept here for reference only.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Toolbox padrão ECharts — garante consistência visual em todos os gráficos.
// extra: objeto com features adicionais (magicType, dataZoom, etc.)
// ---------------------------------------------------------------------------
function _toolbox(extra = {}, name = 'PMAS') {
  return {
    right: 10,
    top: 10,
    feature: {
      dataView:    { readOnly: true, title: _t('toolbox.data_view'), lang: _t('toolbox.data_view_lang') },
      restore:     { title: _t('toolbox.restore') },
      saveAsImage: { title: _t('toolbox.save'), name, pixelRatio: 2 },
      ...extra,
    },
  };
}

// _buildHoursBarOption, _buildEffortSeriesOnly — moved to charts/effort.js


// _buildEvmQuadrantOption — moved to charts/portfolio.js

// _buildTreemapOption — moved to charts/portfolio.js

// _buildBulletOption — moved to charts/portfolio.js

// ---------------------------------------------------------------------------
// Collaborator Inline Detail Panel
// ---------------------------------------------------------------------------
function _closeCollabDetail() {
  _selectedCollaborator = null;
  document.getElementById('collabDetailPanel').hidden = true;
  // dispose inline charts
  ['collabInlineTimelineChart','collabCalendarChart'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const c = echarts.getInstanceByDom(el);
    if (c && !c.isDisposed()) c.dispose();
  });
  // remove highlight from effort chart
  const effEl = document.getElementById('effortChart');
  if (effEl) { const c = echarts.getInstanceByDom(effEl); if (c) c.dispatchAction({ type: 'downplay' }); }
}

async function _openCollabDetail(name) {
  _selectedCollaborator = name;

  // highlight bar in effort chart
  const effEl = document.getElementById('effortChart');
  if (effEl) {
    const c = echarts.getInstanceByDom(effEl);
    if (c) {
      c.dispatchAction({ type: 'downplay' });
      c.dispatchAction({ type: 'highlight', name });
    }
  }

  // show panel, set title — re-anchor after effortPanel in case panels were reordered
  const panel = document.getElementById('collabDetailPanel');
  const effortPanel = document.getElementById('effortPanel');
  if (effortPanel && effortPanel.nextSibling !== panel) effortPanel.after(panel);
  panel.hidden = false;
  document.getElementById('collabDetailName').textContent = name;

  // scroll panel into view smoothly
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  // Section 1: cycle timeline
  await _renderCollabTimeline(name);

  // Section 2: calendar heatmap — use current calendar month
  _calYear  = new Date().getFullYear();
  _calMonth = new Date().getMonth() + 1;
  await _renderCollabCalendar(name, _calYear, _calMonth);
}

async function _renderCollabTimeline(name) {
  const emptyEl = document.getElementById('collabInlineTimelineEmpty');
  const chartEl = document.getElementById('collabInlineTimelineChart');

  // reuse existing filters from the main filter bar
  const pepCodes = pepMs.getValues();
  const pepDescs = pepDescMs.getValues();
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  p.set('collaborator_name', name);
  pepCodes.forEach(c => p.append('pep_code', c));
  pepDescs.forEach(d => p.append('pep_description', d));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  let rows = [];
  try { rows = await apiFetch(`/api/dashboard/collaborator-timeline?${p}`); }
  catch (e) { notify(_t('msg.err_load_timeline'), 'error'); return; }

  // dispose old chart
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  if (!rows.length) {
    emptyEl.hidden = false;
    chartEl.style.visibility = 'hidden';
    return;
  }
  emptyEl.hidden = true;
  chartEl.style.visibility = '';

  const tc = echarts.init(chartEl, 'dark', { renderer: 'svg' });
  tc.setOption({ aria: { enabled: true } });
  _charts['collabInlineTimelineChart'] = tc;
  tc.setOption(_buildHoursBarOption({
    data: rows, categoryKey: 'cycle_name',
    orientation: 'vertical', stacked: true,
    showTotal: true, richLabel: false,
    maxItems: 40, toolboxName: 'PMAS-CollabTimeline',
  }), true);

  // Click a cycle bar → jump the calendar to that cycle's start month
  tc.off('click');
  tc.on('click', async (params) => {
    if (!params?.name) return;
    const rec = rows.find(r => r.cycle_name === params.name);
    if (!rec?.cycle_start) return;
    const [y, m] = rec.cycle_start.split('-').map(Number);
    _calYear  = y;
    _calMonth = m;
    await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
    document.getElementById('collabCalendarChart')
      .scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

async function _renderCollabCalendar(name, year, month) {
  const emptyEl  = document.getElementById('collabCalendarEmpty');
  const chartEl  = document.getElementById('collabCalendarChart');
  const statsEl  = document.getElementById('collabCalendarStats');
  const inputEl  = document.getElementById('calMonthInput');

  const nowDate  = new Date();
  inputEl.max    = `${nowDate.getFullYear()}-${String(nowDate.getMonth()+1).padStart(2,'0')}`;
  inputEl.value  = `${year}-${String(month).padStart(2,'0')}`;

  let data = [];
  try {
    data = await apiFetch(`/api/dashboard/collaborator-daily?collaborator_name=${encodeURIComponent(name)}&year=${year}&month=${month}`);
  } catch(e) { notify(_t('msg.err_load_daily'), 'error'); return; }

  // dispose old
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  const workPoints = data.filter(d => d.hours > 0);
  const quarantineDates = new Set(data.filter(d => d.has_quarantine).map(d => d.date));
  // include quarantine-only days so tooltip can show ⚠ even when hours=0
  const calPoints = data.filter(d => d.hours > 0 || d.has_quarantine);

  const dayHeaderEl = document.getElementById('calDayHeader');
  if (!calPoints.length) {
    emptyEl.hidden = false;
    chartEl.style.visibility = 'hidden';
    if (dayHeaderEl) dayHeaderEl.style.display = 'none';
    statsEl.innerHTML = '';
    return;
  }
  emptyEl.hidden = true;
  chartEl.style.visibility = '';
  if (dayHeaderEl) dayHeaderEl.style.display = 'flex';

  // data: [date, total, normal, extra, standby]
  // All days in the month — inactive days use value=-1 so visualMap.outOfRange
  // applies a neutral background while the label still shows the day number.
  const lastDay    = new Date(year, month, 0).getDate();
  const allDaysData = [];
  for (let d = 1; d <= lastDay; d++) {
    const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const rec = data.find(r => r.date === dateStr);
    if (rec) {
      allDaysData.push([dateStr, rec.hours, rec.normal_hours || 0, rec.extra_hours || 0, rec.standby_hours || 0]);
    } else {
      allDaysData.push([dateStr, -1, 0, 0, 0]);
    }
  }

  const rangeStart = `${year}-${String(month).padStart(2,'0')}-01`;
  const rangeEnd   = `${year}-${String(month).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}`;
  // maxHours removed — visualMap now uses discrete pieces, no continuous scale needed

  // Read theme CSS variables so the chart adapts to Admin > Aparência settings
  const primaryColor  = _cssVar('--primary')    || '#4f8ef7';
  const accentColor   = _cssVar('--accent')     || '#07b3d7';
  const cardColor     = _cssVar('--card')       || '#0e2038';
  const borderColor   = _cssVar('--border-hi')  || '#1d4068';
  const inactiveText  = _cssVar('--text-3')     || '#3d6080';
  const activeText    = _cssVar('--text')       || '#e0e0e0';
  const textMuted     = _cssVar('--text-2')     || '#94a3b8';
  const pal           = _getPalette();

  // Square cell size — compute from container, then force chart width to match exactly
  const containerW = chartEl.parentElement?.offsetWidth || chartEl.offsetWidth || 560;
  const cellW      = Math.min(Math.max(Math.floor((containerW - 16) / 7), 44), 80);
  const calWidth   = cellW * 7;
  chartEl.style.width  = `${calWidth + 8}px`;
  chartEl.style.maxWidth = '100%';
  chartEl.style.margin = '0 auto';

  // Day-of-week header row rendered in HTML (ECharts vertical orient puts dayLabel on left)
  const dayHeader = document.getElementById('calDayHeader');
  if (dayHeader) {
    const dayNames = _t('cal.day_names');
    dayHeader.style.cssText = `display:flex;width:${calWidth + 8}px;max-width:100%;margin:0 auto 2px`;
    dayHeader.innerHTML = dayNames.map(n =>
      `<div style="flex:0 0 ${cellW}px;text-align:center;font-size:10px;font-weight:600;color:${textMuted}">${n}</div>`
    ).join('');
  }

  // Dynamic height: weeks
  const firstDow  = new Date(year, month - 1, 1).getDay(); // 0=Sun
  const numWeeks  = Math.ceil((firstDow + lastDay) / 7);
  chartEl.style.height = `${numWeeks * cellW + 8}px`;

  const cc = echarts.init(chartEl, 'dark', { renderer: 'svg' });
  cc.setOption({ aria: { enabled: true } });
  _charts['collabCalendarChart'] = cc;
  cc.setOption({
    ..._chartDefaults(),
    tooltip: {
      ..._chartDefaults().tooltip,
      formatter(p) {
        if (!p.value || p.value[1] < 0) return '';
        const [d_date, , n, e, s] = p.value;
        const q = quarantineDates.has(d_date) ? ' ⚠' : '';
        let tip = `<b>${d_date}</b>${q}`;
        if (n > 0) tip += `<br/>${_t('trends.normal')}: ${n.toFixed(1)}h`;
        if (e > 0) tip += `<br/>${_t('trends.extra')}: ${e.toFixed(1)}h`;
        if (s > 0) tip += `<br/>${_t('trends.standby')}: ${s.toFixed(1)}h`;
        return tip;
      },
    },
    visualMap: {
      show: false,
      type: 'piecewise',
      // 6 discrete bands matching the blue scale in the reference legend.
      // Values 0 and -1 (inactive / zero-hour days) fall through to outOfRange.
      pieces: [
        { gte:  1, lte:  3, color: '#d4e3f5' },
        { gte:  4, lte:  6, color: '#96bcdf' },
        { gte:  7, lte:  9, color: '#5490c8' },
        { gte: 10, lte: 12, color: '#2662ae' },
        { gte: 13, lte: 15, color: '#103c8c' },
        { gt:  15,           color: '#071e60' },
      ],
      outOfRange: { color: [cardColor] },
    },
    calendar: {
      orient: 'vertical',
      top: 4, left: 4, right: 4, bottom: 4,
      width: calWidth,
      range: [rangeStart, rangeEnd],
      cellSize: [cellW, cellW],
      dayLabel: { show: false },
      monthLabel: { show: false },
      yearLabel:  { show: false },
      itemStyle:  { color: cardColor, borderColor: borderColor, borderWidth: 2 },
      splitLine:  { show: false },
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: allDaysData,
      label: {
        show: true,
        formatter(params) {
          const [d_date, total, n, e, s] = params.data;
          const day = parseInt(d_date.split('-')[2], 10);
          if (total < 0) return `{inactive|${day}}`;
          const isQ = quarantineDates.has(d_date);
          const dayStr = isQ ? `{qday|${day}⚠}` : `{day|${day}}`;
          const lines = [dayStr];
          if (n > 0) lines.push(`{n|${n.toFixed(1)}}`);
          if (e > 0) lines.push(`{e|${e.toFixed(1)}}`);
          if (s > 0) lines.push(`{s|${s.toFixed(1)}}`);
          return lines.join('\n');
        },
        rich: {
          inactive: { fontSize: 9, color: inactiveText,  lineHeight: 14, align: 'center' },
          day:      { fontSize: 9, fontWeight: 'bold', color: activeText, lineHeight: 14, align: 'center' },
          qday:     { fontSize: 9, fontWeight: 'bold', color: '#f59e0b',  lineHeight: 14, align: 'center' },
          n:    { fontSize: 9, color: pal[0] || '#4f8ef7', lineHeight: 13, align: 'center' },
          e:    { fontSize: 9, color: pal[1] || '#d9b273', lineHeight: 13, align: 'center' },
          s:    { fontSize: 9, color: pal[2] || '#a78bfa', lineHeight: 13, align: 'center' },
        },
      },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: primaryColor } },
    }],
  }, true);

  // stats row
  const totalHours = workPoints.reduce((s, d) => s + d.hours, 0);
  const workDays   = workPoints.length;
  const avgPerDay  = workDays > 0 ? totalHours / workDays : 0;
  const peak       = workPoints.length ? workPoints.reduce((m, d) => d.hours > m.hours ? d : m, workPoints[0]) : null;

  const stat = (lbl, val) =>
    `<div style="display:flex;flex-direction:column;gap:.15rem">
       <span style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;letter-spacing:.04em">${lbl}</span>
       <span style="font-size:.88rem;font-weight:600;color:var(--text)">${val}</span>
     </div>`;

  statsEl.innerHTML =
    stat(_t('cal.stat.total'), `${totalHours.toFixed(1)}h`) +
    stat(_t('cal.stat.active_days'), workDays) +
    stat(_t('cal.stat.avg_day'), `${avgPerDay.toFixed(1)}h`) +
    (peak ? stat(_t('cal.stat.peak'), `${peak.hours.toFixed(1)}h (${peak.date})`) : '') +
    (quarantineDates.size ? stat(_t('cal.stat.quarantine'), quarantineDates.size) : '');
}



// _buildPepCpiOption — moved to charts/forecast.js

// ---------------------------------------------------------------------------
// Stats row (effort tab)
// ---------------------------------------------------------------------------
function _buildStatsRow(data, budgetData = []) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;
  const row   = document.createElement('div'); row.className = 'stats-row';
  const pal   = _getPalette();
  const cards = [
    { val: fmt(normal)  + 'h', lbl: _t('stat.normal_h'),  cls: 'blue',    color: pal[0] },
    { val: fmt(extra)   + 'h', lbl: _t('stat.extra_h'),   cls: 'amber',   color: pal[1] },
    { val: fmt(standby) + 'h', lbl: _t('stat.standby_h'), cls: 'violet',  color: pal[2] },
    { val: fmt(total)   + 'h', lbl: _t('stat.total'),     cls: 'green'    },
    { val: data.length,        lbl: _t('stat.collabs'),   cls: 'neutral'  },
  ];
  if (budgetData.length > 0) {
    const totalBudget = budgetData.reduce((s, d) => s + d.budget_hours, 0);
    const totalActual = budgetData.reduce((s, d) => s + d.actual_hours, 0);
    const pct  = totalBudget > 0 ? (totalActual / totalBudget * 100).toFixed(1) : '—';
    const over = totalBudget > 0 && totalActual > totalBudget;
    cards.push(
      { val: fmt(totalBudget) + 'h', lbl: _t('stat.budgeted'),   cls: 'neutral' },
      { val: `${pct}%`,              lbl: _t('stat.vs_budget'),  cls: over ? 'red' : 'green' },
    );
  }
  cards.forEach(({ val, lbl, cls, color }) => {
    const card = document.createElement('div'); card.className = `stat-card ${cls}`;
    const style = color ? ` style="color:${color}"` : '';
    card.innerHTML = `<div class="val"${style}>${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Stats row (portfolio tab) — KPIs de custo proporcional
// ---------------------------------------------------------------------------
function _buildPortfolioStatsRow(health, trends) {
  const pepsActive = health.filter(d => d.total_hours > 0).length;
  const lastTrend  = trends && trends.length ? trends[trends.length - 1] : null;

  const _fmtDelta = (pct, abs) => {
    if (pct != null) {
      const dir = pct > 0.5 ? '↑' : pct < -0.5 ? '↓' : '→';
      const cls = pct > 5 ? 'delta-up' : pct < -5 ? 'delta-down' : 'delta-neutral';
      return ` <span class="${cls}">${dir} ${Math.abs(pct).toFixed(1)}%</span>`;
    }
    if (abs != null && abs !== 0) {
      const dir = abs > 0 ? '↑' : '↓';
      const cls = abs > 0 ? 'delta-up' : 'delta-down';
      return ` <span class="${cls}">${dir} ${abs > 0 ? '+' : ''}${abs.toFixed(1)}</span>`;
    }
    return '';
  };

  const pal = _getPalette();
  let cards;

  if (!_evmMode) {
    // ── Hours mode ──────────────────────────────────────────────
    let hNormal = 0, hExtra = 0, hStandby = 0;
    (trends || []).forEach(r => {
      hNormal  += r.normal_hours  || 0;
      hExtra   += r.extra_hours   || 0;
      hStandby += r.standby_hours || 0;
    });
    const totalHours  = health.reduce((s, d) => s + (d.total_hours || 0), 0);
    const budgetHours = health
      .filter(d => d.budget_hours != null && d.budget_hours > 0)
      .reduce((s, d) => s + d.budget_hours, 0);
    const pctH  = budgetHours > 0 ? (totalHours / budgetHours * 100).toFixed(1) : '—';
    const overH = budgetHours > 0 && totalHours > budgetHours;
    const totalHoursVal = `${fmt(totalHours)}h${lastTrend ? _fmtDelta(lastTrend.hours_delta_pct, lastTrend.hours_delta) : ''}`;

    cards = [
      { val: `${fmt(hNormal)}h${_fmtDelta(lastTrend?.normal_hours_delta_pct,  lastTrend?.normal_hours_delta)}`,   lbl: _t('stat.normal_h'),    cls: 'blue',    color: pal[0] },
      { val: `${fmt(hExtra)}h${_fmtDelta(lastTrend?.extra_hours_delta_pct,    lastTrend?.extra_hours_delta)}`,    lbl: _t('stat.extra_h'),     cls: 'amber',   color: pal[1] },
      { val: `${fmt(hStandby)}h${_fmtDelta(lastTrend?.standby_hours_delta_pct, lastTrend?.standby_hours_delta)}`, lbl: _t('stat.standby_h'),   cls: 'violet',  color: pal[2] },
      { val: totalHoursVal,                                                          lbl: _t('stat.total'),       cls: 'green'   },
      { val: pepsActive,                                                              lbl: _t('stat.peps_active'), cls: 'neutral' },
    ];
    if (budgetHours > 0) {
      cards.push(
        { val: fmt(budgetHours) + 'h',                 lbl: _t('stat.budgeted'),   cls: 'neutral'              },
        { val: pctH !== '—' ? `${pctH}%` : '—',       lbl: _t('stat.vs_budget'),  cls: overH ? 'red' : 'green' },
      );
    }
  } else {
    // ── Cost mode (R$) ───────────────────────────────────────────
    let costNormal = 0, costExtra = 0, costStandby = 0;
    (trends || []).forEach(r => {
      costNormal  += r.normal_cost  || 0;
      costExtra   += r.extra_cost   || 0;
      costStandby += r.standby_cost || 0;
    });
    const totalCost   = health.reduce((s, d) => s + (d.total_cost || 0), 0);
    const budgetCost  = health
      .filter(d => d.budget_cost != null)
      .reduce((s, d) => s + d.budget_cost, 0);
    const pctC  = budgetCost > 0 ? (totalCost / budgetCost * 100).toFixed(1) : '—';
    const overC = budgetCost > 0 && totalCost > budgetCost;
    const costTotalVal = `${_fmtCost(totalCost)}${lastTrend ? _fmtDelta(lastTrend.cost_delta_pct, lastTrend.cost_delta) : ''}`;

    cards = [
      { val: `${_fmtCost(costNormal)}${_fmtDelta(lastTrend?.normal_cost_delta_pct,  lastTrend?.normal_cost_delta)}`,   lbl: _t('stat.cost_normal'),  cls: 'blue',    color: pal[0] },
      { val: `${_fmtCost(costExtra)}${_fmtDelta(lastTrend?.extra_cost_delta_pct,    lastTrend?.extra_cost_delta)}`,    lbl: _t('stat.cost_extra'),   cls: 'amber',   color: pal[1] },
      { val: `${_fmtCost(costStandby)}${_fmtDelta(lastTrend?.standby_cost_delta_pct, lastTrend?.standby_cost_delta)}`, lbl: _t('stat.cost_standby'), cls: 'violet',  color: pal[2] },
      { val: costTotalVal,                                                                lbl: _t('stat.cost_total'),   cls: 'green'   },
      { val: pepsActive,                                                                  lbl: _t('stat.peps_active'),  cls: 'neutral' },
    ];
    if (budgetCost > 0) {
      cards.push(
        { val: _fmtCost(budgetCost),                    lbl: _t('stat.budget_cost'),    cls: 'neutral'              },
        { val: pctC !== '—' ? `${pctC}%` : '—',        lbl: _t('stat.vs_budget_cost'), cls: overC ? 'red' : 'green' },
      );
    }
  }

  const row = document.createElement('div');
  row.className = 'stats-row';
  cards.forEach(({ val, lbl, cls, color }) => {
    const card = document.createElement('div');
    card.className = `stat-card ${cls}`;
    const style = color ? ` style="color:${color}"` : '';
    card.innerHTML = `<div class="val"${style}>${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;
let _allCycles = [];

const _cyclesPag = _makePaginator(
  { container: 'cyclesPagination', prev: 'cyclesPrevBtn', next: 'cyclesNextBtn', pageSize: 'cyclesPageSize', label: 'cyclesPageLabel' },
  rows => {
    const admin = _isAdmin();
    _renderTable('cyclesBody', rows, {
      colspan: 6,
      emptyKey: 'no_cycles',
      rowFn: c => `
    <tr style="${!c.is_active ? 'opacity:.5' : ''}">
      <td>${escHtml(c.name)}${!c.is_active ? ' <em style="color:#64748b;font-size:.8rem">(arquivado)</em>' : ''}</td>
      <td>${c.start_date}</td>
      <td>${c.end_date}</td>
      <td><span class="badge-status ativo">${_t('badge.regular')}</span></td>
      <td style="text-align:right">${c.record_count.toLocaleString('pt-BR')}</td>
      <td><div class="actions">
        ${admin ? `<button class="btn btn-sm ${c.is_closed ? 'btn-warning' : 'btn-secondary'}" onclick="toggleCycleLock(${c.id}, ${c.is_closed})" title="${c.is_closed ? _t('title.unlock') : _t('title.lock')}">${c.is_closed ? '🔒' : '🔓'}</button>` : ''}
        ${admin ? `<button class="btn btn-sm btn-secondary" onclick="toggleCycleArchive(${c.id}, ${c.is_active})" title="${c.is_active ? _t('title.archive') : _t('title.restore')}">${c.is_active ? '📦' : '↩'}</button>` : ''}
        <button class="btn btn-secondary btn-sm" onclick="openCycleModal(${c.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteCycle(${c.id}, ${escHtml(JSON.stringify(c.name))}, ${c.record_count})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`,
    });
  }
);

async function loadCyclesTable() {
  _cyclesPag.reset();
  const showArchived = document.getElementById('showArchivedCycles')?.checked;
  const url = showArchived ? '/api/cycles?include_archived=true' : '/api/cycles';
  await _loadTable(url, data => {
    _allCycles = data;
    _renderCyclesTable(_applySort('cyclesTable', _allCycles));
  });
}

function _renderCyclesTable(cycles) { _cyclesPag.render(cycles); }

function toggleCycleLock(id, isClosed) {
  confirmDialog(_t(isClosed ? 'confirm.unlock_cycle' : 'confirm.lock_cycle'), async () => {
    try {
      await apiFetchJSON(`/api/cycles/${id}/toggle-status`, 'PATCH');
      loadCyclesTable();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

function toggleCycleArchive(id, isActive) {
  confirmDialog(_t(isActive ? 'confirm.archive_cycle' : 'confirm.restore_cycle'), async () => {
    try {
      await apiFetchJSON(`/api/cycles/${id}/toggle-archive`, 'PATCH');
      loadCyclesTable();
      loadDashboardCycles();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

document.getElementById('showArchivedCycles').addEventListener('change', loadCyclesTable);

function openCycleModal(id = null) {
  _cycleEditId = id;
  document.getElementById('cycleModalTitle').textContent = id ? _t('cm.title_edit') : _t('cm.title_new');
  document.getElementById('cycleError').textContent = '';
  if (id) {
    const c = _allCycles.find(x => x.id === id);
    if (c) {
      document.getElementById('cycleNameInput').value  = c.name;
      document.getElementById('cycleStartInput').value = c.start_date;
      document.getElementById('cycleEndInput').value   = c.end_date;
    }
  } else {
    document.getElementById('cycleNameInput').value  = '';
    document.getElementById('cycleStartInput').value = '';
    document.getElementById('cycleEndInput').value   = '';
  }
  openModal('cycleModal', document.activeElement);
}

function closeCycleModal() { closeModal('cycleModal'); }

document.getElementById('cycleSaveBtn').addEventListener('click', async () => {
  const body = {
    name:       document.getElementById('cycleNameInput').value.trim(),
    start_date: document.getElementById('cycleStartInput').value,
    end_date:   document.getElementById('cycleEndInput').value,
  };
  if (!body.name || !body.start_date || !body.end_date) {
    document.getElementById('cycleError').textContent = _t('msg.fields_required');
    return;
  }
  try {
    if (_cycleEditId) {
      await apiFetchJSON(`/api/cycles/${_cycleEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/cycles', 'POST', body);
    }
    closeCycleModal();
    loadCyclesTable();
    loadDashboardCycles();
  } catch (e) {
    document.getElementById('cycleError').textContent = e.message;
  }
});

document.getElementById('cycleCancelBtn').addEventListener('click', closeCycleModal);
document.getElementById('cycleModalClose').addEventListener('click', closeCycleModal);
document.getElementById('newCycleBtn').addEventListener('click', () => openCycleModal());

document.getElementById('cycleSearch').addEventListener('input', e => {
  _cyclesPag.reset();
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles;
  _renderCyclesTable(_applySort('cyclesTable', filtered));
});

function deleteCycle(id, name, count) {
  if (count > 0) { notify(_t('msg.cycle_has_records').replace('{name}', name).replace('{count}', count), 'error'); return; }
  confirmDialog(_t('confirm.delete_cycle'), async () => {
    try { await apiFetchJSON(`/api/cycles/${id}`, 'DELETE'); loadCyclesTable(); loadDashboardCycles(); }
    catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

document.getElementById('exportCyclesBtn').addEventListener('click', () => {
  if (!_allCycles.length) { notify(_t('msg.no_cycles_export'), 'info'); return; }
  const header = 'name,start_date,end_date,is_closed,record_count';
  const rows = _allCycles.map(c =>
    `"${c.name}",${c.start_date},${c.end_date},${c.is_closed},${c.record_count}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'ciclos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importCyclesInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/cycles/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadCyclesTable();
    loadDashboardCycles();
  } catch (err) { notify(`${_t('msg.err_import')}: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId  = null;
let _allProjects    = [];
let _consumedByPep  = {};

let _baselineByProject = {};   // project_id → active ProjectBaselineOut | null

const _projectsPag = _makePaginator(
  { container: 'projectsPagination', prev: 'projectsPrevBtn', next: 'projectsNextBtn', pageSize: 'projectsPageSize', label: 'projectsPageLabel' },
  rows => _renderTable('projectsBody', rows, {
    colspan: 8,
    emptyKey: 'no_projects',
    rowFn: p => {
      const bl = _baselineByProject[p.id];
      const blBadge = bl
        ? `<span class="badge-baseline active" title="${_t('baseline.locked_at')} ${_fmtDateShort(bl.locked_at)} ${_t('baseline.locked_by')} ${escHtml(bl.locked_by || '?')}${bl.label ? ' — ' + escHtml(bl.label) : ''}">${_t('baseline.badge')}</span>`
        : '';
      return `
    <tr>
      <td><code>${escHtml(p.pep_wbs)}</code></td>
      <td>${escHtml(p.name || '—')}</td>
      <td>${escHtml(p.client || '—')}</td>
      <td>${escHtml(p.manager || '—')}</td>
      <td style="text-align:right">${_buildBudgetCell(p)} ${blBadge}</td>
      <td>${_buildDatesCell(p)}</td>
      <td><span class="badge-status ${p.status}">${p.status}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">${_t('btn.edit')}</button>
        <button class="btn btn-secondary btn-sm" onclick="selectProjectPlan(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))}, ${escHtml(JSON.stringify(p.name || p.pep_wbs))})">${_t('plan.btn.open')}</button>
        <button class="btn btn-secondary btn-sm" onclick="_openBudgetHistory(${p.id}, ${escHtml(JSON.stringify(p.name || p.pep_wbs))})" data-i18n-title="budget.history.btn">${_t('budget.history.btn')}</button>
        <button class="btn btn-secondary btn-sm" onclick="_openBaselineModal(${p.id})" title="${_t('baseline.title')}">📍</button>
        ${_isAdmin() ? `<button class="btn btn-secondary btn-sm" onclick="_openAclModal(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">🔑 Acesso</button>` : ''}
        <button class="btn btn-danger btn-sm" onclick="deleteProject(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`;
    },
  })
);

async function loadProjectsTable() {
  _projectsPag.reset();
  try {
    const [projects, health] = await Promise.all([
      apiFetch('/api/projects'),
      apiFetch('/api/v2/portfolio').catch(() => []),
    ]);
    _allProjects   = projects;
    _consumedByPep = Object.fromEntries(health.map(h => [h.pep_wbs, { hours: h.total_hours, health: h.health_hours }]));

    // Fetch active baselines for all projects in parallel (best-effort)
    const blResults = await Promise.allSettled(
      projects.map(p => apiFetch(`/api/projects/${p.id}/baselines`))
    );
    _baselineByProject = {};
    blResults.forEach((r, i) => {
      if (r.status === 'fulfilled' && Array.isArray(r.value)) {
        const active = r.value.find(b => b.is_active);
        _baselineByProject[projects[i].id] = active || null;
      }
    });

    _renderProjectsTable(_applySort('projectsTable', projects));
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

function _buildBudgetCell(p) {
  if (p.budget_hours == null) return '—';
  const entry = _consumedByPep[p.pep_wbs];
  const budgetStr = p.budget_hours.toLocaleString('pt-BR') + 'h';
  if (!entry) return budgetStr;
  const { hours: consumed, health } = entry;
  const wPct = Math.round(_budgetWarning * 100);
  if (health === 'overrun' || health === 'critical') return `${budgetStr}<span class="badge-budget critical" title="${consumed.toFixed(1)}h consumidas">${_t('budget.exceeded')}</span>`;
  if (health === 'warning') return `${budgetStr}<span class="badge-budget warning" title="${consumed.toFixed(1)}h consumidas">${_t('budget.warning')} ≥${wPct}%</span>`;
  return budgetStr;
}

function _fmtDateBR(iso) {
  if (!iso) return null;
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function _buildDatesCell(p) {
  const parts = [];
  if (p.start_date)       parts.push(`▸ ${_fmtDateBR(p.start_date)}`);
  if (p.planned_end_date) parts.push(`→ ${_fmtDateBR(p.planned_end_date)}`);
  if (p.completion_date)  parts.push(`✓ ${_fmtDateBR(p.completion_date)}`);
  return parts.length ? `<span style="font-size:.8rem;color:#94a3b8">${parts.join(' ')}</span>` : '—';
}

function _renderProjectsTable(projects) { _projectsPag.render(projects); }

function selectProjectPlan(projectId, pepWbs, projectName) {
  _planProjectId = projectId;
  const nameEl = document.getElementById('planProjectName');
  if (nameEl) nameEl.textContent = projectName;
  const panel = document.getElementById('projectPlanPanel');
  panel.hidden = false;
  _renderPlanTable();
  setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
}

function _closeProjectPlan() {
  _planProjectId = null;
  document.getElementById('projectPlanPanel').hidden = true;
}

document.getElementById('closePlanPanelBtn').addEventListener('click', _closeProjectPlan);

// ── F7: Budget Revision History ───────────────────────────────────────────────

let _budgetHistChart = null;

async function _openBudgetHistory(projectId, projectName) {
  document.getElementById('budgetHistoryTitle').textContent =
    `${_t('budget.history.title')} — ${projectName}`;
  document.getElementById('budgetHistoryBody').innerHTML =
    `<tr><td colspan="5" class="td-empty">${_t('loading')}</td></tr>`;
  const sparkEl = document.getElementById('budgetSparkline');
  if (sparkEl) { sparkEl.hidden = true; }
  openModal('budgetHistoryModal');
  try {
    const rows = await apiFetch(`/api/projects/${projectId}/budget-history`);
    if (!rows.length) {
      document.getElementById('budgetHistoryBody').innerHTML =
        `<tr><td colspan="5" class="td-empty">${_t('budget.history.empty')}</td></tr>`;
      return;
    }
    document.getElementById('budgetHistoryBody').innerHTML = rows.map(r => `
      <tr>
        <td>${_fmtDateBR(r.changed_at?.split('T')[0]) || '—'}</td>
        <td>${escHtml(r.changed_by)}</td>
        <td class="text-right">${r.old_budget_hours != null ? r.old_budget_hours.toFixed(1) + 'h' : '—'}
          → ${r.new_budget_hours != null ? r.new_budget_hours.toFixed(1) + 'h' : '—'}</td>
        <td class="text-right">${r.old_budget_cost != null ? _fmtCost(r.old_budget_cost) : '—'}
          → ${r.new_budget_cost != null ? _fmtCost(r.new_budget_cost) : '—'}</td>
        <td>${escHtml(r.reason || '—')}</td>
      </tr>`).join('');

    // Sparkline — chronological order (rows arrive newest-first)
    if (sparkEl && rows.length >= 2) {
      const sorted = [...rows].reverse();
      const dates  = sorted.map(r => r.changed_at?.split('T')[0] || '');
      const bHours = sorted.map(r => r.new_budget_hours ?? null);
      const bCosts = sorted.map(r => r.new_budget_cost  ?? null);
      if (_budgetHistChart) { _budgetHistChart.dispose(); _budgetHistChart = null; }
      _budgetHistChart = echarts.init(sparkEl, 'dark', { renderer: 'svg' });
      _budgetHistChart.setOption({
        backgroundColor: 'transparent',
        grid: { top: 28, right: 12, bottom: 24, left: 8, containLabel: true },
        legend: {
          data: [_t('budget.history.sparkline.hours'), _t('budget.history.sparkline.cost')],
          top: 2, left: 'center',
          textStyle: { color: _cssVar('--text'), fontSize: 10 },
          itemGap: 16, itemWidth: 12, itemHeight: 8,
        },
        xAxis: { type: 'category', data: dates,
          axisLabel: { color: _cssVar('--text-3'), fontSize: 9 },
          axisTick: { show: false },
        },
        yAxis: [
          { type: 'value', name: 'h', nameTextStyle: { color: _cssVar('--text-3'), fontSize: 9 },
            axisLabel: { color: _cssVar('--text-3'), fontSize: 9, formatter: v => `${v}h` },
            splitLine: { lineStyle: { color: _cssVar('--surface') } } },
          { type: 'value', name: 'R$', nameTextStyle: { color: _cssVar('--text-3'), fontSize: 9 },
            axisLabel: { color: _cssVar('--text-3'), fontSize: 9, formatter: v => `${(v/1000).toFixed(0)}k` },
            splitLine: { show: false } },
        ],
        tooltip: { trigger: 'axis', ...(_chartDefaults().tooltip) },
        series: [
          { name: _t('budget.history.sparkline.hours'), type: 'line', yAxisIndex: 0,
            data: bHours, itemStyle: { color: _cssVar('--primary') },
            lineStyle: { width: 2 }, symbol: 'circle', symbolSize: 5 },
          { name: _t('budget.history.sparkline.cost'), type: 'line', yAxisIndex: 1,
            data: bCosts, itemStyle: { color: _cssVar('--amber') },
            lineStyle: { width: 2 }, symbol: 'circle', symbolSize: 5 },
        ],
      });
      sparkEl.hidden = false;
    }
  } catch (e) {
    document.getElementById('budgetHistoryBody').innerHTML =
      `<tr><td colspan="5" class="td-empty">${_t('msg.err_generic')}</td></tr>`;
  }
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectModalTitle').textContent = id ? _t('pm.title_edit') : _t('pm.title_new');
  document.getElementById('projectError').textContent = '';
  if (id) {
    const p = _allProjects.find(x => x.id === id);
    if (p) {
      document.getElementById('projectPepInput').value         = p.pep_wbs;
      document.getElementById('projectNameInput').value        = p.name    || '';
      document.getElementById('projectClientInput').value      = p.client  || '';
      document.getElementById('projectManagerInput').value     = p.manager || '';
      document.getElementById('projectBudgetInput').value         = p.budget_hours ?? '';
      document.getElementById('projectBudgetCostInput').value      = p.budget_cost ?? '';
      document.getElementById('projectStatusInput').value          = p.status;
      document.getElementById('projectStartInput').value           = p.start_date       || '';
      document.getElementById('projectPlannedEndInput').value      = p.planned_end_date || '';
      document.getElementById('projectCompletionInput').value      = p.completion_date  || '';
    }
  } else {
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput',
     'projectBudgetInput','projectBudgetCostInput',
     'projectStartInput','projectPlannedEndInput','projectCompletionInput']
      .forEach(fid => { document.getElementById(fid).value = ''; });
    document.getElementById('projectStatusInput').value = 'ativo';
  }
  // show budget reason field only when editing (budget change may occur)
  document.getElementById('budgetReasonGroup').hidden = !id;
  document.getElementById('projectBudgetReasonInput').value = '';
  openModal('projectModal');
}

function closeProjectModal() { closeModal('projectModal'); }

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep = document.getElementById('projectPepInput').value.trim();
  if (!pep) { document.getElementById('projectError').textContent = _t('msg.pep_required'); return; }
  const budget         = document.getElementById('projectBudgetInput').value;
  const budgetCost     = document.getElementById('projectBudgetCostInput').value;
  const completionDate = document.getElementById('projectCompletionInput').value || null;
  let status = document.getElementById('projectStatusInput').value;
  if (completionDate && status !== 'encerrado') {
    if (confirm(_t('confirm.set_encerrado'))) status = 'encerrado';
  }
  const budgetReason = document.getElementById('projectBudgetReasonInput')?.value.trim() || null;
  const body = {
    pep_wbs:               pep,
    name:                  document.getElementById('projectNameInput').value.trim()    || null,
    client:                document.getElementById('projectClientInput').value.trim()  || null,
    manager:               document.getElementById('projectManagerInput').value.trim() || null,
    budget_hours:          budget     !== '' ? parseFloat(budget)     : null,
    budget_cost:           budgetCost !== '' ? parseFloat(budgetCost) : null,
    status,
    start_date:            document.getElementById('projectStartInput').value       || null,
    planned_end_date:      document.getElementById('projectPlannedEndInput').value  || null,
    completion_date:       completionDate,
    budget_change_reason:  budgetReason,
  };
  try {
    if (_projectEditId) {
      await apiFetchJSON(`/api/projects/${_projectEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/projects', 'POST', body);
    }
    closeProjectModal();
    loadProjectsTable();
  } catch (e) {
    document.getElementById('projectError').textContent = e.message;
  }
});

document.getElementById('projectCancelBtn').addEventListener('click', closeProjectModal);
document.getElementById('projectModalClose').addEventListener('click', closeProjectModal);
document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal());

document.getElementById('projectSearch').addEventListener('input', e => {
  _projectsPag.reset();
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allProjects.filter(p =>
    (p.pep_wbs || '').toLowerCase().includes(q) ||
    (p.name    || '').toLowerCase().includes(q) ||
    (p.client  || '').toLowerCase().includes(q)
  ) : _allProjects;
  _renderProjectsTable(_applySort('projectsTable', filtered));
});

function deleteProject(id, pep) {
  confirmDialog(_t('confirm.delete_project'), async () => {
    try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); loadProjectsTable(); }
    catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

// ── Baseline Modal ─────────────────────────────────────────────────────────

function _fmtDateShort(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric' });
}

let _baselineModalProjectId = null;

async function _openBaselineModal(projectId) {
  _baselineModalProjectId = projectId;
  const proj = _allProjects.find(p => p.id === projectId);
  const title = proj ? `${_t('baseline.title')} — ${proj.pep_wbs}${proj.name ? ' · ' + proj.name : ''}` : _t('baseline.title');
  document.getElementById('baselineModalTitle').textContent = title;
  document.getElementById('baselineModalBody').innerHTML = '<p style="color:#64748b">Carregando…</p>';
  openModal('baselineModal');
  await _refreshBaselineModal(projectId);
}

async function _refreshBaselineModal(projectId) {
  try {
    const baselines = await apiFetch(`/api/projects/${projectId}/baselines`);
    const active = baselines.find(b => b.is_active);
    const proj = _allProjects.find(p => p.id === projectId);
    const hasbudget = proj && proj.budget_cost != null;

    let html = '';

    // Active baseline info
    if (active) {
      html += `<div class="baseline-info-box active">
        <strong>📍 ${_t('baseline.active')}</strong>${active.label ? ` — <em>${escHtml(active.label)}</em>` : ''}
        <br><span class="text-dim">${_t('baseline.locked_at')} ${_fmtDateShort(active.locked_at)} ${_t('baseline.locked_by')} ${escHtml(active.locked_by || '?')}</span>
        <br><span class="text-dim">${_t('baseline.budget_h')}: <b>${active.budget_hours != null ? active.budget_hours.toLocaleString('pt-BR') + 'h' : '—'}</b>
        &nbsp;·&nbsp; ${_t('baseline.budget_cost')}: <b>${active.budget_cost != null ? _fmtCost(active.budget_cost) : '—'}</b></span>
      </div>`;
    } else {
      html += `<div class="baseline-info-box warning">⚠️ ${_t('baseline.none')}</div>`;
    }

    // Create new baseline form
    html += `<div style="margin:1rem 0;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">
      <input type="text" id="baselineLabelInput" class="form-control" style="flex:1;min-width:180px"
             placeholder="${_t('baseline.label_ph')}" />
      <button class="btn btn-primary btn-sm" onclick="_createBaseline(${projectId})"
              ${hasbudget ? '' : 'disabled title="Defina budget_cost no projeto primeiro"'}>
        📍 ${_t('baseline.create')}
      </button>
    </div>`;
    if (!hasbudget) {
      html += `<p class="hint" style="color:var(--amber);margin-top:-.5rem">Defina o orçamento (budget_cost) do projeto para habilitar baseline.</p>`;
    }

    // History table
    html += `<h4 style="margin:.75rem 0 .4rem;font-size:.875rem">${_t('baseline.history')}</h4>`;
    if (!baselines.length) {
      html += `<p class="text-dim" style="font-size:.85rem">${_t('baseline.no_history')}</p>`;
    } else {
      html += `<table class="data-table" style="font-size:.82rem"><thead><tr>
        <th>${_t('baseline.locked_at')}</th><th>${_t('baseline.locked_by')}</th>
        <th>${_t('baseline.budget_h')}</th><th>${_t('baseline.budget_cost')}</th>
        <th>Rótulo</th><th></th>
      </tr></thead><tbody>`;
      baselines.forEach(b => {
        html += `<tr style="${b.is_active ? 'background:rgba(79,142,247,.08)' : ''}">
          <td>${_fmtDateShort(b.locked_at)}</td>
          <td>${escHtml(b.locked_by || '—')}</td>
          <td>${b.budget_hours != null ? b.budget_hours.toLocaleString('pt-BR') + 'h' : '—'}</td>
          <td>${b.budget_cost != null ? _fmtCost(b.budget_cost) : '—'}</td>
          <td>${escHtml(b.label || '—')}</td>
          <td><div class="actions" style="gap:.25rem">
            ${!b.is_active ? `<button class="btn btn-secondary btn-sm" onclick="_activateBaseline(${projectId},${b.id})">${_t('baseline.activate')}</button>` : '<span class="badge-baseline active" style="font-size:.75rem">ativo</span>'}
            ${_isAdmin() ? `<button class="btn btn-danger btn-sm" onclick="_deleteBaseline(${projectId},${b.id})">✕</button>` : ''}
          </div></td>
        </tr>`;
      });
      html += '</tbody></table>';
    }

    document.getElementById('baselineModalBody').innerHTML = html;
  } catch(e) {
    document.getElementById('baselineModalBody').innerHTML = `<p style="color:var(--red)">Erro: ${e.message}</p>`;
  }
}

async function _createBaseline(projectId) {
  const label = document.getElementById('baselineLabelInput')?.value.trim() || null;
  try {
    await apiFetchJSON(`/api/projects/${projectId}/baseline`, 'POST', { label });
    notify(_t('baseline.created'), 'success');
    await _refreshBaselineModal(projectId);
    loadProjectsTable();
  } catch(e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _activateBaseline(projectId, baselineId) {
  try {
    await apiFetchJSON(`/api/projects/${projectId}/baselines/${baselineId}/activate`, 'POST', {});
    await _refreshBaselineModal(projectId);
    loadProjectsTable();
  } catch(e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _deleteBaseline(projectId, baselineId) {
  confirmDialog(_t('confirm.remove_baseline') || 'Remover este baseline?', async () => {
    try {
      await apiFetchJSON(`/api/projects/${projectId}/baselines/${baselineId}`, 'DELETE');
      notify(_t('baseline.deleted'), 'success');
      await _refreshBaselineModal(projectId);
      loadProjectsTable();
    } catch(e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

document.getElementById('baselineModalClose').addEventListener('click', () => closeModal('baselineModal'));

// ---------------------------------------------------------------------------
// ACL de projetos — controle de acesso por PEP (item 3)
// ---------------------------------------------------------------------------
let _aclProjectId = null;

async function _openAclModal(projectId, pepWbs) {
  _aclProjectId = projectId;
  document.getElementById('aclModalTitle').textContent = _t('msg.acl_title') + pepWbs;
  document.getElementById('aclError').textContent = '';
  openModal('aclModal');
  await Promise.all([_loadAclEntries(), _populateAclUserSelect()]);
}

async function _loadAclEntries() {
  const tbody = document.getElementById('aclEntriesBody');
  tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:.75rem">${_t('loading')}</td></tr>`;
  try {
    const entries = await apiFetch(`/api/projects/${_aclProjectId}/access`);
    if (!entries.length) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:.75rem">${_t('msg.no_access_granted')}</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(e => `
      <tr>
        <td>${escHtml(e.username)}</td>
        <td style="text-align:right">
          <button class="btn btn-danger btn-sm" onclick="_revokeAccess(${e.user_id})">${_t('btn.revoke')}</button>
        </td>
      </tr>`).join('');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _populateAclUserSelect() {
  const sel = document.getElementById('aclUserSelect');
  try {
    const users = await apiFetch('/api/users');
    sel.innerHTML = `<option value="">${_t('ms.select_ph')}</option>` +
      users.filter(u => u.role !== 'admin').map(u =>
        `<option value="${u.id}">${escHtml(u.username)}</option>`
      ).join('');
  } catch (_) {}
}

document.getElementById('aclGrantBtn')?.addEventListener('click', async () => {
  const sel = document.getElementById('aclUserSelect');
  const userId = parseInt(sel.value);
  const errEl  = document.getElementById('aclError');
  if (!userId) { errEl.textContent = _t('msg.select_user'); return; }
  errEl.textContent = '';
  try {
    await apiFetchJSON(`/api/projects/${_aclProjectId}/access`, 'POST', { user_id: userId });
    sel.value = '';
    await _loadAclEntries();
  } catch (e) { errEl.textContent = e.message; }
});

function _revokeAccess(userId) {
  confirmDialog(_t('confirm.revoke_access'), async () => {
    try {
      await apiFetchJSON(`/api/projects/${_aclProjectId}/access/${userId}`, 'DELETE');
      await _loadAclEntries();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

document.getElementById('aclModalClose')?.addEventListener('click', () => { closeModal('aclModal'); });
document.getElementById('aclModalCloseBtn')?.addEventListener('click', () => { closeModal('aclModal'); });

document.getElementById('exportProjectsBtn').addEventListener('click', () => {
  if (!_allProjects.length) { notify(_t('msg.no_projects_export'), 'info'); return; }
  const header = 'pep_wbs,name,client,manager,budget_hours,budget_cost,status,start_date,planned_end_date,completion_date';
  const esc = v => (v == null ? '' : `"${String(v).replace(/"/g, '""')}"`);
  const rows = _allProjects.map(p =>
    `${esc(p.pep_wbs)},${esc(p.name)},${esc(p.client)},${esc(p.manager)},${p.budget_hours ?? ''},${p.budget_cost ?? ''},${p.status},${p.start_date ?? ''},${p.planned_end_date ?? ''},${p.completion_date ?? ''}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'projetos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importProjectsInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}, ${data.updated} ${_t('msg.updated_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadProjectsTable();
  } catch (err) { notify(`${_t('msg.err_import')}: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Team / RateCard management
// ---------------------------------------------------------------------------
let _allSeniorityLevels = [];
let _allRateCards       = [];
let _allTeam            = [];
let _seniorityEditId    = null;
let _rateCardEditId     = null;
let _assignCollabId     = null;

async function loadTeamTab() {
  await Promise.all([loadSeniorityLevels(), loadRateCards(), loadGlobalConfig()]);
  await loadTeamTable();
  await _loadOverAllocation();
}

// ── F5: Over-allocation Detection ─────────────────────────────────────────────

let _overAllocData = [];

function _renderOverAllocRows(items) {
  const body = document.getElementById('overAllocBody');
  if (!body) return;
  if (!items.length) {
    body.innerHTML = `<tr><td colspan="4" class="td-empty">${_t('over_alloc.empty')}</td></tr>`;
    return;
  }
  body.innerHTML = items.map(it => `
    <tr>
      <td>${escHtml(it.collaborator)}</td>
      <td>${_fmtDateBR(it.date)}</td>
      <td class="text-right" style="color:var(--red);font-weight:600">${it.total_hours.toFixed(1)}h</td>
      <td style="font-size:.8rem;color:var(--text-2)">${it.pep_list.map(escHtml).join(', ') || '—'}</td>
    </tr>`).join('');
}

async function _loadOverAllocation() {
  const card = document.getElementById('overAllocCard');
  const body = document.getElementById('overAllocBody');
  if (!card || !body) return;
  body.innerHTML = `<tr><td colspan="4" class="td-empty">${_t('loading')}</td></tr>`;
  card.hidden = false;

  const params = new URLSearchParams();
  const from = document.getElementById('overAllocFrom')?.value;
  const to   = document.getElementById('overAllocTo')?.value;
  const thr  = document.getElementById('overAllocThreshold')?.value;
  if (from) params.set('date_from', from);
  if (to)   params.set('date_to',   to);
  if (thr)  params.set('threshold', thr);
  const qs = params.toString() ? `?${params}` : '';

  try {
    const items = await apiFetch(`/api/v2/over-allocation${qs}`);
    _overAllocData = items;
    _renderOverAllocRows(_applySort('overAllocTable', _overAllocData));
  } catch (e) {
    _overAllocData = [];
    body.innerHTML = `<tr><td colspan="4" class="td-empty">${_t('msg.err_generic')}</td></tr>`;
  }
}

function _exportOverAllocCsv() {
  if (!_overAllocData.length) return;
  const header = [
    _t('over_alloc.th.collaborator'),
    _t('over_alloc.th.date'),
    _t('over_alloc.th.hours'),
    'Limite (h)',
    _t('over_alloc.th.peps'),
  ].join(',');
  const rows = _overAllocData.map(it =>
    [
      `"${it.collaborator}"`,
      it.date,
      it.total_hours.toFixed(2),
      it.threshold,
      `"${it.pep_list.join('; ')}"`,
    ].join(',')
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'sobre-alocacao.csv'; a.click();
  URL.revokeObjectURL(url);
}

const _seniorityPag = _makePaginator(
  { container: 'seniorityPagination', prev: 'seniorityPrevBtn', next: 'seniorityNextBtn', pageSize: 'seniorityPageSize', label: 'seniorityPageLabel' },
  rows => _renderTable('seniorityBody', rows, {
    colspan: 2,
    emptyKey: 'no_seniority',
    rowFn: l => `
    <tr>
      <td>${escHtml(l.name)}</td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openSeniorityModal(${l.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSeniorityLevel(${l.id}, ${escHtml(JSON.stringify(l.name))})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`,
  })
);

function _renderSeniorityTable(rows) { _seniorityPag.render(rows); }

async function loadSeniorityLevels() {
  _seniorityPag.reset();
  await _loadTable('/api/seniority-levels', data => {
    _allSeniorityLevels = data;
    _renderSeniorityTable(_applySort('seniorityTable', _allSeniorityLevels));
  });
}

const _rateCardPag = _makePaginator(
  { container: 'rateCardPagination', prev: 'rateCardPrevBtn', next: 'rateCardNextBtn', pageSize: 'rateCardPageSize', label: 'rateCardPageLabel' },
  rows => _renderTable('rateCardBody', rows, {
    colspan: 5,
    emptyKey: 'no_rates',
    rowFn: c => `
    <tr>
      <td>${escHtml(c.seniority_level_name)}</td>
      <td style="text-align:right">R$ ${Number(c.hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2})}</td>
      <td>${c.valid_from}</td>
      <td>${c.valid_to ?? '—'}</td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openRateCardModal(${c.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteRateCard(${c.id})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`,
  })
);

function _renderRateCardsTable(rows) { _rateCardPag.render(rows); }

async function loadRateCards() {
  _rateCardPag.reset();
  await _loadTable('/api/rate-cards', data => {
    _allRateCards = data;
    _renderRateCardsTable(_applySort('rateCardTable', _allRateCards));
  });
}

const _teamPag = _makePaginator(
  { container: 'teamPagination', prev: 'teamPrevBtn', next: 'teamNextBtn', pageSize: 'teamPageSize', label: 'teamPageLabel' },
  rows => _renderTable('teamBody', rows, {
    colspan: 4,
    emptyKey: 'no_team',
    rowFn: m => `
    <tr>
      <td>${escHtml(m.name)}</td>
      <td>${m.seniority_level_name ? escHtml(m.seniority_level_name) : '<span style="color:#475569">—</span>'}</td>
      <td style="text-align:right">${m.current_hourly_rate != null ? 'R$ ' + Number(m.current_hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2}) : '—'}</td>
      <td><button class="btn btn-secondary btn-sm" onclick="openAssignSeniority(${m.id}, ${escHtml(JSON.stringify(m.name))}, ${m.seniority_level_id ?? 'null'})">${_t('btn.assign')}</button></td>
    </tr>`,
  })
);

function _renderTeamTable(rows) { _teamPag.render(rows); }

document.getElementById('teamSearch').addEventListener('input', e => {
  _teamPag.reset();
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allTeam.filter(t => t.name.toLowerCase().includes(q)) : _allTeam;
  _renderTeamTable(_applySort('teamTable', filtered));
});

async function loadTeamTable() {
  _teamPag.reset();
  await _loadTable('/api/team', data => {
    _allTeam = data;
    _renderTeamTable(_applySort('teamTable', _allTeam));
    // Populate bulk seniority select
    const bulkSel = document.getElementById('bulkSenioritySelect');
    bulkSel.innerHTML = `<option value="">${_t('as.none_opt')}</option>` +
      _allSeniorityLevels.map(l => `<option value="${l.id}">${escHtml(l.name)}</option>`).join('');
  });
}

// Seniority level modal
function openSeniorityModal(id = null) {
  _seniorityEditId = id;
  document.getElementById('seniorityModalTitle').textContent = id ? _t('sm.title_edit') : _t('sm.title_new');
  document.getElementById('seniorityError').textContent = '';
  const l = id ? _allSeniorityLevels.find(x => x.id === id) : null;
  document.getElementById('seniorityNameInput').value = l ? l.name : '';
  openModal('seniorityModal');
}
function closeSeniorityModal() { closeModal('seniorityModal'); }

document.getElementById('senioritySaveBtn').addEventListener('click', async () => {
  const name = document.getElementById('seniorityNameInput').value.trim();
  if (!name) { document.getElementById('seniorityError').textContent = _t('msg.name_required'); return; }
  try {
    if (_seniorityEditId) {
      await apiFetchJSON(`/api/seniority-levels/${_seniorityEditId}`, 'PUT', { name });
    } else {
      await apiFetchJSON('/api/seniority-levels', 'POST', { name });
    }
    closeSeniorityModal();
    await loadSeniorityLevels();
  } catch (e) { document.getElementById('seniorityError').textContent = e.message; }
});
document.getElementById('seniorityCancelBtn').addEventListener('click', closeSeniorityModal);
document.getElementById('seniorityModalClose').addEventListener('click', closeSeniorityModal);
document.getElementById('newSeniorityBtn').addEventListener('click', () => openSeniorityModal());

document.getElementById('exportSeniorityBtn').addEventListener('click', () => {
  if (!_allSeniorityLevels.length) { notify(_t('msg.no_levels_export'), 'info'); return; }
  const rows = _allSeniorityLevels.map(l => `"${l.name.replace(/"/g, '""')}"`);
  const blob = new Blob(['﻿' + ['name', ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), { href: url, download: 'senioridade.csv' }).click();
  URL.revokeObjectURL(url);
});

document.getElementById('importSeniorityInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/seniority-levels/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0, 3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    await loadTeamTab();
  } catch (err) { notify(`${_t('msg.err_import')}: ${err.message}`, 'error'); }
  e.target.value = '';
});

function deleteSeniorityLevel(id, name) {
  confirmDialog(_t('confirm.delete_level'), async () => {
    try { await apiFetchJSON(`/api/seniority-levels/${id}`, 'DELETE'); await loadSeniorityLevels(); }
    catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

// Rate card modal
function _populateLevelSelect(selectId, selectedId = null) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = _allSeniorityLevels.map(l =>
    `<option value="${l.id}" ${l.id === selectedId ? 'selected' : ''}>${escHtml(l.name)}</option>`
  ).join('');
}

function openRateCardModal(id = null) {
  _rateCardEditId = id;
  document.getElementById('rateCardModalTitle').textContent = id ? _t('rm.title_edit') : _t('rm.title_new');
  document.getElementById('rateCardError').textContent = '';
  const c = id ? _allRateCards.find(x => x.id === id) : null;
  _populateLevelSelect('rateCardLevelInput', c?.seniority_level_id ?? null);
  document.getElementById('rateCardRateInput').value = c ? c.hourly_rate : '';
  document.getElementById('rateCardFromInput').value = c ? c.valid_from : '';
  document.getElementById('rateCardToInput').value   = c ? (c.valid_to ?? '') : '';
  openModal('rateCardModal');
}
function closeRateCardModal() { closeModal('rateCardModal'); }

document.getElementById('rateCardSaveBtn').addEventListener('click', async () => {
  const rate = document.getElementById('rateCardRateInput').value;
  const from = document.getElementById('rateCardFromInput').value;
  if (!rate || !from) { document.getElementById('rateCardError').textContent = _t('msg.fields_required'); return; }
  const to = document.getElementById('rateCardToInput').value;
  const body = {
    seniority_level_id: parseInt(document.getElementById('rateCardLevelInput').value),
    hourly_rate: parseFloat(rate),
    valid_from: from,
    valid_to: to || null,
  };
  try {
    if (_rateCardEditId) {
      await apiFetchJSON(`/api/rate-cards/${_rateCardEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/rate-cards', 'POST', body);
    }
    closeRateCardModal();
    await loadRateCards();
    await loadTeamTable();
  } catch (e) { document.getElementById('rateCardError').textContent = e.message; }
});
document.getElementById('rateCardCancelBtn').addEventListener('click', closeRateCardModal);
document.getElementById('rateCardModalClose').addEventListener('click', closeRateCardModal);
document.getElementById('newRateCardBtn').addEventListener('click', () => openRateCardModal());

document.getElementById('exportRateCardBtn').addEventListener('click', () => {
  if (!_allRateCards.length) { notify(_t('msg.no_rates_export'), 'info'); return; }
  const esc = v => (v == null || v === '') ? '' : `"${String(v).replace(/"/g, '""')}"`;
  const rows = _allRateCards.map(r =>
    `${esc(r.seniority_level_name)},${r.valid_from},${r.valid_to ?? ''},${r.hourly_rate}`
  );
  const blob = new Blob(['﻿' + ['seniority_level,valid_from,valid_to,hourly_rate', ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), { href: url, download: 'rate_cards.csv' }).click();
  URL.revokeObjectURL(url);
});

document.getElementById('importRateCardInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/rate-cards/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}, ${data.updated} ${_t('msg.updated_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0, 3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    await loadTeamTab();
  } catch (err) { notify(`${_t('msg.err_import')}: ${err.message}`, 'error'); }
  e.target.value = '';
});

function deleteRateCard(id) {
  confirmDialog(_t('confirm.delete_rate'), async () => {
    try { await apiFetchJSON(`/api/rate-cards/${id}`, 'DELETE'); await loadRateCards(); await loadTeamTable(); }
    catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

// Assign seniority modal
function openAssignSeniority(collabId, name, currentLevelId) {
  _assignCollabId = collabId;
  document.getElementById('assignSeniorityTitle').textContent = _t('msg.seniority_title') + name;
  document.getElementById('assignSeniorityError').textContent = '';
  const sel = document.getElementById('assignSenioritySelect');
  sel.innerHTML = `<option value="">${_t('as.none_opt')}</option>` +
    _allSeniorityLevels.map(l =>
      `<option value="${l.id}" ${l.id === currentLevelId ? 'selected' : ''}>${escHtml(l.name)}</option>`
    ).join('');
  openModal('assignSeniorityModal');
}
function closeAssignSeniority() { closeModal('assignSeniorityModal'); }

document.getElementById('assignSenioritySaveBtn').addEventListener('click', async () => {
  const val = document.getElementById('assignSenioritySelect').value;
  const body = { seniority_level_id: val ? parseInt(val) : null };
  try {
    await apiFetchJSON(`/api/team/${_assignCollabId}/seniority`, 'PUT', body);
    closeAssignSeniority();
    await loadTeamTable();
  } catch (e) { document.getElementById('assignSeniorityError').textContent = e.message; }
});
document.getElementById('assignSeniorityCancelBtn').addEventListener('click', closeAssignSeniority);
document.getElementById('assignSeniorityClose').addEventListener('click', closeAssignSeniority);

// Bulk assign seniority
document.getElementById('bulkSeniorityBtn').addEventListener('click', () => {
  const val = document.getElementById('bulkSenioritySelect').value;
  const label = val
    ? _allSeniorityLevels.find(l => l.id === parseInt(val))?.name
    : _t('as.none_opt');
  confirmDialog(_t('confirm.assign_all'), async () => {
    try {
      const body = { seniority_level_id: val ? parseInt(val) : null };
      await apiFetchJSON('/api/team/bulk-seniority', 'PUT', body);
      await loadTeamTable();
      notify(_t('msg.seniority_assigned_all').replace('{label}', label), 'success');
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
});

// Global config (multipliers)
let _anomalyMaxHours = 24;
let _budgetWarning  = 0.9;
let _budgetCritical = 1.0;

function _updateBulletLegend() {
  const wPct = Math.round(_budgetWarning  * 100);
  const cPct = Math.round(_budgetCritical * 100);
  const okEl   = document.getElementById('bulletOkLabel');
  const warnEl = document.getElementById('bulletWarnLabel');
  const critEl = document.getElementById('bulletCritLabel');
  if (okEl)   okEl.textContent   = `< ${wPct}%`;
  if (warnEl) warnEl.textContent = `${wPct}–${cPct - 1}%`;
  if (critEl) critEl.textContent = `≥ ${cPct}%`;
}

async function loadGlobalConfig() {
  try {
    const cfg = await apiFetch('/api/config');
    document.getElementById('extraMultiplierInput').value   = cfg.extra_hours_multiplier;
    document.getElementById('standbyMultiplierInput').value = cfg.standby_hours_multiplier;
    if (cfg.anomaly_max_daily_hours) _anomalyMaxHours = cfg.anomaly_max_daily_hours;
    if (cfg.timezone) document.getElementById('timezoneSelect').value = cfg.timezone;
    if (cfg.budget_warning_threshold  != null) { _budgetWarning  = cfg.budget_warning_threshold;  document.getElementById('budgetWarningInput').value  = cfg.budget_warning_threshold; }
    if (cfg.budget_critical_threshold != null) { _budgetCritical = cfg.budget_critical_threshold; document.getElementById('budgetCriticalInput').value = cfg.budget_critical_threshold; }
    _updateBulletLegend();
  } catch (e) { _updateBulletLegend(); /* use defaults */ }
}

document.getElementById('saveConfigBtn').addEventListener('click', async () => {
  const em  = parseFloat(document.getElementById('extraMultiplierInput').value);
  const sm  = parseFloat(document.getElementById('standbyMultiplierInput').value);
  const tz  = document.getElementById('timezoneSelect').value;
  const wt  = parseFloat(document.getElementById('budgetWarningInput').value);
  const ct  = parseFloat(document.getElementById('budgetCriticalInput').value);
  const msg = document.getElementById('configMsg');
  if (isNaN(em) || isNaN(sm) || em <= 0 || sm <= 0 || isNaN(wt) || isNaN(ct) || wt <= 0 || ct <= 0) {
    msg.style.color = _cssVar('--red');
    msg.textContent = _t('msg.positive_numbers');
    return;
  }
  try {
    await apiFetchJSON('/api/config', 'PUT', {
      extra_hours_multiplier: em,
      standby_hours_multiplier: sm,
      anomaly_max_daily_hours: _anomalyMaxHours,
      timezone: tz,
      budget_warning_threshold: wt,
      budget_critical_threshold: ct,
    });
    _budgetWarning  = wt;
    _budgetCritical = ct;
    _updateBulletLegend();
    msg.style.color = _cssVar('--green');
    msg.textContent = _t('msg.config_saved');
    setTimeout(() => { msg.textContent = ''; }, 3000);
  } catch (e) {
    msg.style.color = _cssVar('--red');
    msg.textContent = e.message;
  }
});

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Auth helpers
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

async function apiFetch(url) {
  const res = await fetch(url, { headers: _authHeaders() });
  if (res.status === 401) { _handleUnauthorized(); throw new Error('Sessão expirada. Faça login novamente.'); }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: _authHeaders({ 'Content-Type': 'application/json' }),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { _handleUnauthorized(); throw new Error('Sessão expirada. Faça login novamente.'); }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  const textEl = document.getElementById('notificationText');
  clearTimeout(el._timer);
  textEl.textContent = msg;
  el.className = type;
  el.hidden = false;
  if (type !== 'error') {
    el._timer = setTimeout(() => { el.hidden = true; }, 6000);
  }
}
document.getElementById('notificationClose').addEventListener('click', () => {
  const el = document.getElementById('notification');
  clearTimeout(el._timer);
  el.hidden = true;
});

function fmt(h) {
  return Number(h).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  });
}

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
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

document.getElementById('logoutBtn').addEventListener('click', () => {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('username');
  sessionStorage.removeItem('role');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
});

document.getElementById('collabDetailClose').addEventListener('click', _closeCollabDetail);
document.getElementById('calPrevMonth').addEventListener('click', async () => {
  if (!_selectedCollaborator) return;
  _calMonth--;
  if (_calMonth < 1) { _calMonth = 12; _calYear--; }
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});
document.getElementById('calNextMonth').addEventListener('click', async () => {
  if (!_selectedCollaborator) return;
  const now = new Date();
  if (_calYear > now.getFullYear() || (_calYear === now.getFullYear() && _calMonth >= now.getMonth() + 1)) return;
  _calMonth++;
  if (_calMonth > 12) { _calMonth = 1; _calYear++; }
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});
document.getElementById('calMonthInput').addEventListener('change', async () => {
  if (!_selectedCollaborator) return;
  const val = document.getElementById('calMonthInput').value;
  if (!val) return;
  const [y, m] = val.split('-').map(Number);
  _calYear = y; _calMonth = m;
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});

// ---------------------------------------------------------------------------
// Users management (Admin tab)
// ---------------------------------------------------------------------------
let _allUsers = [];

const _usersPag = _makePaginator(
  { container: 'usersPagination', prev: 'usersPrevBtn', next: 'usersNextBtn', pageSize: 'usersPageSize', label: 'usersPageLabel' },
  rows => {
    const selfId = _getTokenPayload()?.sub ?? null;
    _renderTable('usersBody', rows, {
      colspan: 3,
      emptyKey: 'no_users',
      rowFn: u => `
    <tr>
      <td>${escHtml(u.username)}</td>
      <td><span class="badge-status ${u.role === 'admin' ? 'ativo' : 'quarantine'}">${u.role === 'admin' ? _t('lbl.admin') : _t('lbl.user')}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openPwdModal(${u.id})">${_t('btn.pwd')}</button>
        ${u.username !== selfId ? `<button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, ${escHtml(JSON.stringify(u.username))})">${_t('btn.delete')}</button>` : ''}
      </div></td>
    </tr>`,
    });
  }
);

document.getElementById('userSearch').addEventListener('input', e => {
  _usersPag.reset();
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allUsers.filter(u =>
    u.username.toLowerCase().includes(q) || (u.role || '').toLowerCase().includes(q)
  ) : _allUsers;
  _renderUsersTable(_applySort('usersTable', filtered));
});

async function loadUsersTable() {
  _usersPag.reset();
  await _loadTable('/api/users', data => {
    _allUsers = data;
    _renderUsersTable(_applySort('usersTable', _allUsers));
  });
}

function _renderUsersTable(users) { _usersPag.render(users); }

document.getElementById('newUserBtn').addEventListener('click', () => {
  document.getElementById('userUsernameInput').value = '';
  document.getElementById('userPasswordInput').value = '';
  document.getElementById('userRoleSelect').value    = 'user';
  document.getElementById('userError').textContent   = '';
  openModal('userModal');
});

document.getElementById('userModalClose').addEventListener('click',  () => { closeModal('userModal'); });
document.getElementById('userCancelBtn').addEventListener('click',   () => { closeModal('userModal'); });

document.getElementById('userSaveBtn').addEventListener('click', async () => {
  const username = document.getElementById('userUsernameInput').value.trim();
  const password = document.getElementById('userPasswordInput').value;
  const role     = document.getElementById('userRoleSelect').value;
  const errEl    = document.getElementById('userError');
  errEl.textContent = '';
  if (!username || !password) { errEl.textContent = _t('msg.fields_required'); return; }
  try {
    await apiFetchJSON('/api/users', 'POST', { username, password, role });
    closeModal('userModal');
    loadUsersTable();
    notify(_t('msg.user_created'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

function openPwdModal(userId) {
  document.getElementById('pwdTargetId').value  = userId;
  document.getElementById('pwdNewInput').value  = '';
  document.getElementById('pwdError').textContent = '';
  openModal('pwdModal');
}

document.getElementById('pwdModalClose').addEventListener('click', () => { closeModal('pwdModal'); });
document.getElementById('pwdCancelBtn').addEventListener('click',  () => { closeModal('pwdModal'); });

document.getElementById('pwdSaveBtn').addEventListener('click', async () => {
  const userId      = document.getElementById('pwdTargetId').value;
  const new_password = document.getElementById('pwdNewInput').value;
  const errEl       = document.getElementById('pwdError');
  errEl.textContent = '';
  if (!new_password) { errEl.textContent = _t('msg.pwd_field_required'); return; }
  try {
    await apiFetchJSON(`/api/users/${userId}/password`, 'PATCH', { new_password });
    closeModal('pwdModal');
    notify(_t('msg.pwd_changed'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

function deleteUser(id, username) {
  confirmDialog(_t('confirm.delete_user'), async () => {
    try {
      await apiFetchJSON(`/api/users/${id}`, 'DELETE');
      loadUsersTable();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

// ---------------------------------------------------------------------------
// Audit Log (Admin tab)
// ---------------------------------------------------------------------------

let _auditLogCache = [];

const _auditPag = _makePaginator(
  { container: 'auditPagination', prev: 'auditPrevBtn', next: 'auditNextBtn', pageSize: 'auditPageSize', label: 'auditPageLabel' },
  rows => _renderTable('auditBody', rows, {
    colspan: 6,
    emptyKey: 'no_audit',
    rowFn: r => {
      const when = new Date(r.timestamp).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
      let detail = '';
      if (r.detail) {
        try {
          const obj = JSON.parse(r.detail);
          detail = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ');
        } catch { detail = r.detail; }
      }
      return `<tr>
      <td style="white-space:nowrap">${escHtml(when)}</td>
      <td>${escHtml(r.username || '—')}</td>
      <td><code>${escHtml(r.action)}</code></td>
      <td>${escHtml(r.entity)}</td>
      <td style="text-align:right">${r.entity_id ?? '—'}</td>
      <td style="font-size:.78rem;color:#94a3b8;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(detail)}">${escHtml(detail)}</td>
    </tr>`;
    },
  })
);

async function loadAuditLog() {
  _auditPag.reset();
  const entity = document.getElementById('auditEntityFilter').value;
  const action = document.getElementById('auditActionFilter').value;
  const params = new URLSearchParams({ limit: 200 });
  if (entity) params.set('entity', entity);
  if (action) params.set('action', action);
  await _loadTable(`/api/audit-log?${params}`, data => {
    _auditLogCache = data;
    _renderAuditLog(_applySort('auditTable', _auditLogCache));
  });
}

function _renderAuditLog(rows) { _auditPag.render(rows); }

document.getElementById('auditRefreshBtn').addEventListener('click', loadAuditLog);
document.getElementById('auditEntityFilter').addEventListener('change', loadAuditLog);
document.getElementById('auditActionFilter').addEventListener('change', loadAuditLog);

// ---------------------------------------------------------------------------
// Chart series names (for color picker UI) — evaluated lazily so _t() returns
// the active locale at call time instead of the locale at module load.
// ---------------------------------------------------------------------------
function _chartSeriesNames(chartId) {
  const map = {
    effortChart:   [_t('ch.normal_h'),        _t('ch.extra_h'),          _t('ch.standby_h')],
    trendsChart:   [_t('ch.normal_h'),        _t('ch.extra_h'),          _t('ch.standby_h')],
    treemapChart:  [],
    bulletChart:   [_t('bullet.planned'),     _t('bullet.realized')],
    scatterChart:  [],
    forecastChart: [_t('forecast.realized'),  _t('forecast.projection'), _t('forecast.budget_line')],
  };
  return map[chartId] ?? [];
}

// ---------------------------------------------------------------------------
// Theme presets
// ---------------------------------------------------------------------------
const _THEME_PRESETS = {
  pmas: {
    color_primary: '#4f8ef7', color_background: '#081122',
    color_surface: '#0e2038', color_accent: '#07b3d7',
    color_success: '#5ad388', color_warning: '#d9b273',
    color_danger:  '#c56d76', color_text: '#e0e0e0',
    color_text_muted: '#818998', density: 'normal',
    chart_palette: ['#4f8ef7','#d9b273','#a78bfa','#35a1f3','#5ad388','#01c1b9'],
  },
  corporate: {
    color_primary: '#0070f3', color_background: '#0a0a23',
    color_surface: '#111133', color_accent: '#00d4ff',
    color_success: '#00c853', color_warning: '#ffab00',
    color_danger:  '#ff1744', color_text: '#f0f4ff',
    color_text_muted: '#7986cb', density: 'normal',
    chart_palette: ['#0070f3','#00d4ff','#00c853','#ffab00','#7c4dff','#26c6da'],
  },
  high_contrast: {
    color_primary: '#ffffff', color_background: '#000000',
    color_surface: '#111111', color_accent: '#ffff00',
    color_success: '#00ff00', color_warning: '#ff8800',
    color_danger:  '#ff0000', color_text: '#ffffff',
    color_text_muted: '#aaaaaa', density: 'relaxed',
    chart_palette: ['#ffffff','#ffff00','#00ff00','#ff8800','#00ffff','#ff00ff'],
  },
};

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

    // Density
    const density = _DENSITY_MAP[t.density] || _DENSITY_MAP.normal;
    root.style.setProperty('--density-spacing',   density.spacing);
    root.style.setProperty('--density-font-size', density.fontSize);

    // Font family
    if (t.font_family) root.style.setProperty('--font-family', t.font_family);

    // Chart palette
    window._CHART_PALETTE = t.chart_palette?.length ? t.chart_palette : undefined;

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

// ---------------------------------------------------------------------------
// My Area tab
// ---------------------------------------------------------------------------
let _currentUserInfo = null;

function _switchMyTab(tabId) {
  document.querySelectorAll('.my-tab-btn').forEach(btn => {
    const active = btn.dataset.myTab === tabId;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.my-tab-section').forEach(el => {
    el.hidden = el.id !== `my-tab-${tabId}`;
  });
  if (tabId === 'upload') { loadMyHistory(); loadMyQr(); }
}

document.querySelectorAll('.my-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => _switchMyTab(btn.dataset.myTab));
});

function _initMyArea() {
  const usernameEl = document.getElementById('myProfileUsername');
  if (usernameEl) {
    const payload = _getTokenPayload() || {};
    const stored  = sessionStorage.getItem('username') || payload.sub || '—';
    const role    = payload.role || '';
    usernameEl.textContent = `${stored} (${role})`;
    _currentUserInfo = { username: stored, role };
  }
  _initChartLayout();
  _loadMyPreferences();
}

// Chart layout drag-drop
let _sortableLayout = null;
const _panelSortables = {};
function _initChartLayout() {
  const list = document.getElementById('chartLayoutList');
  if (!list || typeof Sortable === 'undefined') return;
  if (_sortableLayout) _sortableLayout.destroy();
  _sortableLayout = Sortable.create(list, { animation: 150, handle: '.tab-handle' });
  ['effort', 'portfolio', 'forecast'].forEach(tabId => {
    const pList = document.getElementById(`panelList-${tabId}`);
    if (!pList) return;
    if (_panelSortables[tabId]) _panelSortables[tabId].destroy();
    _panelSortables[tabId] = Sortable.create(pList, { animation: 120, handle: '.panel-handle' });
  });
}

async function _loadMyPreferences() {
  try {
    _userPrefs = await apiFetch('/api/my/preferences');
    _applyLayoutPreferences();
    const order = _userPrefs?.dashboard?.chart_order;
    if (Array.isArray(order)) {
      const list = document.getElementById('chartLayoutList');
      if (list) {
        const items = [...list.querySelectorAll(':scope > .sortable-item')];
        order.forEach(chartId => {
          const item = items.find(i => i.dataset.chart === chartId);
          if (item) list.appendChild(item);
        });
      }
    }
    const panelOrder = _userPrefs?.dashboard?.panel_order || {};
    Object.entries(panelOrder).forEach(([tabId, panelIds]) => {
      const pList = document.getElementById(`panelList-${tabId}`);
      if (!pList) return;
      const items = [...pList.querySelectorAll(':scope > .sortable-item')];
      panelIds.forEach(pid => {
        const item = items.find(i => i.dataset.panel === pid);
        if (item) pList.appendChild(item);
      });
    });
  } catch (_) {}
}

function _applyLayoutPreferences() {
  const prefs = _userPrefs?.dashboard;
  if (!prefs) return;

  // Sub-tab order (reorder nav buttons + sections)
  const order = prefs.chart_order;
  if (Array.isArray(order) && order.length) {
    const nav = document.querySelector('.analytics-tabs');
    const firstSection = document.querySelector('.atab-section');
    const parent = firstSection?.parentElement;
    order.forEach(tabId => {
      const btn = nav?.querySelector(`[data-atab="${tabId}"]`);
      if (btn) nav.appendChild(btn);
      const section = document.getElementById(`atab-${tabId}`);
      if (section && parent) parent.appendChild(section);
    });
  }

  // Panel order within each dashboard tab
  const panelOrder = prefs.panel_order || {};
  Object.entries(panelOrder).forEach(([tabId, panelIds]) => {
    const section = document.getElementById(`atab-${tabId}`);
    if (!section) return;
    panelIds.forEach(panelId => {
      const panel = section.querySelector(`[data-panel-id="${panelId}"]`);
      if (panel) section.appendChild(panel);
    });
  });

  // Grid columns — apply to each visible atab-section
  if (prefs.grid_cols && prefs.grid_cols > 1) {
    document.querySelectorAll('.atab-section').forEach(s => {
      s.dataset.cols = prefs.grid_cols;
    });
  } else {
    document.querySelectorAll('.atab-section').forEach(s => {
      delete s.dataset.cols;
    });
  }

  // Per-chart size and order (visibility stays under business-logic control)
  (prefs.charts || []).forEach(cp => {
    const panel = document.querySelector(`[data-chart-id="${cp.id}"]`);
    if (!panel) return;
    if (cp.size) panel.dataset.size = cp.size;
    if (cp.order != null) panel.style.order = cp.order;
  });

  Object.values(_charts).forEach(c => {
    try { if (!c.isDisposed()) c.resize(); } catch (_) {}
  });
}

document.getElementById('saveLayoutBtn')?.addEventListener('click', async () => {
  const list = document.getElementById('chartLayoutList');
  if (!list) return;
  const order = [...list.querySelectorAll(':scope > .sortable-item')].map(i => i.dataset.chart);
  const panelOrder = {};
  ['effort', 'portfolio', 'forecast'].forEach(tabId => {
    const pList = document.getElementById(`panelList-${tabId}`);
    if (pList) panelOrder[tabId] = [...pList.querySelectorAll(':scope > .sortable-item')].map(i => i.dataset.panel);
  });
  try {
    _userPrefs = await apiFetchJSON('/api/my/preferences', 'PUT', { dashboard: { chart_order: order, panel_order: panelOrder } });
    _applyLayoutPreferences();
    notify(_t('msg.layout_saved'), 'success');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
});

// My Area — change password
document.getElementById('myChangePwdBtn')?.addEventListener('click', () => {
  document.getElementById('myCurrentPwdInput').value = '';
  document.getElementById('myNewPwdInput').value = '';
  document.getElementById('myPwdError').textContent = '';
  openModal('myPwdModal');
});
document.getElementById('myPwdModalClose')?.addEventListener('click', () => {
  closeModal('myPwdModal');
});
document.getElementById('myPwdCancelBtn')?.addEventListener('click', () => {
  closeModal('myPwdModal');
});
document.getElementById('myPwdSaveBtn')?.addEventListener('click', async () => {
  const currentPwd = document.getElementById('myCurrentPwdInput').value.trim();
  const newPwd     = document.getElementById('myNewPwdInput').value.trim();
  const errEl      = document.getElementById('myPwdError');
  errEl.textContent = '';
  if (!currentPwd || !newPwd) { errEl.textContent = _t('msg.pwd_fill_all'); return; }
  try {
    const stored = sessionStorage.getItem('username') || '';
    // Find own user id first
    const users = await apiFetch('/api/users');
    const me = users.find(u => u.username === stored);
    if (!me) { errEl.textContent = _t('msg.user_not_found'); return; }
    await apiFetchJSON(`/api/users/${me.id}/password`, 'PATCH', {
      new_password: newPwd,
      current_password: currentPwd,
    });
    closeModal('myPwdModal');
    notify(_t('msg.pwd_changed'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

// ---------------------------------------------------------------------------
// My Area — Upload sub-tab
// ---------------------------------------------------------------------------
document.getElementById('myAreaCsvInput')?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const resultEl = document.getElementById('myAreaUploadResult');
  resultEl.textContent = _t('loading');
  try {
    const fd = new FormData();
    fd.append('file', file);
    const resp = await fetch('/api/upload-timesheet', {
      method: 'POST',
      headers: _authHeaders(),
      body: fd,
    });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || resp.statusText);
    _showIngestResult(json, file.name);
    const msg = `✅ ${json.records_inserted} ${_t('upload.inserted')}${json.quarantine_records_added ? ` · ⚠ ${json.quarantine_records_added} ${_t('upload.quarantine')}` : ''}`;
    resultEl.textContent = msg;
    notify(msg, json.quarantine_records_added ? 'warning' : 'success');
    _refreshTabBadges();
    loadMyHistory();
    loadMyQr();
  } catch (e) {
    resultEl.textContent = `${_t('msg.err_generic')}: ${e.message}`;
    notify(e.message, 'error');
  }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// My Area — Histórico sub-tab
// ---------------------------------------------------------------------------
let _myHistoryCache = [];

const _historyPag = _makePaginator(
  { container: 'myHistoryPagination', prev: 'myHistoryPrevBtn', next: 'myHistoryNextBtn', pageSize: 'myHistoryPageSize', label: 'myHistoryPageLabel' },
  rows => _renderTable('myHistoryBody', rows, {
    colspan: 9,
    emptyKey: 'msg.no_import_sessions',
    rowFn: r => {
      const when = new Date(r.uploaded_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
      const statusKey = r.status === 'ok' ? 'history.status.ok'
        : r.status === 'warnings' ? 'history.status.warnings'
        : r.status === 'quarantine' ? 'history.status.quarantine'
        : 'history.status.rejected';
      const warnCell = r.warning_count > 0 ? `<strong style="color:${_cssVar('--amber')}">${r.warning_count}</strong>` : '0';
      const infoCell = r.info_count    > 0 ? `<strong style="color:${_cssVar('--primary')}">${r.info_count}</strong>`    : '0';
      return `<tr style="cursor:pointer" onclick="_openSessionDetail(${r.id})" title="Clique para ver detalhes">
      <td style="white-space:nowrap;font-size:.78rem">${escHtml(when)}</td>
      <td style="font-size:.78rem">${escHtml(r.source_file)}</td>
      <td style="font-size:.78rem">${escHtml(r.uploaded_by_username)}</td>
      <td style="text-align:right">${r.records_inserted}</td>
      <td style="text-align:right">${r.records_skipped}</td>
      <td style="text-align:right">${r.quarantine_added > 0 ? `<strong style="color:${_cssVar('--red')}">${r.quarantine_added}</strong>` : '0'}</td>
      <td style="text-align:right">${warnCell}</td>
      <td style="text-align:right">${infoCell}</td>
      <td>${escHtml(_t(statusKey))}</td>
    </tr>`;
    },
  })
);

async function loadMyHistory() {
  _historyPag.reset();
  await _loadTable('/api/upload-history', data => {
    _myHistoryCache = data;
    _renderMyHistory(_applySort('myHistoryTable', _myHistoryCache));
  });
}

function _renderMyHistory(rows) {
  const filter = document.getElementById('myHistoryFilter')?.value || '';
  const filtered = filter ? rows.filter(r => r.status === filter) : rows;
  _historyPag.render(filtered);
}

document.getElementById('myHistoryFilter')?.addEventListener('change', () => {
  _historyPag.reset();
  _renderMyHistory(_applySort('myHistoryTable', _myHistoryCache));
});
document.getElementById('myHistoryExportBtn')?.addEventListener('click', () => {
  const rows = _historyPag.getRows();
  if (!rows.length) { notify(_t('msg.no_import_sessions'), 'info'); return; }
  const esc = v => (v == null || v === '') ? '' : `"${String(v).replace(/"/g, '""')}"`;
  const header = ['Quando','Arquivo','Enviado por','Inseridos','Ignorados','Quarentena','Avisos','Infos','Status'];
  const lines = rows.map(r => {
    const when = new Date(r.uploaded_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    return [esc(when), esc(r.source_file), esc(r.uploaded_by_username),
      r.records_inserted, r.records_skipped, r.quarantine_added,
      r.warning_count, r.info_count, esc(r.status)].join(',');
  });
  const blob = new Blob(['﻿' + [header.join(','), ...lines].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), { href: url, download: 'historico_importacoes.csv' }).click();
  URL.revokeObjectURL(url);
});

// ---------------------------------------------------------------------------
// My Area — Quarentena sub-tab
// ---------------------------------------------------------------------------
let _myQrCache = [];

async function loadMyQr() {
  _myQrPag.reset();
  const filter = document.getElementById('myQrFilter')?.value;
  const params = new URLSearchParams({ limit: 500 });
  if (filter === 'pending')   params.set('review_status', 'pending');
  if (filter === 'approved')  params.set('review_status', 'approved');
  if (filter === 'rejected')  params.set('review_status', 'rejected');
  await _loadTable(`/api/my/quarantine?${params}`, data => {
    _myQrCache = data;
    _qrCache = _myQrCache;
    _renderMyQrTable(_applySort('myQrTable', _myQrCache));
  });
}

const _myQrPag = _makePaginator(
  { container: 'myQrPagination', prev: 'myQrPrevBtn', next: 'myQrNextBtn', pageSize: 'myQrPageSize', label: 'myQrPageLabel' },
  rows => {
    const tbody = document.getElementById('myQrBody');
    if (!tbody) return;
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">${_t('msg.no_quarantine')}</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map(r => {
      const raw  = r.raw_data || {};
      const when = new Date(r.ingested_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
      return `<tr style="cursor:pointer" onclick="_openQRDetail(${r.id})">
      <td style="font-size:.78rem;white-space:nowrap">${escHtml(when)}</td>
      <td>${escHtml(raw['Colaborador'] || '—')}</td>
      <td style="font-size:.78rem">${escHtml(raw['Data'] || '—')}</td>
      <td style="text-align:right">${raw['Horas totais (decimal)'] ?? '—'}</td>
      <td style="font-size:.78rem">${escHtml(raw['Código PEP'] || '—')}</td>
      <td style="font-size:.78rem;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
          title="${escHtml(r.quarantine_reason)}">${escHtml(r.quarantine_reason)}</td>
      <td>${_qrStatusBadge(r.review_status)}</td>
    </tr>`;
    }).join('');
  }
);

function _renderMyQrTable(rows) { _myQrPag.render(rows); }

document.getElementById('myQrFilter')?.addEventListener('change', loadMyQr);

// ---------------------------------------------------------------------------
// My Area — Exportar quarentena (item 5)
// ---------------------------------------------------------------------------
document.getElementById('myQrExportBtn')?.addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/my/quarantine/export', { headers: _authHeaders() });
    if (!resp.ok) { notify(_t('msg.err_export_quarantine'), 'error'); return; }
    const blob = await resp.blob();
    const cd   = resp.headers.get('Content-Disposition') || '';
    const name = cd.match(/filename="([^"]+)"/)?.[1] || 'quarantine_export.csv';
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
});


// ---------------------------------------------------------------------------
// Validation Rules (Admin tab)
// ---------------------------------------------------------------------------
let _rules = [];
let _rulesSortable = null;
let _editingRuleId = null;

async function loadRulesList() {
  await _loadTable('/api/validation-rules', data => {
    _rules = data;
    _renderRulesList();
  });
}

function _renderRulesList() {
  const ul = document.getElementById('rulesList');
  if (!ul) return;
  if (!_rules.length) {
    ul.innerHTML = `<li style="text-align:center;color:#475569;padding:1rem;font-size:.85rem">${_t('vr.empty')}</li>`;
    return;
  }
  ul.innerHTML = _rules.map(r => {
    const actionBadge = `<span class="rule-badge ${r.action}">${r.action}</span>`;
    const systemBadge = r.is_system ? `<span class="rule-badge system">🔒 ${_t('vr.badge.system')}</span>` : '';
    const activeClass = r.is_active ? '' : 'rule-inactive';
    const editBtn  = r.is_system ? '' :
      `<button class="btn btn-secondary btn-sm" onclick="openEditRule(${r.id})">✎</button>`;
    const delBtn = r.is_system ? '' :
      `<button class="btn btn-danger btn-sm" onclick="deleteRule(${r.id})">✕</button>`;
    const toggleTitle = _t(r.is_active ? 'vr.btn.deactivate' : 'vr.btn.activate');
    return `<li class="sortable-item ${activeClass}" data-rule-id="${r.id}">
      <span class="sortable-handle">⠿</span>
      <span class="sortable-item-label">
        <strong>${escHtml(r.field)}</strong>
        <span style="color:#64748b;font-size:.75rem;margin:0 .3rem">${escHtml(r.operator)}</span>
        <span style="color:#e2e8f0">${escHtml(r.value || '—')}</span>
        ${r.description ? `<span style="color:#64748b;font-size:.75rem;margin-left:.5rem">— ${escHtml(r.description)}</span>` : ''}
      </span>
      ${actionBadge}${systemBadge}
      <div class="sortable-item-actions">
        <button class="btn btn-secondary btn-sm" title="${toggleTitle}" onclick="toggleRule(${r.id})">${r.is_active ? '⏸' : '▶'}</button>
        ${editBtn}${delBtn}
      </div>
    </li>`;
  }).join('');

  // Init SortableJS on rules list (non-system rules can be reordered)
  if (_rulesSortable) _rulesSortable.destroy();
  _rulesSortable = Sortable.create(ul, {
    animation: 150,
    handle: '.sortable-handle',
    onEnd: async () => {
      const items = [...ul.querySelectorAll('[data-rule-id]')];
      const orderMap = {};
      items.forEach((el, idx) => { orderMap[el.dataset.ruleId] = idx + 1; });
      try {
        await apiFetchJSON('/api/validation-rules/reorder', 'POST', orderMap);
        loadRulesList();
      } catch (e) { notify(`${_t('msg.rule_reorder_error')}: ${e.message}`, 'error'); }
    },
  });
}

const _AGGREGATE_RULE_FIELDS = new Set(['soma_diaria', 'soma_semanal']);

function _updateRuleActionOptions() {
  const field     = document.getElementById('ruleFieldInput')?.value;
  const actionSel = document.getElementById('ruleActionInput');
  const hintEl    = document.getElementById('ruleAggregateHint');
  if (!actionSel) return;
  const isAgg = _AGGREGATE_RULE_FIELDS.has(field);
  [...actionSel.options].forEach(opt => {
    if (opt.value === 'quarentena' || opt.value === 'descarte') {
      opt.disabled = isAgg;
    }
  });
  if (isAgg && (actionSel.value === 'quarentena' || actionSel.value === 'descarte')) {
    actionSel.value = 'warning';
  }
  if (hintEl) hintEl.hidden = !isAgg;
}

function _openRuleModal(rule = null) {
  _editingRuleId = rule ? rule.id : null;
  document.getElementById('ruleModalTitle').textContent = _t(rule ? 'vr.modal.edit' : 'vr.modal.new');
  document.getElementById('ruleFieldInput').value    = rule?.field    || 'horas_individuais';
  document.getElementById('ruleOperatorInput').value = rule?.operator || 'gt';
  document.getElementById('ruleValueInput').value    = rule?.value    || '';
  document.getElementById('ruleActionInput').value   = rule?.action   || 'warning';
  document.getElementById('ruleOrderInput').value    = rule?.order    || 10;
  document.getElementById('ruleActiveInput').value   = rule ? (rule.is_active ? 'true' : 'false') : 'true';
  document.getElementById('ruleDescInput').value     = rule?.description || '';
  document.getElementById('ruleError').textContent   = '';
  _updateRuleActionOptions();
  openModal('ruleModal');
}

function openEditRule(id) {
  const rule = _rules.find(r => r.id === id);
  if (rule) _openRuleModal(rule);
}

document.getElementById('ruleFieldInput')?.addEventListener('change', _updateRuleActionOptions);
document.getElementById('newRuleBtn')?.addEventListener('click', () => _openRuleModal());
document.getElementById('ruleModalClose')?.addEventListener('click',  () => closeModal('ruleModal'));
document.getElementById('ruleCancelBtn')?.addEventListener('click',   () => closeModal('ruleModal'));

document.getElementById('ruleSaveBtn')?.addEventListener('click', async () => {
  const errEl = document.getElementById('ruleError');
  errEl.textContent = '';
  const payload = {
    field:       document.getElementById('ruleFieldInput').value,
    operator:    document.getElementById('ruleOperatorInput').value,
    value:       document.getElementById('ruleValueInput').value || null,
    action:      document.getElementById('ruleActionInput').value,
    order:       parseInt(document.getElementById('ruleOrderInput').value) || 10,
    is_active:   document.getElementById('ruleActiveInput').value === 'true',
    description: document.getElementById('ruleDescInput').value || null,
  };
  try {
    if (_editingRuleId) {
      await apiFetchJSON(`/api/validation-rules/${_editingRuleId}`, 'PUT', payload);
    } else {
      await apiFetchJSON('/api/validation-rules', 'POST', payload);
    }
    closeModal('ruleModal');
    loadRulesList();
    notify(_t('vr.saved'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

async function toggleRule(id) {
  try {
    await apiFetchJSON(`/api/validation-rules/${id}/toggle`, 'PATCH');
    loadRulesList();
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

function deleteRule(id) {
  confirmDialog(_t('confirm.delete_rule'), async () => {
    try {
      await apiFetchJSON(`/api/validation-rules/${id}`, 'DELETE');
      loadRulesList();
      notify(_t('msg.rule_deleted'), 'success');
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

// ---------------------------------------------------------------------------
// Quarantine helpers (shared by My Area)
// ---------------------------------------------------------------------------
let _qrCache = [];

function _qrStatusBadge(status) {
  const cls = status === 'approved' ? 'ativo' : status === 'rejected' ? 'rejected' : 'suspenso';
  return `<span class="badge-status ${cls}">${_t('qr.status.' + status)}</span>`;
}

function _openQRDetail(id) {
  const r = _qrCache.find(x => x.id === id);
  if (!r) return;
  const raw = r.raw_data || {};

  document.getElementById('qrModalTitle').textContent = _t('qr.modal.title') + r.id;
  document.getElementById('qrDCollab').textContent    = raw['Colaborador'] || '—';
  document.getElementById('qrDDate').textContent      = raw['Data'] || '—';
  document.getElementById('qrDHours').textContent     = raw['Horas totais (decimal)'] ?? '—';
  document.getElementById('qrDPep').textContent       = (raw['Código PEP'] ? `${raw['Código PEP']} — ${raw['PEP'] || ''}` : '—');
  document.getElementById('qrDExtra').textContent     = raw['Hora extra'] || '—';
  document.getElementById('qrDStandby').textContent   = raw['Hora sobreaviso'] || '—';
  document.getElementById('qrDReason').textContent    = r.quarantine_reason;
  document.getElementById('qrDRule').textContent      = r.rule_description || (r.rule_id ? `Regra #${r.rule_id}` : '—');
  document.getElementById('qrDSession').textContent   = r.upload_session_id ?? '—';
  document.getElementById('qrDStatus').innerHTML      = _qrStatusBadge(r.review_status);
  document.getElementById('qrDReviewedBy').textContent = r.reviewed_by
    ? `${r.reviewed_by} em ${new Date(r.reviewed_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle:'short', timeStyle:'short' })}`
    : '—';
  document.getElementById('qrDRawData').textContent   = JSON.stringify(raw, null, 2);

  const isPending = r.review_status === 'pending';
  document.getElementById('qrApproveBtn').hidden = !isPending || !_isAdmin();
  document.getElementById('qrRejectBtn').hidden  = !isPending || !_isAdmin();

  document.getElementById('qrApproveBtn').onclick = () => _doQRAction(id, 'approve');
  document.getElementById('qrRejectBtn').onclick  = () => _doQRAction(id, 'reject');

  openModal('qrDetailModal');
}

async function _doQRAction(id, action) {
  try {
    const rec = await apiFetchJSON(`/api/quarantine/${id}/${action}`, 'POST', {});
    closeModal('qrDetailModal');
    if (action === 'approve' && rec?.raw_data) {
      const raw    = rec.raw_data;
      const collab = raw['Colaborador']             || '—';
      const date   = raw['Data']                    || '—';
      const hours  = raw['Horas totais (decimal)']  || '—';
      const pep    = raw['Código PEP'] || raw['PEP']|| '—';
      notify(`${_t('msg.qr_approved')}: ${collab} · ${date} · ${hours}h · ${pep}`, 'success');
    } else {
      notify(_t(action === 'approve' ? 'msg.qr_approved' : 'msg.qr_rejected'), 'success');
    }
    _refreshTabBadges();
    loadMyQr();
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

document.getElementById('qrModalClose')?.addEventListener('click',    () => closeModal('qrDetailModal'));
document.getElementById('qrModalCloseBtn')?.addEventListener('click', () => closeModal('qrDetailModal'));


// ---------------------------------------------------------------------------
// Session detail modal
// ---------------------------------------------------------------------------
async function _openSessionDetail(sessionId) {
  try {
    const endpoint = `/api/upload-history/${sessionId}`;
    const r = await apiFetch(endpoint);
    const modal  = document.getElementById('sessionDetailModal');
    const title  = document.getElementById('sessionDetailTitle');
    const meta   = document.getElementById('sessionDetailMeta');
    const counts = document.getElementById('sessionDetailCounts');
    const wDiv   = document.getElementById('sessionDetailWarnings');
    const wList  = document.getElementById('sessionDetailWarningsList');
    const iDiv   = document.getElementById('sessionDetailInfos');
    const iList  = document.getElementById('sessionDetailInfosList');

    const when = new Date(r.uploaded_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    title.textContent = `Importação — ${r.source_file}`;
    meta.innerHTML = [
      `<span style="color:#64748b">Data</span><span>${escHtml(when)}</span>`,
      `<span style="color:#64748b">Usuário</span><span>${escHtml(r.uploaded_by_username)}</span>`,
      `<span style="color:#64748b">Arquivo</span><span style="word-break:break-all">${escHtml(r.source_file)}</span>`,
      `<span style="color:#64748b">Status</span><span>${escHtml(r.status)}</span>`,
    ].join('');

    const chip = (label, val, color) =>
      `<span style="background:${color}22;color:${color};border:1px solid ${color}44;border-radius:.3rem;padding:.15rem .6rem;font-size:.78rem">${label}: <strong>${val}</strong></span>`;
    counts.innerHTML =
      chip('Inseridos',  r.records_inserted,        '#2ecc71') +
      chip('Ignorados',  r.records_skipped,          '#94a3b8') +
      chip('Quarentena', r.quarantine_added,         _cssVar('--red')) +
      chip('Avisos',     r.warning_count,            _cssVar('--amber')) +
      chip('Infos',      r.info_count,               '#60a5fa');

    const _exportDetailCsv = (items, label) => {
      const header = 'tipo,mensagem\n';
      const body = items.map(m => `"${label}","${String(m).replace(/"/g, '""')}"`).join('\n');
      const blob = new Blob([header + body], { type: 'text/csv' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${label.toLowerCase()}_${r.source_file.replace(/\.[^.]+$/, '')}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    };

    if (r.warnings_detail?.length) {
      wList.innerHTML = r.warnings_detail.map(w => `<li>${escHtml(w)}</li>`).join('');
      document.getElementById('sessionDetailWarningsHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#f59e0b;margin:0">⚠ Avisos</p>
         <button type="button" id="sdWarnCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdWarnCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.warnings_detail, 'Avisos')), 0);
      wDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailWarningsHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#f59e0b;margin:0">⚠ Avisos</p>`;
      wDiv.hidden = true;
    }
    if (r.infos_detail?.length) {
      iList.innerHTML = r.infos_detail.map(i => `<li>${escHtml(i)}</li>`).join('');
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#60a5fa;margin:0">ℹ Informações</p>
         <button type="button" id="sdInfoCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdInfoCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.infos_detail, 'Informações')), 0);
      iDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#60a5fa;margin:0">ℹ Informações</p>`;
      iDiv.hidden = true;
    }

    openModal('sessionDetailModal');
  } catch (e) { notify(`${_t('msg.err_load_details')}: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Theme editor (Admin tab)
// ---------------------------------------------------------------------------
const _THEME_FIELDS = [
  { key: 'color_primary',     label: 'Cor primária' },
  { key: 'color_background',  label: 'Fundo' },
  { key: 'color_surface',     label: 'Superfície' },
  { key: 'color_accent',      label: 'Destaque' },
  { key: 'color_success',     label: 'Sucesso' },
  { key: 'color_warning',     label: 'Alerta' },
  { key: 'color_danger',      label: 'Perigo' },
  { key: 'color_text',        label: 'Texto' },
  { key: 'color_text_muted',  label: 'Texto muted' },
];

let _currentTheme = {};

async function _loadThemeEditor() {
  try {
    _currentTheme = await fetch('/api/theme').then(r => r.json());
    _renderThemeEditor();
    _renderCustomPresets();
  } catch (e) { notify(`${_t('msg.err_load_theme')}: ${e.message}`, 'error'); }
}

function _applyThemePreset(key) {
  const preset = _THEME_PRESETS[key];
  if (!preset) return;
  _applyThemePresetConfig(preset);
}

function _applyThemePresetConfig(preset) {
  if (!preset) return;
  _THEME_FIELDS.forEach(f => {
    if (preset[f.key]) {
      const picker = document.getElementById(`themeColor_${f.key}`);
      const txt    = document.getElementById(`themeColorTxt_${f.key}`);
      if (picker) picker.value = preset[f.key];
      if (txt)    txt.value   = preset[f.key];
    }
  });
  if (preset.density) {
    document.querySelectorAll('.theme-density-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.density === preset.density);
    });
    const d = _DENSITY_MAP[preset.density] || _DENSITY_MAP.normal;
    document.documentElement.style.setProperty('--density-spacing',   d.spacing);
    document.documentElement.style.setProperty('--density-font-size', d.fontSize);
  }
  if (preset.chart_palette) {
    preset.chart_palette.forEach((c, i) => {
      const picker = document.getElementById(`themePalColor_${i}`);
      const txt    = document.getElementById(`themePalTxt_${i}`);
      if (picker) picker.value = c;
      if (txt)    txt.value   = c;
    });
  }
}

async function _renderCustomPresets() {
  const sel = document.getElementById('presetSelect');
  if (!sel) return;
  try {
    const presets = await fetch('/api/theme/presets').then(r => r.json());
    const builtin = presets.filter(p => p.is_builtin);
    const custom  = presets.filter(p => !p.is_builtin);
    const prev = sel.value;
    sel.innerHTML = `<option value="">${_t('appearance.preset_select_placeholder')}</option>`;
    if (builtin.length) {
      const grp = document.createElement('optgroup');
      grp.label = _t('appearance.presets');
      builtin.forEach(p => {
        const opt = new Option(p.name, `builtin:${p.id}`);
        opt.dataset.config = JSON.stringify(p.config);
        grp.appendChild(opt);
      });
      sel.appendChild(grp);
    }
    if (custom.length) {
      const grp = document.createElement('optgroup');
      grp.label = _t('appearance.my_presets');
      custom.forEach(p => {
        const opt = new Option(p.name, `custom:${p.id}`);
        opt.dataset.config = JSON.stringify(p.config);
        grp.appendChild(opt);
      });
      sel.appendChild(grp);
    }
    if (prev && sel.querySelector(`option[value="${prev}"]`)) sel.value = prev;
    _updatePresetDeleteBtn();
  } catch (e) { /* ignore */ }
}

function _updatePresetDeleteBtn() {
  const sel = document.getElementById('presetSelect');
  const btn = document.getElementById('presetDeleteBtn');
  if (!sel || !btn) return;
  const isCustom = sel.value.startsWith('custom:');
  btn.disabled = !isCustom;
  btn.style.opacity = isCustom ? '1' : '0.4';
}

function _loadSelectedPreset() {
  const sel = document.getElementById('presetSelect');
  const opt = sel?.options[sel.selectedIndex];
  if (!opt || !opt.dataset.config) return;
  try { _applyThemePresetConfig(JSON.parse(opt.dataset.config)); } catch (e) { /* ignore */ }
}

async function _deleteSelectedPreset() {
  const sel = document.getElementById('presetSelect');
  if (!sel?.value.startsWith('custom:')) return;
  const id   = parseInt(sel.value.split(':')[1], 10);
  const name = sel.options[sel.selectedIndex]?.text || '';
  confirmDialog(_t('confirm.delete_preset').replace('{name}', name), async () => {
    try {
      const resp = await fetch(`/api/theme/presets/${id}`, { method: 'DELETE', headers: _authHeaders() });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        notify(err.detail || _t('msg.err_delete_preset'), 'error');
        return;
      }
      notify(_t('appearance.preset_deleted'), 'success');
      _renderCustomPresets();
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
}

async function _deleteCustomPreset(id, name) {
  try {
    const resp = await fetch(`/api/theme/presets/${id}`, { method: 'DELETE', headers: _authHeaders() });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      notify(err.detail || _t('msg.err_delete_preset'), 'error');
      return;
    }
    notify(_t('appearance.preset_deleted'), 'success');
    _renderCustomPresets();
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _saveCurrentAsPreset() {
  const nameInput = document.getElementById('presetNameInput');
  const name = (nameInput?.value || '').trim();
  if (!name) { notify(_t('msg.name_required'), 'error'); return; }
  const payload = { ..._currentTheme };
  _THEME_FIELDS.forEach(f => {
    const txt = document.getElementById(`themeColorTxt_${f.key}`);
    if (txt) payload[f.key] = txt.value;
  });
  const appNameEl = document.getElementById('themeAppName');
  if (appNameEl) payload.app_name = appNameEl.value.trim() || 'PMAS';
  const activeBtn = document.querySelector('.theme-density-btn.active');
  if (activeBtn) payload.density = activeBtn.dataset.density;
  payload.chart_palette = Array.from({ length: 6 }, (_, i) => {
    return document.getElementById(`themePalTxt_${i}`)?.value || _THEME_PRESETS.pmas.chart_palette[i];
  });
  try {
    await apiFetchJSON('/api/theme/presets', 'POST', { name, config: payload });
    notify(_t('appearance.preset_saved'), 'success');
    if (nameInput) nameInput.value = '';
    _renderCustomPresets();
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _exportPresetsCSV() {
  try {
    const resp = await fetch('/api/theme/presets/export', { headers: _authHeaders() });
    if (!resp.ok) throw new Error(resp.statusText);
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'theme_presets.csv'; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
}

async function _importPresetsCSV(input) {
  const file = input.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const resp = await fetch('/api/theme/presets/import', {
      method: 'POST',
      headers: _authHeaders(),
      body: fd,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      notify(err.detail || `${_t('msg.err_import')}.`, 'error');
      return;
    }
    const data = await resp.json();
    const n = (data.created || 0) + (data.updated || 0);
    notify(_t('appearance.preset_imported').replace('{n}', n), 'success');
    _renderCustomPresets();
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  input.value = '';
}

function _renderThemeEditor() {
  const grid = document.getElementById('themeColorGrid');
  if (!grid) return;
  const t   = _currentTheme;
  const pal = t.chart_palette?.length ? t.chart_palette : _THEME_PRESETS.pmas.chart_palette;

  // Section: app name + density
  const densitySection = `
    <div class="form-group full" style="margin-bottom:.25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.app_name')}</label>
      <input type="text" id="themeAppName" value="${escHtml(t.app_name || 'PMAS')}"
        style="max-width:240px;margin-top:.25rem" />
    </div>
    <div class="form-group full" style="margin-bottom:.5rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.density')}</label>
      <div style="display:flex;gap:.5rem;margin-top:.25rem">
        ${['compact','normal','relaxed'].map(d => `
          <button class="btn btn-secondary btn-sm theme-density-btn${(t.density || 'normal') === d ? ' active' : ''}"
            data-density="${d}" type="button">${_t('appearance.density.'+d)}</button>
        `).join('')}
      </div>
    </div>`;

  // Section: profile (load + save presets in one row)
  const presetsSection = `
    <div class="form-group full" style="margin-bottom:.75rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.profile')}</label>
      <div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin-top:.35rem">
        <select id="presetSelect" onchange="_updatePresetDeleteBtn()"
          style="flex:2;min-width:180px;padding:.35rem .6rem;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:.82rem">
          <option value="">${_t('appearance.preset_select_placeholder')}</option>
        </select>
        <button type="button" class="btn btn-secondary btn-sm" onclick="_loadSelectedPreset()">${_t('appearance.preset_load')}</button>
        <button type="button" id="presetDeleteBtn" class="btn btn-sm" disabled
          style="padding:.3rem .6rem;background:transparent;color:#c56d76;border:1px solid #c56d76;border-radius:6px;opacity:.4"
          onclick="_deleteSelectedPreset()">${_t('appearance.preset_delete')}</button>
        <div style="width:1px;height:1.5rem;background:var(--border);margin:0 .25rem"></div>
        <input id="presetNameInput" type="text" placeholder="${_t('appearance.preset_name')}"
          style="flex:2;min-width:140px;padding:.35rem .6rem;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:.82rem">
        <button type="button" class="btn btn-primary btn-sm" onclick="_saveCurrentAsPreset()">${_t('appearance.save_preset')}</button>
        <button type="button" class="btn btn-secondary btn-sm" onclick="_exportPresetsCSV()">${_t('appearance.preset_export')}</button>
        <button type="button" class="btn btn-secondary btn-sm" onclick="document.getElementById('presetImportInput').click()">${_t('appearance.preset_import')}</button>
        <input id="presetImportInput" type="file" accept=".csv" style="display:none" onchange="_importPresetsCSV(this)">
      </div>
    </div>`;

  // Section: colors
  const colorSection = `
    <div class="form-group full" style="margin-bottom:.25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.colors')}</label>
    </div>
    ${_THEME_FIELDS.map(f => `
      <div class="form-group">
        <label style="font-size:.7rem;color:#94a3b8">${escHtml(f.label)}</label>
        <div class="theme-swatch-row">
          <input type="color" id="themeColor_${f.key}" value="${escHtml(t[f.key] || '#000000')}" />
          <input type="text" id="themeColorTxt_${f.key}" value="${escHtml(t[f.key] || '')}"
            style="flex:1;font-size:.8rem" />
        </div>
      </div>
    `).join('')}`;

  // Section: chart palette
  const paletteSection = `
    <div class="form-group full" style="margin:.5rem 0 .25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.palette')}</label>
    </div>
    ${Array.from({ length: 6 }, (_, i) => `
      <div class="form-group">
        <label style="font-size:.7rem;color:#94a3b8">Cor ${i + 1}</label>
        <div class="theme-swatch-row">
          <input type="color" id="themePalColor_${i}" value="${escHtml(pal[i] || '#4f8ef7')}" />
          <input type="text" id="themePalTxt_${i}" value="${escHtml(pal[i] || '')}"
            style="flex:1;font-size:.8rem" />
        </div>
      </div>
    `).join('')}`;

  grid.innerHTML = densitySection + presetsSection + colorSection + paletteSection;
  _renderCustomPresets();

  // Wire color pickers ↔ text inputs
  _THEME_FIELDS.forEach(f => {
    const picker = document.getElementById(`themeColor_${f.key}`);
    const txt    = document.getElementById(`themeColorTxt_${f.key}`);
    picker?.addEventListener('input', () => { txt.value = picker.value; });
    txt?.addEventListener('change',  () => { if (/^#[0-9a-f]{6}$/i.test(txt.value)) picker.value = txt.value; });
  });
  Array.from({ length: 6 }, (_, i) => {
    const picker = document.getElementById(`themePalColor_${i}`);
    const txt    = document.getElementById(`themePalTxt_${i}`);
    picker?.addEventListener('input', () => { txt.value = picker.value; });
    txt?.addEventListener('change',  () => { if (/^#[0-9a-f]{6}$/i.test(txt.value)) picker.value = txt.value; });
  });

  // Density button toggle — apply preview immediately
  grid.querySelectorAll('.theme-density-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      grid.querySelectorAll('.theme-density-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const d = _DENSITY_MAP[btn.dataset.density] || _DENSITY_MAP.normal;
      document.documentElement.style.setProperty('--density-spacing',   d.spacing);
      document.documentElement.style.setProperty('--density-font-size', d.fontSize);
    });
  });
}

document.getElementById('saveThemeBtn')?.addEventListener('click', async () => {
  const payload = { ..._currentTheme };
  _THEME_FIELDS.forEach(f => {
    const txt = document.getElementById(`themeColorTxt_${f.key}`);
    if (txt) payload[f.key] = txt.value;
  });
  const appNameEl = document.getElementById('themeAppName');
  if (appNameEl) payload.app_name = appNameEl.value.trim() || 'PMAS';
  const activeBtn = document.querySelector('.theme-density-btn.active');
  if (activeBtn) payload.density = activeBtn.dataset.density;
  payload.chart_palette = Array.from({ length: 6 }, (_, i) => {
    return document.getElementById(`themePalTxt_${i}`)?.value || _THEME_PRESETS.pmas.chart_palette[i];
  });
  try {
    _currentTheme = await apiFetchJSON('/api/theme', 'PUT', payload);
    _loadTheme();
    notify(_t('appearance.saved'), 'success');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
});

document.getElementById('restoreDefaultThemeBtn')?.addEventListener('click', () => {
  _applyThemePreset('pmas');
});

document.getElementById('logoUploadInput')?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const resp = await fetch('/api/theme/logo', {
      method: 'POST',
      headers: _authHeaders(),
      body: fd,
    });
    if (!resp.ok) throw new Error((await resp.json()).detail || resp.statusText);
    _currentTheme = await resp.json();
    _loadTheme();
    notify(_t('msg.logo_updated'), 'success');
  } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  e.target.value = '';
});

document.getElementById('deleteLogoBtn')?.addEventListener('click', () => {
  confirmDialog(_t('confirm.delete_logo'), async () => {
    try {
      _currentTheme = await apiFetchJSON('/api/theme/logo', 'DELETE');
      _loadTheme();
      notify(_t('msg.logo_removed'), 'success');
    } catch (e) { notify(`${_t('msg.err_generic')}: ${e.message}`, 'error'); }
  });
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
function _updateHeaderUser() {
  const el = document.getElementById('headerUserInfo');
  if (!el) return;
  const username = sessionStorage.getItem('username') || _getTokenPayload()?.sub || '';
  el.textContent = username || 'PMAS';
}

async function loadSemaphore() {
  const bar = document.getElementById('semaphoreBar');
  if (!bar) return;
  try {
    const data = await apiFetch('/api/v2/portfolio');
    if (!data.length) {
      bar.style.display = 'none';
      const hdr = document.getElementById('headerSemaphore');
      if (hdr) hdr.style.display = 'none';
      return;
    }

    // v2 returns health_hours and health_cost already classified by the server
    const _semClass = p => _healthToSemColor(p.health_hours || 'no_budget', p.health_cost || 'no_budget');

    const wPct = Math.round(_budgetWarning  * 100);
    const cPct = Math.round(_budgetCritical * 100);

    const counts = { green: 0, yellow: 0, red: 0, grey: 0 };
    const pills  = data.map(p => {
      const s = _semClass(p);
      counts[s]++;
      const pH = p.budget_hours ? (p.total_hours / p.budget_hours * 100).toFixed(0) + '% h' : '— h';
      const pC = p.budget_cost  ? (p.total_cost  / p.budget_cost  * 100).toFixed(0) + '% R$': '— R$';
      const tip = `${p.pep_wbs}: ${pH} · ${pC} — clique para detalhar`;
      return `<span class="sem-project ${s}" data-pep="${escHtml(p.pep_wbs)}" title="${escHtml(tip)}">${escHtml(p.pep_wbs)}</span>`;
    });

    const dot = (cls, label) => counts[cls]
      ? `<span class="sem-count" title="${label}"><span class="sem-dot ${cls}"></span>${counts[cls]}</span>`
      : '';

    const summaryHtml =
      `<span class="sem-title">${_t('sem.portfolio')}</span>
      ${dot('green',  _t('sem.ok_label').replace('{pct}', wPct))}
      ${dot('yellow', _t('sem.warning_label').replace('{pct}', wPct))}
      ${dot('red',    _t('sem.overrun_label').replace('{pct}', cPct))}
      ${dot('grey',   _t('sem.no_budget'))}`;

    bar.innerHTML =
      `<div class="sem-summary">${summaryHtml}</div>
      <div class="sem-divider"></div>
      <div class="sem-projects">${pills.join('')}</div>`;
    bar.style.display = 'flex';

    const hdr = document.getElementById('headerSemaphore');
    if (hdr) { hdr.innerHTML = summaryHtml; hdr.style.display = 'flex'; }
  } catch (_) {
    bar.style.display = 'none';
    const hdr = document.getElementById('headerSemaphore');
    if (hdr) hdr.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Semaphore drill-down: click a pill → filter Portfolio tab by that PEP
// ---------------------------------------------------------------------------
document.getElementById('semaphoreBar').addEventListener('click', e => {
  const pill = e.target.closest('[data-pep]');
  if (pill) _drillDownToPep(pill.dataset.pep);
});

async function _drillDownToPep(pepCode) {
  // Navigate to Dashboard tab
  document.querySelector('.tab-btn[data-tab="dashboard"]')?.click();

  // Reset all filters so we fetch the full PEP list, then pin to target PEP
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  await refreshPeps();
  if (!pepMs.items.some(i => String(i.value) === String(pepCode))) {
    notify(_t('msg.pep_not_available'), 'warning');
    return;
  }
  pepMs.selectOnly(pepCode);
  refreshPepDescriptions();

  // Switch to portfolio sub-tab programmatically and render
  _disposeTabCharts(_activeATab);
  document.querySelectorAll('.atab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.atab-section').forEach(s => { s.hidden = true; });
  const portfolioBtn = document.querySelector('.atab-btn[data-atab="portfolio"]');
  if (portfolioBtn) portfolioBtn.classList.add('active');
  _activeATab = 'portfolio';
  document.getElementById('atab-portfolio').hidden = false;

  await _renderPortfolioTab();
  document.getElementById('runwayPanel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------------------------------------------------------------------------
// Tab badges — pending quarantine indicators
// ---------------------------------------------------------------------------
async function _refreshTabBadges() {
  // Admin badge — pending quarantine records (admin only)
  if (_isAdmin()) {
    try {
      const rows = await apiFetch('/api/quarantine?review_status=pending');
      const badge = document.getElementById('adminTabBadge');
      if (badge) {
        const n = rows.length;
        if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
        else badge.setAttribute('hidden', '');
      }
    } catch (_) {}
  }
  // Minha Área badge — user's own pending quarantine records
  try {
    const rows = await apiFetch('/api/my/quarantine');
    const pending = rows.filter(r => r.review_status === 'pending');
    const badge = document.getElementById('myTabBadge');
    if (badge) {
      const n = pending.length;
      if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
      else badge.setAttribute('hidden', '');
    }
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Wire up sortable column headers
// ---------------------------------------------------------------------------
_makeSortable('cyclesTable',
  [{key:'name',type:'str'}, {key:'start_date',type:'date'}, {key:'end_date',type:'date'}, null, {key:'record_count',type:'num'}, null],
  () => { const q = document.getElementById('cycleSearch')?.value?.toLowerCase(); return q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles; },
  _renderCyclesTable
);
_makeSortable('projectsTable',
  [{key:'pep_wbs',type:'str'}, {key:'name',type:'str'}, {key:'client',type:'str'}, {key:'manager',type:'str'}, {key:'budget_hours',type:'num'}, {key:'status',type:'str'}, null],
  () => { const q = document.getElementById('projectSearch')?.value?.toLowerCase(); return q ? _allProjects.filter(p => (p.pep_wbs||'').toLowerCase().includes(q) || (p.name||'').toLowerCase().includes(q) || (p.client||'').toLowerCase().includes(q)) : _allProjects; },
  _renderProjectsTable
);
_makeSortable('seniorityTable',   [{key:'name',type:'str'}, null], () => _allSeniorityLevels, _renderSeniorityTable);
_makeSortable('rateCardTable',    [{key:'seniority_level_name',type:'str'}, {key:'hourly_rate',type:'num'}, {key:'valid_from',type:'date'}, {key:'valid_to',type:'date'}, null], () => _allRateCards, _renderRateCardsTable);
_makeSortable('teamTable',        [{key:'name',type:'str'}, {key:'seniority_level_name',type:'str'}, {key:'current_hourly_rate',type:'num'}, null], () => { const q = document.getElementById('teamSearch')?.value?.toLowerCase(); return q ? _allTeam.filter(t => t.name.toLowerCase().includes(q)) : _allTeam; }, _renderTeamTable);
_makeSortable('usersTable',       [{key:'username',type:'str'}, {key:'role',type:'str'}, null], () => { const q = document.getElementById('userSearch')?.value?.toLowerCase(); return q ? _allUsers.filter(u => u.username.toLowerCase().includes(q) || (u.role||'').toLowerCase().includes(q)) : _allUsers; }, _renderUsersTable);
_makeSortable('auditTable',       [{key:'timestamp',type:'date'}, {key:'username',type:'str'}, {key:'action',type:'str'}, {key:'entity',type:'str'}, {key:'entity_id',type:'num'}, null], () => _auditLogCache, _renderAuditLog);
_makeSortable('myHistoryTable',   [{key:'uploaded_at',type:'date'}, {key:'source_file',type:'str'}, {key:'uploaded_by_username',type:'str'}, {key:'records_inserted',type:'num'}, {key:'records_skipped',type:'num'}, {key:'quarantine_added',type:'num'}, {key:'warning_count',type:'num'}, {key:'info_count',type:'num'}, {key:'status',type:'str'}], () => _myHistoryCache, _renderMyHistory);
_makeSortable('myQrTable',        [{key:'ingested_at',type:'date'}, null, null, null, null, {key:'quarantine_reason',type:'str'}, {key:'review_status',type:'str'}], () => _myQrCache, _renderMyQrTable);
_makeSortable('runwayTable',      [{key:'pep_wbs',type:'str'}, {key:'name',type:'str'}, {key:'_sortPlanned',type:'num'}, null, {key:'_sortAvg',type:'num'}, {key:'cpi',type:'num'}, {key:'cycles_to_complete',type:'num'}, {key:'estimated_completion_cycle',type:'str'}, {key:'spi',type:'num'}, {key:'schedule_status',type:'str'}], () => (_lastRunwayData||[]).filter(r => _evmMode ? r.budget_cost != null : r.budget_hours != null).map(r => Object.assign({}, r, {_sortPlanned: _evmMode ? (r.budget_cost||0) : (r.budget_hours||0), _sortAvg: _evmMode ? (r.avg_cost_per_cycle||0) : (r.avg_hours_per_cycle||0)})), _drawRunwayRows);
_makeSortable('overAllocTable',   [{key:'collaborator',type:'str'}, {key:'date',type:'date'}, {key:'total_hours',type:'num'}, null], () => _overAllocData, rows => _renderOverAllocRows(rows));

function _bootApp() {
  if (_isAdmin()) document.getElementById('adminTabBtn').removeAttribute('hidden');
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  _loadTheme();
  _loadPreferences().then(() => _applyLayoutPreferences());
  _updateHeaderUser();
  _restoreFilterDates();
  loadDashboardCycles().then(() => {
    if (!_allCycles.length && _isAdmin()) _showOnboardingBanner();
  });
  loadSemaphore();
  loadGlobalConfig();
  _refreshTabBadges();
  _renderActiveTab();
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

document.getElementById('confirmModalClose')?.addEventListener('click', () => closeModal('confirmModal'));
document.getElementById('confirmModalCancel')?.addEventListener('click', () => closeModal('confirmModal'));

if (sessionStorage.getItem('access_token')) {
  document.getElementById('loginOverlay').setAttribute('hidden', '');
  document.getElementById('appShell').removeAttribute('hidden');
  _bootApp();
}
