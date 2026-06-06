/* PMAS — Projects CRUD (including Baseline Modal, ACL, Budget History)
 * Depends on globals defined in app.js:
 *   _makePaginator, _renderTable, _isAdmin, _applySort, _loadTable
 *   apiFetch, apiFetchJSON, _authHeaders
 *   _t, _locale, _cssVar, escHtml, fmt, fmtDateBR, _fmtCost
 *   notify, _friendlyError, openModal, closeModal, confirmDialog
 *   _budgetWarning, _planProjectId, _renderPlanTable, _chartDefaults
 *   echarts, _currencySymbol
 * Must be loaded AFTER app.js in index.html.
 */

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId  = null;
let _allProjects    = [];
let _consumedByPep  = {};

let _baselineByProject = {};   // project_id → active ProjectBaselineOut | null

const _projectsPag = _makePaginator(
  { container: 'projectsPagination', prev: 'projectsPrevBtn', next: 'projectsNextBtn', pageSize: 'projectsPageSize', label: 'projectsPageLabel', entity: 'projects.title' },
  rows => _renderTable('projectsBody', rows, {
    colspan: 8,
    emptyKey: 'no_projects',
    rowFn: p => {
      const bl = _baselineByProject[p.id];
      const blBadge = bl
        ? `<span class="badge-baseline active" title="${_t('baseline.locked_at')} ${_fmtDateShort(bl.locked_at)} ${_t('baseline.locked_by')} ${escHtml(bl.locked_by || '?')}${bl.label ? ' — ' + escHtml(bl.label) : ''}">${_t('baseline.badge')}</span>`
        : '';
      return `
    <tr>
      <td><code>${escHtml(p.pep_wbs)}</code></td>
      <td>${escHtml(p.name || '—')}</td>
      <td>${escHtml(p.client || '—')}</td>
      <td>${escHtml(p.manager || '—')}</td>
      <td style="text-align:right">${_buildBudgetCell(p)} ${blBadge}</td>
      <td>${_buildDatesCell(p)}</td>
      <td><span class="badge-status ${p.status}">${p.status}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">${_t('btn.edit')}</button>
        <button class="btn btn-primary btn-sm" onclick="selectProjectPlan(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))}, ${escHtml(JSON.stringify(p.name || p.pep_wbs))})">${_t('plan.btn.open')}</button>
        <div class="row-actions-wrap">
          <button class="btn btn-secondary btn-sm row-actions-trigger" title="${_t('btn.more_actions')}" aria-label="${_t('btn.more_actions')}" aria-haspopup="menu" aria-expanded="false">⋮</button>
          <div class="row-actions-menu" role="menu">
            <button class="row-actions-item" role="menuitem" onclick="_openBudgetHistory(${p.id}, ${escHtml(JSON.stringify(p.name || p.pep_wbs))})">${_t('budget.history.btn')}</button>
            <button class="row-actions-item" role="menuitem" onclick="_openBaselineModal(${p.id})">📍 ${_t('baseline.title')}</button>
            ${_isAdmin() ? `<button class="row-actions-item" role="menuitem" onclick="_openAclModal(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">🔑 ${_t('acl.title')}</button>` : ''}
            <div class="row-actions-sep"></div>
            <button class="row-actions-item danger" role="menuitem" onclick="deleteProject(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">${_t('btn.delete')}</button>
          </div>
        </div>
      </div></td>
    </tr>`;
    },
  })
);

