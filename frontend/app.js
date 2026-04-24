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

    this.btn.addEventListener('click', e => {
      e.stopPropagation();
      this.panel.hidden = !this.panel.hidden;
    });
    document.addEventListener('click', e => {
      if (!this.el.contains(e.target)) this.panel.hidden = true;
    });

    this._updateBtn();
  }

  setItems(items, preserve = false) {
    this.items = items;
    if (!preserve) {
      this.selected.clear();
    } else {
      const valid = new Set(items.map(i => String(i.value)));
      for (const v of [...this.selected]) {
        if (!valid.has(v)) this.selected.delete(v);
      }
    }
    this._renderPanel();
    this._updateBtn();
  }

  getValues() { return [...this.selected]; }

  clear() {
    this.selected.clear();
    this._renderPanel();
    this._updateBtn();
  }

  _updateBtn() {
    const lbl = this.btn.querySelector('.ms-label');
    if (this.selected.size === 0) {
      lbl.textContent = this.placeholder;
      this.btn.classList.remove('has-value');
    } else if (this.selected.size === 1) {
      const v = [...this.selected][0];
      const item = this.items.find(i => String(i.value) === v);
      lbl.textContent = item ? item.label : v;
      this.btn.classList.add('has-value');
    } else {
      lbl.textContent = `${this.selected.size} selecionados`;
      this.btn.classList.add('has-value');
    }
  }

  _renderPanel() {
    this.panel.innerHTML = '';

    if (this.items.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'ms-empty';
      empty.textContent = 'Sem opções disponíveis';
      this.panel.appendChild(empty);
      return;
    }

    // "Select all" row
    const allLbl = this._makeRow('__all__', 'Selecionar todos', true);
    const allChk = allLbl.querySelector('input');
    allChk.checked = this.selected.size === this.items.length && this.items.length > 0;
    allChk.indeterminate = this.selected.size > 0 && this.selected.size < this.items.length;
    allChk.addEventListener('change', e => {
      e.stopPropagation();
      if (allChk.checked) this.items.forEach(i => this.selected.add(String(i.value)));
      else this.selected.clear();
      this._renderPanel();
      this._updateBtn();
      this.onChange?.();
    });
    this.panel.appendChild(allLbl);

    this.items.forEach(item => {
      const lbl = this._makeRow(item.value, item.label, false);
      const chk = lbl.querySelector('input');
      chk.checked = this.selected.has(String(item.value));
      chk.addEventListener('change', e => {
        e.stopPropagation();
        if (chk.checked) this.selected.add(String(item.value));
        else this.selected.delete(String(item.value));
        this._renderPanel();
        this._updateBtn();
        this.onChange?.();
      });
      this.panel.appendChild(lbl);
    });
  }

  _makeRow(value, label, isAll) {
    const lbl = document.createElement('label');
    lbl.className = 'ms-option' + (isAll ? ' ms-all' : '');
    lbl.addEventListener('click', e => e.stopPropagation());
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.value = value;
    const span = document.createElement('span');
    span.textContent = label;
    lbl.appendChild(chk);
    lbl.appendChild(span);
    return lbl;
  }
}

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const csvInput   = document.getElementById('csvInput');
const uploadZone = document.getElementById('uploadZone');
const loadBtn    = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const cycleMs      = new MultiSelect(document.getElementById('cycleMs'),       '— Selecione ciclo(s) —',      onCycleChange);
const pepMs        = new MultiSelect(document.getElementById('pepMs'),          '— Todos os PEPs —',           onPepChange);
const pepDescMs    = new MultiSelect(document.getElementById('pepDescMs'),      '— Todas as descrições —',     onPepDescChange);
const collaboratorMs = new MultiSelect(document.getElementById('collaboratorMs'), '— Todos —',                 onCollabChange);

let pepDataCache = {};   // code → {code, descriptions, total_records}

// ---------------------------------------------------------------------------
// Cascading dropdowns
// ---------------------------------------------------------------------------
async function onCycleChange() {
  updateLoadBtn();
  await Promise.all([refreshPeps(), refreshCollaborators()]);
}

async function onPepChange() {
  refreshPepDescriptions();
  await refreshCollaborators();
}

async function onPepDescChange() {
  await refreshCollaborators();
}

async function onCollabChange() {
  await refreshPeps();
}

function updateLoadBtn() {
  loadBtn.disabled = cycleMs.getValues().length === 0;
}

async function loadCycles() {
  try {
    const list = await apiFetch('/api/cycles');
    cycleMs.setItems(
      list.map(c => ({ value: String(c.id), label: c.name + (c.is_quarantine ? ' ⚠' : '') })),
      true
    );
    updateLoadBtn();
  } catch (err) {
    notify(`Erro ao carregar ciclos: ${err.message}`, 'error');
  }
}

