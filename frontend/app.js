/* PMAS — Frontend App */

// ---------------------------------------------------------------------------
// Top-level tab navigation
// ---------------------------------------------------------------------------
const tabBtns     = document.querySelectorAll('.tab-btn');
const tabSections = document.querySelectorAll('.tab-section');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;

    if (btn.dataset.tab === 'cycles')   loadCyclesTable();
    if (btn.dataset.tab === 'projects') loadProjectsTable();
    if (btn.dataset.tab === 'team')     loadTeamTab();
  });
});

// ---------------------------------------------------------------------------
// Analytics sub-tab navigation + ECharts instance registry
// ---------------------------------------------------------------------------

// Chart instance registry — keyed by DOM element id
const _charts = {};

// Which chart IDs belong to each sub-tab (to dispose on leave)
const CHARTS_PER_TAB = {
  effort:    ['effortChart', 'budgetChart'],
  portfolio: ['treemapChart', 'bulletChart'],
  trends:    ['trendsChart'],
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
    _charts[id] = echarts.init(document.getElementById(id), 'dark');
  }
  return _charts[id];
}

// ResizeObserver — resize all live charts when container changes
const _ro = new ResizeObserver(() => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.resize(); } catch (_) {} });
});
_ro.observe(document.querySelector('main'));

// Sub-tab state
let _activeATab = 'effort';
let _stackMode  = true;   // true = stacked, false = grouped
let _evmMode    = false;  // false = hours, true = R$

const atabBtns     = document.querySelectorAll('.atab-btn');
const atabSections = document.querySelectorAll('.atab-section');

atabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    _disposeTabCharts(_activeATab);
    atabBtns.forEach(b => b.classList.remove('active'));
    atabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    _activeATab = btn.dataset.atab;
    document.getElementById(`atab-${_activeATab}`).hidden = false;
    _renderActiveTab();
  });
});

document.getElementById('evmToggleBtn').addEventListener('click', () => {
  _evmMode = !_evmMode;
  document.getElementById('evmToggleBtn').textContent = _evmMode ? 'Vista: R$' : 'Vista: Horas';
  _renderPortfolioTab();
});

document.getElementById('exportCsvBtn').addEventListener('click', () => {
  if (!_lastEffortData.length) { notify('Carregue dados antes de exportar.', 'info'); return; }
  const header = 'Colaborador,Horas Normais,Horas Extras,Sobreaviso,Total';
  const rows = _lastEffortData.map(d => {
    const total = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
    return `"${d.collaborator}",${d.normal_hours.toFixed(1)},${d.extra_hours.toFixed(1)},${d.standby_hours.toFixed(1)},${total}`;
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'esforco-equipe.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('stackToggleBtn').addEventListener('click', () => {
  _stackMode = !_stackMode;
  document.getElementById('stackToggleBtn').textContent =
    _stackMode ? 'Vista: Empilhada' : 'Vista: Agrupada';
  const ch = _charts['effortChart'];
  if (ch && !ch.isDisposed()) {
    ch.setOption(_buildEffortSeriesOnly(_stackMode), false);
  }
});

// ---------------------------------------------------------------------------
// Dashboard — DOM refs and multi-selects
// ---------------------------------------------------------------------------
const csvInput   = document.getElementById('csvInput');
const uploadZone = document.getElementById('uploadZone');
const loadBtn    = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const cycleMs        = new MultiSelect(document.getElementById('cycleMs'),        '— Selecione ciclo(s) —',   onCycleChange);
const pepMs          = new MultiSelect(document.getElementById('pepMs'),           '— Todos os PEPs —',        onPepChange);
const pepDescMs      = new MultiSelect(document.getElementById('pepDescMs'),       '— Todas as descrições —',  onPepDescChange);
const collaboratorMs = new MultiSelect(document.getElementById('collaboratorMs'),  '— Todos —',                onCollabChange);

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
    const cycles = await apiFetch('/api/cycles');
    cycleMs.setItems(cycles.map(c => ({ value: c.id, label: c.name })));
  } catch (e) { notify(`Erro ao carregar ciclos: ${e.message}`, 'error'); }
}

async function refreshPeps() {
  const cycleIds  = cycleMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  collabIds.forEach(id => p.append('collaborator_id', id));
  try {
    const peps = await apiFetch(`/api/peps?${p}`);
    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();
  } catch (_) {}
}