async function loadProjectsTable() {
  _projectsPag.reset();
  try {
    const [projects, health, summaryStatus] = await Promise.all([
      apiFetch('/api/projects'),
      apiFetch('/api/v2/portfolio').catch(() => []),
      _isAdmin() ? apiFetch('/api/summaries/status').catch(() => null) : Promise.resolve(null),
    ]);
    _allProjects   = projects;
    _consumedByPep = Object.fromEntries(health.map(h => [h.pep_wbs, { hours: h.total_hours, health: h.health_hours }]));

    // Fetch active baselines for all projects in parallel (best-effort)
    const blResults = await Promise.allSettled(
      projects.map(p => apiFetch(`/api/projects/${p.id}/baselines`))
    );
    _baselineByProject = {};
    blResults.forEach((r, i) => {
      if (r.status === 'fulfilled' && Array.isArray(r.value)) {
        const active = r.value.find(b => b.is_active);
        _baselineByProject[projects[i].id] = active || null;
      }
    });

    _renderProjectsTable(_applySort('projectsTable', projects));
    _renderProjectStats();
    _renderSummaryStaleWarning(summaryStatus);
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

function _renderSummaryStaleWarning(status) {
  const el = document.getElementById('summaryStaleWarning');
  if (!el) return;
  if (status?.stale) {
    el.textContent = '⚠ ' + _t('summaries.stale');
    el.hidden = false;
  } else {
    el.hidden = true;
  }
}

function _renderProjectStats() {
  const el = document.getElementById('projectsStats');
  if (!el || !_allProjects.length) { if (el) el.hidden = true; return; }

  const counts = { ativo: 0, suspenso: 0, encerrado: 0 };
  let totalBudgetH = 0, withBaseline = 0, atRisk = 0;

  _allProjects.forEach(p => {
    counts[p.status] = (counts[p.status] || 0) + 1;
    if (p.budget_hours) totalBudgetH += p.budget_hours;
    if (_baselineByProject[p.id]) withBaseline++;
    const h = _consumedByPep[p.pep_wbs]?.health;
    if (h === 'warning' || h === 'overrun') atRisk++;
  });

  const total = _allProjects.length;
  const budgetStr = totalBudgetH > 0 ? fmt(totalBudgetH) : '—';
  const riskHtml = atRisk > 0
    ? `<div class="stat-sep"></div>
       <div class="stat-item">
         <span class="stat-value" style="color:var(--amber)">${atRisk}</span>
         <span class="stat-label">${_t('stats.at_risk')}</span>
       </div>`
    : '';

  el.innerHTML = `
    <div class="stat-item">
      <span class="stat-value">${total}</span>
      <span class="stat-label">${_t('stats.projects')}</span>
    </div>
    <div class="stat-sep"></div>
    <div class="stat-item">
      <span class="stat-value"><span class="stat-dot ativo"></span>${counts.ativo || 0}</span>
      <span class="stat-label">${_t('opt.ativo')}</span>
    </div>
    <div class="stat-item">
      <span class="stat-value"><span class="stat-dot suspenso"></span>${counts.suspenso || 0}</span>
      <span class="stat-label">${_t('opt.suspenso')}</span>
    </div>
    <div class="stat-item">
      <span class="stat-value"><span class="stat-dot encerrado"></span>${counts.encerrado || 0}</span>
      <span class="stat-label">${_t('opt.encerrado')}</span>
    </div>
    <div class="stat-sep"></div>
    <div class="stat-item">
      <span class="stat-value">${budgetStr}</span>
      <span class="stat-label">${_t('stats.budget_h')}</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${withBaseline}/${total}</span>
      <span class="stat-label">${_t('stats.with_baseline')}</span>
    </div>
    ${riskHtml}
  `;
  el.hidden = false;
}

function _buildBudgetCell(p) {
  if (p.budget_hours == null) return '—';
  const entry = _consumedByPep[p.pep_wbs];
  const budgetStr = fmt(p.budget_hours);
  if (!entry) return budgetStr;
  const { hours: consumed, health } = entry;
  const wPct = Math.round(_budgetWarning * 100);
  if (health === 'overrun' || health === 'critical') return `${budgetStr}<span class="badge-budget critical" title="${consumed.toFixed(1)}h consumidas">${_t('budget.exceeded')}</span>`;
  if (health === 'warning') return `${budgetStr}<span class="badge-budget warning" title="${consumed.toFixed(1)}h consumidas">${_t('budget.warning')} ≥${wPct}%</span>`;
  return budgetStr;
}

function _buildDatesCell(p) {
  const parts = [];
  if (p.start_date)       parts.push(`▸ ${fmtDateBR(p.start_date)}`);
  if (p.planned_end_date) parts.push(`→ ${fmtDateBR(p.planned_end_date)}`);
  if (p.completion_date)  parts.push(`✓ ${fmtDateBR(p.completion_date)}`);
  return parts.length ? `<span style="font-size:.8rem;color:${_cssVar('--text-3')}">${parts.join(' ')}</span>` : '—';
}

function _renderProjectsTable(projects) { _projectsPag.render(projects); }

function selectProjectPlan(projectId, pepWbs, projectName) {
  _planProjectId = projectId;
  const nameEl = document.getElementById('planProjectName');
  if (nameEl) nameEl.textContent = projectName;
  _renderPlanTable();
  openModal('planModal', document.activeElement);
}

function _closeProjectPlan() {
  _planProjectId = null;
  closeModal('planModal');
}

document.getElementById('planModalClose').addEventListener('click', _closeProjectPlan);

// ── F7: Budget Revision History ───────────────────────────────────────────────

let _budgetHistChart = null;

async function _openBudgetHistory(projectId, projectName) {
  document.getElementById('budgetHistoryTitle').textContent =
    `${_t('budget.history.title')} — ${projectName}`;
  document.getElementById('budgetHistoryBody').innerHTML =
    `<tr><td colspan="5" class="td-empty">${_t('loading')}</td></tr>`;
  const sparkEl = document.getElementById('budgetSparkline');
  if (sparkEl) { sparkEl.hidden = true; }
  openModal('budgetHistoryModal');
  try {
    const rows = await apiFetch(`/api/projects/${projectId}/budget-history`);
    if (!rows.length) {
      document.getElementById('budgetHistoryBody').innerHTML =
        `<tr><td colspan="5" class="td-empty">${_t('budget.history.empty')}</td></tr>`;
      return;
    }
    document.getElementById('budgetHistoryBody').innerHTML = rows.map(r => `
      <tr>
        <td>${fmtDateBR(r.changed_at?.split('T')[0]) || '—'}</td>
        <td>${escHtml(r.changed_by)}</td>
        <td class="text-right">${r.old_budget_hours != null ? r.old_budget_hours.toFixed(1) + 'h' : '—'}
          → ${r.new_budget_hours != null ? r.new_budget_hours.toFixed(1) + 'h' : '—'}</td>
        <td class="text-right">${r.old_budget_cost != null ? _fmtCost(r.old_budget_cost) : '—'}
          → ${r.new_budget_cost != null ? _fmtCost(r.new_budget_cost) : '—'}</td>
        <td>${escHtml(r.reason || '—')}</td>
      </tr>`).join('');

    // Sparkline — chronological order (rows arrive newest-first)
    if (sparkEl && rows.length >= 2) {
      const sorted = [...rows].reverse();
      const dates  = sorted.map(r => r.changed_at?.split('T')[0] || '');
      const bHours = sorted.map(r => r.new_budget_hours ?? null);
      const bCosts = sorted.map(r => r.new_budget_cost  ?? null);
      if (_budgetHistChart) { _budgetHistChart.dispose(); _budgetHistChart = null; }
      _budgetHistChart = echarts.init(sparkEl, 'pmas', { renderer: 'svg' });
      _budgetHistChart.setOption({
        backgroundColor: 'transparent',
        grid: { top: 28, right: 12, bottom: 24, left: 8, containLabel: true },
        legend: {
          data: [_t('budget.history.sparkline.hours'), _t('budget.history.sparkline.cost')],
          top: 2, left: 'center',
          textStyle: { color: _cssVar('--text'), fontSize: 10 },
          itemGap: 16, itemWidth: 12, itemHeight: 8,
        },
        xAxis: { type: 'category', data: dates,
          axisLabel: { color: _cssVar('--text-3'), fontSize: 9 },
          axisTick: { show: false },
        },
        yAxis: [
          { type: 'value', name: 'h', nameTextStyle: { color: _cssVar('--text-3'), fontSize: 9 },
            axisLabel: { color: _cssVar('--text-3'), fontSize: 9, formatter: v => `${v}h` },
            splitLine: { lineStyle: { color: _cssVar('--surface') } } },
          { type: 'value', name: _currencySymbol, nameTextStyle: { color: _cssVar('--text-3'), fontSize: 9 },
            axisLabel: { color: _cssVar('--text-3'), fontSize: 9, formatter: v => `${(v/1000).toFixed(0)}k` },
            splitLine: { show: false } },
        ],
        tooltip: { trigger: 'axis', ...(_chartDefaults().tooltip) },
        series: [
          { name: _t('budget.history.sparkline.hours'), type: 'line', yAxisIndex: 0,
            data: bHours, itemStyle: { color: _cssVar('--primary') },
            lineStyle: { width: 2 }, symbol: 'circle', symbolSize: 5 },
          { name: _t('budget.history.sparkline.cost'), type: 'line', yAxisIndex: 1,
            data: bCosts, itemStyle: { color: _cssVar('--amber') },
            lineStyle: { width: 2 }, symbol: 'circle', symbolSize: 5 },
        ],
      });
      sparkEl.hidden = false;
    }
  } catch (e) {
    document.getElementById('budgetHistoryBody').innerHTML =
      `<tr><td colspan="5" class="td-empty">${_t('msg.err_generic')}</td></tr>`;
  }
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectModalTitle').textContent = id ? _t('pm.title_edit') : _t('pm.title_new');
  document.getElementById('projectError').textContent = '';
  if (id) {
    const p = _allProjects.find(x => x.id === id);
    if (p) {
      document.getElementById('projectPepInput').value         = p.pep_wbs;
      document.getElementById('projectNameInput').value        = p.name    || '';
      document.getElementById('projectClientInput').value      = p.client  || '';
      document.getElementById('projectManagerInput').value     = p.manager || '';
      document.getElementById('projectBudgetInput').value         = p.budget_hours ?? '';
      document.getElementById('projectBudgetCostInput').value      = p.budget_cost ?? '';
      document.getElementById('projectStatusInput').value          = p.status;
      document.getElementById('projectStartInput').value           = p.start_date       || '';
      document.getElementById('projectPlannedEndInput').value      = p.planned_end_date || '';
      document.getElementById('projectCompletionInput').value      = p.completion_date  || '';
    }
  } else {
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput',
     'projectBudgetInput','projectBudgetCostInput',
     'projectStartInput','projectPlannedEndInput','projectCompletionInput']
      .forEach(fid => { document.getElementById(fid).value = ''; });
    document.getElementById('projectStatusInput').value = 'ativo';
  }
  // show budget reason field only when editing (budget change may occur)
  document.getElementById('budgetReasonGroup').hidden = !id;
  document.getElementById('projectBudgetReasonInput').value = '';
  openModal('projectModal');
}

function closeProjectModal() { closeModal('projectModal'); }

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep = document.getElementById('projectPepInput').value.trim();
  if (!pep) { document.getElementById('projectError').textContent = _t('msg.pep_required'); return; }
  const completionDate = document.getElementById('projectCompletionInput').value || null;
  const statusRaw      = document.getElementById('projectStatusInput').value;

  const _doSave = async (status) => {
    const budget     = document.getElementById('projectBudgetInput').value;
    const budgetCost = document.getElementById('projectBudgetCostInput').value;
    const budgetReason = document.getElementById('projectBudgetReasonInput')?.value.trim() || null;
    const body = {
      pep_wbs:              pep,
      name:                 document.getElementById('projectNameInput').value.trim()    || null,
      client:               document.getElementById('projectClientInput').value.trim()  || null,
      manager:              document.getElementById('projectManagerInput').value.trim() || null,
      budget_hours:         budget     !== '' ? parseFloat(budget)     : null,
      budget_cost:          budgetCost !== '' ? parseFloat(budgetCost) : null,
      status,
      start_date:           document.getElementById('projectStartInput').value       || null,
      planned_end_date:     document.getElementById('projectPlannedEndInput').value  || null,
      completion_date:      completionDate,
      budget_change_reason: budgetReason,
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
  };

  if (completionDate && statusRaw !== 'encerrado') {
    return confirmDialog(_t('confirm.set_encerrado'), () => _doSave('encerrado'), false);
  }
  _doSave(statusRaw);
});

