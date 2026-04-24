/* PMAS — Frontend App */

// ---------------------------------------------------------------------------
// MultiSelect component
// ---------------------------------------------------------------------------
class MultiSelect {
  constructor(el, placeholder, onChange) {
    this.el = el;
    this.placeholder = placeholder;
    this.onChange = onChange;
    this.items = [];
    this.selected = new Set();
    this._build();
  }

  _build() {
    this.el.classList.add('ms-root');
    this.btn = document.createElement('button');
    this.btn.type = 'button';
    this.btn.className = 'ms-toggle';
    this.btn.innerHTML = `<span class="ms-label"></span><span class="ms-arrow">▾</span>`;
    this.panel = document.createElement('div');
    this.panel.className = 'ms-dropdown';
    this.panel.hidden = true;
    this.el.appendChild(this.btn);
    this.el.appendChild(this.panel);
    this.btn.addEventListener('click', e => { e.stopPropagation(); this.panel.hidden = !this.panel.hidden; });
    document.addEventListener('click', e => { if (!this.el.contains(e.target)) this.panel.hidden = true; });
    this._updateBtn();
  }

  setItems(items, preserve = false) {
    this.items = items;
    if (!preserve) {
      this.selected.clear();
    } else {
      const valid = new Set(items.map(i => String(i.value)));
      for (const v of [...this.selected]) { if (!valid.has(v)) this.selected.delete(v); }
    }
    this._renderPanel();
    this._updateBtn();
  }

  getValues() { return [...this.selected]; }

  clear() { this.selected.clear(); this._renderPanel(); this._updateBtn(); }

  _updateBtn() {
    const lbl = this.btn.querySelector('.ms-label');
    if (this.selected.size === 0) {
      lbl.textContent = this.placeholder; this.btn.classList.remove('has-value');
    } else if (this.selected.size === 1) {
      const v = [...this.selected][0];
      const item = this.items.find(i => String(i.value) === v);
      lbl.textContent = item ? item.label : v; this.btn.classList.add('has-value');
    } else {
      lbl.textContent = `${this.selected.size} selecionados`; this.btn.classList.add('has-value');
    }
  }

  _renderPanel() {
    this.panel.innerHTML = '';
    if (this.items.length === 0) {
      const e = document.createElement('div'); e.className = 'ms-empty'; e.textContent = 'Sem opções'; this.panel.appendChild(e); return;
    }
    const allLbl = this._makeRow('__all__', 'Selecionar todos', true);
    const allChk = allLbl.querySelector('input');
    allChk.checked = this.selected.size === this.items.length && this.items.length > 0;
    allChk.indeterminate = this.selected.size > 0 && this.selected.size < this.items.length;
    allChk.addEventListener('change', e => {
      e.stopPropagation();
      if (allChk.checked) this.items.forEach(i => this.selected.add(String(i.value))); else this.selected.clear();
      this._renderPanel(); this._updateBtn(); this.onChange?.();
    });
    this.panel.appendChild(allLbl);
    this.items.forEach(item => {
      const lbl = this._makeRow(item.value, item.label, false);
      const chk = lbl.querySelector('input');
      chk.checked = this.selected.has(String(item.value));
      chk.addEventListener('change', e => {
        e.stopPropagation();
        if (chk.checked) this.selected.add(String(item.value)); else this.selected.delete(String(item.value));
        this._renderPanel(); this._updateBtn(); this.onChange?.();
      });
      this.panel.appendChild(lbl);
    });
  }

  _makeRow(value, label, isAll) {
    const lbl = document.createElement('label');
    lbl.className = 'ms-option' + (isAll ? ' ms-all' : '');
    lbl.addEventListener('click', e => e.stopPropagation());
    const chk = document.createElement('input'); chk.type = 'checkbox'; chk.value = value;
    const span = document.createElement('span'); span.textContent = label;
    lbl.appendChild(chk); lbl.appendChild(span); return lbl;
  }
}

// ---------------------------------------------------------------------------
// Tab navigation
// ---------------------------------------------------------------------------
const tabBtns = document.querySelectorAll('.tab-btn');
const tabSections = document.querySelectorAll('.tab-section');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;

    if (btn.dataset.tab === 'cycles')   loadCyclesTable();
    if (btn.dataset.tab === 'projects') loadProjectsTable();
  });
});

// ---------------------------------------------------------------------------
// Dashboard — DOM refs and multi-select
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

