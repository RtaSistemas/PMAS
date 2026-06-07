/* PMAS — Dashboard tab module
 * Extracted from app.js — MA-01 refactor
 */

// ---------------------------------------------------------------------------
// Dashboard — DOM refs and multi-selects
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Dirty-filter state — visual indicator when filters change without reloading
// ---------------------------------------------------------------------------
let _filtersDirty = false;
function _markFiltersDirty() {
  if (_filtersDirty) return;
  _filtersDirty = true;
  const btn = document.getElementById('loadBtn');
  if (btn) {
    btn.classList.add('btn-dirty');
    btn.setAttribute('aria-description', _t('filter.dirty_hint'));
    const span = btn.querySelector('[data-i18n="btn.load"]');
    if (span) span.textContent = _t('btn.load_update');
  }
}
function _clearFiltersDirty() {
  _filtersDirty = false;
  const btn = document.getElementById('loadBtn');
  if (btn) {
    btn.classList.remove('btn-dirty');
    btn.removeAttribute('aria-description');
    const span = btn.querySelector('[data-i18n="btn.load"]');
    if (span) span.textContent = _t('btn.load');
  }
}

const loadBtn  = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const _msRegistry = [];
function _createMS(el, placeholder, onChange) {
  const ms = new MultiSelect(el, placeholder, async () => {
    _markFiltersDirty();
    if (onChange) await onChange();
  });
  _msRegistry.push(ms);
  return ms;
}

const cycleMs        = _createMS(document.getElementById('cycleMs'),        _t('ms.cycle_ph'),    onCycleChange);
const pepMs          = _createMS(document.getElementById('pepMs'),           _t('ms.pep_ph'),      onPepChange);
const pepDescMs      = _createMS(document.getElementById('pepDescMs'),       _t('ms.pep_desc_ph'), onPepDescChange);
const collaboratorMs = _createMS(document.getElementById('collaboratorMs'),  _t('ms.collab_ph'),   onCollabChange);

document.getElementById('dateFromInput').addEventListener('change', _markFiltersDirty);
document.getElementById('dateToInput').addEventListener('change', _markFiltersDirty);

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
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

async function refreshPeps() {
  try {
    const filters = await apiFetch('/api/v2/filters');
    const peps = filters.peps;
    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();
  } catch (e) { notify(`${_t('msg.err_update_pep_filter')}: ${e.message}`, 'warning'); }
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
  } catch (e) { notify(`${_t('msg.err_update_collab_filter')}: ${e.message}`, 'warning'); }
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
    `<span style="font-weight:600;color:${_cssVar('--text')}">${escHtml(filename)}</span>` +
    chip('Inseridos',   json.records_inserted,         _cssVar('--green')) +
    chip('Ignorados',   json.records_skipped,           _cssVar('--text-3')) +
    chip('Quarentena',  json.quarantine_records_added,  _cssVar('--red')) +
    chip('Avisos',      json.warning_count,             _cssVar('--amber')) +
    chip('Infos',       json.info_count,                _cssVar('--primary'));

  let html = '';
  if (json.warnings?.length) {
    html += `<details open style="padding:.6rem 1rem;border-bottom:1px solid ${_cssVar('--surface')}">
      <summary style="cursor:pointer;color:${_cssVar('--amber')};font-weight:600;font-size:.8rem;list-style:none">⚠ ${json.warnings.length} aviso(s)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.warnings.map(w => `<li style="color:${_cssVar('--amber')};font-size:.79rem">${escHtml(w)}</li>`).join('')}
      </ul></details>`;
  }
  if (json.infos?.length) {
    html += `<details open style="padding:.6rem 1rem">
      <summary style="cursor:pointer;color:${_cssVar('--primary')};font-weight:600;font-size:.8rem;list-style:none">ℹ ${json.infos.length} informação(ões)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.infos.map(i => `<li style="color:${_cssVar('--primary')};font-size:.79rem">${escHtml(i)}</li>`).join('')}
      </ul></details>`;
  }
  details.innerHTML = html || `<p style="padding:.6rem 1rem;color:${_cssVar('--text-3')};font-size:.8rem;margin:0">${_t('msg.no_warnings_infos')}</p>`;
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
  document.documentElement.lang = _locale === 'pt' ? 'pt-BR' : 'en';
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
loadBtn.addEventListener('click', () => { _clearFiltersDirty(); _saveFilters(); _renderActiveTab(); });

