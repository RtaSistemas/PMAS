/* PMAS — Admin tab module
 * Extracted from app.js — MA-01 refactor
 */

// ---------------------------------------------------------------------------
// Users management (Admin tab)
// ---------------------------------------------------------------------------
let _allUsers = [];

const _usersPag = _makePaginator(
  { container: 'usersPagination', prev: 'usersPrevBtn', next: 'usersNextBtn', pageSize: 'usersPageSize', label: 'usersPageLabel', entity: 'admin.title' },
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
    } catch (e) { notify(_friendlyError(e), 'error'); }
  });
}

// ---------------------------------------------------------------------------
// Audit Log (Admin tab)
// ---------------------------------------------------------------------------

let _auditLogCache = [];

const _auditPag = _makePaginator(
  { container: 'auditPagination', prev: 'auditPrevBtn', next: 'auditNextBtn', pageSize: 'auditPageSize', label: 'auditPageLabel', entity: 'auditlog.title' },
  rows => _renderTable('auditBody', rows, {
    colspan: 6,
    emptyKey: 'no_audit',
    rowFn: r => {
      const when = _fmtDate(r.timestamp);
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
      <td style="font-size:.78rem;color:${_cssVar('--text-3')};max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(detail)}">${escHtml(detail)}</td>
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
    color_text_muted: '#818998', color_card: '#0e2038',
    color_border: '#1e3a5f', color_text_hint: '#818998',
    color_violet: '#a78bfa', density: 'normal', border_radius: 'normal',
    chart_palette: ['#4f8ef7','#d9b273','#a78bfa','#35a1f3','#5ad388','#01c1b9','#f472b6','#fb923c'],
  },
  corporate: {
    color_primary: '#0070f3', color_background: '#0a0a23',
    color_surface: '#111133', color_accent: '#00d4ff',
    color_success: '#00c853', color_warning: '#ffab00',
    color_danger:  '#ff1744', color_text: '#f0f4ff',
    color_text_muted: '#7986cb', color_card: '#111133',
    color_border: '#1e2f60', color_text_hint: '#7986cb',
    color_violet: '#7c4dff', density: 'normal', border_radius: 'normal',
    chart_palette: ['#0070f3','#00d4ff','#00c853','#ffab00','#7c4dff','#26c6da','#e040fb','#ff7043'],
  },
  high_contrast: {
    color_primary: '#ffffff', color_background: '#000000',
    color_surface: '#111111', color_accent: '#ffff00',
    color_success: '#00ff00', color_warning: '#ff8800',
    color_danger:  '#ff0000', color_text: '#ffffff',
    color_text_muted: '#aaaaaa', color_card: '#111111',
    color_border: '#444444', color_text_hint: '#aaaaaa',
    color_violet: '#dd88ff', density: 'relaxed', border_radius: 'sharp',
    chart_palette: ['#ffffff','#ffff00','#00ff00','#ff8800','#00ffff','#ff00ff','#88ff88','#ff8888'],
  },
};


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

async function moveRule(id, direction) {
  const idx = _rules.findIndex(r => r.id === id);
  if (idx < 0) return;
  const newIdx = idx + direction;
  if (newIdx < 0 || newIdx >= _rules.length) return;
  [_rules[idx], _rules[newIdx]] = [_rules[newIdx], _rules[idx]];
  const orderMap = {};
  _rules.forEach((r, i) => { orderMap[r.id] = i + 1; });
  try {
    await apiFetchJSON('/api/validation-rules/reorder', 'POST', orderMap);
    _renderRulesList();
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

function _renderRulesList() {
  const ul = document.getElementById('rulesList');
  if (!ul) return;
  if (!_rules.length) {
    ul.innerHTML = `<li style="text-align:center;color:${_cssVar('--text-3')};padding:1rem;font-size:.85rem">${_t('vr.empty')}</li>`;
    return;
  }
  ul.innerHTML = _rules.map((r, ruleIdx) => {
    const actionBadge = `<span class="rule-badge ${r.action}">${r.action}</span>`;
    const systemBadge = r.is_system ? `<span class="rule-badge system">🔒 ${_t('vr.badge.system')}</span>` : '';
    const activeClass = r.is_active ? '' : 'rule-inactive';
    const editBtn  = r.is_system ? '' :
      `<button class="btn btn-secondary btn-sm" onclick="openEditRule(${r.id})">✎</button>`;
    const delBtn = r.is_system ? '' :
      `<button class="btn btn-danger btn-sm" onclick="deleteRule(${r.id})">✕</button>`;
    const toggleTitle = _t(r.is_active ? 'vr.btn.deactivate' : 'vr.btn.activate');
    const moveUpBtn  = `<button class="btn btn-secondary btn-sm" title="${_t('vr.btn.move_up') || 'Mover acima'}" aria-label="${_t('vr.btn.move_up') || 'Mover acima'}" onclick="moveRule(${r.id}, -1)" ${ruleIdx === 0 ? 'disabled' : ''}>↑</button>`;
    const moveDnBtn  = `<button class="btn btn-secondary btn-sm" title="${_t('vr.btn.move_down') || 'Mover abaixo'}" aria-label="${_t('vr.btn.move_down') || 'Mover abaixo'}" onclick="moveRule(${r.id}, 1)" ${ruleIdx === _rules.length - 1 ? 'disabled' : ''}>↓</button>`;
    return `<li class="sortable-item ${activeClass}" data-rule-id="${r.id}">
      <span class="sortable-handle">⠿</span>
      <span class="sortable-item-label">
        <strong>${escHtml(r.field)}</strong>
        <span style="color:${_cssVar('--text-3')};font-size:.75rem;margin:0 .3rem">${escHtml(r.operator)}</span>
        <span style="color:${_cssVar('--text')}">${escHtml(r.value || '—')}</span>
        ${r.description ? `<span style="color:${_cssVar('--text-3')};font-size:.75rem;margin-left:.5rem">— ${escHtml(r.description)}</span>` : ''}
      </span>
      ${actionBadge}${systemBadge}
      <div class="sortable-item-actions">
        ${moveUpBtn}${moveDnBtn}
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
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    onEnd: async () => {
      const items = [...ul.querySelectorAll('[data-rule-id]')];
      const orderMap = {};
      items.forEach((el, idx) => { orderMap[el.dataset.ruleId] = idx + 1; });
      try {
        await apiFetchJSON('/api/validation-rules/reorder', 'POST', orderMap);
        loadRulesList();
      } catch (e) { notify(_friendlyError(e), 'error'); }
    },
  });
  _addKeyboardReorder(ul);
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

function deleteRule(id) {
  confirmDialog(_t('confirm.delete_rule'), async () => {
    try {
      await apiFetchJSON(`/api/validation-rules/${id}`, 'DELETE');
      loadRulesList();
      notify(_t('msg.rule_deleted'), 'success');
    } catch (e) { notify(_friendlyError(e), 'error'); }
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
    ? `${r.reviewed_by} em ${_fmtDate(r.reviewed_at)}`
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
}



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

    const when = _fmtDate(r.uploaded_at);
    title.textContent = `Importação — ${r.source_file}`;
    meta.innerHTML = [
      `<span style="color:${_cssVar('--text-3')}">Data</span><span>${escHtml(when)}</span>`,
      `<span style="color:${_cssVar('--text-3')}">Usuário</span><span>${escHtml(r.uploaded_by_username)}</span>`,
      `<span style="color:${_cssVar('--text-3')}">Arquivo</span><span style="word-break:break-all">${escHtml(r.source_file)}</span>`,
      `<span style="color:${_cssVar('--text-3')}">Status</span><span>${escHtml(r.status)}</span>`,
    ].join('');

    const chip = (label, val, color) =>
      `<span style="background:${color}22;color:${color};border:1px solid ${color}44;border-radius:.3rem;padding:.15rem .6rem;font-size:.78rem">${label}: <strong>${val}</strong></span>`;
    counts.innerHTML =
      chip('Inseridos',  r.records_inserted,        _cssVar('--green')) +
      chip('Ignorados',  r.records_skipped,          _cssVar('--text-3')) +
      chip('Quarentena', r.quarantine_added,         _cssVar('--red')) +
      chip('Avisos',     r.warning_count,            _cssVar('--amber')) +
      chip('Infos',      r.info_count,               _cssVar('--primary'));

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
        `<p style="font-size:.78rem;font-weight:600;color:${_cssVar('--amber')};margin:0">⚠ Avisos</p>
         <button type="button" id="sdWarnCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdWarnCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.warnings_detail, 'Avisos')), 0);
      wDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailWarningsHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:${_cssVar('--amber')};margin:0">⚠ Avisos</p>`;
      wDiv.hidden = true;
    }
    if (r.infos_detail?.length) {
      iList.innerHTML = r.infos_detail.map(i => `<li>${escHtml(i)}</li>`).join('');
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:${_cssVar('--primary')};margin:0">ℹ Informações</p>
         <button type="button" id="sdInfoCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdInfoCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.infos_detail, 'Informações')), 0);
      iDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:${_cssVar('--primary')};margin:0">ℹ Informações</p>`;
      iDiv.hidden = true;
    }

    openModal('sessionDetailModal');
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

// ---------------------------------------------------------------------------
// Theme editor (Admin tab)
// ---------------------------------------------------------------------------
const _THEME_COLS = [
  { id: 'Structure', fields: [
    { key: 'color_background',  label: 'appearance.f_bg' },
    { key: 'color_surface',     label: 'appearance.f_surface' },
    { key: 'color_card',        label: 'appearance.f_card',   optional: true },
    { key: 'color_border',      label: 'appearance.f_border', optional: true },
    { key: 'color_text',        label: 'appearance.f_text' },
    { key: 'color_text_muted',  label: 'appearance.f_text2' },
    { key: 'color_text_hint',   label: 'appearance.f_text3',  optional: true },
  ]},
  { id: 'Interaction', fields: [
    { key: 'color_primary',     label: 'appearance.f_primary' },
    { key: 'color_accent',      label: 'appearance.f_accent' },
    { key: 'color_violet',      label: 'appearance.f_violet',  optional: true },
  ]},
  { id: 'Semantic', fields: [
    { key: 'color_success',     label: 'appearance.f_success' },
    { key: 'color_warning',     label: 'appearance.f_warning' },
    { key: 'color_danger',      label: 'appearance.f_danger' },
  ]},
];
const _THEME_FIELDS = _THEME_COLS.flatMap(c => c.fields);

let _currentTheme = {};

async function _loadThemeEditor() {
  try {
    _currentTheme = await fetch('/api/theme').then(r => r.json());
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

function _applyThemePreset(key) {
  const preset = _THEME_PRESETS[key];
  if (!preset) return;
  _applyThemePresetConfig(preset);
}

function _applyThemePresetConfig(preset) {
  if (!preset) return;
  _THEME_FIELDS.forEach(f => {
    const v = preset[f.key];
    if (v !== undefined) {
      const picker = document.getElementById(`themeColor_${f.key}`);
      const txt    = document.getElementById(`themeColorTxt_${f.key}`);
      if (picker) picker.value = v || '#000000';
      if (txt)    txt.value   = v || '';
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
  if (preset.border_radius !== undefined) {
    document.querySelectorAll('.theme-radius-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.radius === (preset.border_radius || 'normal'));
    });
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
    } catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
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
  const activeR2 = document.querySelector('.theme-radius-btn.active');
  if (activeR2) payload.border_radius = activeR2.dataset.radius;
  const fontEl2 = document.getElementById('themeFont');
  if (fontEl2) payload.font_family = fontEl2.value || null;
  const pal2 = Array.from({ length: 8 }, (_, i) =>
    document.getElementById(`themePalTxt_${i}`)?.value?.trim() || ''
  ).filter(c => c);
  payload.chart_palette = pal2.length >= 6 ? pal2 : _THEME_PRESETS.pmas.chart_palette;
  try {
    await apiFetchJSON('/api/theme/presets', 'POST', { name, config: payload });
    notify(_t('appearance.preset_saved'), 'success');
    if (nameInput) nameInput.value = '';
    _renderCustomPresets();
  } catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
  input.value = '';
}

function _buildColorField(f, value) {
  const v = (value != null && value !== '') ? value : '';
  const colorVal = v || '#000000';
  return `
    <div class="theme-field">
      <label style="font-size:.7rem;color:var(--text-3)">${escHtml(_t(f.label))}</label>
      <div class="theme-swatch-row">
        <input type="color" id="themeColor_${f.key}" value="${escHtml(colorVal)}" />
        <input type="text" id="themeColorTxt_${f.key}" value="${escHtml(v)}"
          style="flex:1;font-size:.8rem" placeholder="${f.optional ? _t('appearance.optional') : ''}" />
      </div>
    </div>`;
}

function _renderThemeEditor() {
  const t   = _currentTheme;
  const pal = (t.chart_palette?.length >= 6) ? t.chart_palette : _THEME_PRESETS.pmas.chart_palette;

  // Populate 3 columns
  _THEME_COLS.forEach(col => {
    const el = document.getElementById(`themeCol${col.id}Fields`);
    if (!el) return;
    el.innerHTML = col.fields.map(f => _buildColorField(f, t[f.key])).join('');
  });

  // Palette (8 swatches)
  const palEl = document.getElementById('themeModalPalette');
  if (palEl) {
    palEl.innerHTML = Array.from({ length: 8 }, (_, i) => `
      <div class="theme-pal-item">
        <input type="color" id="themePalColor_${i}" value="${escHtml(pal[i] || '#4f8ef7')}" />
        <input type="text"  id="themePalTxt_${i}"   value="${escHtml(pal[i] || '')}"
          placeholder="Cor ${i + 1}" style="font-size:.75rem" />
      </div>`).join('');
  }

  // App name
  const appNameEl = document.getElementById('themeAppName');
  if (appNameEl) appNameEl.value = t.app_name || 'PMAS';

  // Font
  const fontEl = document.getElementById('themeFont');
  if (fontEl) fontEl.value = t.font_family || '';

  // Density buttons
  const density = t.density || 'normal';
  document.querySelectorAll('.theme-density-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.density === density);
  });

  // Radius buttons
  const radius = t.border_radius || 'normal';
  document.querySelectorAll('.theme-radius-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.radius === radius);
  });

  _renderCustomPresets();

  // Wire color pickers ↔ text inputs
  _THEME_FIELDS.forEach(f => {
    const picker = document.getElementById(`themeColor_${f.key}`);
    const txt    = document.getElementById(`themeColorTxt_${f.key}`);
    picker?.addEventListener('input', () => { if (txt) txt.value = picker.value; });
    txt?.addEventListener('change',  () => {
      const v = txt.value.trim();
      if (/^#[0-9a-f]{6}$/i.test(v) && picker) picker.value = v;
    });
  });
  Array.from({ length: 8 }, (_, i) => {
    const picker = document.getElementById(`themePalColor_${i}`);
    const txt    = document.getElementById(`themePalTxt_${i}`);
    picker?.addEventListener('input', () => { if (txt) txt.value = picker.value; });
    txt?.addEventListener('change',  () => {
      const v = txt.value.trim();
      if (/^#[0-9a-f]{6}$/i.test(v) && picker) picker.value = v;
    });
  });

  // Density toggle + live preview
  document.getElementById('themeDensityBtns')?.querySelectorAll('.theme-density-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.theme-density-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const d = _DENSITY_MAP[btn.dataset.density] || _DENSITY_MAP.normal;
      document.documentElement.style.setProperty('--density-spacing',   d.spacing);
      document.documentElement.style.setProperty('--density-font-size', d.fontSize);
    });
  });

  // Radius toggle + live preview
  document.getElementById('themeRadiusBtns')?.querySelectorAll('.theme-radius-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.theme-radius-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const radMap = { sharp: '2px',  normal: '8px',  rounded: '16px' };
      const lgMap  = { sharp: '4px',  normal: '12px', rounded: '24px' };
      document.documentElement.style.setProperty('--radius',    radMap[btn.dataset.radius] || '8px');
      document.documentElement.style.setProperty('--radius-lg', lgMap[btn.dataset.radius]  || '12px');
    });
  });
}

document.getElementById('saveThemeBtn')?.addEventListener('click', async () => {
  const payload = { ..._currentTheme };
  _THEME_FIELDS.forEach(f => {
    const txt = document.getElementById(`themeColorTxt_${f.key}`);
    if (txt !== null) payload[f.key] = txt.value.trim() || null;
  });
  // Required fields must not be null
  const _required = ['color_primary','color_background','color_surface','color_accent','color_success','color_warning','color_danger','color_text','color_text_muted'];
  _required.forEach(k => { if (!payload[k]) payload[k] = _THEME_PRESETS.pmas[k]; });
  const appNameEl = document.getElementById('themeAppName');
  if (appNameEl) payload.app_name = appNameEl.value.trim() || 'PMAS';
  const fontEl = document.getElementById('themeFont');
  if (fontEl) payload.font_family = fontEl.value || null;
  const activeD = document.querySelector('.theme-density-btn.active');
  if (activeD) payload.density = activeD.dataset.density;
  const activeR = document.querySelector('.theme-radius-btn.active');
  if (activeR) payload.border_radius = activeR.dataset.radius;
  const pal = Array.from({ length: 8 }, (_, i) =>
    document.getElementById(`themePalTxt_${i}`)?.value?.trim() || ''
  ).filter(c => c);
  payload.chart_palette = pal.length >= 6 ? pal : _THEME_PRESETS.pmas.chart_palette;
  try {
    _currentTheme = await apiFetchJSON('/api/theme', 'PUT', payload);
    _loadTheme();
    closeModal('themeModal');
    notify(_t('appearance.saved'), 'success');
  } catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (e) { notify(_friendlyError(e), 'error'); }
  e.target.value = '';
});

document.getElementById('deleteLogoBtn')?.addEventListener('click', () => {
  confirmDialog(_t('confirm.delete_logo'), async () => {
    try {
      _currentTheme = await apiFetchJSON('/api/theme/logo', 'DELETE');
      _loadTheme();
      notify(_t('msg.logo_removed'), 'success');
    } catch (e) { notify(_friendlyError(e), 'error'); }
  });
});

document.getElementById('openThemeModalBtn')?.addEventListener('click', async () => {
  if (!Object.keys(_currentTheme).length) {
    try { _currentTheme = await fetch('/api/theme').then(r => r.json()); }
    catch { /* ignore */ }
  }
  _renderThemeEditor();
  openModal('themeModal');
});



// ---------------------------------------------------------------------------
// Sortable column headers for Admin tables
// ---------------------------------------------------------------------------
_makeSortable('usersTable',  [{key:'username',type:'str'}, {key:'role',type:'str'}, null], () => { const q = document.getElementById('userSearch')?.value?.toLowerCase(); return q ? _allUsers.filter(u => u.username.toLowerCase().includes(q) || (u.role||'').toLowerCase().includes(q)) : _allUsers; }, _renderUsersTable);
_makeSortable('auditTable',  [{key:'timestamp',type:'date'}, {key:'username',type:'str'}, {key:'action',type:'str'}, {key:'entity',type:'str'}, {key:'entity_id',type:'num'}, null], () => _auditLogCache, _renderAuditLog);