function refreshPepDescriptions() {
  const selected = pepMs.getValues();
  const descs = [...new Set(selected.flatMap(code => pepDataCache[code] || []))];
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  const cycleIds = cycleMs.getValues();
  const pepCodes = pepMs.getValues();
  const pepDescs = pepDescMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id => p.append('cycle_id', id));
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  try {
    const collabs = await apiFetch(`/api/collaborators?${p}`);
    collaboratorMs.setItems(collabs.map(c => ({ value: c.id, label: c.name })), true);
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
csvInput.addEventListener('change', async () => {
  const file = csvInput.files[0]; if (!file) return;
  notify(`Enviando "${file.name}"…`, 'info');
  const form = new FormData(); form.append('file', file);
  try {
    const res  = await fetch('/api/upload-timesheet', { method: 'POST', body: form });
    const json = await res.json();
    if (!res.ok) { notify(`Erro: ${json.detail ?? res.statusText}`, 'error'); return; }
    let msg = `✔ ${json.records_inserted.toLocaleString('pt-BR')} registro(s) importado(s).`;
    if (json.records_skipped > 0)           msg += ` (${json.records_skipped} duplicata(s) ignorada(s))`;
    if (json.quarantine_cycles_created > 0) msg += ` ⚠ ${json.quarantine_cycles_created} ciclo(s) de Quarentena criado(s).`;
    notify(msg, json.quarantine_cycles_created > 0 ? 'info' : 'success');
    await loadDashboardCycles();
    _renderActiveTab();
  } catch (err) { notify(`Falha na conexão: ${err.message}`, 'error'); }
});

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.style.borderColor = '#3b82f6'; });
uploadZone.addEventListener('dragleave', () => { uploadZone.style.borderColor = ''; });
uploadZone.addEventListener('drop', e => {
  e.preventDefault(); uploadZone.style.borderColor = '';
  const file = e.dataTransfer.files[0];
  if (file) { const dt = new DataTransfer(); dt.items.add(file); csvInput.files = dt.files; csvInput.dispatchEvent(new Event('change')); }
});

// ---------------------------------------------------------------------------
// Load button
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', () => _renderActiveTab());

clearBtn.addEventListener('click', () => {
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  pepDataCache = {};
  _evmMode = false;
  document.getElementById('evmToggleBtn').textContent = 'Vista: Horas';
  _disposeTabCharts('effort');
  _disposeTabCharts('portfolio');
  _disposeTabCharts('trends');
  document.getElementById('effortStats').innerHTML = '';
  document.getElementById('budgetPanel').hidden  = true;
  document.getElementById('bulletPanel').hidden  = true;
  _showEmpty('effortEmpty',    false);
  _showEmpty('portfolioEmpty', false);
  _showEmpty('trendsEmpty',    false);
});

// ---------------------------------------------------------------------------
// Analytics — render dispatcher
// ---------------------------------------------------------------------------
async function _renderActiveTab() {
  if (_activeATab === 'effort')    await _renderEffortTab();
  if (_activeATab === 'portfolio') await _renderPortfolioTab();
  if (_activeATab === 'trends')    await _renderTrendsTab();
}

function _showEmpty(id, show) {
  const el = document.getElementById(id);
  if (el) el.hidden = !show;
}

// ---------------------------------------------------------------------------
// Esforço da Equipe
// ---------------------------------------------------------------------------
let _lastEffortData = [];

