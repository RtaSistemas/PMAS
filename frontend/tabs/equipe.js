/* PMAS — Equipe (Team) tab module
 * Extracted from app.js — MA-01 refactor
 */

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
  const hintEl = document.getElementById('overAllocHint');
  if (hintEl) hintEl.style.display = _isAdmin() ? 'none' : 'block';
  if (_isAdmin()) await _loadOverAllocation();
}

// ── F5: Over-allocation Detection ─────────────────────────────────────────────

let _overAllocData = [];

const _overAllocPag = _makePaginator(
  { container: 'overAllocPagination', prev: 'overAllocPrevBtn', next: 'overAllocNextBtn', pageSize: 'overAllocPageSize', label: 'overAllocPageLabel', entity: 'over_alloc.title' },
  rows => _renderTable('overAllocBody', rows, {
    colspan: 4,
    emptyKey: 'over_alloc.empty',
    rowFn: it => `
    <tr>
      <td>${escHtml(it.collaborator)}</td>
      <td>${fmtDateBR(it.date)}</td>
      <td class="text-right" style="color:var(--red);font-weight:600">${formatHours(it.total_hours)}</td>
      <td style="font-size:.8rem;color:var(--text-2)">${it.pep_list.map(escHtml).join(', ') || '—'}</td>
    </tr>`,
  })
);

function _renderOverAllocTable(rows) { _overAllocPag.render(rows); }

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
    _overAllocPag.reset();
    _renderOverAllocTable(_applySort('overAllocTable', _overAllocData));
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
  { container: 'seniorityPagination', prev: 'seniorityPrevBtn', next: 'seniorityNextBtn', pageSize: 'seniorityPageSize', label: 'seniorityPageLabel', entity: 'seniority.title' },
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
  { container: 'rateCardPagination', prev: 'rateCardPrevBtn', next: 'rateCardNextBtn', pageSize: 'rateCardPageSize', label: 'rateCardPageLabel', entity: 'ratecard.title' },
  rows => _renderTable('rateCardBody', rows, {
    colspan: 5,
    emptyKey: 'no_rates',
    rowFn: c => `
    <tr>
      <td>${escHtml(c.seniority_level_name)}</td>
      <td style="text-align:right">${_fmtCost(c.hourly_rate)}</td>
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
  { container: 'teamPagination', prev: 'teamPrevBtn', next: 'teamNextBtn', pageSize: 'teamPageSize', label: 'teamPageLabel', entity: 'team.title' },
  rows => _renderTable('teamBody', rows, {
    colspan: 4,
    emptyKey: 'no_team',
    rowFn: m => `
    <tr>
      <td>${escHtml(m.name)}</td>
      <td>${m.seniority_level_name ? escHtml(m.seniority_level_name) : `<span style="color:${_cssVar('--text-3')}">—</span>`}</td>
      <td style="text-align:right">${m.current_hourly_rate != null ? _fmtCost(m.current_hourly_rate) : '—'}</td>
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
  } catch (err) { notify(_friendlyError(err), 'error'); }
  e.target.value = '';
});

function deleteSeniorityLevel(id, name) {
  confirmDialog(_t('confirm.delete_level'), async () => {
    try { await apiFetchJSON(`/api/seniority-levels/${id}`, 'DELETE'); await loadSeniorityLevels(); }
    catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (err) { notify(_friendlyError(err), 'error'); }
  e.target.value = '';
});

function deleteRateCard(id) {
  confirmDialog(_t('confirm.delete_rate'), async () => {
    try { await apiFetchJSON(`/api/rate-cards/${id}`, 'DELETE'); await loadRateCards(); await loadTeamTable(); }
    catch (e) { notify(_friendlyError(e), 'error'); }
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
    } catch (e) { notify(_friendlyError(e), 'error'); }
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
// Sortable column headers for Equipe tables
// ---------------------------------------------------------------------------
_makeSortable('seniorityTable',   [{key:'name',type:'str'}, null], () => _allSeniorityLevels, _renderSeniorityTable);
_makeSortable('rateCardTable',    [{key:'seniority_level_name',type:'str'}, {key:'hourly_rate',type:'num'}, {key:'valid_from',type:'date'}, {key:'valid_to',type:'date'}, null], () => _allRateCards, _renderRateCardsTable);
_makeSortable('teamTable',        [{key:'name',type:'str'}, {key:'seniority_level_name',type:'str'}, {key:'current_hourly_rate',type:'num'}, null], () => { const q = document.getElementById('teamSearch')?.value?.toLowerCase(); return q ? _allTeam.filter(t => t.name.toLowerCase().includes(q)) : _allTeam; }, _renderTeamTable);
_makeSortable('overAllocTable',   [{key:'collaborator',type:'str'}, {key:'date',type:'date'}, {key:'total_hours',type:'num'}, null], () => _overAllocData, _renderOverAllocTable);