// ---------------------------------------------------------------------------
// Cascading dropdowns
// ---------------------------------------------------------------------------
async function onCycleChange()    { updateLoadBtn(); await Promise.all([refreshPeps(), refreshCollaborators()]); }
async function onPepChange()      { updateLoadBtn(); refreshPepDescriptions(); await refreshCollaborators(); }
async function onPepDescChange()  { updateLoadBtn(); await refreshCollaborators(); }
async function onCollabChange()   { updateLoadBtn(); await refreshPeps(); }

function updateLoadBtn() {
  loadBtn.disabled = !(cycleMs.getValues().length || pepMs.getValues().length ||
                        pepDescMs.getValues().length || collaboratorMs.getValues().length);
}

async function loadDashboardCycles() {
  try {
    const list = await apiFetch('/api/cycles');
    cycleMs.setItems(list.map(c => ({ value: String(c.id), label: c.name + (c.is_quarantine ? ' ⚠' : '') })), true);
    updateLoadBtn();
  } catch (err) { notify(`Erro ao carregar ciclos: ${err.message}`, 'error'); }
}

async function refreshPeps() {
  const params = new URLSearchParams();
  cycleMs.getValues().forEach(id => params.append('cycle_id', id));
  collaboratorMs.getValues().forEach(id => params.append('collaborator_id', id));
  try {
    const data = await apiFetch(`/api/peps?${params}`);
    pepDataCache = {};
    data.forEach(p => { pepDataCache[p.code] = p; });
    pepMs.setItems(data.map(p => ({ value: p.code, label: `${p.code}  (${p.total_records} reg.)` })), true);
    refreshPepDescriptions();
  } catch (err) { notify(`Erro ao carregar PEPs: ${err.message}`, 'error'); }
}

function refreshPepDescriptions() {
  const sel = pepMs.getValues();
  const src = sel.length > 0 ? sel.map(c => pepDataCache[c]).filter(Boolean) : Object.values(pepDataCache);
  const descs = [...new Set(src.flatMap(p => p.descriptions))].sort();
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  const params = new URLSearchParams();
  cycleMs.getValues().forEach(id => params.append('cycle_id', id));
  pepMs.getValues().forEach(c  => params.append('pep_code', c));
  pepDescMs.getValues().forEach(d => params.append('pep_description', d));
  try {
    const list = await apiFetch(`/api/collaborators?${params}`);
    collaboratorMs.setItems(list.map(c => ({ value: String(c.id), label: c.name })), true);
  } catch (err) { notify(`Erro ao carregar colaboradores: ${err.message}`, 'error'); }
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
    if (json.records_skipped > 0) msg += ` (${json.records_skipped} duplicata(s) ignorada(s))`;
    if (json.quarantine_cycles_created > 0) msg += ` ⚠ ${json.quarantine_cycles_created} ciclo(s) de Quarentena criado(s).`;
    notify(msg, json.quarantine_cycles_created > 0 ? 'info' : 'success');
    await loadDashboardCycles();
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
// Load dashboard
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', async () => {
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  if (!(cycleIds.length || pepCodes.length || pepDescs.length || collabIds.length)) return;

  loadBtn.disabled = true; loadBtn.textContent = 'Carregando…';

  const buildParams = () => {
    const p = new URLSearchParams();
    pepCodes.forEach(c  => p.append('pep_code', c));
    pepDescs.forEach(d  => p.append('pep_description', d));
    collabIds.forEach(id => p.append('collaborator_id', id));
    return p;
  };

  try {
    if (cycleIds.length === 0) {
      try { addChartPanel(await apiFetch(`/api/dashboard?${buildParams()}`)); }
      catch (err) { notify(`Erro: ${err.message}`, 'error'); }
    } else {
      for (const cycleId of cycleIds) {
        try { addChartPanel(await apiFetch(`/api/dashboard/${cycleId}?${buildParams()}`)); }
        catch (err) { notify(`Erro no ciclo ${cycleId}: ${err.message}`, 'error'); }
      }
    }
  } finally { updateLoadBtn(); loadBtn.textContent = 'Carregar'; }
});

clearBtn.addEventListener('click', () => {
  pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  updateLoadBtn(); refreshPepDescriptions(); refreshCollaborators();
});

// ---------------------------------------------------------------------------
// Chart panels
// ---------------------------------------------------------------------------
let _chartSeq = 0;