async function _renderEffortTab() {
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    let payload;
    if (cycleIds.length === 0) {
      payload = await apiFetch(`/api/dashboard?${p}`);
    } else {
      payload = await apiFetch(`/api/dashboard/${cycleIds[0]}?${p}`);
    }

    const data = payload.data || [];
    _lastEffortData = data;
    const bva  = (payload.budget_vs_actual || []).filter(d => d.budget_hours > 0);

    // Stats row
    document.getElementById('effortStats').innerHTML = '';
    document.getElementById('effortStats').appendChild(_buildStatsRow(data, bva));

    // Title
    document.getElementById('effortTitle').textContent = _buildEffortTitle(payload, cycleIds.length);

    if (data.length === 0) {
      _showEmpty('effortEmpty', true);
      _disposeTabCharts('effort');
      document.getElementById('budgetPanel').hidden = true;
      return;
    }
    _showEmpty('effortEmpty', false);

    // Effort chart
    const h = calcHeight(data.length);
    document.getElementById('effortChart').style.height = `${h}px`;
    const ch = _getOrCreateChart('effortChart');
    ch.setOption(_buildEffortOption(data, _stackMode), true);
    ch.resize();

    // Budget chart
    if (bva.length > 0) {
      document.getElementById('budgetPanel').hidden = false;
      document.getElementById('budgetChart').style.height =
        `${Math.max(220, bva.length * 56 + 80)}px`;
      const bch = _getOrCreateChart('budgetChart');
      bch.setOption(_buildBudgetOption(bva), true);
      bch.resize();
    } else {
      document.getElementById('budgetPanel').hidden = true;
    }
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Saúde do Portfólio
// ---------------------------------------------------------------------------
async function _renderPortfolioTab() {
  const cycleIds = cycleMs.getValues();
  const pepCodes = pepMs.getValues();
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;
  const p = new URLSearchParams();
  if (cycleIds.length > 0) p.set('cycle_id', cycleIds[0]);
  pepCodes.forEach(c => p.append('pep_wbs', c));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const health = await apiFetch(`/api/portfolio-health?${p}`);

    if (!health.length) {
      _showEmpty('portfolioEmpty', true);
      _disposeTabCharts('portfolio');
      document.getElementById('bulletPanel').hidden = true;
      return;
    }
    _showEmpty('portfolioEmpty', false);

    // Update treemap title
    document.getElementById('portfolioTreemapTitle').textContent =
      _evmMode ? 'Custo Real por PEP (Treemap)' : 'Distribuição de Horas por PEP (Treemap)';

    // Treemap
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
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Tendências
// ---------------------------------------------------------------------------
async function _renderTrendsTab() {
  const pepCodes = pepMs.getValues();
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;
  const p = new URLSearchParams();
  pepCodes.forEach(c => p.append('pep_wbs', c));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const trends = await apiFetch(`/api/trends?${p}`);

    if (!trends.length) {
      _showEmpty('trendsEmpty', true);
      _disposeTabCharts('trends');
      return;
    }
    _showEmpty('trendsEmpty', false);

    const tc = _getOrCreateChart('trendsChart');
    tc.setOption(_buildTrendsOption(trends), true);
    tc.resize();
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Chart option builders
// ---------------------------------------------------------------------------

function calcHeight(count) { return Math.max(420, Math.min(count, 40) * 52 + 120); }

function _buildEffortTitle(payload, cycleCount) {
  const { cycle, filters } = payload;
  let t = cycleCount > 1 ? `${cycle.name} (+${cycleCount - 1} ciclo(s))` : cycle.name;
  if (filters.pep_codes?.length) t += `  |  PEP: ${filters.pep_codes.join(', ')}`;
  return t;
}

function _buildEffortOption(data, stacked) {
  const MAX   = 40;
  const slice = data.length > MAX ? data.slice(0, MAX) : data;
  const stack = stacked ? 'total' : undefined;
  const byName = Object.fromEntries(data.map(d => [d.collaborator, d]));
  const truncNote = data.length > MAX ? `  (top ${MAX} de ${data.length})` : '';

  return {
    backgroundColor: 'transparent',
    title: {
      subtext: truncNote.trim(),
      left: 'center', top: 4,
      subtextStyle: { color: '#64748b', fontSize: 11 },
    },
    legend: {
      data: ['Horas Normais', 'Horas Extras', 'Sobreaviso'],
      top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24, itemWidth: 14, itemHeight: 10,
    },
    grid: { top: 44, right: '3%', bottom: 28, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`;
        let total = 0;
        params.forEach(p => { if (p.value > 0) { html += `<div>${p.marker} ${p.seriesName}: <b>${p.value.toFixed(2)}h</b></div>`; total += p.value; } });
        if (params.length > 1) html += `<div style="margin-top:4px;border-top:1px solid #475569;padding-top:4px">Total: <b>${total.toFixed(2)}h</b></div>`;
        return html;
      },
    },
    xAxis: {
      type: 'value', name: 'Horas',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
    yAxis: {
      type: 'category',
      data: slice.map(r => r.collaborator),
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10, lineHeight: 16,
        formatter: name => {
          const d = byName[name]; if (!d) return name;
          const t = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
          const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
          return `{nm|${nm}}\n{hr|N: ${d.normal_hours.toFixed(1)}h  E: ${d.extra_hours.toFixed(1)}h  S: ${d.standby_hours.toFixed(1)}h  T: ${t}h}`;
        },
        rich: {
          nm: { color: '#e2e8f0', fontSize: 11, lineHeight: 18 },
          hr: { color: '#64748b', fontSize: 9,  lineHeight: 14 },
        },
      },
    },
    series: [
      { name: 'Horas Normais', type: 'bar', stack, data: slice.map(r => +r.normal_hours.toFixed(2)),  itemStyle: { color: '#3b82f6' }, barMaxWidth: 32 },
      { name: 'Horas Extras',  type: 'bar', stack, data: slice.map(r => +r.extra_hours.toFixed(2)),   itemStyle: { color: '#f59e0b' }, barMaxWidth: 32 },
      { name: 'Sobreaviso',    type: 'bar', stack, data: slice.map(r => +r.standby_hours.toFixed(2)), itemStyle: { color: '#8b5cf6' }, barMaxWidth: 32 },
    ],
  };
}

// Only update the stack property — avoids full re-render flicker
function _buildEffortSeriesOnly(stacked) {
  const stack = stacked ? 'total' : undefined;
  return {
    series: [
      { name: 'Horas Normais', stack },
      { name: 'Horas Extras',  stack },
      { name: 'Sobreaviso',    stack },
    ],
  };
}

function _buildBudgetOption(budgetData) {
  const labels  = budgetData.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 30)}` : ''));
  const budgets = budgetData.map(d => +(d.budget_hours.toFixed(2)));
  const actuals = budgetData.map((d, i) => ({
    value: +(d.actual_hours.toFixed(2)),
    itemStyle: { color: d.actual_hours > budgets[i] ? '#f87171' : '#34d399' },
  }));
  return {
    backgroundColor: 'transparent',
    legend: {
      data: ['Orçado', 'Realizado'], top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 }, itemGap: 24, itemWidth: 14, itemHeight: 10,
    },
    grid: { top: 44, right: '3%', bottom: 28, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const bVal = params.find(p => p.seriesName === 'Orçado')?.value ?? 0;
        const aVal = params.find(p => p.seriesName === 'Realizado')?.value ?? 0;
        const pct  = bVal > 0 ? ` (${(aVal / bVal * 100).toFixed(1)}%)` : '';
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue.replace('\n', ' — ')}</div>`;
        params.forEach(p => {
          const extra = p.seriesName === 'Realizado' ? pct : '';
          html += `<div>${p.marker} ${p.seriesName}: <b>${p.value.toFixed(1)}h</b>${extra}</div>`;
        });
        if (bVal > 0 && aVal > bVal) html += `<div style="color:#f87171;font-size:11px;margin-top:4px">⚠ Acima do orçado</div>`;
        return html;
      },
    },
    xAxis: { type: 'value', name: 'Horas', nameTextStyle: { color: '#94a3b8', fontSize: 11 }, axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` }, splitLine: { lineStyle: { color: '#1e293b' } } },
    yAxis: { type: 'category', data: labels, axisTick: { show: false }, axisLabel: { color: '#e2e8f0', fontSize: 10, lineHeight: 16 } },
    series: [
      { name: 'Orçado',    type: 'bar', data: budgets, itemStyle: { color: '#22d3ee' }, barMaxWidth: 28, barGap: '10%' },
      { name: 'Realizado', type: 'bar', data: actuals,                                  barMaxWidth: 28, barGap: '10%' },
    ],
  };
}

