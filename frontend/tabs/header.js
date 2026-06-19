/* PMAS — Header / Semaphore module
 * Extracted from app.js — MA-01 refactor
 */

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
function _updateHeaderUser() {
  const el = document.getElementById('headerUserInfo');
  if (!el) return;
  const username = sessionStorage.getItem('username') || _getTokenPayload()?.sub || '';
  el.textContent = username || 'PMAS';
}

async function loadSemaphore() {
  const bar = document.getElementById('semaphoreBar');
  if (!bar) return;
  try {
    const data = await apiFetch('/api/v2/portfolio');
    if (!data.length) {
      bar.style.display = 'none';
      const hdr = document.getElementById('headerSemaphore');
      if (hdr) hdr.style.display = 'none';
      return;
    }

    // v2 returns health_hours and health_cost already classified by the server
    const _semClass = p => _healthToSemColor(p.health_hours || 'no_budget', p.health_cost || 'no_budget');

    const wPct = Math.round(_budgetWarning  * 100);
    const cPct = Math.round(_budgetCritical * 100);

    const counts = { green: 0, yellow: 0, red: 0, grey: 0 };
    const pills  = data.map(p => {
      const s = _semClass(p);
      counts[s]++;
      const pH = p.budget_hours ? (p.total_hours / p.budget_hours * 100).toFixed(0) + '% h' : '— h';
      const pC = p.budget_cost  ? (p.total_cost  / p.budget_cost  * 100).toFixed(0) + '% ' + _currencySymbol: '— ' + _currencySymbol;
      const tip = `${p.pep_wbs}: ${pH} · ${pC} — clique para detalhar`;
      return `<span class="sem-project ${s}" data-pep="${escHtml(p.pep_wbs)}" title="${escHtml(tip)}">${escHtml(p.pep_wbs)}</span>`;
    });

    const dot = (cls, label) => counts[cls]
      ? `<span class="sem-count" title="${label}"><span class="sem-dot ${cls}"></span>${counts[cls]}</span>`
      : '';

    const summaryHtml =
      `<span class="sem-title">${_t('sem.portfolio')}</span>
      ${dot('green',  _t('sem.ok_label').replace('{pct}', wPct))}
      ${dot('yellow', _t('sem.warning_label').replace('{pct}', wPct))}
      ${dot('red',    _t('sem.overrun_label').replace('{pct}', cPct))}
      ${dot('grey',   _t('sem.no_budget'))}`;

    bar.innerHTML =
      `<div class="sem-summary">${summaryHtml}</div>
      <div class="sem-divider"></div>
      <div class="sem-projects">${pills.join('')}</div>`;
    bar.style.display = 'flex';

    const hdr = document.getElementById('headerSemaphore');
    if (hdr) { hdr.innerHTML = summaryHtml; hdr.style.display = 'flex'; }
  } catch (_) {
    bar.style.display = 'none';
    const hdr = document.getElementById('headerSemaphore');
    if (hdr) hdr.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Semaphore drill-down: click a pill → filter Portfolio tab by that PEP
// ---------------------------------------------------------------------------
document.getElementById('semaphoreBar').addEventListener('click', e => {
  const pill = e.target.closest('[data-pep]');
  if (pill) _drillDownToPep(pill.dataset.pep);
});

async function _drillDownToPep(pepCode) {
  // Navigate to Dashboard tab
  document.querySelector('.tab-btn[data-tab="dashboard"]')?.click();

  // Reset all filters so we fetch the full PEP list, then pin to target PEP
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  await refreshPeps();
  if (!pepMs.items.some(i => String(i.value) === String(pepCode))) {
    notify(_t('msg.pep_not_available'), 'warning');
    return;
  }
  pepMs.selectOnly(pepCode);
  refreshPepDescriptions();

  // Switch to portfolio sub-tab programmatically and render
  _disposeTabCharts(_activeATab);
  document.querySelectorAll('.atab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.atab-section').forEach(s => { s.hidden = true; });
  const portfolioBtn = document.querySelector('.atab-btn[data-atab="portfolio"]');
  if (portfolioBtn) portfolioBtn.classList.add('active');
  _activeATab = 'portfolio';
  document.getElementById('atab-portfolio').hidden = false;

  await _renderPortfolioTab();
  document.getElementById('runwayPanel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------------------------------------------------------------------------
// Tab badges — pending quarantine indicators
// ---------------------------------------------------------------------------
async function _refreshTabBadges() {
  // Admin badge — pending quarantine records (admin only)
  if (_isAdmin()) {
    try {
      const rows = await apiFetch('/api/quarantine?review_status=pending');
      const badge = document.getElementById('adminTabBadge');
      if (badge) {
        const n = rows.length;
        if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
        else badge.setAttribute('hidden', '');
      }
    } catch (_) {}
  }
  // Minha Área badge — user's own pending quarantine records
  try {
    const rows = await apiFetch('/api/my/quarantine');
    const pending = rows.filter(r => r.review_status === 'pending');
    const badge = document.getElementById('myTabBadge');
    if (badge) {
      const n = pending.length;
      if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
      else badge.setAttribute('hidden', '');
    }
  } catch (_) {}
}

async function _initNotifications() {
  const btn = document.getElementById('notifBtn');
  const badge = document.getElementById('notifBadge');
  if (!btn) return;

  let panel = null;
  let open = false;

  async function _fetchNotifs() {
    try {
      const r = await fetch('/api/my/notifications/', { headers: _authHeaders() });
      if (!r.ok) return;
      const data = await r.json();
      const unread = data.filter(n => !n.is_read).length;
      if (unread > 0) {
        badge.textContent = unread;
        badge.style.display = '';
      } else {
        badge.style.display = 'none';
      }
      return data;
    } catch { return []; }
  }

  function _renderPanel(notifs) {
    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'notif-panel';
      btn.parentElement.appendChild(panel);
    }
    if (!notifs || notifs.length === 0) {
      panel.innerHTML = `<p style="padding:1rem;text-align:center;color:var(--text-2)">${_t('notif.empty')}</p>`;
      return;
    }
    const markAll = `<button class="btn btn-ghost btn-xs" id="notifMarkAll" style="margin:0.5rem 1rem">${_t('notif.mark_all_read')}</button>`;
    panel.innerHTML = markAll + notifs.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
        <div style="flex:1">
          <div class="notif-msg">${escHtml(n.message)}</div>
          <div class="notif-time">${fmtDateBR(n.created_at?.slice(0,10))}</div>
        </div>
        <button class="btn btn-ghost btn-xs notif-del" data-id="${n.id}" aria-label="${_t('notif.delete')}" title="${_t('notif.delete')}">✕</button>
      </div>`).join('');
    panel.querySelector('#notifMarkAll')?.addEventListener('click', async () => {
      await fetch('/api/my/notifications/read-all', { method: 'POST', headers: _authHeaders() });
      const d = await _fetchNotifs();
      _renderPanel(d);
    });
    panel.querySelectorAll('.notif-del').forEach(b => {
      b.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        await fetch(`/api/my/notifications/${id}`, { method: 'DELETE', headers: _authHeaders() });
        const d = await _fetchNotifs();
        _renderPanel(d);
      });
    });
    panel.querySelectorAll('.notif-item').forEach(item => {
      item.addEventListener('click', async (e) => {
        if (e.target.classList.contains('notif-del')) return;
        const id = item.dataset.id;
        await fetch(`/api/my/notifications/${id}/read`, { method: 'POST', headers: _authHeaders() });
        item.classList.remove('unread');
        await _fetchNotifs();
      });
    });
  }

  btn.addEventListener('click', async () => {
    open = !open;
    if (open) {
      const d = await _fetchNotifs();
      _renderPanel(d);
      panel.style.display = '';
    } else {
      if (panel) panel.style.display = 'none';
    }
  });

  document.addEventListener('click', (e) => {
    if (open && panel && !btn.contains(e.target) && !panel.contains(e.target)) {
      open = false;
      panel.style.display = 'none';
    }
  });

  // Poll every 60 seconds
  _fetchNotifs();
  setInterval(_fetchNotifs, 60000);
}