document.getElementById('projectCancelBtn').addEventListener('click', closeProjectModal);
document.getElementById('projectModalClose').addEventListener('click', closeProjectModal);
document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal());

document.getElementById('projectSearch').addEventListener('input', e => {
  _projectsPag.reset();
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allProjects.filter(p =>
    (p.pep_wbs || '').toLowerCase().includes(q) ||
    (p.name    || '').toLowerCase().includes(q) ||
    (p.client  || '').toLowerCase().includes(q)
  ) : _allProjects;
  _renderProjectsTable(_applySort('projectsTable', filtered));
});

function deleteProject(id, pep) {
  confirmDialog(_t('confirm.delete_project'), async () => {
    try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); loadProjectsTable(); }
    catch (e) { notify(_friendlyError(e), 'error'); }
  });
}

// ── Baseline Modal ─────────────────────────────────────────────────────────

function _fmtDateShort(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString(_locale === 'pt' ? 'pt-BR' : 'en-US', { day:'2-digit', month:'2-digit', year:'numeric' });
}

let _baselineModalProjectId = null;

async function _openBaselineModal(projectId) {
  _baselineModalProjectId = projectId;
  const proj = _allProjects.find(p => p.id === projectId);
  const title = proj ? `${_t('baseline.title')} — ${proj.pep_wbs}${proj.name ? ' · ' + proj.name : ''}` : _t('baseline.title');
  document.getElementById('baselineModalTitle').textContent = title;
  document.getElementById('baselineModalBody').innerHTML = `<p style="color:${_cssVar('--text-3')}">Carregando…</p>`;
  openModal('baselineModal');
  await _refreshBaselineModal(projectId);
}