function _buildTreemapOption(health, evmMode = false) {
  const fmtVal = v => evmMode
    ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })
    : v.toFixed(1) + 'h';
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const d = health.find(x => x.pep_wbs === params.name);
        if (!d) return params.name;
        let html = `<b>${d.pep_wbs}</b>`;
        if (d.pep_description) html += `<br><span style="color:#94a3b8">${d.pep_description}</span>`;
        if (d.name)            html += `<br>Projeto: ${d.name}`;
        const consumed = evmMode ? d.actual_cost : d.consumed_hours;
        const budget   = evmMode ? d.budget_cost : d.budget_hours;
        html += `<br>${evmMode ? 'Custo real' : 'Consumido'}: <b>${fmtVal(consumed)}</b>`;
        if (budget != null) {
          const pct = (consumed / budget * 100).toFixed(1);
          html += `<br>Budget: ${fmtVal(budget)} (${pct}% utilizado)`;
        }
        if (!d.is_registered) html += `<br><span style="color:#f59e0b">⚠ PEP não cadastrado</span>`;
        return html;
      },
    },
    series: [{
      type: 'treemap',
      roam: false,
      width: '100%',
      height: '100%',
      breadcrumb: { show: false },
      label: {
        show: true, fontSize: 11, color: '#f1f5f9',
        formatter: params => {
          const d = health.find(x => x.pep_wbs === params.name);
          const val = d ? (evmMode ? d.actual_cost : d.consumed_hours) : 0;
          const valStr = evmMode
            ? 'R$' + (val / 1000 >= 1 ? (val / 1000).toFixed(0) + 'k' : val.toFixed(0))
            : val.toFixed(0) + 'h';
          const nm = params.name.length > 16 ? params.name.slice(0, 15) + '…' : params.name;
          return `${nm}\n${valStr}${d && !d.is_registered ? '\n⚠' : ''}`;
        },
      },
      itemStyle: { gapWidth: 2, borderRadius: 4 },
      levels: [{
        itemStyle: { borderWidth: 0, gapWidth: 4 },
        upperLabel: { show: false },
      }],
      data: health.map(d => {
        const consumed = evmMode ? d.actual_cost : d.consumed_hours;
        const budget   = evmMode ? d.budget_cost : d.budget_hours;
        return {
          name: d.pep_wbs,
          value: consumed,
          itemStyle: {
            color: !d.is_registered
              ? '#475569'
              : budget != null && consumed >= budget
                ? 'rgba(248,113,113,0.75)'
                : 'rgba(59,130,246,0.75)',
            borderColor: '#0f172a',
          },
        };
      }),
    }],
  };
}