function addChartPanel(payload) {
  const id = `chart-${++_chartSeq}`;
  const panel = document.createElement('div'); panel.className = 'chart-panel card';
  const header = document.createElement('div'); header.className = 'panel-header';
  const titleEl = document.createElement('div'); titleEl.className = 'panel-title'; titleEl.textContent = buildPanelTitle(payload);
  const closeBtn = document.createElement('button'); closeBtn.className = 'panel-close'; closeBtn.title = 'Fechar'; closeBtn.textContent = '×';
  header.appendChild(titleEl); header.appendChild(closeBtn); panel.appendChild(header);
  panel.appendChild(buildStatsRow(payload.data));
  const chartDiv = document.createElement('div'); chartDiv.id = id;
  chartDiv.style.cssText = `width:100%;height:${calcHeight(payload.data.length)}px`;
  panel.appendChild(chartDiv);
  document.getElementById('chartsContainer').prepend(panel);
  const instance = echarts.init(chartDiv, 'dark');
  instance.setOption(buildChartOption(payload));
  const onResize = () => instance.resize(); window.addEventListener('resize', onResize);
  closeBtn.addEventListener('click', () => { window.removeEventListener('resize', onResize); instance.dispose(); panel.remove(); });
}

function buildPanelTitle(payload) {
  const { cycle, filters } = payload; let t = cycle.name;
  if (filters.pep_codes?.length)        t += `  |  PEP: ${filters.pep_codes.join(', ')}`;
  if (filters.pep_descriptions?.length) t += `  →  ${filters.pep_descriptions.join(', ')}`;
  return t;
}

function buildStatsRow(data) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;
  const row = document.createElement('div'); row.className = 'stats-row';
  [
    { val: fmt(normal),  lbl: 'Horas Normais', cls: 'blue' },
    { val: fmt(extra),   lbl: 'Horas Extras',  cls: 'amber' },
    { val: fmt(standby), lbl: 'Sobreaviso',    cls: 'violet' },
    { val: fmt(total),   lbl: 'Total',         cls: 'green' },
    { val: data.length,  lbl: 'Colaboradores', cls: 'neutral' },
  ].forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div'); card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

function calcHeight(count) { return Math.max(420, Math.min(count, 40) * 52 + 120); }

