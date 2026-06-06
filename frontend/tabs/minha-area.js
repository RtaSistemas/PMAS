/* PMAS — Minha Área tab module
 * Extracted from app.js — MA-01 refactor
 */

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

function _addKeyboardReorder(list) {
  list.addEventListener('keydown', e => {
    const item = e.target.closest('.sortable-item');
    if (!item || !list.contains(item)) return;
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    e.preventDefault();
    const sibling = e.key === 'ArrowUp' ? item.previousElementSibling : item.nextElementSibling;
    if (sibling) {
      if (e.key === 'ArrowUp') list.insertBefore(item, sibling);
      else list.insertBefore(sibling, item);
      item.focus();
      list.dispatchEvent(new Event('sortable-keyboard-update', { bubbles: true }));
    }
  });
  list.querySelectorAll('.sortable-item').forEach(item => {
    if (!item.hasAttribute('tabindex')) item.setAttribute('tabindex', '0');
  });
}

function _initChartLayout() {
  const list = document.getElementById('chartLayoutList');
  if (!list || typeof Sortable === 'undefined') return;
  if (_sortableLayout) _sortableLayout.destroy();
  _sortableLayout = Sortable.create(list, { animation: 150, handle: '.tab-handle', ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen' });
  _addKeyboardReorder(list);
  ['effort', 'portfolio', 'forecast'].forEach(tabId => {
    const pList = document.getElementById(`panelList-${tabId}`);
    if (!pList) return;
    if (_panelSortables[tabId]) _panelSortables[tabId].destroy();
    _panelSortables[tabId] = Sortable.create(pList, { animation: 120, handle: '.panel-handle', ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen' });
    _addKeyboardReorder(pList);
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

  // Forecast section collapse states (restore persisted open/closed)
  const fcs = prefs.forecast_sections;
  if (fcs) {
    _forecastAllocExpanded  = fcs.alloc      !== false;
    _whatIfExpanded         = fcs.whatif     !== false;
    _mcExpanded             = fcs.montecarlo !== false;
    _burnUpBaselineExpanded = fcs.baseline   !== false;
    _applyFcSection(_forecastAllocExpanded,  'forecastAllocBody',  'forecastAllocChevron',  'forecastAllocToggle');
    _applyFcSection(_whatIfExpanded,         'whatIfBody',         'whatIfChevron',          'whatIfToggle');
    _applyFcSection(_mcExpanded,             'mcBody',             'mcChevron',              'mcToggle');
    _applyFcSection(_burnUpBaselineExpanded, 'burnUpBaselineBody', 'burnUpBaselineChevron',  'burnUpBaselineToggle');
  }

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
    const dash = _userPrefs?.dashboard || {};
    _userPrefs = await apiFetchJSON('/api/my/preferences', 'PUT', { dashboard: { ...dash, chart_order: order, panel_order: panelOrder } });
    _applyLayoutPreferences();
    notify(_t('msg.layout_saved'), 'success');
  } catch (e) { notify(_friendlyError(e), 'error'); }
});

// My Area — change password
document.getElementById('myChangePwdBtn')?.addEventListener('click', () => {
  document.getElementById('myCurrentPwdInput').value = '';
  document.getElementById('myNewPwdInput').value = '';
  document.getElementById('myPwdError').textContent = '';
  openModal('myPwdModal');
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
  const resultEl   = document.getElementById('myAreaUploadResult');
  const uploadLabel = document.getElementById('myAreaCsvInput')?.closest('label');
  resultEl.textContent = '⏳ ' + _t('loading');
  if (uploadLabel) { uploadLabel.setAttribute('aria-disabled', 'true'); uploadLabel.style.opacity = '0.6'; uploadLabel.style.pointerEvents = 'none'; }
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
    notify(_friendlyError(e), 'error');
  }
  if (uploadLabel) { uploadLabel.removeAttribute('aria-disabled'); uploadLabel.style.opacity = ''; uploadLabel.style.pointerEvents = ''; }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// My Area — Histórico sub-tab
// ---------------------------------------------------------------------------
let _myHistoryCache = [];

const _historyPag = _makePaginator(
  { container: 'myHistoryPagination', prev: 'myHistoryPrevBtn', next: 'myHistoryNextBtn', pageSize: 'myHistoryPageSize', label: 'myHistoryPageLabel', entity: 'myarea.history' },
  rows => _renderTable('myHistoryBody', rows, {
    colspan: 9,
    emptyKey: 'msg.no_import_sessions',
    rowFn: r => {
      const when = _fmtDate(r.uploaded_at);
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
    const when = _fmtDate(r.uploaded_at);
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
  { container: 'myQrPagination', prev: 'myQrPrevBtn', next: 'myQrNextBtn', pageSize: 'myQrPageSize', label: 'myQrPageLabel', entity: 'myarea.quarantine' },
  rows => {
    const tbody = document.getElementById('myQrBody');
    if (!tbody) return;
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:${_cssVar('--text-3')};padding:2rem">${_t('msg.no_quarantine')}</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map(r => {
      const raw  = r.raw_data || {};
      const when = _fmtDate(r.ingested_at);
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
});



// ---------------------------------------------------------------------------
// Sortable column headers for Minha Área tables
// ---------------------------------------------------------------------------
_makeSortable('myHistoryTable', [{key:'uploaded_at',type:'date'}, {key:'source_file',type:'str'}, {key:'uploaded_by_username',type:'str'}, {key:'records_inserted',type:'num'}, {key:'records_skipped',type:'num'}, {key:'quarantine_added',type:'num'}, {key:'warning_count',type:'num'}, {key:'info_count',type:'num'}, {key:'status',type:'str'}], () => _myHistoryCache, _renderMyHistory);
_makeSortable('myQrTable',      [{key:'ingested_at',type:'date'}, null, null, null, null, {key:'quarantine_reason',type:'str'}, {key:'review_status',type:'str'}], () => _myQrCache, _renderMyQrTable);
