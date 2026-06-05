/* PMAS — Global UI Helpers */

// ---------------------------------------------------------------------------
// EVM color maps (shared between chart builders and stat cards)
// ---------------------------------------------------------------------------

// Backend EVM color → CSS variable name (for charts and table cells)
const _EVM_COLOR_CSS = {
  success: 'var(--green,#10d98a)',
  warning: 'var(--amber,#d9b273)',
  danger:  'var(--red,#c56d76)',
};

// Backend EVM color → stat-card CSS class
const _EVM_COLOR_CARD = { success: 'green', warning: 'amber', danger: 'red' };

// Health-color → CSS variable name (used in Treemap and Bullet chart)
const _HCSS = { success: '--green', warning: '--amber', danger: '--red', muted: '--text-3' };

// ---------------------------------------------------------------------------
// H1 — Health label → semaphore color (single source of truth)
// Accepts two health strings (health_hours, health_cost) from the API and
// returns the worst-case semaphore color: 'green' | 'yellow' | 'red' | 'grey'
// ---------------------------------------------------------------------------
const _HEALTH_RANK = { overrun: 3, critical: 2, warning: 1, ok: 0, no_budget: -1 };
const _HEALTH_TO_SEM = { ok: 'green', warning: 'yellow', critical: 'red', overrun: 'red', no_budget: 'grey' };

function _healthToSemColor(a, b) {
  if (a === 'no_budget' && b === 'no_budget') return 'grey';
  const worst = (_HEALTH_RANK[a] ?? 0) >= (_HEALTH_RANK[b] ?? 0) ? a : b;
  return _HEALTH_TO_SEM[worst] || 'grey';
}

// ---------------------------------------------------------------------------
// C1 — Stat card builder
// ---------------------------------------------------------------------------
function _mkStatCard({ val, lbl, cls, evm, sublbl, delta }) {
  const lblHtml = evm
    ? `<span data-evm="${evm}">${escHtml(lbl)}</span>`
    : escHtml(lbl);
  const sublblHtml = sublbl ? `<div class="sublbl">${escHtml(sublbl)}</div>` : '';
  const deltaHtml  = delta  ? delta : '';
  const ariaLbl = [lbl, val != null ? String(val) : '—', sublbl].filter(Boolean).join(', ');
  return `<div class="stat-card ${cls}" aria-label="${escHtml(ariaLbl)}">${deltaHtml}<div class="val">${val}</div><div class="lbl">${lblHtml}</div>${sublblHtml}</div>`;
}

// ---------------------------------------------------------------------------
// C2 — Loading state wrapper for async button handlers
// ---------------------------------------------------------------------------
async function _withLoading(btn, asyncFn) {
  const orig = btn ? btn.textContent : null;
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  try {
    return await asyncFn();
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = orig; }
  }
}

// ---------------------------------------------------------------------------
// C3 — Confirm-before-delete helper
// ---------------------------------------------------------------------------
function _confirmDelete(entityName, asyncFn) {
  confirmDialog(
    `Excluir ${entityName}? Esta ação não pode ser desfeita.`,
    asyncFn,
    true
  );
}

// ---------------------------------------------------------------------------
// C4 — ECharts default theme base (for use in new chart builders)
// ---------------------------------------------------------------------------
function _chartDefaults() {
  return {
    backgroundColor: 'transparent',
    textStyle:       { color: _cssVar('--text'), fontFamily: 'inherit' },
    tooltip: {
      backgroundColor: _cssVar('--card'),
      borderColor:     _cssVar('--border'),
      textStyle:       { color: _cssVar('--text'), fontSize: 12 },
    },
    aria: { enabled: true, decal: { show: true } },
  };
}

// ---------------------------------------------------------------------------
// C5 — Render an empty-state message into a container element
// ---------------------------------------------------------------------------
function _renderEmptyState(container, message) {
  container.innerHTML = `<p class="empty-state" style="text-align:center;color:var(--text-3);padding:2rem">${escHtml(message)}</p>`;
}

// ---------------------------------------------------------------------------
// C6 — Build a <tr> element from an array of cell descriptors
// Each cell is either a plain string (used as innerHTML) or an object:
//   { html: '...', style: '...', cls: '...' }
// Optional attrs object sets attributes on the <tr> itself.
// ---------------------------------------------------------------------------
function _buildTableRow(cells, attrs = {}) {
  const tr = document.createElement('tr');
  Object.entries(attrs).forEach(([k, v]) => tr.setAttribute(k, v));
  tr.innerHTML = cells.map(c =>
    typeof c === 'string'
      ? `<td>${c}</td>`
      : `<td style="${c.style || ''}" class="${c.cls || ''}">${c.html ?? c}</td>`
  ).join('');
  return tr;
}

// ---------------------------------------------------------------------------
// C7 — Generic table loader — handles fetch + error notification
// ---------------------------------------------------------------------------
async function _loadTable(endpoint, onSuccess) {
  try {
    const data = await apiFetch(endpoint);
    onSuccess(data);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// C8 — Generic table renderer — handles empty state + row injection
// ---------------------------------------------------------------------------
function _renderTable(tbodyId, data, { colspan, emptyKey, rowFn }) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-3);padding:2rem">${_t(emptyKey)}</td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(rowFn).join('');
}

// ---------------------------------------------------------------------------
// C9 — Pagination factory
// ---------------------------------------------------------------------------
// Creates a paginator for a table. `ids` maps logical roles to element IDs;
// `onPage(pageRows)` is called with the current page slice on every render.
// Returns { render(allRows), reset(), getRows() }.
//
// Usage:
//   const _myPag = _makePaginator(
//     { container:'myPagination', prev:'myPrevBtn', next:'myNextBtn',
//       pageSize:'myPageSize', label:'myPageLabel' },
//     rows => _renderTable('myBody', rows, { ... })
//   );
//   function _renderMyTable(rows) { _myPag.render(rows); }
//   async function loadMyTable() { _myPag.reset(); await ...; }
// ---------------------------------------------------------------------------
function _makePaginator(ids, onPage) {
  let _page = 0, _pageSize = 25, _rows = [];

  function _updateControls(total) {
    const pg = document.getElementById(ids.container);
    if (!pg) return;
    pg.hidden = total <= 1;
    document.getElementById(ids.label).textContent =
      `${_t('page.label')} ${_page + 1} ${_t('page.of')} ${total}`;
    document.getElementById(ids.prev).disabled  = _page === 0;
    document.getElementById(ids.next).disabled  = _page >= total - 1;
  }

  function render(rows) {
    if (rows !== undefined) _rows = rows;
    const total = Math.max(1, Math.ceil(_rows.length / _pageSize));
    _page = Math.max(0, Math.min(_page, total - 1));
    onPage(_rows.slice(_page * _pageSize, (_page + 1) * _pageSize));
    _updateControls(total);
  }

  document.getElementById(ids.prev)?.addEventListener('click', () => { _page--; render(); });
  document.getElementById(ids.next)?.addEventListener('click', () => { _page++; render(); });
  document.getElementById(ids.pageSize)?.addEventListener('change', e => {
    _pageSize = +e.target.value; _page = 0; render();
  });

  return {
    render,
    reset()    { _page = 0; },
    getRows()  { return _rows; },
  };
}