function buildChartOption(payload) {
  const { cycle, data } = payload; const MAX = 40;
  const slice = data.length > MAX ? data.slice(0, MAX) : data;
  const byName = {}; data.forEach(d => { byName[d.collaborator] = d; });
  const truncNote = data.length > MAX ? `   (top ${MAX} de ${data.length})` : '';
  return {
    backgroundColor: 'transparent',
    title: {
      text: cycle.is_quarantine ? `${cycle.name}  ⚠ QUARENTENA` : cycle.name,
      subtext: cycle.start_date ? `${cycle.start_date}  →  ${cycle.end_date}${truncNote}` : truncNote.trim(),
      left: 'center', top: 4,
      textStyle: { color: '#f1f5f9', fontSize: 13, fontWeight: 600 },
      subtextStyle: { color: '#64748b', fontSize: 11 },
    },
    legend: { data: ['Horas Normais', 'Horas Extras', 'Sobreaviso'], top: 52, left: 'center', textStyle: { color: '#cbd5e1', fontSize: 12 }, itemGap: 24, itemWidth: 14, itemHeight: 10 },
    grid: { top: 96, right: '3%', bottom: 28, left: '2%', containLabel: true },
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
    xAxis: { type: 'value', name: 'Horas', nameTextStyle: { color: '#94a3b8', fontSize: 11 }, axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` }, splitLine: { lineStyle: { color: '#1e293b' } } },
    yAxis: {
      type: 'category', data: slice.map(r => r.collaborator), axisTick: { show: false },
      axisLabel: {
        fontSize: 10, lineHeight: 16,
        formatter: name => {
          const d = byName[name]; if (!d) return name;
          const t = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
          const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
          return `{nm|${nm}}\n{hr|N: ${d.normal_hours.toFixed(1)}h  E: ${d.extra_hours.toFixed(1)}h  S: ${d.standby_hours.toFixed(1)}h  T: ${t}h}`;
        },
        rich: { nm: { color: '#e2e8f0', fontSize: 11, lineHeight: 18 }, hr: { color: '#64748b', fontSize: 9, lineHeight: 14 } },
      },
    },
    series: [
      { name: 'Horas Normais', type: 'bar', stack: 'total', data: slice.map(r => +r.normal_hours.toFixed(2)),  itemStyle: { color: '#3b82f6' }, barMaxWidth: 32 },
      { name: 'Horas Extras',  type: 'bar', stack: 'total', data: slice.map(r => +r.extra_hours.toFixed(2)),   itemStyle: { color: '#f59e0b' }, barMaxWidth: 32 },
      { name: 'Sobreaviso',    type: 'bar', stack: 'total', data: slice.map(r => +r.standby_hours.toFixed(2)), itemStyle: { color: '#8b5cf6' }, barMaxWidth: 32 },
    ],
  };
}

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;

async function loadCyclesTable() {
  const tbody = document.getElementById('cyclesBody');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">Carregando…</td></tr>';
  try {
    const cycles = await apiFetch('/api/cycles');
    if (!cycles.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">Nenhum ciclo cadastrado.</td></tr>'; return; }
    tbody.innerHTML = cycles.map(c => `
      <tr>
        <td>${escHtml(c.name)}</td>
        <td>${c.start_date}</td>
        <td>${c.end_date}</td>
        <td><span class="badge-status ${c.is_quarantine ? 'quarantine' : 'ativo'}">${c.is_quarantine ? 'Quarentena' : 'Regular'}</span></td>
        <td style="text-align:right">${c.record_count.toLocaleString('pt-BR')}</td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openCycleModal(${c.id})">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteCycle(${c.id},'${escHtml(c.name)}',${c.record_count})">Excluir</button>
        </div></td>
      </tr>`).join('');
  } catch (err) { tbody.innerHTML = `<tr><td colspan="6" style="color:#f87171;padding:1rem">${err.message}</td></tr>`; }
}

function openCycleModal(id = null) {
  _cycleEditId = id;
  document.getElementById('cycleError').textContent = '';
  if (id === null) {
    document.getElementById('cycleModalTitle').textContent = 'Novo Ciclo';
    document.getElementById('cycleNameInput').value = '';
    document.getElementById('cycleStartInput').value = '';
    document.getElementById('cycleEndInput').value = '';
  } else {
    apiFetch('/api/cycles').then(cycles => {
      const c = cycles.find(x => x.id === id); if (!c) return;
      document.getElementById('cycleModalTitle').textContent = 'Editar Ciclo';
      document.getElementById('cycleNameInput').value  = c.name;
      document.getElementById('cycleStartInput').value = c.start_date;
      document.getElementById('cycleEndInput').value   = c.end_date;
    });
  }
  document.getElementById('cycleModal').hidden = false;
}

function closeCycleModal() { document.getElementById('cycleModal').hidden = true; }

document.getElementById('cycleModalClose').addEventListener('click', closeCycleModal);
document.getElementById('cycleCancelBtn').addEventListener('click', closeCycleModal);
document.getElementById('newCycleBtn').addEventListener('click', () => openCycleModal());

document.getElementById('cycleSaveBtn').addEventListener('click', async () => {
  const name  = document.getElementById('cycleNameInput').value.trim();
  const start = document.getElementById('cycleStartInput').value;
  const end   = document.getElementById('cycleEndInput').value;
  const errEl = document.getElementById('cycleError');
  errEl.textContent = '';
  if (!name || !start || !end) { errEl.textContent = 'Preencha todos os campos obrigatórios.'; return; }
  try {
    const url = _cycleEditId ? `/api/cycles/${_cycleEditId}` : '/api/cycles';
    const method = _cycleEditId ? 'PUT' : 'POST';
    await apiFetchJSON(url, method, { name, start_date: start, end_date: end });
    closeCycleModal();
    await loadCyclesTable();
    await loadDashboardCycles();
  } catch (err) { errEl.textContent = err.message; }
});

async function deleteCycle(id, name, count) {
  if (count > 0) { alert(`O ciclo "${name}" possui ${count.toLocaleString('pt-BR')} registro(s) e não pode ser excluído.`); return; }
  if (!confirm(`Excluir o ciclo "${name}"?`)) return;
  try { await apiFetchJSON(`/api/cycles/${id}`, 'DELETE'); await loadCyclesTable(); await loadDashboardCycles(); }
  catch (err) { alert(`Erro: ${err.message}`); }
}

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId = null;

async function loadProjectsTable() {
  const tbody = document.getElementById('projectsBody');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">Carregando…</td></tr>';
  try {
    const projects = await apiFetch('/api/projects');
    if (!projects.length) { tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">Nenhum projeto cadastrado.</td></tr>'; return; }
    tbody.innerHTML = projects.map(p => `
      <tr>
        <td><code style="color:#93c5fd;font-size:0.85rem">${escHtml(p.pep_wbs)}</code></td>
        <td>${escHtml(p.name || '—')}</td>
        <td>${escHtml(p.client || '—')}</td>
        <td>${escHtml(p.manager || '—')}</td>
        <td style="text-align:right">${p.budget_hours != null ? p.budget_hours.toLocaleString('pt-BR') + 'h' : '—'}</td>
        <td><span class="badge-status ${p.status}">${p.status.charAt(0).toUpperCase() + p.status.slice(1)}</span></td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProject(${p.id},'${escHtml(p.pep_wbs)}')">Excluir</button>
        </div></td>
      </tr>`).join('');
  } catch (err) { tbody.innerHTML = `<tr><td colspan="7" style="color:#f87171;padding:1rem">${err.message}</td></tr>`; }
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectError').textContent = '';
  if (id === null) {
    document.getElementById('projectModalTitle').textContent = 'Novo Projeto';
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput','projectBudgetInput'].forEach(i => document.getElementById(i).value = '');
    document.getElementById('projectStatusInput').value = 'ativo';
  } else {
    apiFetch('/api/projects').then(projects => {
      const p = projects.find(x => x.id === id); if (!p) return;
      document.getElementById('projectModalTitle').textContent = 'Editar Projeto';
      document.getElementById('projectPepInput').value     = p.pep_wbs;
      document.getElementById('projectNameInput').value    = p.name || '';
      document.getElementById('projectClientInput').value  = p.client || '';
      document.getElementById('projectManagerInput').value = p.manager || '';
      document.getElementById('projectBudgetInput').value  = p.budget_hours ?? '';
      document.getElementById('projectStatusInput').value  = p.status;
    });
  }
  document.getElementById('projectModal').hidden = false;
}

function closeProjectModal() { document.getElementById('projectModal').hidden = true; }

document.getElementById('projectModalClose').addEventListener('click', closeProjectModal);
document.getElementById('projectCancelBtn').addEventListener('click', closeProjectModal);
document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal());

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep     = document.getElementById('projectPepInput').value.trim();
  const errEl   = document.getElementById('projectError');
  errEl.textContent = '';
  if (!pep) { errEl.textContent = 'Código PEP é obrigatório.'; return; }
  const budget = document.getElementById('projectBudgetInput').value;
  const body = {
    pep_wbs:      pep,
    name:         document.getElementById('projectNameInput').value.trim() || null,
    client:       document.getElementById('projectClientInput').value.trim() || null,
    manager:      document.getElementById('projectManagerInput').value.trim() || null,
    budget_hours: budget !== '' ? parseFloat(budget) : null,
    status:       document.getElementById('projectStatusInput').value,
  };
  try {
    const url = _projectEditId ? `/api/projects/${_projectEditId}` : '/api/projects';
    const method = _projectEditId ? 'PUT' : 'POST';
    await apiFetchJSON(url, method, body);
    closeProjectModal(); await loadProjectsTable();
  } catch (err) { errEl.textContent = err.message; }
});

async function deleteProject(id, pep) {
  if (!confirm(`Excluir o projeto "${pep}"?`)) return;
  try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); await loadProjectsTable(); }
  catch (err) { alert(`Erro: ${err.message}`); }
}

// Close modals clicking backdrop
document.getElementById('cycleModal').addEventListener('click', e => { if (e.target === e.currentTarget) closeCycleModal(); });
document.getElementById('projectModal').addEventListener('click', e => { if (e.target === e.currentTarget) closeProjectModal(); });

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) { const j = await res.json().catch(() => ({})); throw new Error(j.detail ?? res.statusText); }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const opts = { method, headers: {} };
  if (body && method !== 'DELETE') { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  const res = await fetch(url, opts);
  if (res.status === 204) return null;
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.detail ?? res.statusText);
  return json;
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg; el.className = type; el.style.display = 'block';
  if (type === 'success') setTimeout(() => { el.style.display = 'none'; }, 6000);
}

function fmt(h) { return h >= 1000 ? (h / 1000).toFixed(1) + 'k' : h.toFixed(1); }

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
loadDashboardCycles();