async function _refreshBaselineModal(projectId) {
  try {
    const baselines = await apiFetch(`/api/projects/${projectId}/baselines`);
    const active = baselines.find(b => b.is_active);
    const proj = _allProjects.find(p => p.id === projectId);
    const hasbudget = proj && proj.budget_cost != null;

    let html = '';

    // Active baseline info
    if (active) {
      html += `<div class="baseline-info-box active">
        <strong>📍 ${_t('baseline.active')}</strong>${active.label ? ` — <em>${escHtml(active.label)}</em>` : ''}
        <br><span class="text-dim">${_t('baseline.locked_at')} ${_fmtDateShort(active.locked_at)} ${_t('baseline.locked_by')} ${escHtml(active.locked_by || '?')}</span>
        <br><span class="text-dim">${_t('baseline.budget_h')}: <b>${active.budget_hours != null ? fmt(active.budget_hours) : '—'}</b>
        &nbsp;·&nbsp; ${_t('baseline.budget_cost')}: <b>${active.budget_cost != null ? _fmtCost(active.budget_cost) : '—'}</b></span>
      </div>`;
    } else {
      html += `<div class="baseline-info-box warning">⚠️ ${_t('baseline.none')}</div>`;
    }

    // Create new baseline form
    html += `<div style="margin:1rem 0;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">
      <input type="text" id="baselineLabelInput" class="form-control" style="flex:1;min-width:180px"
             placeholder="${_t('baseline.label_ph')}" />
      <button class="btn btn-primary btn-sm" onclick="_createBaseline(${projectId})"
              ${hasbudget ? '' : 'disabled title="Defina budget_cost no projeto primeiro"'}>
        📍 ${_t('baseline.create')}
      </button>
    </div>`;
    if (!hasbudget) {
      html += `<p class="hint" style="color:var(--amber);margin-top:-.5rem">Defina o orçamento (budget_cost) do projeto para habilitar baseline.</p>`;
    }

    // Diff between two most recent baselines
    if (baselines.length >= 2) {
      const sorted = [...baselines].sort((a, b) => new Date(b.locked_at) - new Date(a.locked_at));
      const newer = sorted[0], older = sorted[1];
      const _diffCell = (n, o) => {
        if (n == null && o == null) return '<td>—</td><td>—</td><td class="text-dim">—</td>';
        const nStr = n != null ? n : '—';
        const oStr = o != null ? o : '—';
        const delta = (n != null && o != null) ? n - o : null;
        const color = delta == null ? '' : delta > 0 ? `color:var(--amber)` : delta < 0 ? `color:var(--green)` : '';
        const sign  = delta > 0 ? '+' : '';
        const dStr  = delta != null ? `${sign}${delta.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US')}` : '—';
        return `<td>${oStr}</td><td>${nStr}</td><td style="${color};font-weight:600">${dStr}</td>`;
      };
      const dH = older.budget_hours != null || newer.budget_hours != null
        ? _diffCell(newer.budget_hours, older.budget_hours) : null;
      const dC = older.budget_cost != null || newer.budget_cost != null
        ? _diffCell(newer.budget_cost, older.budget_cost) : null;
      if (dH || dC) {
        html += `<div class="baseline-diff-box">
          <span style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-3)">${_t('baseline.diff_title')}</span>
          <table class="data-table" style="font-size:.82rem;margin-top:.4rem"><thead><tr>
            <th></th><th>${escHtml(older.label || _fmtDateShort(older.locked_at))}</th>
            <th>${escHtml(newer.label || _fmtDateShort(newer.locked_at))}</th>
            <th>Δ</th>
          </tr></thead><tbody>
          ${dH ? `<tr><td style="color:var(--text-3)">${_t('baseline.budget_h')}</td>${dH}</tr>` : ''}
          ${dC ? `<tr><td style="color:var(--text-3)">${_t('baseline.budget_cost')}</td>${dC}</tr>` : ''}
          </tbody></table>
        </div>`;
      }
    }

    // History table
    html += `<h4 style="margin:.75rem 0 .4rem;font-size:.875rem">${_t('baseline.history')}</h4>`;
    if (!baselines.length) {
      html += `<p class="text-dim" style="font-size:.85rem">${_t('baseline.no_history')}</p>`;
    } else {
      html += `<table class="data-table" style="font-size:.82rem"><thead><tr>
        <th>${_t('baseline.locked_at')}</th><th>${_t('baseline.locked_by')}</th>
        <th>${_t('baseline.budget_h')}</th><th>${_t('baseline.budget_cost')}</th>
        <th>Rótulo</th><th></th>
      </tr></thead><tbody>`;
      baselines.forEach(b => {
        html += `<tr style="${b.is_active ? 'background:rgba(79,142,247,.08)' : ''}">
          <td>${_fmtDateShort(b.locked_at)}</td>
          <td>${escHtml(b.locked_by || '—')}</td>
          <td>${b.budget_hours != null ? fmt(b.budget_hours) : '—'}</td>
          <td>${b.budget_cost != null ? _fmtCost(b.budget_cost) : '—'}</td>
          <td>${escHtml(b.label || '—')}</td>
          <td><div class="actions" style="gap:.25rem">
            ${!b.is_active ? `<button class="btn btn-secondary btn-sm" onclick="_activateBaseline(${projectId},${b.id})">${_t('baseline.activate')}</button>` : '<span class="badge-baseline active" style="font-size:.75rem">ativo</span>'}
            ${_isAdmin() ? `<button class="btn btn-danger btn-sm" onclick="_deleteBaseline(${projectId},${b.id})">✕</button>` : ''}
          </div></td>
        </tr>`;
      });
      html += '</tbody></table>';
    }

    document.getElementById('baselineModalBody').innerHTML = html;
  } catch(e) {
    document.getElementById('baselineModalBody').innerHTML = `<p style="color:var(--red)">Erro: ${e.message}</p>`;
  }
}