clearBtn.addEventListener('click', () => {
  _clearFiltersDirty();
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  try { localStorage.removeItem('pmas_filters_v1'); } catch (_) {}
  pepDataCache = {};
  _evmMode = false;
  document.getElementById('evmToggleBtn').textContent = _t('btn.view_hours');
  _portfolioTimelineMode = false;
  const _tlBtn = document.getElementById('timelineToggleBtn');
  if (_tlBtn) { _tlBtn.textContent = _t('btn.timeline_on'); _tlBtn.className = 'btn btn-secondary btn-sm'; }
  _showTrajectory = false;
  const _trajBtn = document.getElementById('toggleTrajectoryBtn');
  if (_trajBtn) { _trajBtn.setAttribute('aria-pressed', 'false'); _trajBtn.className = 'btn btn-ghost btn-sm'; }
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
  _runwayPag.reset();
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

const _runwayPag = _makePaginator(
  { container: 'runwayPagination', prev: 'runwayPrevBtn', next: 'runwayNextBtn', pageSize: 'runwayPageSize', label: 'runwayPageLabel', entity: 'runway.title' },
  _drawRunwayRows
);
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
    notify(_friendlyError(err), 'error');
  }
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Portfolio Runway panel
// ---------------------------------------------------------------------------
function _riskColor(risk) {
  if (risk === 'ok') return _getPalette()[0] || _cssVar('--primary');
  const colors = {
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
  _runwayPag.reset();
  _runwayPag.render(_applySort('runwayTable', withBudget));
}

function _drawRunwayRows(data) {
  const tbody = document.getElementById('runwayBody');
  tbody.innerHTML = '';
  data.forEach(item => {
    const rawPct = _evmMode ? item.pct_consumed_cost : item.pct_consumed;
    const pct    = rawPct != null ? Math.min(rawPct, 100) : 0;

    const color = _riskColor(_evmMode ? item.cost_risk : item.risk);

    const absLabel = _evmMode
      ? _fmtCost(item.actual_cost, 0)
      : formatHours(item.consumed_hours);
    const pctLabel = rawPct != null ? `${rawPct.toFixed(1)}% (${absLabel})` : '—';
    const bar = `<div style="background:${_cssVar('--bg')};border-radius:3px;height:6px;width:120px">` +
      `<div style="height:6px;border-radius:3px;background:${color};width:${pct}%"></div></div>` +
      `<span style="font-size:.75rem;color:${_cssVar('--text-3')};margin-left:.4rem">${pctLabel}</span>`;

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
      const spiColor = item.spi_color === 'success' ? _getPalette()[0] : (_EVM_COLOR_CSS[item.spi_color] || _EVM_COLOR_CSS.warning);
      spiCell = `<span style="color:${spiColor};font-weight:600">${item.spi.toFixed(2)}</span>`;
    }

    const statusMap = {
      on_track:    { label: _t('runway.status.on_track')    || 'No prazo',     color: _getPalette()[0] || _cssVar('--primary') },
      at_risk:     { label: _t('runway.status.at_risk')     || 'Atenção',      color: _cssVar('--amber') },
      behind:      { label: _t('runway.status.behind')      || 'Atrasado',     color: _cssVar('--red') },
      no_baseline: { label: _t('runway.status.no_baseline') || 'Sem baseline', color: _cssVar('--text-3') },
    };
    const st = statusMap[item.schedule_status] || statusMap.no_baseline;
    const statusCell = `<span style="font-size:.78rem;font-weight:600;color:${st.color}">${st.label}</span>`;

    let cpiCell = '—';
    if (item.cpi != null) {
      const cpiColor = item.cpi_color === 'success' ? _getPalette()[0] : (_EVM_COLOR_CSS[item.cpi_color] || _EVM_COLOR_CSS.warning);
      cpiCell = `<span style="color:${cpiColor};font-weight:600">${item.cpi.toFixed(2)}</span>`;
    }

    const rowBg = (item.risk === 'critical' || item.risk === 'overrun')
      ? 'background:rgba(197,109,118,.07)'
      : '';

    const tr = document.createElement('tr');
    tr.style.cssText = rowBg;
    tr.innerHTML = `
      <td style="font-family:monospace;font-size:.82rem">${escHtml(item.pep_wbs)}</td>
      <td style="font-size:.82rem;color:${_cssVar('--text-3')}">${escHtml(item.name || '—')}</td>
      <td style="text-align:right">${_evmMode
        ? (item.budget_cost != null ? _fmtCost(item.budget_cost, 0) : '—')
        : (item.budget_hours != null ? item.budget_hours.toFixed(1) : '—')}</td>
      <td style="white-space:nowrap">${bar}</td>
      <td style="text-align:right">${_evmMode
        ? (item.avg_cost_per_cycle  != null ? _fmtCost(item.avg_cost_per_cycle, 0) : '—')
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
        `<span style="font-size:.78rem;color:${_cssVar('--text-3')};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100px" title="${escHtml(cName)}">${escHtml(cName)}</span>` +
        `<div style="flex:1;min-width:40px;max-width:80px;background:${_cssVar('--bg')};border-radius:2px;height:8px">` +
          `<div style="height:8px;border-radius:2px;background:${dotColor};width:${barWidth}%"></div>` +
        `</div>` +
        `<span style="font-size:.75rem;color:${_cssVar('--text-3')};white-space:nowrap">${pct.toFixed(0)}%</span>` +
        `</div>`;
    }).join('');

    const totalDisplay = _evmMode
      ? _fmtCost(item.total_cost, 0)
      : formatHours(item.total_hours, 0);

    const row = document.createElement('div');
    row.style.cssText = `display:flex;align-items:center;gap:1rem;padding:.4rem .5rem;border-radius:.35rem;background:${_cssVar('--card')}`;
    row.innerHTML = `
      <div style="min-width:14px;display:flex;align-items:center"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;flex-shrink:0;background:${dotColor}"></span></div>
      <div style="min-width:130px">
        <div style="font-family:monospace;font-size:.8rem;color:${_cssVar('--text')}">${escHtml(item.pep_wbs)}</div>
        <div style="font-size:.72rem;color:${_cssVar('--text-3')};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:130px" title="${escHtml(item.name || '')}">${escHtml(item.name || '')}</div>
      </div>
      <div style="display:flex;gap:.75rem;flex-wrap:wrap;flex:1">${barsHtml}</div>
      <div style="font-size:.72rem;color:${_cssVar('--text-3')};white-space:nowrap">${totalDisplay}</div>
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

  // by-cycle uses only PEP filter (no date range — cycle is the time axis)
  const byCycleP = new URLSearchParams();
  pepCodes.forEach(c => byCycleP.append('pep_wbs', c));

  _setChartLoading(['treemapChart'], true);
  try {
    const [health, trends, runway, concentration, byCycle] = await Promise.all([
      apiFetch(`/api/v2/portfolio?${p}`),
      apiFetch(`/api/v2/trends?${p}`).catch(() => []),
      apiFetch(`/api/v2/runway?${p}`).catch(() => []),
      apiFetch(`/api/v2/concentration?${p}`).catch(() => []),
      _portfolioTimelineMode
        ? apiFetch(`/api/v2/portfolio/by-cycle?${byCycleP}`).catch(() => [])
        : Promise.resolve([]),
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
    document.getElementById('portfolioTreemapTitle').textContent = _portfolioTimelineMode
      ? (_evmMode ? _t('portfolio.treemap_timeline_r') : _t('portfolio.treemap_timeline_h'))
      : (_evmMode ? _t('portfolio.treemap_r') : _t('portfolio.treemap_h'));

    // Treemap — dynamic height: 220px for ≤4 PEPs, +55px per extra PEP, cap 440px
    // Timeline mode adds 72px for the cycle scrubber
    const treemapBaseH = health.length <= 4 ? 220 : Math.min(440, 220 + (health.length - 4) * 55);
    document.getElementById('treemapChart').style.height =
      (_portfolioTimelineMode && byCycle.length ? treemapBaseH + 72 : treemapBaseH) + 'px';
    // Always dispose to avoid stale timeline component when switching modes
    if (_charts['treemapChart'] && !_charts['treemapChart'].isDisposed()) {
      _charts['treemapChart'].dispose();
      delete _charts['treemapChart'];
    }
    const tm = _getOrCreateChart('treemapChart');
    if (_portfolioTimelineMode && byCycle.length) {
      tm.setOption(_buildTimelineTreemapOption(byCycle, _evmMode), true);
    } else {
      tm.setOption(_buildTreemapOption(health, _evmMode), true);
    }
    tm.resize();

    // Bullet chart — in hours mode use budget_hours, in R$ mode use budget_cost
    const withBudget = _evmMode
      ? health.filter(d => d.budget_cost != null)
      : health.filter(d => d.budget_hours != null);
    if (withBudget.length > 0) {
      document.getElementById('bulletPanel').hidden = false;
      document.getElementById('bulletChart').style.height =
        `${Math.max(220, withBudget.length * 60 + 80)}px`;
      if (_charts['bulletChart'] && !_charts['bulletChart'].isDisposed()) {
        _charts['bulletChart'].dispose();
        delete _charts['bulletChart'];
      }
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
      sc.setOption(_buildEvmQuadrantOption(quadrantItems, _showTrajectory), true);
      sc.resize();
      sc.off('brushSelected');
      sc.on('brushSelected', params => {
        const indices = params.batch?.[0]?.selected?.[0]?.dataIndex ?? [];
        _renderScatterBrushResult(indices, quadrantItems);
      });
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
    notify(_friendlyError(err), 'error');
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

  const sym = _currencySymbol;
  const factor = _currencyFactor;

  const categories = filtered.map(t => t.cycle_name);
  const normalData  = filtered.map(t => +((t.normal_cost  || 0) * factor).toFixed(2));
  const extraData   = filtered.map(t => +((t.extra_cost   || 0) * factor).toFixed(2));
  const standbyData = filtered.map(t => +((t.standby_cost || 0) * factor).toFixed(2));

  const ZOOM_VISIBLE = 12;
  const needsZoom = categories.length > ZOOM_VISIBLE;
  const _zoomBase = {
    backgroundColor: _cssVar('--surface'), fillerColor: _cssVar('--primary') + '22',
    borderColor: _cssVar('--border'), brushSelect: false,
    handleStyle: { color: _cssVar('--primary') },
    textStyle:   { color: _cssVar('--text-3'), fontSize: 9 },
    startValue: 0, endValue: ZOOM_VISIBLE - 1,
  };
  const dataZoom = needsZoom ? [
    { ..._zoomBase, type: 'slider', xAxisIndex: 0, height: 14, bottom: 4, filterMode: 'filter' },
    { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: false, moveOnMouseWheel: true },
  ] : [];

  const pal = _getPalette();
  const cc = _getOrCreateChart('costCompositionChart');
  cc.setOption({
    ..._chartDefaults(),
    toolbox: _toolbox({
      magicType: { type: ['stack', 'tiled'], title: { stack: _t('toolbox.stack'), tiled: _t('toolbox.tiled') } },
    }, 'PMAS-CostComp'),
    legend: { top: 0, textStyle: { color: _cssVar('--text-2'), fontSize: 11 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ..._chartDefaults().tooltip,
      formatter(params) {
        const total = params.reduce((s, p) => s + (p.value || 0), 0);
        let html = `<b>${params[0].axisValue}</b><br/>`;
        params.forEach(p => {
          const pct = total > 0 ? (p.value / total * 100).toFixed(1) : '0.0';
          html += `${p.marker}${p.seriesName}: ${_fmtCost(p.value)} (${pct}%)<br/>`;
        });
        html += `<b>Total: ${_fmtCost(total)}</b>`;
        return html;
      },
    },
    grid: { left: '3%', right: '4%', bottom: needsZoom ? 44 : '3%', containLabel: true },
    xAxis: { type: 'category', data: categories, axisLabel: { color: _cssVar('--text-2'), fontSize: 11, rotate: categories.length > 8 ? 30 : 0 } },
    yAxis: { type: 'value', axisLabel: { color: _cssVar('--text-2'), fontSize: 11, formatter: v => _fmtCost(v, 0) } },
    ...(dataZoom.length ? { dataZoom } : {}),
    series: [
      { name: _t('trends.normal'),  type: 'bar', stack: 'cost', data: normalData,  itemStyle: { color: pal[0] }, emphasis: { focus: 'series' } },
      { name: _t('trends.extra'),   type: 'bar', stack: 'cost', data: extraData,   itemStyle: { color: pal[1] }, emphasis: { focus: 'series' } },
      { name: _t('trends.standby'), type: 'bar', stack: 'cost', data: standbyData, itemStyle: { color: pal[2] }, emphasis: { focus: 'series' } },
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
    if (!el) return;
    el.toggleAttribute('data-chart-loading', on);
    if (on) {
      el.setAttribute('aria-busy', 'true');
      el.setAttribute('aria-label', _t('loading'));
    } else {
      el.removeAttribute('aria-busy');
    }
  });
}

// ---------------------------------------------------------------------------
// Filter persistence — dateFrom / dateTo saved across sessions
// ---------------------------------------------------------------------------
function _saveFilters() {
  try {
    localStorage.setItem('pmas_filters_v1', JSON.stringify({
      dateFrom:  document.getElementById('dateFromInput').value,
      dateTo:    document.getElementById('dateToInput').value,
      cycles:    cycleMs.getValues?.() ?? [],
      peps:      pepMs.getValues?.() ?? [],
      pepsDesc:  pepDescMs.getValues?.() ?? [],
      collabs:   collaboratorMs.getValues?.() ?? [],
    }));
  } catch (_) {}
}
function _restoreFilterDates() {
  try {
    const s = JSON.parse(localStorage.getItem('pmas_filters_v1') || 'null');
    if (!s) return;
    if (s.dateFrom) document.getElementById('dateFromInput').value = s.dateFrom;
    if (s.dateTo)   document.getElementById('dateToInput').value   = s.dateTo;
    // Store selections for deferred restore after MultiSelects are populated
    window._savedFilterSelections = s;
  } catch (_) {}
}
function _restoreFilterSelections() {
  const s = window._savedFilterSelections;
  if (!s) return;
  window._savedFilterSelections = null;
  if (s.cycles?.length)   cycleMs.setValues?.(s.cycles);
  if (s.peps?.length)     pepMs.setValues?.(s.peps);
  if (s.pepsDesc?.length) pepDescMs.setValues?.(s.pepsDesc);
  if (s.collabs?.length)  collaboratorMs.setValues?.(s.collabs);
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
      maxItems:    40,
      toolboxName: 'PMAS-Queima',
    });
    const tc = _getOrCreateChart('trendsChart');
    tc.setOption(trendsOpt, true);
    tc.resize();

    // Cost Composition chart — G3
    _renderCostCompositionChart(trends);

    // Sync tooltips: hover on a cycle in either chart highlights the same cycle in the other
    const cc = _charts['costCompositionChart'];
    if (tc && cc && !tc.isDisposed() && !cc.isDisposed()) {
      echarts.connect([tc, cc]);
    }

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
      notify(_friendlyError(err), 'error');
    }
  } catch (err) {
    _setChartLoading(['trendsChart'], false);
    notify(_friendlyError(err), 'error');
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
    notify(_friendlyError(err), 'error');
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
    ? _fmtCost(v, 0)
    : formatHours(v);

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
  const fmtH = formatHours;
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
  const svFmt   = fc.sv   != null ? (fc.sv  >= 0 ? '+' : '') + fmtH(fc.sv)  : '—';
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
    ? fmtDateBR(fc.completed_on)
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
  ].map(_mkStatCard).join('');

  const row2 = [
    { val: fc.actual_cost != null ? fmtR(fc.actual_cost) : '—',                        lbl: 'AC',                            cls: 'blue',    evm: 'AC'      },
    { val: fc.remaining_cost != null ? fmtR(Math.max(0, fc.remaining_cost)) : '—',    lbl: 'ETC',                           cls: 'neutral', evm: 'ETC'     },
    { val: pctC,                                                                        lbl: _t('forecast.utilization_cost'), cls: overC ? 'red' : 'green'   },
    { val: cpiVal,                                                                      lbl: 'CPI',  cls: cpiCls,  evm: 'CPI',  sublbl: fc.cpi_label  || null },
    { val: cvFmt,                                                                       lbl: 'CV',   cls: cvCls,   evm: 'CV',   sublbl: fc.cv_label  || null },
    { val: fc.eac != null ? fmtR(fc.eac) : '—',                                        lbl: 'EAC',  cls: 'neutral', evm: 'EAC', sublbl: eacSublbl           },
    { val: vacFmt,                                                                      lbl: 'VAC',  cls: vacCls,  evm: 'VAC',  sublbl: fc.vac_label  || null },
    { val: tcpiVal,                                                                     lbl: 'TCPI', cls: tcpiCls, evm: 'TCPI', sublbl: fc.tcpi_label || null },
  ].map(_mkStatCard).join('');

  return `<div class="stats-row">${row1}</div><div class="stats-row">${row2}</div>`;
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
  if (fc.start_date)       dateChips.push(`▸ ${_t('forecast.info.start')}: ${fmtDateBR(fc.start_date)}`);
  if (fc.planned_end_date) dateChips.push(`→ ${_t('forecast.info.planned_end')}: ${fmtDateBR(fc.planned_end_date)}`);
  if (fc.completed_on)     dateChips.push(`✓ ${_t('forecast.info.completed')}: ${fmtDateBR(fc.completed_on)}`);

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
    document.getElementById('simsCard').hidden = true;
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
    else { document.getElementById('simsCard').hidden = true; }
    try {
      const chart = _getOrCreateChart('forecastChart');
      chart.setOption(_buildForecastOption(fc), true);
      chart.resize();
    } catch (_) { /* chart lib may not be loaded in offline envs */ }
    _renderVelocitySparkline(fc);
    _renderBurnUpChart(fc);
    // Sync cross-highlight: hovering a cycle in any forecast chart highlights the same cycle in all others
    const fChart = _charts['forecastChart'];
    const bChart = _charts['burnUpChart'];
    const vChart = _charts['velocitySparklineChart'];
    const syncGroup = [fChart, bChart, vChart].filter(c => c && !c.isDisposed());
    if (syncGroup.length > 1) echarts.connect(syncGroup);
    _renderForecastBaseline(fc);
    await _renderForecastAllocTable(pep, dateFrom, dateTo);
    await _renderForecastAllocCostTable(pep, dateFrom, dateTo);
    await _loadForecastAlerts(pep);
  } catch (err) {
    _setChartLoading(['forecastChart', 'burnUpChart'], false);
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    if (infoEl) infoEl.hidden = true;
    document.getElementById('burnUpCard').hidden = true;
    document.getElementById('forecastAllocCard').hidden = true;
    document.getElementById('simsCard').hidden = true;
    const alertsCard = document.getElementById('forecastAlertsCard');
    if (alertsCard) alertsCard.hidden = true;
    _disposeTabCharts('forecast');
    if (!err.message?.includes('404')) notify(_friendlyError(err), 'error');
  }
}

async function _loadForecastAlerts(pepWbs) {
  const card = document.getElementById('forecastAlertsCard');
  const list = document.getElementById('forecastAlertsList');
  if (!card || !list) return;
  const filterEl = document.getElementById('forecastAlertFilter');
  const isResolved = filterEl ? filterEl.value : '';
  try {
    const params = new URLSearchParams({ alert_type: '' });
    params.set('limit', '50');
    if (isResolved !== '') params.set('is_resolved', isResolved);
    const alerts = await apiFetch(`/api/my/alerts?${params}`);
    const pepAlerts = alerts.filter(a => a.pep_wbs === pepWbs);
    if (pepAlerts.length === 0) { card.hidden = true; return; }
    card.hidden = false;
    const _fmtType = t => ({ budget_warning: 'Orçamento Atenção', budget_overrun: 'Orçamento Estourado', schedule_risk: 'Risco de Prazo' }[t] || t);
    list.innerHTML = `<div class="forecast-alerts-list">${pepAlerts.map(a => `
      <div class="forecast-alert-item level-${a.level}${a.is_resolved ? ' is-resolved' : ''}">
        <span class="alert-level-tag alert-level-${a.level}">${a.level === 'error' ? 'Crítico' : a.level === 'warning' ? 'Atenção' : 'Info'}</span>
        <div>
          <div class="forecast-alert-msg">${a.message}</div>
          <div class="forecast-alert-meta">${_fmtType(a.alert_type)} · ${fmt.datetime ? fmt.datetime(a.created_at) : a.created_at.replace('T', ' ').slice(0,16)}${a.is_resolved ? ' · <span class="alert-status-resolved">Resolvido</span>' : ''}</div>
        </div>
      </div>`).join('')}</div>`;
  } catch (_) {
    if (card) card.hidden = true;
  }
}

document.getElementById('forecastAlertFilter')?.addEventListener('change', () => {
  if (_activeATab === 'forecast' && _currentForecastPep) _loadForecastAlerts(_currentForecastPep);
});

function _renderVelocitySparkline(fc) {
  const el = document.getElementById('velocitySparklineChart');
  if (!el) return;
  const history = (fc.history || []).filter(h => h.period_hours > 0);
  if (history.length < 2) { el.hidden = true; return; }
  el.hidden = false;

  const labels   = history.map(h => h.cycle_name);
  const vals     = history.map(h => h.period_hours);
  const last3    = vals.slice(-3);
  const avg3     = last3.reduce((s, v) => s + v, 0) / last3.length;
  const barColor = _getPalette()[0] || _cssVar('--primary');
  const avgColor = _cssVar('--amber');

  const chart = _getOrCreateChart('velocitySparklineChart');
  chart.setOption({
    ..._chartDefaults(),
    backgroundColor: _cssVar('--bg'),
    grid: { top: 18, bottom: 28, left: 44, right: 16, containLabel: false },
    tooltip: {
      trigger: 'axis', ..._chartDefaults().tooltip,
      formatter: p => {
        const bar = p[0];
        return `<b>${bar.name}</b><br/>${bar.marker}${(+bar.value).toFixed(1)} h` +
          `<br/><span style="color:${avgColor}">— — </span>${_t('forecast.avg3')}: <b style="color:${avgColor}">${avg3.toFixed(1)} h</b>`;
      },
    },
    xAxis: {
      type: 'category', data: labels,
      axisLabel: { color: _cssVar('--text-3'), fontSize: 9, interval: 'auto' },
      axisTick: { show: false }, axisLine: { lineStyle: { color: _cssVar('--border') } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: _cssVar('--text-3'), fontSize: 9, formatter: v => v + 'h' },
      splitLine: { lineStyle: { color: _cssVar('--surface') } },
    },
    series: [{
      type: 'bar', data: vals, name: _t('forecast.realized'),
      barMaxWidth: 32,
      itemStyle: { color: barColor, borderRadius: [2, 2, 0, 0] },
      emphasis: { focus: 'series' },
      markLine: {
        silent: true, symbol: 'none',
        lineStyle: { color: avgColor, width: 1.5, type: 'dashed' },
        label: {
          formatter: `${_t('forecast.avg3')}: {c}h`,
          fontSize: 9, color: avgColor, position: 'end',
        },
        data: [{ yAxis: +avg3.toFixed(1) }],
      },
    }],
  }, true);
  chart.resize();
}

function _renderForecastBaseline(fc) {
  const section = document.getElementById('burnUpBaselineSection');
  const body    = document.getElementById('burnUpBaselineBody');
  if (!section || !body) return;
  const history = (fc.history || []).filter(h => h.planned_hours != null || h.planned_cost != null);
  if (!history.length) {
    section.hidden = true;
    return;
  }
  section.hidden = false;

  const hasHours = history.some(h => h.planned_hours != null);
  const hasCost  = history.some(h => h.planned_cost  != null);
  const fmtH = formatHours;
  const fmtC = v => v != null ? _fmtCost(v) : '—';
  const delta = (plan, real) => {
    if (plan == null || real == null) return '—';
    const d = real - plan;
    const cls = d > 0 ? 'red' : d < 0 ? 'green' : 'neutral';
    return `<span style="color:var(--${cls})">${d >= 0 ? '+' : ''}${formatHours(d)}</span>`;
  };

  let html = `<div class="table-responsive"><table class="data-table">
    <thead><tr>
      <th data-i18n="plan.th.cycle">${_t('plan.th.cycle')}</th>
      ${hasHours ? `<th class="text-right" data-i18n="plan.th.hours">${_t('plan.th.hours')}</th>
      <th class="text-right" data-i18n="forecast.realized">${_t('forecast.realized')}</th>
      <th class="text-right">Δ Horas</th>` : ''}
      ${hasCost  ? `<th class="text-right" data-i18n="plan.th.cost">${_t('plan.th.cost')}</th>
      <th class="text-right">AC</th>` : ''}
    </tr></thead><tbody>`;
  for (const h of history) {
    html += `<tr>
      <td>${escHtml(h.cycle_name)}</td>
      ${hasHours ? `<td class="text-right">${fmtH(h.planned_hours)}</td>
      <td class="text-right">${fmtH(h.period_hours)}</td>
      <td class="text-right">${delta(h.planned_hours, h.period_hours)}</td>` : ''}
      ${hasCost  ? `<td class="text-right">${fmtC(h.planned_cost)}</td>
      <td class="text-right">${fmtC(h.period_cost)}</td>` : ''}
    </tr>`;
  }
  html += '</tbody></table></div>';
  body.innerHTML = html;
}

function _renderBurnUpChart(fc) {
  const card    = document.getElementById('burnUpCard');
  const esKpis  = document.getElementById('burnUpEsKpis');
  const history = fc.history || [];
  const hasEV   = history.some(h => h.cumulative_ev_cost != null);
  if (!hasEV) {
    card.hidden = true;
    if (_charts['burnUpChart'] && !_charts['burnUpChart'].isDisposed()) {
      _charts['burnUpChart'].dispose();
      delete _charts['burnUpChart'];
    }
    return;
  }
  card.hidden = false;

  // Earned Schedule KPI strip — lives here because ES is derived from the PV cost curve
  if (esKpis) {
    const hasES = fc.es != null || fc.spi_t != null || fc.sv_t != null || fc.ieac_t != null;
    if (hasES) {
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
      esKpis.innerHTML = `<div class="stats-row">${cards}</div>`;
      esKpis.hidden = false;
    } else {
      esKpis.hidden = true;
      esKpis.innerHTML = '';
    }
  }

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
  const simsCard = document.getElementById('simsCard');
  if (!simsCard) return;
  simsCard.hidden = false;
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
        grid: { top: 44, right: '4%', bottom: 32, left: '2%', containLabel: true },
        legend: {
          data: [_t('sim.burnup.projected'), ...(budget != null ? [_t('sim.burnup.budget')] : [])],
          top: 4, left: 'center',
          textStyle: { color: _cssVar('--text'), fontSize: 11 },
          itemGap: 20, itemWidth: 14, itemHeight: 8,
        },
        tooltip: { trigger: 'axis', ..._chartDefaults().tooltip,
          formatter: params => {
            let html = `<b>${params[0]?.axisValue}</b><br>`;
            params.forEach(p => p.value != null && (html += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br>`)); // intentional: ECharts tooltip formatters don't support locale HTML
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
            areaStyle: { color: _cssVar('--primary') + '22' },
            emphasis: { focus: 'series' },
          },
          ...(budget != null ? [{
            name: _t('sim.burnup.budget'), type: 'line', data: cats.map(() => budget),
            symbol: 'none', lineStyle: { color: _cssVar('--amber'), width: 1.5, type: 'dashed' },
            itemStyle: { color: _cssVar('--amber') },
            emphasis: { focus: 'series' },
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
  const el     = document.getElementById('mcResult');
  const histEl = document.getElementById('mcHistogramChart');
  el.innerHTML = `<span class="hint">${_t('loading')}</span>`;
  if (histEl) histEl.hidden = true;
  try {
    const r = await apiFetch(`/api/v2/projects/${_simProjectId}/monte-carlo?iterations=1000`);
    if (r.error === 'insufficient_data') {
      el.innerHTML = `<div class="chart-empty">${_t('mc.insufficient_data')}</div>`;
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

      // Color each bar by percentile region
      const barData = cats.map((cat, i) => {
        const v = Number(cat);
        let color;
        if      (r.p10 != null && v <= r.p10) color = _cssVar('--green');
        else if (r.p50 != null && v <= r.p50) color = _cssVar('--primary');
        else if (r.p90 != null && v <= r.p90) color = _cssVar('--amber');
        else                                   color = _cssVar('--red');
        return { value: freqs[i], itemStyle: { color } };
      });

      // Bell curve — theoretical N(μ, σ) of the OUTPUT distribution (cycle counts),
      // scaled so its area matches the histogram area (iterations × binWidth).
      // A good fit means the simulation output is approximately normal.
      // Visible skew / heavy tail means the remaining work is large relative to
      // velocity variance — the gap between histogram and curve is informative.
      const bellColor  = _cssVar('--text-3');
      const bellSeries = [];
      if (r.mean_cycles != null && r.stdev_cycles > 0) {
        const mu    = r.mean_cycles;
        const sigma = r.stdev_cycles;
        const nums  = cats.map(Number);
        const binW  = nums.length > 1 ? (nums[nums.length - 1] - nums[0]) / (nums.length - 1) : 1;
        const scale = r.iterations * binW;
        const K     = scale / (sigma * Math.sqrt(2 * Math.PI));
        bellSeries.push({
          name:      _t('mc.bell_curve'),
          type:      'line',
          data:      nums.map(x => +(K * Math.exp(-0.5 * ((x - mu) / sigma) ** 2)).toFixed(2)),
          smooth:    true,
          symbol:    'none',
          lineStyle: { color: bellColor, width: 1.5, type: 'dashed' },
          emphasis:  { focus: 'series' },
          z:         10,
        });
      }

      hc.setOption({
        ..._chartDefaults(),
        grid: { top: 36, right: '4%', bottom: 40, left: '2%', containLabel: true },
        legend: bellSeries.length ? {
          data: [_t('mc.bell_curve')],
          right: '4%', top: 4,
          textStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          itemWidth: 18, itemHeight: 2,
        } : { show: false },
        tooltip: {
          trigger: 'axis', ..._chartDefaults().tooltip,
          formatter: params => {
            const bar  = params.find(p => p.seriesType === 'bar') || params[0];
            const bell = params.find(p => p.seriesType === 'line');
            let html = `<b>${bar.axisValue} ${_t('sim.cycles_to_complete')}</b><br>`;
            html += `${bar.marker}${_t('mc.histogram.frequency')}: <b>${bar.value}</b>`;
            if (bell?.value != null) html += `<br><span style="color:${bellColor}">- -</span> ${_t('mc.bell_curve')}: <b>${(+bell.value).toFixed(1)}</b>`;
            return html;
          },
        },
        xAxis: {
          type: 'category', data: cats,
          name: _t('sim.cycles_to_complete'), nameLocation: 'middle', nameGap: 28,
          nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          axisLabel:     { color: _cssVar('--text-3'), fontSize: 10 },
          axisTick:      { alignWithLabel: true },
        },
        yAxis: {
          type: 'value', name: _t('mc.histogram.frequency'),
          nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
          axisLabel:     { color: _cssVar('--text-3'), fontSize: 10 },
          splitLine:     { lineStyle: { color: _cssVar('--border') } },
        },
        series: [
          {
            type: 'bar', data: barData, barMaxWidth: 36, emphasis: { focus: 'series' },
            markLine: {
              symbol: 'none',
              silent: true,
              data: [
                ...(r.p10 != null ? [{ xAxis: String(r.p10),
                  lineStyle: { color: _cssVar('--green'),   type: 'dashed', width: 1.5 },
                  label: { formatter: `P10 · ${r.p10}`, color: _cssVar('--green'),
                    position: 'end', offset: [0,  0], fontSize: 9,
                    backgroundColor: _cssVar('--card'), padding: [2, 4], borderRadius: 2 } }] : []),
                ...(r.p50 != null ? [{ xAxis: String(r.p50),
                  lineStyle: { color: _cssVar('--primary'), type: 'solid',  width: 2   },
                  label: { formatter: `P50 · ${r.p50}`, color: _cssVar('--primary'),
                    position: 'end', offset: [0, 16], fontSize: 9,
                    backgroundColor: _cssVar('--card'), padding: [2, 4], borderRadius: 2 } }] : []),
                ...(r.p90 != null ? [{ xAxis: String(r.p90),
                  lineStyle: { color: _cssVar('--red'),     type: 'dashed', width: 1.5 },
                  label: { formatter: `P90 · ${r.p90}`, color: _cssVar('--red'),
                    position: 'end', offset: [0, 32], fontSize: 9,
                    backgroundColor: _cssVar('--card'), padding: [2, 4], borderRadius: 2 } }] : []),
              ],
            },
          },
          ...bellSeries,
        ],
      }, true);
      hc.resize();
    }
  } catch (e) {
    if (histEl) histEl.hidden = true;
    el.innerHTML = `<div class="chart-empty" style="color:var(--red,#f04040)">${_t('mc.error')}</div>`;
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
  document.getElementById('filterToggle').setAttribute('aria-expanded', String(_filterExpanded));
});
document.getElementById('filterToggle').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('filterToggle').click(); }
});

let _forecastAllocExpanded    = true;
let _whatIfExpanded           = false;
let _mcExpanded               = false;
let _burnUpBaselineExpanded   = true;

let _saveFcSecTimer = null;
function _saveForecastSections() {
  clearTimeout(_saveFcSecTimer);
  _saveFcSecTimer = setTimeout(async () => {
    try {
      const dash = _userPrefs?.dashboard || {};
      _userPrefs = await apiFetchJSON('/api/my/preferences', 'PUT', {
        dashboard: { ...dash, forecast_sections: {
          alloc:      _forecastAllocExpanded,
          whatif:     _whatIfExpanded,
          montecarlo: _mcExpanded,
          baseline:   _burnUpBaselineExpanded,
        }},
      });
    } catch (_) {}
  }, 400);
}

function _applyFcSection(expanded, bodyId, chevronId, toggleId) {
  const body    = document.getElementById(bodyId);
  const chevron = document.getElementById(chevronId);
  const toggle  = document.getElementById(toggleId);
  if (body)   body.style.display = expanded ? '' : 'none';
  if (chevron) chevron.style.transform = expanded ? '' : 'rotate(-90deg)';
  if (toggle) toggle.setAttribute('aria-expanded', String(expanded));
}

// Apply initial collapsed state for advanced sections
_applyFcSection(_whatIfExpanded,  'whatIfBody',    'whatIfChevron',   'whatIfToggle');
_applyFcSection(_mcExpanded,      'mcBody',        'mcChevron',       'mcToggle');

document.getElementById('forecastAllocToggle').addEventListener('click', () => {
  _forecastAllocExpanded = !_forecastAllocExpanded;
  _applyFcSection(_forecastAllocExpanded, 'forecastAllocBody', 'forecastAllocChevron', 'forecastAllocToggle');
  _saveForecastSections();
});
document.getElementById('forecastAllocToggle').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('forecastAllocToggle').click(); }
});

document.getElementById('whatIfToggle').addEventListener('click', () => {
  _whatIfExpanded = !_whatIfExpanded;
  _applyFcSection(_whatIfExpanded, 'whatIfBody', 'whatIfChevron', 'whatIfToggle');
  _saveForecastSections();
});
document.getElementById('whatIfToggle').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('whatIfToggle').click(); }
});

document.getElementById('mcToggle').addEventListener('click', () => {
  _mcExpanded = !_mcExpanded;
  _applyFcSection(_mcExpanded, 'mcBody', 'mcChevron', 'mcToggle');
  _saveForecastSections();
});
document.getElementById('mcToggle').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('mcToggle').click(); }
});

document.getElementById('burnUpBaselineToggle').addEventListener('click', () => {
  _burnUpBaselineExpanded = !_burnUpBaselineExpanded;
  _applyFcSection(_burnUpBaselineExpanded, 'burnUpBaselineBody', 'burnUpBaselineChevron', 'burnUpBaselineToggle');
  _saveForecastSections();
});
document.getElementById('burnUpBaselineToggle').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('burnUpBaselineToggle').click(); }
});

function _setAllocMode(mode) {
  document.getElementById('forecastAllocTableHours').hidden = (mode !== 'hours');
  document.getElementById('forecastAllocTableCost').hidden  = (mode !== 'cost');
  document.getElementById('allocBtnHours').className = mode === 'hours' ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
  document.getElementById('allocBtnCost').className  = mode === 'cost'  ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
}

async function _renderForecastAllocTable(pep, dateFrom, dateTo) {
  const card = document.getElementById('forecastAllocCard');
  const tbl  = document.getElementById('forecastAllocTableHours');
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
    const fmt = v => v > 0 ? formatHours(v) : '—';

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
  const card = document.getElementById('forecastAllocCard');
  const tbl  = document.getElementById('forecastAllocTableCost');
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
    tbody.innerHTML = `<tr><td colspan="4" style="color:${_cssVar('--text-3')};font-size:.85rem;padding:.75rem">${_t('plan.panel.select_hint')}</td></tr>`;
    return;
  }
  try {
    const plans = await apiFetch(`/api/projects/${_planProjectId}/plans`);
    if (!plans.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="color:${_cssVar('--text-3')};font-size:.85rem;padding:.75rem">${_t('plan.no_plans')}</td></tr>`;
      return;
    }
    tbody.innerHTML = plans.map(pl => {
      const costStr = pl.planned_cost != null
        ? _fmtCost(pl.planned_cost)
        : '<span style="color:var(--text-3)">—</span>';
      const physStr = pl.physical_pct != null
        ? `<span style="color:var(--color-accent);font-weight:600">${(pl.physical_pct * 100).toFixed(0)}%</span>`
        : '<span style="color:var(--text-3)">—</span>';
      return `<tr>
        <td>${escHtml(pl.cycle_name)}</td>
        <td style="text-align:right">${fmt(pl.planned_hours)}</td>
        <td style="text-align:right">${costStr}</td>
        <td style="text-align:right">${physStr}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-secondary btn-sm" onclick="editPlan(${pl.cycle_id}, ${escHtml(JSON.stringify(pl.cycle_name))}, ${pl.planned_hours}, ${pl.planned_cost ?? 'null'})" style="margin-right:.25rem">${_t('btn.edit')}</button>
          <button class="btn btn-danger btn-sm" onclick="deletePlan(${pl.cycle_id})">${_t('btn.delete')}</button>
        </td>
      </tr>`;
    }).join('');
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

function deletePlan(cycle_id) {
  if (!_planProjectId) return;
  confirmDialog(_t('confirm.remove_baseline'), async () => {
    try {
      await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${cycle_id}`, 'DELETE');
      await _renderPlanTable();
    } catch (e) { notify(_friendlyError(e), 'error'); }
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

document.getElementById('addPlanRowBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const [allCycles, existingPlans] = await Promise.all([
      apiFetch('/api/cycles?include_archived=false'),
      apiFetch(`/api/projects/${_planProjectId}/plans`),
    ]);
    const plannedCycleIds = new Set(existingPlans.map(p => p.cycle_id));
    const available = allCycles.filter(c => !plannedCycleIds.has(c.id));
    if (!available.length) { notify(_t('msg.all_baseline_set'), 'info'); return; }
    document.getElementById('addPlanRows').innerHTML = available.map(c => `
      <tr>
        <td><input type="checkbox" class="plan-cycle-check" data-cycle-id="${c.id}" /></td>
        <td>${escHtml(c.name)}</td>
        <td><input type="number" min="0" step="0.5" class="plan-hours form-input input-sm"
             style="width:6rem;text-align:right" placeholder="0" /></td>
        <td><input type="number" min="0" step="0.01" class="plan-cost form-input input-sm"
             style="width:7rem;text-align:right" placeholder="${_t('label.optional')}" /></td>
      </tr>`).join('');
    const checkAll = document.getElementById('addPlanCheckAll');
    checkAll.checked = false;
    checkAll.indeterminate = false;
    document.getElementById('addPlanError').textContent = '';
    openModal('addPlanModal');
  } catch (e) { notify(_friendlyError(e), 'error'); }
});

document.getElementById('addPlanCheckAll').addEventListener('change', e => {
  document.getElementById('addPlanRows').querySelectorAll('.plan-cycle-check')
    .forEach(cb => { cb.checked = e.target.checked; });
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
      const hStr = fmt(pl.planned_hours) + 'h';
      const cStr = pl.planned_cost != null
        ? ' / ' + _fmtCost(pl.planned_cost)
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
});


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

function _closeAddPlanModal() { closeModal('addPlanModal'); }

document.getElementById('addPlanSaveBtn').addEventListener('click', async () => {
  const rows = document.getElementById('addPlanRows').querySelectorAll('tr');
  const errEl = document.getElementById('addPlanError');
  errEl.textContent = '';
  const entries = [];
  for (const row of rows) {
    const check = row.querySelector('.plan-cycle-check');
    if (!check?.checked) continue;
    const cycleId = parseInt(check.dataset.cycleId);
    const hours   = parseFloat(row.querySelector('.plan-hours').value);
    const rawC    = row.querySelector('.plan-cost').value.trim();
    const cost    = rawC === '' ? null : parseFloat(rawC);
    if (isNaN(hours) || hours < 0) { errEl.textContent = _t('msg.valid_hours'); return; }
    if (cost !== null && (isNaN(cost) || cost < 0)) { errEl.textContent = 'Custo inválido.'; return; }
    entries.push({ cycle_id: cycleId, planned_hours: hours, planned_cost: cost });
  }
  if (!entries.length) { _closeAddPlanModal(); return; }
  try {
    await Promise.all(entries.map(e =>
      apiFetchJSON(`/api/projects/${_planProjectId}/plans/${e.cycle_id}`, 'PUT', e)
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
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

// ---------------------------------------------------------------------------
// _renderScatterBrushResult — summary table shown below the EVM quadrant
// when the user draws a brush rectangle selecting one or more projects.
// ---------------------------------------------------------------------------
function _renderScatterBrushResult(indices, items) {
  const panel = document.getElementById('scatterBrushResult');
  if (!panel) return;

  if (!indices.length) { panel.hidden = true; return; }

  const sel  = indices.map(i => items[i]).filter(Boolean);
  const hcss = { success: '--green', warning: '--amber', danger: '--red' };
  const dim  = 'color:var(--text-3)';

  const rows = sel.map(d => {
    const cC = `color:var(${hcss[d.cpi_color] || '--text'})`;
    const sC = `color:var(${hcss[d.spi_color] || '--text'})`;
    return `<tr>
      <td style="font-weight:600;white-space:nowrap">${escHtml(d.pep_wbs)}</td>
      <td style="${dim};font-size:10px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(d.name || '—')}</td>
      <td style="${cC};font-weight:700;text-align:right">${d.cpi.toFixed(2)}</td>
      <td style="${sC};font-weight:700;text-align:right">${d.spi.toFixed(2)}</td>
      <td style="text-align:right;${dim};font-size:10px">${d.total_hours != null ? formatHours(d.total_hours, 0) : '—'}</td>
    </tr>`;
  }).join('');

  panel.hidden = false;
  panel.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem">
      <span style="font-size:.8rem;color:var(--text-2);font-weight:600">
        ${_t('scatter.brush_n_selected').replace('{n}', sel.length)}
      </span>
      <button id="scatterBrushClear" class="btn btn-sm"
        style="font-size:.75rem;padding:2px 10px;line-height:1.4">${_t('scatter.brush_clear')}</button>
    </div>
    <div style="overflow-x:auto">
      <table class="data-table" style="font-size:11px;width:100%">
        <thead><tr>
          <th>PEP</th>
          <th data-i18n="lbl.name">Nome</th>
          <th style="text-align:right">CPI</th>
          <th style="text-align:right">SPI</th>
          <th style="text-align:right" data-i18n="ch.hours">Horas</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;

  document.getElementById('scatterBrushClear')?.addEventListener('click', () => {
    const sc = _charts['scatterChart'];
    if (sc && !sc.isDisposed()) sc.dispatchAction({ type: 'brush', areas: [] });
    panel.hidden = true;
  });
}

// _buildTreemapOption — moved to charts/portfolio.js

// _buildBulletOption — moved to charts/portfolio.js

// ---------------------------------------------------------------------------
// Collaborator Inline Detail Panel
// ---------------------------------------------------------------------------
function _closeCollabDetail() {
  _selectedCollaborator = null;
  document.getElementById('collabDetailPanel').hidden = true;
  // dispose inline charts
  ['collabInlineTimelineChart','collabRadarChart','collabCalendarChart'].forEach(id => {
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
    _renderCollabRadar(name, []);
    return;
  }
  emptyEl.hidden = true;
  chartEl.style.visibility = '';

  const tc = echarts.init(chartEl, 'pmas', { renderer: 'svg' });
  tc.setOption({ aria: { enabled: true } });
  _charts['collabInlineTimelineChart'] = tc;
  tc.setOption(_buildHoursBarOption({
    data: rows, categoryKey: 'cycle_name',
    orientation: 'vertical', stacked: true,
    showTotal: true,
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

  _renderCollabRadar(name, rows);
}

function _renderCollabRadar(name, rows) {
  const section = document.getElementById('collabRadarSection');
  const chartEl = document.getElementById('collabRadarChart');
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  if (!rows.length) { section.hidden = true; return; }
  section.hidden = false;

  // --- compute 5 axes ---
  const cycleTotals = rows.map(r => (r.normal_hours || 0) + (r.extra_hours || 0) + (r.standby_hours || 0));
  const totalH  = cycleTotals.reduce((a, b) => a + b, 0);
  const extraH  = rows.reduce((a, r) => a + (r.extra_hours || 0), 0);
  const standbyH = rows.reduce((a, r) => a + (r.standby_hours || 0), 0);

  // Volume: collab total vs portfolio max (from last effort load)
  const portfolioMax = _lastEffortData.length
    ? Math.max(..._lastEffortData.map(d => (d.normal_hours || 0) + (d.extra_hours || 0) + (d.standby_hours || 0)))
    : totalH;
  const volume = portfolioMax > 0 ? Math.min(100, (totalH / portfolioMax) * 100) : 0;

  // Extra% and Sobreaviso% of total hours
  const extraPct   = totalH > 0 ? Math.min(100, (extraH  / totalH) * 100) : 0;
  const standbyPct = totalH > 0 ? Math.min(100, (standbyH / totalH) * 100) : 0;

  // Regularidade: 100 - CV×100 (CV = stdev / mean of per-cycle totals)
  const activeTotals = cycleTotals.filter(h => h > 0);
  let regularity = 100;
  if (activeTotals.length > 1) {
    const mean = activeTotals.reduce((a, b) => a + b, 0) / activeTotals.length;
    const variance = activeTotals.reduce((a, h) => a + (h - mean) ** 2, 0) / activeTotals.length;
    const cv = Math.sqrt(variance) / mean;
    regularity = Math.max(0, 100 - cv * 100);
  }

  // Presença: % of cycles with any hours
  const presence = rows.length > 0 ? (activeTotals.length / rows.length) * 100 : 0;

  const palette = _getPalette();
  const color   = palette[0];
  const defaults = _chartDefaults();

  const option = {
    ...defaults,
    tooltip: {
      ...defaults.tooltip,
      trigger: 'item',
      formatter: params => {
        const [vol, ext, sby, reg, pres] = params.value;
        return [
          `<b>${params.name}</b>`,
          `${_t('radar.volume')}: ${vol.toFixed(1)}`,
          `${_t('radar.extra')}: ${ext.toFixed(1)}`,
          `${_t('radar.standby')}: ${sby.toFixed(1)}`,
          `${_t('radar.regularity')}: ${reg.toFixed(1)}`,
          `${_t('radar.presence')}: ${pres.toFixed(1)}`,
        ].join('<br>');
      },
    },
    radar: {
      indicator: [
        { name: _t('radar.volume'),     max: 100 },
        { name: _t('radar.extra'),      max: 100 },
        { name: _t('radar.standby'),    max: 100 },
        { name: _t('radar.regularity'), max: 100 },
        { name: _t('radar.presence'),   max: 100 },
      ],
      shape: 'polygon',
      splitNumber: 4,
      center: ['50%', '52%'],
      radius: '62%',
      axisName: { color: _cssVar('--text-3'), fontSize: 11 },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: _cssVar('--border') } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [volume, extraPct, standbyPct, regularity, presence],
        name,
        itemStyle: { color },
        lineStyle: { color, width: 2 },
        areaStyle: { color, opacity: 0.2 },
      }],
      emphasis: { focus: 'self' },
    }],
  };

  const rc = echarts.init(chartEl, 'pmas', { renderer: 'svg' });
  rc.setOption(option);
  _charts['collabRadarChart'] = rc;
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

  const cc = echarts.init(chartEl, 'pmas', { renderer: 'svg' });
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
        { gte:  1, lte:  3, color: _cssVar('--heatmap-1') },
        { gte:  4, lte:  6, color: _cssVar('--heatmap-2') },
        { gte:  7, lte:  9, color: _cssVar('--heatmap-3') },
        { gte: 10, lte: 12, color: _cssVar('--heatmap-4') },
        { gte: 13, lte: 15, color: _cssVar('--heatmap-5') },
        { gt:  15,           color: _cssVar('--heatmap-6') },
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
          qday:     { fontSize: 9, fontWeight: 'bold', color: _cssVar('--amber'), lineHeight: 14, align: 'center' },
          n:    { fontSize: 9, color: pal[0] || _cssVar('--primary'), lineHeight: 13, align: 'center' },
          e:    { fontSize: 9, color: pal[1] || _cssVar('--accent'),  lineHeight: 13, align: 'center' },
          s:    { fontSize: 9, color: pal[2] || _cssVar('--violet'),  lineHeight: 13, align: 'center' },
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

  const _fmtDeltaBadge = (pct, abs) => {
    if (pct != null) {
      const dir = pct > 0.5 ? '↑' : pct < -0.5 ? '↓' : '→';
      const cls = pct > 5 ? 'delta-up' : pct < -5 ? 'delta-down' : 'delta-neutral';
      return `<span class="stat-delta ${cls}">${dir}${Math.abs(pct).toFixed(1)}%</span>`;
    }
    // pct is null when prev=0 (division undefined) — show direction-only arrow
    if (abs != null && abs !== 0) {
      const dir = abs > 0 ? '↑' : '↓';
      const cls = abs > 0 ? 'delta-up' : 'delta-down';
      return `<span class="stat-delta ${cls}">${dir}</span>`;
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
    cards = [
      { val: `${fmt(hNormal)}h`,    delta: _fmtDeltaBadge(lastTrend?.normal_hours_delta_pct,   lastTrend?.normal_hours_delta),   lbl: _t('stat.normal_h'),    cls: 'blue',    color: pal[0] },
      { val: `${fmt(hExtra)}h`,     delta: _fmtDeltaBadge(lastTrend?.extra_hours_delta_pct,    lastTrend?.extra_hours_delta),    lbl: _t('stat.extra_h'),     cls: 'amber',   color: pal[1] },
      { val: `${fmt(hStandby)}h`,   delta: _fmtDeltaBadge(lastTrend?.standby_hours_delta_pct,  lastTrend?.standby_hours_delta),  lbl: _t('stat.standby_h'),   cls: 'violet',  color: pal[2] },
      { val: `${fmt(totalHours)}h`, delta: _fmtDeltaBadge(lastTrend?.hours_delta_pct,          lastTrend?.hours_delta),          lbl: _t('stat.total'),       cls: 'green'   },
      { val: pepsActive,                                                                         lbl: _t('stat.peps_active'), cls: 'neutral' },
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
    cards = [
      { val: _fmtCost(costNormal),  delta: _fmtDeltaBadge(lastTrend?.normal_cost_delta_pct,   lastTrend?.normal_cost_delta),   lbl: _t('stat.cost_normal'),  cls: 'blue',    color: pal[0] },
      { val: _fmtCost(costExtra),   delta: _fmtDeltaBadge(lastTrend?.extra_cost_delta_pct,    lastTrend?.extra_cost_delta),    lbl: _t('stat.cost_extra'),   cls: 'amber',   color: pal[1] },
      { val: _fmtCost(costStandby), delta: _fmtDeltaBadge(lastTrend?.standby_cost_delta_pct,  lastTrend?.standby_cost_delta),  lbl: _t('stat.cost_standby'), cls: 'violet',  color: pal[2] },
      { val: _fmtCost(totalCost),   delta: _fmtDeltaBadge(lastTrend?.cost_delta_pct,          lastTrend?.cost_delta),          lbl: _t('stat.cost_total'),   cls: 'green'   },
      { val: pepsActive,                                                                         lbl: _t('stat.peps_active'),  cls: 'neutral' },
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
  cards.forEach(({ val, lbl, cls, color, delta }) => {
    const card = document.createElement('div');
    card.className = `stat-card ${cls}`;
    const style = color ? ` style="color:${color}"` : '';
    card.innerHTML = `${delta || ''}<div class="val"${style}>${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Row-actions dropdown (delegated)
// ---------------------------------------------------------------------------
function _openRowMenu(trigger) {
  const wrap = trigger.closest('.row-actions-wrap');
  const menu = wrap?.querySelector('.row-actions-menu');
  if (!menu) return;
  const isOpen = menu.classList.contains('open');
  document.querySelectorAll('.row-actions-menu.open').forEach(m => {
    m.classList.remove('open');
    m.closest('.row-actions-wrap')?.querySelector('.row-actions-trigger')
      ?.setAttribute('aria-expanded', 'false');
  });
  if (!isOpen) {
    menu.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
    menu.querySelector('[role=menuitem]:not([disabled])')?.focus();
  }
}

document.addEventListener('click', e => {
  const trigger = e.target.closest('.row-actions-trigger');
  if (trigger) { e.stopPropagation(); _openRowMenu(trigger); return; }
  document.querySelectorAll('.row-actions-menu.open').forEach(m => {
    m.classList.remove('open');
    m.closest('.row-actions-wrap')?.querySelector('.row-actions-trigger')
      ?.setAttribute('aria-expanded', 'false');
  });
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.row-actions-menu.open').forEach(m => {
      const wrap = m.closest('.row-actions-wrap');
      m.classList.remove('open');
      const trig = wrap?.querySelector('.row-actions-trigger');
      trig?.setAttribute('aria-expanded', 'false');
      trig?.focus();
    });
    return;
  }
  const trigger = e.target.closest('.row-actions-trigger');
  if (trigger && (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown')) {
    e.preventDefault();
    _openRowMenu(trigger);
    return;
  }
  const menuItem = e.target.closest('[role=menuitem]');
  if (menuItem) {
    const menu = menuItem.closest('.row-actions-menu');
    const items = [...menu.querySelectorAll('[role=menuitem]:not([disabled])')];
    const idx = items.indexOf(menuItem);
    if (e.key === 'ArrowDown') { e.preventDefault(); items[(idx + 1) % items.length]?.focus(); }
    if (e.key === 'ArrowUp')   { e.preventDefault(); items[(idx - 1 + items.length) % items.length]?.focus(); }
  }
});


document.getElementById('collabDetailClose').addEventListener('click', _closeCollabDetail);

document.getElementById('collabExportCsvBtn').addEventListener('click', async () => {
  if (!_selectedCollaborator) return;
  const params = new URLSearchParams({ collaborator_name: _selectedCollaborator });
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo)   params.set('date_to',   dateTo);
  pepMs.getValues().forEach(c => params.append('pep_code', c));
  try {
    const resp = await fetch(`/api/dashboard/collaborator-export?${params}`, { headers: _authHeaders() });
    if (!resp.ok) throw new Error(resp.statusText);
    const blob = await resp.blob();
    const safe = _selectedCollaborator.replace(/[^a-zA-Z0-9_\-]/g, '_');
    const url  = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: `timesheets_${safe}.csv` }).click();
    URL.revokeObjectURL(url);
  } catch (e) { notify(_friendlyError(e), 'error'); }
});
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
// Sortable — RunwayTable (defined here because _drawRunwayRows is defined here)
// ---------------------------------------------------------------------------
_makeSortable('runwayTable',
  [{key:'pep_wbs',type:'str'}, {key:'name',type:'str'}, {key:'_sortPlanned',type:'num'}, null, {key:'_sortAvg',type:'num'}, {key:'cpi',type:'num'}, {key:'cycles_to_complete',type:'num'}, {key:'estimated_completion_cycle',type:'str'}, {key:'spi',type:'num'}, {key:'schedule_status',type:'str'}],
  () => (_lastRunwayData||[]).filter(r => _evmMode ? r.budget_cost != null : r.budget_hours != null).map(r => Object.assign({}, r, {_sortPlanned: _evmMode ? (r.budget_cost||0) : (r.budget_hours||0), _sortAvg: _evmMode ? (r.avg_cost_per_cycle||0) : (r.avg_hours_per_cycle||0)})),
  rows => { _runwayPag.reset(); _runwayPag.render(rows); }
);
