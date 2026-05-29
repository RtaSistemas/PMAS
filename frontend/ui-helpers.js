/* PMAS — Global UI Helpers */

// ---------------------------------------------------------------------------
// EVM color maps (shared between chart builders and stat cards)
// ---------------------------------------------------------------------------

// Backend EVM color → CSS variable name (for charts and table cells)
const _EVM_COLOR_CSS = {
  success: 'var(--primary,#4f8ef7)',
  warning: 'var(--amber,#d9b273)',
  danger:  'var(--red,#c56d76)',
};

// Backend EVM color → stat-card CSS class
const _EVM_COLOR_CARD = { success: 'green', warning: 'amber', danger: 'red' };

// Health-color → CSS variable name (used in Treemap and Bullet chart)
const _HCSS = { success: '--primary', warning: '--amber', danger: '--red', muted: '--text-3' };

// ---------------------------------------------------------------------------
// C1 — Stat card builder
// ---------------------------------------------------------------------------
function _mkStatCard({ val, lbl, cls, evm, sublbl }) {
  const lblHtml = evm
    ? `<span data-evm="${evm}">${escHtml(lbl)}</span>`
    : escHtml(lbl);
  const sublblHtml = sublbl ? `<div class="sublbl">${escHtml(sublbl)}</div>` : '';
  return `<div class="stat-card ${cls}"><div class="val">${val}</div><div class="lbl">${lblHtml}</div>${sublblHtml}</div>`;
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
async function _confirmDelete(entityName, asyncFn) {
  if (!confirm(`Excluir ${entityName}? Esta ação não pode ser desfeita.`)) return;
  return asyncFn();
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