async function _createBaseline(projectId) {
  const label = document.getElementById('baselineLabelInput')?.value.trim() || null;
  try {
    await apiFetchJSON(`/api/projects/${projectId}/baseline`, 'POST', { label });
    notify(_t('baseline.created'), 'success');
    await _refreshBaselineModal(projectId);
    loadProjectsTable();
  } catch(e) { notify(_friendlyError(e), 'error'); }
}

async function _activateBaseline(projectId, baselineId) {
  try {
    await apiFetchJSON(`/api/projects/${projectId}/baselines/${baselineId}/activate`, 'POST', {});
    await _refreshBaselineModal(projectId);
    loadProjectsTable();
  } catch(e) { notify(_friendlyError(e), 'error'); }
}

async function _deleteBaseline(projectId, baselineId) {
  confirmDialog(_t('confirm.remove_baseline') || 'Remover este baseline?', async () => {
    try {
      await apiFetchJSON(`/api/projects/${projectId}/baselines/${baselineId}`, 'DELETE');
      notify(_t('baseline.deleted'), 'success');
      await _refreshBaselineModal(projectId);
      loadProjectsTable();
    } catch(e) { notify(_friendlyError(e), 'error'); }
  });
}

document.getElementById('baselineModalClose').addEventListener('click', () => closeModal('baselineModal'));