function _buildBulletOption(withBudget, evmMode = false) {
  const labels  = withBudget.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 28)}` : ''));
  const budgets = withBudget.map(d => (evmMode ? d.budget_cost : d.budget_hours) || 0);
  const actuals = withBudget.map((d, i) => {
    const consumed = evmMode ? d.actual_cost : d.consumed_hours;
    const pct = budgets[i] > 0 ? consumed / budgets[i] : 0;
    const color = pct >= 1.0 ? '#f87171' : pct >= 0.75 ? '#f59e0b' : '#3b82f6';
    return { value: +consumed.toFixed(2), itemStyle: { color, borderRadius: [0, 2, 2, 0] } };
  });
  const unit = evmMode ? 'R$' : 'h';
  const fmtAx = evmMode
    ? v => v >= 1000 ? `R$${(v/1000).toFixed(0)}k` : `R$${v.toFixed(0)}`
    : v => `${v}h`;
  return {
    backgroundColor: 'transparent',
    grid: { top: 16, right: '10%', bottom: 16, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'none' },
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const b = budgets[params[0].dataIndex];
        const a = params.find(p => p.seriesName === 'Realizado')?.value ?? 0;
        const pct = b > 0 ? `${(a / b * 100).toFixed(1)}%` : '—';
        const fmtV = v => evmMode
          ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })
          : v.toFixed(1) + 'h';
        let html = `<b>${params[0].axisValue.replace('\n', ' ')}</b><br>`;
        html += `Orçado: <b>${fmtV(b)}</b><br>Realizado: <b>${fmtV(a)}</b><br>`;
        html += `Utilização: <b>${pct}</b>`;
        if (b > 0 && a > b) html += `<br><span style="color:#f87171">⚠ Acima do orçado</span>`;
        return html;
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 10, formatter: fmtAx },
      splitLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'category', data: labels,
      axisTick: { show: false },
      axisLabel: { color: '#e2e8f0', fontSize: 10, lineHeight: 16 },
    },
    series: [
      {
        name: 'Budget',
        type: 'bar',
        barMaxWidth: 48,
        barGap: '-100%',
        z: 1,
        data: budgets.map(b => ({
          value: b,
          itemStyle: {
            color: 'rgba(148,163,184,0.18)',
            borderColor: 'rgba(148,163,184,0.35)',
            borderWidth: 1,
            borderRadius: [0, 3, 3, 0],
          },
        })),
      },
      {
        name: 'Realizado',
        type: 'bar',
        barMaxWidth: 28,
        barGap: '-100%',
        z: 2,
        data: actuals,
        label: {
          show: true,
          position: 'right',
          fontSize: 10,
          color: '#e2e8f0',
          formatter: params => {
            const b = budgets[params.dataIndex];
            return b > 0 ? `${(params.value / b * 100).toFixed(0)}%` : '';
          },
        },
      },
    ],
  };
}

function _buildTrendsOption(trends) {
  const cats    = trends.map(d => d.cycle_name);
  const normals = trends.map(d => +d.normal_hours.toFixed(2));
  const extras  = trends.map(d => +d.extra_hours.toFixed(2));
  const costs   = trends.map(d => +(d.actual_cost ?? 0).toFixed(2));
  return {
    backgroundColor: 'transparent',
    legend: {
      data: ['Horas Normais', 'Horas Extras', 'Custo Real'],
      top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '8%', bottom: 48, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<b>${params[0].axisValue}</b><br>`;
        let totalHours = 0;
        params.forEach(p => {
          if (p.seriesName === 'Custo Real') {
            html += `${p.marker} ${p.seriesName}: <b>R$ ${p.value.toLocaleString('pt-BR', {minimumFractionDigits:2})}</b><br>`;
          } else {
            html += `${p.marker} ${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br>`;
            totalHours += p.value;
          }
        });
        html += `<div style="border-top:1px solid #475569;padding-top:4px;margin-top:4px">Total horas: <b>${totalHours.toFixed(1)}h</b></div>`;
        return html;
      },
    },
    xAxis: {
      type: 'category',
      data: cats,
      axisLabel: { color: '#94a3b8', rotate: cats.length > 6 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: [
      {
        type: 'value', name: 'Horas',
        nameTextStyle: { color: '#94a3b8', fontSize: 11 },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` },
        splitLine: { lineStyle: { color: '#334155' } },
      },
      {
        type: 'value', name: 'R$',
        nameTextStyle: { color: '#94a3b8', fontSize: 11 },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `R$${(v/1000).toFixed(0)}k` },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Horas Normais', type: 'line', yAxisIndex: 0,
        data: normals, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#3b82f6', width: 2.5 },
        itemStyle: { color: '#3b82f6' },
        areaStyle: { color: 'rgba(59,130,246,0.12)' },
      },
      {
        name: 'Horas Extras', type: 'line', yAxisIndex: 0,
        data: extras, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#f59e0b', width: 2.5 },
        itemStyle: { color: '#f59e0b' },
        areaStyle: { color: 'rgba(245,158,11,0.10)' },
      },
      {
        name: 'Custo Real', type: 'line', yAxisIndex: 1,
        data: costs, smooth: true, symbol: 'diamond', symbolSize: 8,
        lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
        itemStyle: { color: '#10b981' },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Stats row (effort tab)
// ---------------------------------------------------------------------------
function _buildStatsRow(data, budgetData = []) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;
  const row   = document.createElement('div'); row.className = 'stats-row';
  const cards = [
    { val: fmt(normal),  lbl: 'Horas Normais', cls: 'blue'    },
    { val: fmt(extra),   lbl: 'Horas Extras',  cls: 'amber'   },
    { val: fmt(standby), lbl: 'Sobreaviso',    cls: 'violet'  },
    { val: fmt(total),   lbl: 'Total',         cls: 'green'   },
    { val: data.length,  lbl: 'Colaboradores', cls: 'neutral' },
  ];
  if (budgetData.length > 0) {
    const totalBudget = budgetData.reduce((s, d) => s + d.budget_hours, 0);
    const totalActual = budgetData.reduce((s, d) => s + d.actual_hours, 0);
    const pct  = totalBudget > 0 ? (totalActual / totalBudget * 100).toFixed(1) : '—';
    const over = totalBudget > 0 && totalActual > totalBudget;
    cards.push(
      { val: fmt(totalBudget), lbl: 'Orçado (PEPs c/ budget)', cls: 'neutral' },
      { val: `${pct}%`,        lbl: 'Realizado vs Orçado',    cls: over ? 'red' : 'green' },
    );
  }
  cards.forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div'); card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;
let _allCycles   = [];

async function loadCyclesTable() {
  try {
    _allCycles = await apiFetch('/api/cycles');
    _renderCyclesTable(_allCycles);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderCyclesTable(cycles) {
  const tbody = document.getElementById('cyclesBody');
  if (!cycles.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">Nenhum ciclo encontrado.</td></tr>';
    return;
  }
  tbody.innerHTML = cycles.map(c => `
    <tr>
      <td>${escHtml(c.name)}</td>
      <td>${c.start_date}</td>
      <td>${c.end_date}</td>
      <td><span class="badge-status ${c.is_quarantine ? 'quarantine' : 'ativo'}">${c.is_quarantine ? 'Quarentena' : 'Regular'}</span></td>
      <td style="text-align:right">${c.record_count.toLocaleString('pt-BR')}</td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openCycleModal(${c.id})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="deleteCycle(${c.id}, '${escHtml(c.name)}', ${c.record_count})">Excluir</button>
      </div></td>
    </tr>`).join('');
}

function openCycleModal(id = null) {
  _cycleEditId = id;
  document.getElementById('cycleModalTitle').textContent = id ? 'Editar Ciclo' : 'Novo Ciclo';
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
  document.getElementById('cycleModal').hidden = false;
}

function closeCycleModal() { document.getElementById('cycleModal').hidden = true; }

document.getElementById('cycleSaveBtn').addEventListener('click', async () => {
  const body = {
    name:       document.getElementById('cycleNameInput').value.trim(),
    start_date: document.getElementById('cycleStartInput').value,
    end_date:   document.getElementById('cycleEndInput').value,
  };
  if (!body.name || !body.start_date || !body.end_date) {
    document.getElementById('cycleError').textContent = 'Preencha todos os campos obrigatórios.';
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
  const q = e.target.value.toLowerCase();
  _renderCyclesTable(q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles);
});

async function deleteCycle(id, name, count) {
  if (count > 0) { notify(`Ciclo "${name}" possui ${count} registro(s) e não pode ser excluído.`, 'error'); return; }
  if (!confirm(`Excluir o ciclo "${name}"?`)) return;
  try { await apiFetchJSON(`/api/cycles/${id}`, 'DELETE'); loadCyclesTable(); loadDashboardCycles(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId  = null;
let _allProjects    = [];
let _consumedByPep  = {};

async function loadProjectsTable() {
  try {
    const [projects, health] = await Promise.all([
      apiFetch('/api/projects'),
      apiFetch('/api/portfolio-health').catch(() => []),
    ]);
    _allProjects   = projects;
    _consumedByPep = Object.fromEntries(health.map(h => [h.pep_wbs, h.consumed_hours]));
    _renderProjectsTable(projects);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _buildBudgetCell(p) {
  if (p.budget_hours == null) return '—';
  const consumed = _consumedByPep[p.pep_wbs];
  const budgetStr = p.budget_hours.toLocaleString('pt-BR') + 'h';
  if (!consumed) return budgetStr;
  const pct = consumed / p.budget_hours;
  if (pct >= 1.0) return `${budgetStr}<span class="badge-budget critical" title="${consumed.toFixed(1)}h consumidas">Estourado</span>`;
  if (pct >= 0.9) return `${budgetStr}<span class="badge-budget warning" title="${consumed.toFixed(1)}h consumidas">Atenção ≥90%</span>`;
  return budgetStr;
}

function _renderProjectsTable(projects) {
  const tbody = document.getElementById('projectsBody');
  if (!projects.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">Nenhum projeto encontrado.</td></tr>';
    return;
  }
  tbody.innerHTML = projects.map(p => `
    <tr>
      <td><code>${escHtml(p.pep_wbs)}</code></td>
      <td>${escHtml(p.name || '—')}</td>
      <td>${escHtml(p.client || '—')}</td>
      <td>${escHtml(p.manager || '—')}</td>
      <td style="text-align:right">${_buildBudgetCell(p)}</td>
      <td><span class="badge-status ${p.status}">${p.status}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="deleteProject(${p.id}, '${escHtml(p.pep_wbs)}')">Excluir</button>
      </div></td>
    </tr>`).join('');
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectModalTitle').textContent = id ? 'Editar Projeto' : 'Novo Projeto';
  document.getElementById('projectError').textContent = '';
  if (id) {
    const p = _allProjects.find(x => x.id === id);
    if (p) {
      document.getElementById('projectPepInput').value         = p.pep_wbs;
      document.getElementById('projectNameInput').value        = p.name    || '';
      document.getElementById('projectClientInput').value      = p.client  || '';
      document.getElementById('projectManagerInput').value     = p.manager || '';
      document.getElementById('projectBudgetInput').value      = p.budget_hours ?? '';
      document.getElementById('projectBudgetCostInput').value  = p.budget_cost ?? '';
      document.getElementById('projectStatusInput').value      = p.status;
    }
  } else {
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput','projectBudgetInput','projectBudgetCostInput']
      .forEach(fid => { document.getElementById(fid).value = ''; });
    document.getElementById('projectStatusInput').value = 'ativo';
  }
  document.getElementById('projectModal').hidden = false;
}

function closeProjectModal() { document.getElementById('projectModal').hidden = true; }

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep = document.getElementById('projectPepInput').value.trim();
  if (!pep) { document.getElementById('projectError').textContent = 'Código PEP é obrigatório.'; return; }
  const budget     = document.getElementById('projectBudgetInput').value;
  const budgetCost = document.getElementById('projectBudgetCostInput').value;
  const body = {
    pep_wbs:      pep,
    name:         document.getElementById('projectNameInput').value.trim()    || null,
    client:       document.getElementById('projectClientInput').value.trim()  || null,
    manager:      document.getElementById('projectManagerInput').value.trim() || null,
    budget_hours: budget     !== '' ? parseFloat(budget)     : null,
    budget_cost:  budgetCost !== '' ? parseFloat(budgetCost) : null,
    status:       document.getElementById('projectStatusInput').value,
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
  const q = e.target.value.toLowerCase();
  _renderProjectsTable(q ? _allProjects.filter(p =>
    (p.pep_wbs || '').toLowerCase().includes(q) ||
    (p.name    || '').toLowerCase().includes(q) ||
    (p.client  || '').toLowerCase().includes(q)
  ) : _allProjects);
});

async function deleteProject(id, pep) {
  if (!confirm(`Excluir o projeto "${pep}"?`)) return;
  try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); loadProjectsTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

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
  await Promise.all([loadSeniorityLevels(), loadRateCards()]);
  await loadTeamTable();
}

async function loadSeniorityLevels() {
  try {
    _allSeniorityLevels = await apiFetch('/api/seniority-levels');
    const tbody = document.getElementById('seniorityBody');
    if (!_allSeniorityLevels.length) {
      tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;color:#475569;padding:1.5rem">Nenhum nível cadastrado.</td></tr>';
      return;
    }
    tbody.innerHTML = _allSeniorityLevels.map(l => `
      <tr>
        <td>${escHtml(l.name)}</td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openSeniorityModal(${l.id})">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteSeniorityLevel(${l.id}, '${escHtml(l.name)}')">Excluir</button>
        </div></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function loadRateCards() {
  try {
    _allRateCards = await apiFetch('/api/rate-cards');
    const tbody = document.getElementById('rateCardBody');
    if (!_allRateCards.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#475569;padding:1.5rem">Nenhuma taxa cadastrada.</td></tr>';
      return;
    }
    tbody.innerHTML = _allRateCards.map(c => `
      <tr>
        <td>${escHtml(c.seniority_level_name)}</td>
        <td style="text-align:right">R$ ${Number(c.hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2})}</td>
        <td>${c.valid_from}</td>
        <td>${c.valid_to ?? '—'}</td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openRateCardModal(${c.id})">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteRateCard(${c.id})">Excluir</button>
        </div></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function loadTeamTable() {
  try {
    _allTeam = await apiFetch('/api/team');
    const tbody = document.getElementById('teamBody');
    if (!_allTeam.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#475569;padding:1.5rem">Nenhum colaborador encontrado.</td></tr>';
      return;
    }
    tbody.innerHTML = _allTeam.map(m => `
      <tr>
        <td>${escHtml(m.name)}</td>
        <td>${m.seniority_level_name ? escHtml(m.seniority_level_name) : '<span style="color:#475569">—</span>'}</td>
        <td style="text-align:right">${m.current_hourly_rate != null ? 'R$ ' + Number(m.current_hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2}) : '—'}</td>
        <td><button class="btn btn-secondary btn-sm" onclick="openAssignSeniority(${m.id}, '${escHtml(m.name)}', ${m.seniority_level_id ?? 'null'})">Atribuir</button></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Seniority level modal
function openSeniorityModal(id = null) {
  _seniorityEditId = id;
  document.getElementById('seniorityModalTitle').textContent = id ? 'Editar Nível' : 'Novo Nível de Senioridade';
  document.getElementById('seniorityError').textContent = '';
  const l = id ? _allSeniorityLevels.find(x => x.id === id) : null;
  document.getElementById('seniorityNameInput').value = l ? l.name : '';
  document.getElementById('seniorityModal').hidden = false;
}
function closeSeniorityModal() { document.getElementById('seniorityModal').hidden = true; }

document.getElementById('senioritySaveBtn').addEventListener('click', async () => {
  const name = document.getElementById('seniorityNameInput').value.trim();
  if (!name) { document.getElementById('seniorityError').textContent = 'Nome é obrigatório.'; return; }
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

async function deleteSeniorityLevel(id, name) {
  if (!confirm(`Excluir o nível "${name}"?`)) return;
  try { await apiFetchJSON(`/api/seniority-levels/${id}`, 'DELETE'); await loadSeniorityLevels(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
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
  document.getElementById('rateCardModalTitle').textContent = id ? 'Editar Taxa' : 'Nova Taxa';
  document.getElementById('rateCardError').textContent = '';
  const c = id ? _allRateCards.find(x => x.id === id) : null;
  _populateLevelSelect('rateCardLevelInput', c?.seniority_level_id ?? null);
  document.getElementById('rateCardRateInput').value = c ? c.hourly_rate : '';
  document.getElementById('rateCardFromInput').value = c ? c.valid_from : '';
  document.getElementById('rateCardToInput').value   = c ? (c.valid_to ?? '') : '';
  document.getElementById('rateCardModal').hidden = false;
}
function closeRateCardModal() { document.getElementById('rateCardModal').hidden = true; }

document.getElementById('rateCardSaveBtn').addEventListener('click', async () => {
  const rate = document.getElementById('rateCardRateInput').value;
  const from = document.getElementById('rateCardFromInput').value;
  if (!rate || !from) { document.getElementById('rateCardError').textContent = 'Preencha os campos obrigatórios.'; return; }
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

async function deleteRateCard(id) {
  if (!confirm('Excluir esta taxa?')) return;
  try { await apiFetchJSON(`/api/rate-cards/${id}`, 'DELETE'); await loadRateCards(); await loadTeamTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Assign seniority modal
function openAssignSeniority(collabId, name, currentLevelId) {
  _assignCollabId = collabId;
  document.getElementById('assignSeniorityTitle').textContent = `Senioridade — ${name}`;
  document.getElementById('assignSeniorityError').textContent = '';
  const sel = document.getElementById('assignSenioritySelect');
  sel.innerHTML = '<option value="">— Sem senioridade —</option>' +
    _allSeniorityLevels.map(l =>
      `<option value="${l.id}" ${l.id === currentLevelId ? 'selected' : ''}>${escHtml(l.name)}</option>`
    ).join('');
  document.getElementById('assignSeniorityModal').hidden = false;
}
function closeAssignSeniority() { document.getElementById('assignSeniorityModal').hidden = true; }

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

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg; el.className = type; el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 6000);
}

function fmt(h) { return h >= 1000 ? (h / 1000).toFixed(1) + 'k' : Number(h).toFixed(1); }

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
loadDashboardCycles();
_renderActiveTab();