async function refreshPeps() {
  const params = new URLSearchParams();
  cycleMs.getValues().forEach(id => params.append('cycle_id', id));
  collaboratorMs.getValues().forEach(id => params.append('collaborator_id', id));

  try {
    const data = await apiFetch(`/api/peps?${params}`);
    pepDataCache = {};
    data.forEach(p => { pepDataCache[p.code] = p; });
    pepMs.setItems(
      data.map(p => ({ value: p.code, label: `${p.code}  (${p.total_records} reg.)` })),
      true
    );
    refreshPepDescriptions();
  } catch (err) {
    notify(`Erro ao carregar PEPs: ${err.message}`, 'error');
  }
}

function refreshPepDescriptions() {
  const selected = pepMs.getValues();
  const source = selected.length > 0
    ? selected.map(c => pepDataCache[c]).filter(Boolean)
    : Object.values(pepDataCache);

  const descs = [...new Set(source.flatMap(p => p.descriptions))].sort();
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  const params = new URLSearchParams();
  cycleMs.getValues().forEach(id => params.append('cycle_id', id));
  pepMs.getValues().forEach(c => params.append('pep_code', c));
  pepDescMs.getValues().forEach(d => params.append('pep_description', d));

  try {
    const list = await apiFetch(`/api/collaborators?${params}`);
    collaboratorMs.setItems(
      list.map(c => ({ value: String(c.id), label: c.name })),
      true
    );
  } catch (err) {
    notify(`Erro ao carregar colaboradores: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
csvInput.addEventListener('change', async () => {
  const file = csvInput.files[0];
  if (!file) return;
  notify(`Enviando "${file.name}"…`, 'info');

  const form = new FormData();
  form.append('file', file);
  try {
    const res  = await fetch('/api/upload-timesheet', { method: 'POST', body: form });
    const json = await res.json();
    if (!res.ok) { notify(`Erro: ${json.detail ?? res.statusText}`, 'error'); return; }

    let msg = `✔ ${json.records_inserted.toLocaleString('pt-BR')} registro(s) importado(s).`;
    if (json.quarantine_cycles_created > 0)
      msg += ` ⚠ ${json.quarantine_cycles_created} ciclo(s) de Quarentena criado(s) para datas órfãs.`;

    notify(msg, json.quarantine_cycles_created > 0 ? 'info' : 'success');
    await loadCycles();
  } catch (err) {
    notify(`Falha na conexão: ${err.message}`, 'error');
  }
});

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.style.borderColor = '#3b82f6'; });
uploadZone.addEventListener('dragleave', () => { uploadZone.style.borderColor = ''; });
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.style.borderColor = '';
  const file = e.dataTransfer.files[0];
  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    csvInput.files = dt.files;
    csvInput.dispatchEvent(new Event('change'));
  }
});

// ---------------------------------------------------------------------------
// Load dashboard — one chart per selected cycle
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', async () => {
  const cycleIds = cycleMs.getValues();
  if (!cycleIds.length) return;

  loadBtn.disabled = true;
  loadBtn.textContent = 'Carregando…';

  try {
    for (const cycleId of cycleIds) {
      const params = new URLSearchParams();
      pepMs.getValues().forEach(c => params.append('pep_code', c));
      pepDescMs.getValues().forEach(d => params.append('pep_description', d));
      collaboratorMs.getValues().forEach(id => params.append('collaborator_id', id));

      try {
        const json = await apiFetch(`/api/dashboard/${cycleId}?${params}`);
        addChartPanel(json);
      } catch (err) {
        notify(`Erro no ciclo ${cycleId}: ${err.message}`, 'error');
      }
    }
  } finally {
    loadBtn.disabled = cycleMs.getValues().length === 0;
    loadBtn.textContent = 'Carregar';
  }
});

clearBtn.addEventListener('click', () => {
  pepMs.clear();
  pepDescMs.clear();
  collaboratorMs.clear();
  refreshPepDescriptions();
  refreshCollaborators();
});

// ---------------------------------------------------------------------------
// Chart panels
// ---------------------------------------------------------------------------
let _chartSeq = 0;

function addChartPanel(payload) {
  const id = `chart-${++_chartSeq}`;

  const panel = document.createElement('div');
  panel.className = 'chart-panel card';

  // Header
  const header = document.createElement('div');
  header.className = 'panel-header';

  const titleEl = document.createElement('div');
  titleEl.className = 'panel-title';
  titleEl.textContent = buildPanelTitle(payload);

  const closeBtn = document.createElement('button');
  closeBtn.className = 'panel-close';
  closeBtn.title = 'Fechar gráfico';
  closeBtn.textContent = '×';

  header.appendChild(titleEl);
  header.appendChild(closeBtn);
  panel.appendChild(header);

  // Stats
  panel.appendChild(buildStatsRow(payload.data));

  // Chart
  const chartDiv = document.createElement('div');
  chartDiv.id = id;
  const h = calcHeight(payload.data.length);
  chartDiv.style.cssText = `width:100%;height:${h}px`;
  panel.appendChild(chartDiv);

  document.getElementById('chartsContainer').prepend(panel);

  const instance = echarts.init(chartDiv, 'dark');
  instance.setOption(buildChartOption(payload));

  const onResize = () => instance.resize();
  window.addEventListener('resize', onResize);

  closeBtn.addEventListener('click', () => {
    window.removeEventListener('resize', onResize);
    instance.dispose();
    panel.remove();
  });
}

function buildPanelTitle(payload) {
  const { cycle, filters } = payload;
  let t = cycle.name;
  if (filters.pep_codes?.length)        t += `  |  PEP: ${filters.pep_codes.join(', ')}`;
  if (filters.pep_descriptions?.length) t += `  →  ${filters.pep_descriptions.join(', ')}`;
  return t;
}

function buildStatsRow(data) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;

  const row = document.createElement('div');
  row.className = 'stats-row';

  [
    { val: fmt(normal),  lbl: 'Horas Normais', cls: 'blue' },
    { val: fmt(extra),   lbl: 'Horas Extras',  cls: 'amber' },
    { val: fmt(standby), lbl: 'Sobreaviso',    cls: 'violet' },
    { val: fmt(total),   lbl: 'Total',         cls: 'green' },
    { val: data.length,  lbl: 'Colaboradores', cls: 'neutral' },
  ].forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div');
    card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });

  return row;
}

function calcHeight(count) {
  // Each row needs ~52px to fit 2-line label (name + hours breakdown)
  return Math.max(420, Math.min(count, 40) * 52 + 120);
}

function buildChartOption(payload) {
  const { cycle, data } = payload;
  const MAX = 40;
  const slice = data.length > MAX ? data.slice(0, MAX) : data;

  // Build lookup for y-axis label formatter
  const byName = {};
  data.forEach(d => { byName[d.collaborator] = d; });

  const categories = slice.map(r => r.collaborator);
  const normalH  = slice.map(r => +r.normal_hours.toFixed(2));
  const extraH   = slice.map(r => +r.extra_hours.toFixed(2));
  const standbyH = slice.map(r => +r.standby_hours.toFixed(2));

  const truncNote = data.length > MAX ? `   (top ${MAX} de ${data.length})` : '';

  return {
    backgroundColor: 'transparent',

    title: {
      text: cycle.is_quarantine ? `${cycle.name}  ⚠ QUARENTENA` : cycle.name,
      subtext: `${cycle.start_date}  →  ${cycle.end_date}${truncNote}`,
      left: 'center',
      top: 4,
      textStyle:    { color: '#f1f5f9', fontSize: 13, fontWeight: 600 },
      subtextStyle: { color: '#64748b', fontSize: 11 },
    },

    legend: {
      data: ['Horas Normais', 'Horas Extras', 'Sobreaviso'],
      top: 52,
      left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24,
      itemWidth: 14,
      itemHeight: 10,
    },

    grid: {
      top: 96,
      right: '3%',
      bottom: 28,
      left: '2%',
      containLabel: true,
    },

    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#475569',
      textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`;
        let total = 0;
        params.forEach(p => {
          if (p.value > 0) {
            html += `<div>${p.marker} ${p.seriesName}: <b>${p.value.toFixed(2)}h</b></div>`;
            total += p.value;
          }
        });
        if (params.length > 1)
          html += `<div style="margin-top:4px;border-top:1px solid #475569;padding-top:4px">Total: <b>${total.toFixed(2)}h</b></div>`;
        return html;
      },
    },

    xAxis: {
      type: 'value',
      name: 'Horas',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },

    yAxis: {
      type: 'category',
      data: categories,
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        lineHeight: 16,
        formatter: name => {
          const d = byName[name];
          if (!d) return name;
          const t = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
          const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
          return (
            `{nm|${nm}}\n` +
            `{hr|N: ${d.normal_hours.toFixed(1)}h  ` +
            `E: ${d.extra_hours.toFixed(1)}h  ` +
            `S: ${d.standby_hours.toFixed(1)}h  ` +
            `T: ${t}h}`
          );
        },
        rich: {
          nm: { color: '#e2e8f0', fontSize: 11, lineHeight: 18 },
          hr: { color: '#64748b', fontSize: 9,  lineHeight: 14 },
        },
      },
    },

    series: [
      { name: 'Horas Normais', type: 'bar', stack: 'total', data: normalH,  itemStyle: { color: '#3b82f6' }, barMaxWidth: 32 },
      { name: 'Horas Extras',  type: 'bar', stack: 'total', data: extraH,   itemStyle: { color: '#f59e0b' }, barMaxWidth: 32 },
      { name: 'Sobreaviso',    type: 'bar', stack: 'total', data: standbyH, itemStyle: { color: '#8b5cf6' }, barMaxWidth: 32 },
    ],
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const json = await res.json().catch(() => ({}));
    throw new Error(json.detail ?? res.statusText);
  }
  return res.json();
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg;
  el.className = type;
  el.style.display = 'block';
  if (type === 'success') setTimeout(() => { el.style.display = 'none'; }, 6000);
}

function fmt(h) {
  return h >= 1000 ? (h / 1000).toFixed(1) + 'k' : h.toFixed(1);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
loadCycles();