// ---------------------------------------------------------------------------
// ACL de projetos — controle de acesso por PEP
// ---------------------------------------------------------------------------
let _aclProjectId = null;

async function _openAclModal(projectId, pepWbs) {
  _aclProjectId = projectId;
  document.getElementById('aclModalTitle').textContent = _t('msg.acl_title') + pepWbs;
  document.getElementById('aclError').textContent = '';
  openModal('aclModal');
  await Promise.all([_loadAclEntries(), _populateAclUserSelect()]);
}

async function _loadAclEntries() {
  const tbody = document.getElementById('aclEntriesBody');
  tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:${_cssVar('--text-3')};padding:.75rem">${_t('loading')}</td></tr>`;
  try {
    const entries = await apiFetch(`/api/projects/${_aclProjectId}/access`);
    if (!entries.length) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:${_cssVar('--text-3')};padding:.75rem">${_t('msg.no_access_granted')}</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(e => `
      <tr>
        <td>${escHtml(e.username)}</td>
        <td style="text-align:right">
          <button class="btn btn-danger btn-sm" onclick="_revokeAccess(${e.user_id})">${_t('btn.revoke')}</button>
        </td>
      </tr>`).join('');
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

async function _populateAclUserSelect() {
  const sel = document.getElementById('aclUserSelect');
  try {
    const users = await apiFetch('/api/users');
    sel.innerHTML = `<option value="">${_t('ms.select_ph')}</option>` +
      users.filter(u => u.role !== 'admin').map(u =>
        `<option value="${u.id}">${escHtml(u.username)}</option>`
      ).join('');
  } catch (_) {}
}

document.getElementById('aclGrantBtn')?.addEventListener('click', async () => {
  const sel = document.getElementById('aclUserSelect');
  const userId = parseInt(sel.value);
  const errEl  = document.getElementById('aclError');
  if (!userId) { errEl.textContent = _t('msg.select_user'); return; }
  errEl.textContent = '';
  try {
    await apiFetchJSON(`/api/projects/${_aclProjectId}/access`, 'POST', { user_id: userId });
    sel.value = '';
    await _loadAclEntries();
  } catch (e) { errEl.textContent = e.message; }
});

function _revokeAccess(userId) {
  confirmDialog(_t('confirm.revoke_access'), async () => {
    try {
      await apiFetchJSON(`/api/projects/${_aclProjectId}/access/${userId}`, 'DELETE');
      await _loadAclEntries();
    } catch (e) { notify(_friendlyError(e), 'error'); }
  });
}

document.getElementById('aclModalClose')?.addEventListener('click', () => { closeModal('aclModal'); });
document.getElementById('aclModalCloseBtn')?.addEventListener('click', () => { closeModal('aclModal'); });

document.getElementById('exportProjectsBtn').addEventListener('click', () => {
  if (!_allProjects.length) { notify(_t('msg.no_projects_export'), 'info'); return; }
  const header = 'pep_wbs,name,client,manager,budget_hours,budget_cost,status,start_date,planned_end_date,completion_date';
  const esc = v => (v == null ? '' : `"${String(v).replace(/"/g, '""')}"`);
  const rows = _allProjects.map(p =>
    `${esc(p.pep_wbs)},${esc(p.name)},${esc(p.client)},${esc(p.manager)},${p.budget_hours ?? ''},${p.budget_cost ?? ''},${p.status},${p.start_date ?? ''},${p.planned_end_date ?? ''},${p.completion_date ?? ''}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'projetos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importProjectsInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}, ${data.updated} ${_t('msg.updated_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadProjectsTable();
  } catch (err) { notify(_friendlyError(err), 'error'); }
  e.target.value = '';
});
