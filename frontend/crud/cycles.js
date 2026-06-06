/* PMAS — Cycles CRUD
 * Depends on globals defined in app.js:
 *   _makePaginator, _renderTable, _isAdmin, _applySort, _loadTable
 *   apiFetch, apiFetchJSON, _authHeaders
 *   _t, _locale, _cssVar, escHtml
 *   notify, _friendlyError, openModal, closeModal, confirmDialog
 *   loadDashboardCycles
 * Must be loaded AFTER app.js in index.html.
 */

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;
let _allCycles = [];

const _cyclesPag = _makePaginator(
  { container: 'cyclesPagination', prev: 'cyclesPrevBtn', next: 'cyclesNextBtn', pageSize: 'cyclesPageSize', label: 'cyclesPageLabel', entity: 'cycles.title' },
  rows => {
    const admin = _isAdmin();
    _renderTable('cyclesBody', rows, {
      colspan: 6,
      emptyKey: 'no_cycles',
      rowFn: c => `
    <tr style="${!c.is_active ? 'opacity:.5' : ''}">
      <td>${escHtml(c.name)}${!c.is_active ? ` <em style="color:${_cssVar('--text-3')};font-size:.8rem">(arquivado)</em>` : ''}</td>
      <td>${c.start_date}</td>
      <td>${c.end_date}</td>
      <td><span class="badge-status ativo">${_t('badge.regular')}</span></td>
      <td style="text-align:right">${c.record_count.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US')}</td>
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
    } catch (e) { notify(_friendlyError(e), 'error'); }
  });
}

function toggleCycleArchive(id, isActive) {
  confirmDialog(_t(isActive ? 'confirm.archive_cycle' : 'confirm.restore_cycle'), async () => {
    try {
      await apiFetchJSON(`/api/cycles/${id}/toggle-archive`, 'PATCH');
      loadCyclesTable();
      loadDashboardCycles();
    } catch (e) { notify(_friendlyError(e), 'error'); }
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
    catch (e) { notify(_friendlyError(e), 'error'); }
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
  } catch (err) { notify(_friendlyError(err), 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Sortable column headers (moved here so _renderCyclesTable is already defined)
// ---------------------------------------------------------------------------
_makeSortable('cyclesTable',
  [{key:'name',type:'str'}, {key:'start_date',type:'date'}, {key:'end_date',type:'date'}, null, {key:'record_count',type:'num'}, null],
  () => { const q = document.getElementById('cycleSearch')?.value?.toLowerCase(); return q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles; },
  _renderCyclesTable
);
