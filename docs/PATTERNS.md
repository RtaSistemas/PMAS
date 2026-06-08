# PMAS — Implementation Patterns Guide

> This document codifies every pattern established during the project's development.  
> **All new features, bugfixes, and refactors must follow these patterns.**  
> The Golden Rules section is non-negotiable; violations are architectural defects.

---

## Table of Contents

1. [Golden Rules (non-negotiable)](#1-golden-rules)
2. [Backend Patterns](#2-backend-patterns)
3. [EVM Formulas Pattern](#3-evm-formulas-pattern)
4. [Frontend Structure](#4-frontend-structure)
5. [CSS / Design Tokens](#5-css--design-tokens)
6. [Chart Patterns (ECharts)](#6-chart-patterns-echarts)
7. [Modal Pattern](#7-modal-pattern)
8. [Pagination Pattern](#8-pagination-pattern)
9. [CRUD Pattern](#9-crud-pattern)
10. [i18n Pattern](#10-i18n-pattern)
11. [Accessibility Patterns (WCAG 2.2)](#11-accessibility-patterns)
12. [Notification Pattern](#12-notification-pattern)
13. [Error Handling Pattern](#13-error-handling-pattern)
14. [Testing Patterns](#14-testing-patterns)

---

## 1. Golden Rules

These rules are non-negotiable. A PR that violates them must be rejected.

### GR-1 — Data entry via ingestion only

The only pathway for timesheet data into PMAS is `POST /api/upload-timesheet → ingest_file()`.

**Forbidden:**
```python
# ❌ Never create individual rows manually
@router.post("/api/timesheet-records")
def create_record(data: TimesheetIn, db: DbSession): ...

# ❌ Never patch individual rows
@router.patch("/api/timesheet-records/{id}")
def update_record(...): ...
```

**Allowed:**
```python
# ✅ Only the quarantine workflow may mutate existing rows
@router.post("/api/quarantine/{id}/approve")
def approve_quarantine_record(...): ...
```

### GR-2 — EVM formulas live exclusively in `services/evm.py`

No router, frontend script, or test may reimplement an EVM formula.

**Forbidden:**
```python
# ❌ Inline CPI calculation in a router
cpi = ev / actual_cost  # VIOLATION

# ❌ Inline SPI in frontend
const spi = ev / pv;  // VIOLATION
```

**Required:**
```python
# ✅ Always import from evm.py
from backend.app.services.evm import compute_cpi_ev, compute_spi

cpi = compute_cpi_ev(consumed_hours, budget_hours, budget_cost, actual_cost)
spi = compute_spi(planned_hours_cumul, actual_hours_cumul)
```

All v2 responses are **render-ready**: EVM values (CPI, SPI, colors, labels) are computed server-side. The frontend receives final values and renders them — it never does EVM math.

### GR-3 — Chart series colors must use `_getPalette()` or `_cssVar()`

**Forbidden:**
```javascript
// ❌ Hardcoded hex in chart options
series: [{ color: '#3b82f6', ... }]
```

**Required:**
```javascript
// ✅ Palette colors for data series
const palette = _getPalette();
series: [{ color: palette[0], ... }]

// ✅ CSS vars for semantic/status colors
const critColor = _cssVar('--red');
markLine: { lineStyle: { color: critColor } }
```

### GR-4 — No external font CDN

The app must function without internet access.

**Forbidden:**
```html
<!-- ❌ External font dependency -->
<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet">
```

**Required:**
```css
/* ✅ System font stack in style.css :root */
--font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
```

### GR-5 — Mobile chart layout

ECharts containers must be responsive.

```css
/* ✅ Required breakpoints in style.css */
@media (max-width: 768px) {
  [id$="Chart"] { height: 260px !important; min-height: 200px; }
}
@media (max-width: 480px) {
  [id$="Chart"] { height: 200px !important; min-height: 160px; }
}
```

---

## 2. Backend Patterns

### Router structure

Every router follows this template:

```python
from fastapi import APIRouter, Depends, Query
from backend.app.database import DbSession
from backend.app.deps import get_current_user

router = APIRouter(prefix="/api/v2", tags=["v2"])

@router.get("/my-endpoint", summary="Short description", response_model=list)
def get_my_endpoint(
    db: DbSession,
    current_user=Depends(get_current_user),
    # Filters always use List[X] = Query(default=[])
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    ...
```

### ACL enforcement

All analytics endpoints must enforce per-user PEP ACL:

```python
from backend.app.routers.v2.portfolio import _allowed_peps

allowed = _allowed_peps(db, current_user)
if allowed is not None:
    if pep_wbs:
        pep_wbs = [p for p in pep_wbs if p in allowed]
    else:
        pep_wbs = allowed
```

### Budget resolution

Always use `resolve_effective_budget` — never read `project.budget_hours` directly:

```python
from backend.app.services.evm import resolve_effective_budget

budget_hours, budget_cost = resolve_effective_budget(proj, active_baseline)
# Returns: active baseline > project fields > (None, None)
```

### Schema migration

New model columns go through `_migrate_columns()` in `database.py`:

```python
_maybe_add_column(inspector, "project", "my_new_column", "TEXT")
```

Never use Alembic or destructive migrations — production databases upgrade non-destructively on startup.

### Render-ready responses

v2 endpoints return pre-computed display values:

```python
# ✅ Correct: compute server-side
result.append({
    "cpi": cpi,
    "cpi_color": cpi_color(cpi),      # "green" / "amber" / "red"
    "risk": classify_health(consumed, budget, warn_t, crit_t),
    "budget_cost": round(budget_cost, 2) if budget_cost else None,
})
```

### Guard against division by zero

Every EVM function in `evm.py` returns `None` on invalid inputs. Callers must handle `None`:

```python
cpi = compute_cpi_ev(...)
# cpi may be None if budget_hours is None or 0
display_cpi = f"{cpi:.2f}" if cpi is not None else "—"
```

### Shared Python helpers

```python
# ✅ Shared Python helpers — backend/app/utils.py
from backend.app.utils import _str_or_none, now_br

# _str_or_none: returns None for blank/"nan"/"none" strings — used in CSV import parsers
```

---

## 3. EVM Formulas Pattern

All formulas live in `backend/app/services/evm.py`. Reference:

| Function | Inputs | Returns | Notes |
|----------|--------|---------|-------|
| `compute_cpi(ev_cost, ac)` | pre-computed EV in R$, actual_cost | `float\|None` | Use when EV is already computed; see `compute_cpi_ev` when you only have hours |
| `compute_cpi_ev(h, bh, bc, ac)` | consumed_h, budget_h, budget_cost, actual_cost | `float\|None` | Derives EV from hours; use when EV has not been pre-computed |
| `compute_spi(pv, ev)` | planned_h_cumul, actual_h_cumul | `float\|None` |
| `compute_eac(ac, cpi)` | actual_cost, cpi | `float\|None` |
| `compute_eac_schedule(bac, cpi, spi)` | budget_cost, cpi, spi | `float\|None` |
| `compute_tcpi(bac, ev, eac)` | budget_cost, ev, eac | `float\|None` |
| `compute_vac(bac, eac)` | budget_cost, eac | `float\|None` |
| `compute_cv(ev, ac)` | ev in R$, actual_cost | `float\|None` |
| `compute_sv(ev, pv)` | ev in hours, planned_h_cumul | `float\|None` |
| `compute_etc(eac, ac)` | eac, actual_cost | `float\|None` |
| `compute_earned_schedule(...)` | pv_schedule, ev, bac | `float\|None` |
| `resolve_effective_budget(proj, bl)` | Project, ProjectBaseline\|None | `(float\|None, float\|None)` |
| `classify_health(consumed, budget, warn_t, crit_t)` | values + thresholds | `"ok"\|"warning"\|"critical"\|"no_budget"` |
| `freeze_spi_boundary(actual_s, plan_s)` | list of (date,h) pairs | `(float, float)` |

### Velocity window rules (do not standardize without explicit decision)

| Context | Window | Location | Notes |
|---------|--------|----------|-------|
| Forecast | last 3 cycles | `v2/forecast.py` | All cycles in window |
| Runway | last 3 non-zero | `v2/runway.py` | Zero excluded from denominator |
| Simulate | last min(6, N) | `v2/simulate.py` | Smoother base for scenario |
| Monte Carlo | all non-zero | `v2/monte_carlo.py` | Full history for variance |
| Sparkline (frontend) | last 3 non-zero | `app.js` | Aligns with Forecast |

---

## 4. Frontend Structure

```
frontend/
├── index.html          — HTML shell + modal declarations (0 inline style= attributes)
├── app.js              — Core only: globals, auth/fetch/notify, preferences, _bootApp (≤800 lines)
├── style.css           — Design tokens + all CSS rules (+ utility classes from MA-07)
├── utils.js            — Pure utility functions (_fmtH, _fmtCost, _cssVar, _getPalette)
├── ui-helpers.js       — Shared UI: _makePaginator, _confirmDelete, _makeRiskBadge
├── multiselect.js      — Cascading MultiSelect component
├── evm-glossary.js     — EVM tooltip system
├── echarts.min.js      — ECharts local copy (no CDN)
├── charts/
│   ├── effort.js       — Effort tab chart builders
│   ├── portfolio.js    — Portfolio tab chart builders (treemap, bullet, quadrant)
│   └── forecast.js     — Forecast tab chart builders (S-curve, burn-up, MC histogram)
├── crud/
│   ├── cycles.js       — Cycles tab CRUD + _makeSortable for cyclesTable
│   └── projects.js     — Projects tab CRUD (Plan, Baseline, ACL modals) + _makeSortable for projectsTable
├── tabs/
│   ├── dashboard.js    — Dashboard tab: filters, MultiSelects, all render functions (~2969 lines)
│   ├── equipe.js       — Team/Equipe tab: seniority, rate cards, over-alloc + _makeSortable
│   ├── admin.js        — Admin tab: users, audit, validation rules, quarantine, theme editor + _makeSortable
│   ├── minha-area.js   — Minha Área tab: preferences, upload history, quarantine view + _makeSortable
│   └── header.js       — Header: _updateHeaderUser, loadSemaphore, _initNotifications
└── lang/
    ├── pt.js           — pt-BR strings
    └── en.js           — en-US strings
```

### Module loading order in `index.html`

```html
<!-- 1. Utils (no dependencies) -->
<script src="frontend/utils.js"></script>
<!-- 2. Language files -->
<script src="frontend/lang/pt.js"></script>
<script src="frontend/lang/en.js"></script>
<!-- 3. UI helpers (depends on utils + lang) -->
<script src="frontend/ui-helpers.js"></script>
<!-- 4. EVM glossary (depends on utils) -->
<script src="frontend/evm-glossary.js"></script>
<!-- 5. MultiSelect component -->
<script src="multiselect.js"></script>
<!-- 6. Core app: globals, auth/notify, theme, _bootApp -->
<script src="app.js"></script>
<!-- 7. CRUD modules (depend on app.js globals) -->
<script src="frontend/crud/cycles.js"></script>
<script src="frontend/crud/projects.js"></script>
<!-- 8. Chart builders (depend on utils) -->
<script src="frontend/charts/effort.js"></script>
<script src="frontend/charts/portfolio.js"></script>
<script src="frontend/charts/forecast.js"></script>
<!-- 9. Tab modules (depend on app.js + CRUD + charts) -->
<script src="frontend/tabs/dashboard.js"></script>
<script src="frontend/tabs/equipe.js"></script>
<script src="frontend/tabs/admin.js"></script>
<script src="frontend/tabs/minha-area.js"></script>
<script src="frontend/tabs/header.js"></script>
```

> **Cross-file globals:** All scripts run as non-module synchronous `<script>` tags. Top-level `let`/`const` in any file are accessible from files loaded later. Event listener *callbacks* resolve symbols at call time (after all scripts load), so forward references from `app.js` to functions in `tabs/` are safe. The `_makeSortable` call for each table must be in the same file that defines its render function to avoid an undefined-reference bug.

### Global functions available everywhere

These are defined in `utils.js` or `app.js` and usable from any module:

```javascript
// Formatting
_fmtH(n)              // "8.5h" — also: formatHours(n, 0) for zero decimals
_fmtCost(n)           // "R$ 1.234,56" — null-safe; returns '—' for null
_fmtDate(isoStr)      // "15/06/2024, 09:30" — respects _locale + window._timezone
_t(key)               // i18n lookup

// Theming
_cssVar(name)         // getComputedStyle value of CSS custom property
_getPalette()         // Array of 8 palette colors from GlobalConfig

// Modals
openModal(id, triggerEl, focusSelector)
closeModal(id)

// Notifications
notify(msg, type)     // 'info'|'success'|'error'|'warning'

// Auth
_isAdmin()
_authHeaders()        // { Authorization: 'Bearer <token>' }
```

---

## 5. CSS / Design Tokens

### Z-index token system

Every `z-index` must use a token. No literal integers allowed.

```css
/* Defined in style.css :root */
--z-base:          1;    /* In-flow raised elements */
--z-raised:        2;    /* Hover states, cards */
--z-sticky:       90;    /* Sticky headers/nav */
--z-header:      100;    /* Fixed app header */
--z-dropdown:    200;    /* Dropdowns, selects */
--z-overlay:     400;    /* Drawer overlays */
--z-notification:8000;  /* Toast banners */
--z-modal:       9999;  /* Modal backdrops */
--z-tooltip:    10000;  /* Tooltips */
```

Usage:
```css
/* ✅ Correct */
.modal-backdrop { z-index: var(--z-modal); }
.dropdown-menu  { z-index: var(--z-dropdown); }

/* ❌ Forbidden */
.my-element { z-index: 999; }
```

### Color tokens (semantic)

```css
/* Status colors — use for semantic meaning */
_cssVar('--green')    /* success, inserted */
_cssVar('--red')      /* critical, error */
_cssVar('--amber')    /* warning */
_cssVar('--primary')  /* info, selected */
_cssVar('--text-3')   /* secondary text (#7aadcc — WCAG AA compliant) */
```

```javascript
// Data series — use palette index, not semantic colors
const p = _getPalette();
series[0].color = p[0];  // admin-configurable
series[1].color = p[1];
```

### Reduced motion guard

Every CSS animation or transition must be wrapped:

```css
.my-element { transition: opacity 0.2s ease; }

/* Required partner rule */
@media (prefers-reduced-motion: reduce) {
  .my-element { transition: none !important; }
}
```

### Mobile breakpoints for charts

```css
@media (max-width: 768px) {
  [id$="Chart"] { height: 260px !important; min-height: 200px; }
}
@media (max-width: 480px) {
  [id$="Chart"] { height: 200px !important; min-height: 160px; }
}
```

### No inline `style=` attributes in `index.html`

`index.html` must have **zero** `style=` inline attributes. All presentation belongs in `style.css`.

```html
<!-- ❌ Forbidden -->
<div style="display:flex;gap:.5rem;margin-top:.5rem">

<!-- ✅ Correct — use an existing utility class -->
<div class="pagination-bar">

<!-- ✅ Correct — add a CSS rule targeting the element's ID -->
```

**Available utility classes** (all in `style.css`):

| Class | Style |
|-------|-------|
| `.pagination-bar` | `display:flex; align-items:center; justify-content:flex-end; gap:.5rem; margin-top:.5rem` |
| `.pagination-label` | `display:flex; align-items:center; gap:.3rem` |
| `.mb-0`–`.mb-4` | `margin-bottom: 0 / .35rem / .5rem / .75rem / 1rem` |
| `.mt-2` | `margin-top: .5rem` |
| `.m-0` | `margin: 0` |
| `.w-full` | `width: 100%` |
| `.mw-520` | `max-width: 520px` |
| `.flex-wrap-sm` | `display:flex; gap:.4rem; flex-wrap:wrap` |
| `.chevron` / `.chevron-open` | Collapsible chevron icon (normal / rotated) |
| `.label-strong` | `font-size:.88rem; font-weight:600; color:var(--text)` |
| `.col-flex-sm` | `flex:1; display:flex; flex-direction:column; gap:.25rem; font-size:.82rem` |
| `.field-hint-block` | `display:block; min-height:1.1em; margin-top:.25rem` |
| `.collapsible-trigger` | `cursor:pointer; user-select:none; padding:0 0 .5rem` |
| `.clickable` | `cursor:pointer; user-select:none` |
| `.input-sel-sm` | `min-width:160px; height:2rem; font-size:.8rem` |

For one-off element styles, add a CSS rule targeting the element's `id` in `style.css`. For new modals, add `#myModal .modal-box { max-width: Xpx; }` — do not use `style="max-width:Xpx"`.

---

## 6. Chart Patterns (ECharts)

### Chart lifecycle

```javascript
// ✅ Correct pattern
const CHARTS_PER_TAB = {
  dashboard: ['effortChart', 'trendsChart'],
  portfolio: ['treemapChart', 'bulletChart'],
};

// On tab leave
_disposeTabCharts('dashboard');

// On tab enter — lazy init
const chart = _getOrCreateChart('effortChart');
chart.setOption(buildEffortOption(data));
```

Never initialize a chart before its container is visible (display:none). The `_getOrCreateChart()` factory handles this.

### Chart defaults

Always call `_chartDefaults()` as the base:

```javascript
function buildMyChart(data) {
  return {
    ..._chartDefaults(),   // grid, textStyle, animation defaults
    title: { text: _t('chart.my_title') },
    series: [...],
  };
}
```

### EVM quadrant series ordering

In the CPI×SPI scatter chart, trajectory lines must render **behind** dots:

```javascript
// ✅ Trajectories first, scatter last
series: [
  ...trajectoryLines,   // type: 'line', z: 1
  { type: 'scatter', z: 10 },
]
```

### Color rules per chart type

| Chart type | Color source |
|-----------|-------------|
| Data series (bars, lines, treemap tiles) | `_getPalette()[index]` |
| Health status (ok/warning/critical) | `_cssVar('--green'/'--amber'/'--red')` |
| Threshold marks | `_cssVar('--red')` / `_cssVar('--amber')` |
| Reference lines (avg, target) | `_cssVar('--text-3')` |
| Grid lines | `_cssVar('--border')` |
| Background | `_cssVar('--card')` |

---

## 7. Modal Pattern

### Declaration in `index.html`

```html
<div class="modal-backdrop" id="myModal" hidden>
  <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="myModalTitle">
    <div class="modal-header">
      <h3 id="myModalTitle" data-i18n="my_modal.title">Título</h3>
      <!-- ✅ Always data-modal-close, never onclick or individual listener -->
      <button type="button" class="modal-close"
              aria-label="Fechar" data-i18n-aria="btn.close"
              data-modal-close="myModal">×</button>
    </div>
    <div class="modal-body">
      <!-- content -->
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-primary" id="myModalSaveBtn"
              data-i18n="btn.save">Salvar</button>
      <!-- ✅ Cancel button also uses data-modal-close -->
      <button type="button" class="btn btn-secondary"
              data-modal-close="myModal"
              data-i18n="btn.cancel">Cancelar</button>
    </div>
  </div>
</div>
```

### Opening a modal

```javascript
// ✅ Always pass trigger element for focus restoration
openModal('myModal', document.activeElement, '#myModalSaveBtn');

// openModal() automatically:
// - removes hidden attribute
// - traps Tab focus within modal
// - registers Escape handler
// - restores focus to triggerEl on close
```

### Close button handling

A single delegated listener in `app.js` handles all `[data-modal-close]` buttons:

```javascript
// ✅ In app.js — handles every modal automatically
document.addEventListener('click', e => {
  const btn = e.target.closest('[data-modal-close]');
  if (btn) closeModal(btn.dataset.modalClose);
});
```

**Never add individual `getElementById('...').addEventListener('click', () => closeModal(...))` calls.**

### Required form fields in modals

Every input that is required must have both HTML and ARIA attributes:

```html
<input type="text" id="myInput"
       required aria-required="true"
       data-i18n-placeholder="my_input.placeholder">
```

---

## 8. Pagination Pattern

Use `_makePaginator()` from `ui-helpers.js` for every table with pagination.

```javascript
// ✅ Required: entity key for accessible aria-labels
const _myPag = _makePaginator(
  {
    prev:    'myPrevBtn',
    next:    'myNextBtn',
    info:    'myPageInfo',
    entity:  'my_entity.title',   // i18n key → "Prev — My Entity"
  },
  page => _renderMyTable(_allItems, page)
);

// Usage
_myPag.load(_allItems);    // set items + go to page 1
_myPag.refresh();          // re-render current page
```

`_makePaginator` sets `aria-label` on prev/next buttons including the entity name, enabling screen readers to distinguish between multiple paginators on the same page.

**Page size:** default 20 items per page. Change via the `pageSize` option if content justifies it.

---

## 9. CRUD Pattern

Every CRUD section follows this structure:

```javascript
// 1. Cache array
let _allItems = [];

// 2. Load function — fetches + renders
async function loadMyTab() {
  try {
    _allItems = await fetch('/api/my-items', { headers: _authHeaders() }).then(r => r.json());
    _myPag.load(_allItems);
  } catch (e) { notify(_friendlyError(e), 'error'); }
}

// 3. Render function — pure render from data slice
function _renderMyTable(items, page = 1) {
  const tbody = document.getElementById('myTableBody');
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">${_t('my_items.empty')}</td></tr>`;
    return;
  }
  tbody.innerHTML = items.slice((page-1)*20, page*20).map(item => `
    <tr>
      <td>${item.name}</td>
      <td class="text-right">${_fmtCost(item.cost)}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="openEditModal(${item.id})"
                data-i18n="btn.edit">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="_deleteItem(${item.id})"
                data-i18n="btn.delete">Excluir</button>
      </td>
    </tr>
  `).join('');
}

// 4. Delete with confirmation
async function _deleteItem(id) {
  const item = _allItems.find(x => x.id === id);
  _confirmDelete(item.name, async () => {
    await fetch(`/api/my-items/${id}`, { method: 'DELETE', headers: _authHeaders() });
    await loadMyTab();
    notify(_t('my_items.deleted'), 'success');
  });
}
```

### Row-actions dropdown (three-dot menu)

For tables with multiple actions per row, use the standard dropdown:

```javascript
// In render function
`<button class="btn btn-secondary btn-sm row-actions-trigger"
         title="${_t('btn.more_actions')}"
         aria-label="${_t('btn.more_actions')}"
         aria-haspopup="menu"
         aria-expanded="false">⋮</button>
<div class="row-actions-menu" hidden role="menu">
  <button role="menuitem" onclick="doActionA(${item.id})">${_t('action.a')}</button>
  <button role="menuitem" onclick="doActionB(${item.id})">${_t('action.b')}</button>
  <button role="menuitem" class="text-danger" onclick="doActionC(${item.id})">${_t('action.c')}</button>
</div>`
```

`_openRowMenu()` in `app.js` handles keyboard navigation (Enter/Space open, ArrowUp/Down navigate, Escape close) via event delegation.

---

## 10. i18n Pattern

All user-visible strings must use the i18n system. No hardcoded Portuguese or English.

### Adding a new key

Add to **both** `frontend/lang/pt.js` and `frontend/lang/en.js`:

```javascript
// pt.js
'my_feature.title': 'Meu Recurso',
'my_feature.empty': 'Nenhum item encontrado.',
'my_feature.saved': 'Salvo com sucesso!',

// en.js
'my_feature.title': 'My Feature',
'my_feature.empty': 'No items found.',
'my_feature.saved': 'Saved successfully!',
```

### Using in HTML

```html
<!-- Static text -->
<h2 data-i18n="my_feature.title">Meu Recurso</h2>

<!-- Attribute translation -->
<button aria-label="..." data-i18n-aria="btn.close">×</button>
<input placeholder="..." data-i18n-placeholder="my_input.placeholder">
```

### Using in JavaScript

```javascript
// Simple lookup
const label = _t('my_feature.title');

// With substitution (use .replace, not template vars in the key)
const msg = _t('confirm.delete_msg').replace('{entity}', item.name);

// In notify()
notify(_t('my_feature.saved'), 'success');
```

---

## 11. Accessibility Patterns

### Required on every interactive element

```html
<!-- Buttons with icon-only content -->
<button aria-label="Fechar" data-i18n-aria="btn.close">×</button>
<button aria-label="Imprimir" data-i18n-aria="btn.print">
  <span aria-hidden="true">🖨</span>
</button>

<!-- Form inputs without visible label -->
<label for="myInput" class="sr-only" data-i18n="my.label">Data início</label>
<input type="date" id="myInput">

<!-- Required fields -->
<input required aria-required="true" ...>

<!-- Loading states -->
<div id="myChart" aria-busy="false"></div>
<!-- On load start: -->
el.setAttribute('aria-busy', 'true');
el.setAttribute('aria-label', _t('loading'));
<!-- On load end: -->
el.removeAttribute('aria-busy');
```

### Keyboard support requirements

Every interactive element must be keyboard-operable:

```javascript
// Sort headers
th.setAttribute('tabindex', '0');
th.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _sortHandler(); }
});

// Drag-reorderable lists (WCAG 2.5.7)
// Use _addKeyboardReorder(listEl) from app.js
// Provides ArrowUp/ArrowDown as keyboard alternative to drag

// Tooltips (data-evm elements)
el.setAttribute('tabindex', '0');
el.addEventListener('keydown', e => { if (e.key === 'Escape') _hideTooltip(); });
// Also wire focusin/focusout to show/hide (mirrors mouseenter/mouseleave)
```

### Color contrast

Minimum WCAG AA (4.5:1 for normal text, 3:1 for large/UI elements):

| Token | Value | Background | Ratio |
|-------|-------|-----------|-------|
| `--text` | `#e2e8f0` | `--card` (#0e2038) | ~11:1 ✅ |
| `--text-2` | `#b0c4d8` | `--card` | ~6.5:1 ✅ |
| `--text-3` | `#7aadcc` | `--card` | ~5.2:1 ✅ |
| `--text-pale` | `#7891a5` | `--card` | ~4.6:1 ✅ |

**Never use `--text-faint` for meaningful text** (contrast < 3:1).

### Focus management in modals

`openModal()` handles: trapping Tab, Escape key, and restoring focus on close. No additional work needed if using the standard modal pattern.

---

## 12. Notification Pattern

All notifications go through the queue — never call `_showNotif()` directly.

```javascript
// ✅ Always use notify()
notify(_t('my_feature.saved'), 'success');   // 5s timeout
notify(_t('my_feature.error'), 'error');     // 12s timeout
notify(_t('my_feature.warning'), 'warning');
notify(_t('my_feature.info'), 'info');
```

The queue (`_notifQueue` in `app.js`) ensures notifications are shown one at a time with a 150ms gap between them. Multiple rapid `notify()` calls will be displayed sequentially — no stacking or overwriting.

---

## 13. Error Handling Pattern

### API call wrapper

```javascript
async function loadSomething() {
  try {
    const data = await fetch('/api/something', { headers: _authHeaders() }).then(r => {
      if (!r.ok) return r.json().then(e => Promise.reject(e));
      return r.json();
    });
    _renderSomething(data);
  } catch (e) {
    // _friendlyError converts API errors to human-readable messages
    notify(_friendlyError(e), 'error');
  }
}
```

### `_friendlyError` rules

- HTTP 401 → i18n key `err.unauthorized`
- HTTP 403 → i18n key `err.forbidden`
- HTTP 404 → i18n key `err.not_found`
- HTTP 422 → pass through API `detail` **if** `detail.length < 200` and no `traceback`; otherwise use `err.validation`
- HTTP 5xx → i18n key `err.server`
- Network error → i18n key `err.network`

---

## 14. Testing Patterns

**Current test count: 698 tests across 26 files** (`pytest tests/ -v` — all in-memory SQLite, no `pmas.db` touched).

### Backend tests

All tests use an in-memory SQLite database. Never touch `pmas.db`.

```python
# conftest.py provides: client (TestClient), db (Session), admin_headers, user_headers
def test_my_feature(client, admin_headers):
    # Setup
    r = client.post("/api/projects", json={...}, headers=admin_headers)
    assert r.status_code == 201

    # Exercise
    r = client.get("/api/v2/portfolio", headers=admin_headers)
    assert r.status_code == 200

    # Verify — check actual values, not just status codes
    data = r.json()
    assert any(p["pep_wbs"] == "60IT-001-01" for p in data)
```

### EVM formula tests

New EVM functions in `evm.py` require tests in `test_evm_service.py`:

```python
# Test happy path
def test_compute_etc_normal():
    assert compute_etc(100.0, 60.0) == 40.0

# Test zero-floor (ETC cannot be negative)
def test_compute_etc_overrun():
    assert compute_etc(80.0, 100.0) == 0.0

# Test None propagation
def test_compute_etc_none_inputs():
    assert compute_etc(None, 60.0) is None
    assert compute_etc(100.0, None) is None
```

### Ingestion phase tests

`tests/test_ingestion_phases.py` tests each phase function independently via its public signature. When modifying a phase, add/update tests in the corresponding test class:

```python
class TestPhaseLoadAndValidate:   # _phase_load_and_validate
class TestPhaseAuthorizePeps:     # _phase_authorize_peps
class TestPhasePrescanDates:      # _phase_prescan_dates
class TestPhaseValidateRows:      # _phase_validate_rows
class TestPhaseAggregateRules:    # _phase_aggregate_rules
class TestPhaseUpsertRecords:     # _phase_upsert_records
```

### Golden rules tests

Tests in `test_golden_rules.py` verify architectural constraints at the API level. If you add a new GR violation pattern, add a test that would catch it.

### Frontend unit tests

Pure functions in `utils.js` are tested with vitest (`tests/frontend/unit/utils.test.js`):

```javascript
import { _fmtH, _fmtCost } from '../../../frontend/utils.js';

test('_fmtH formats hours', () => {
  expect(_fmtH(1234.5)).toBe('1.234,5 h');
});
```

### E2E tests (Playwright)

E2E tests live in `tests/frontend/e2e/`. They test complete user flows:

```javascript
// tests/frontend/e2e/myfeature.spec.js
test('user can export collaborator CSV', async ({ page }) => {
  await page.goto('http://localhost:8000');
  // login → navigate → interact → assert
});
```

Run with: `make e2e` or `npx playwright test`.

---

## 15. Operations

### Backup

`backup_pmas.sh` (project root) — SQLite backup via `VACUUM INTO`. Run daily via cron:
```
0 2 * * * /opt/pmas/backup_pmas.sh >> /var/log/pmas_backup.log 2>&1
```
Restore: stop app → `cp backup.db pmas.db` → start app → verify `/health`.

---

## Appendix: Quick Reference

### Adding a new v2 analytics endpoint

1. Create `backend/app/routers/v2/my_endpoint.py`
2. Import `_allowed_peps` from `v2/portfolio.py` — enforce ACL
3. Import all EVM functions from `services/evm.py` — no inline formulas
4. Use `resolve_effective_budget(proj, baseline)` for budget values
5. Register in `backend/app/main.py`: `app.include_router(my_endpoint.router)`
6. Add tests in `tests/test_v2_endpoints.py`

### Adding a new modal

1. Declare in `index.html` with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
2. Add `data-modal-close="<modal-id>"` to **all** close and cancel buttons
3. Open with `openModal('myModal', triggerEl, '#firstFocusable')`
4. Add `required aria-required="true"` to all required inputs
5. No individual `getElementById('...').addEventListener('click', closeModal)` calls needed

### Adding a new EVM function

1. Add to `backend/app/services/evm.py`
2. Guard against `None` inputs, return `None` on invalid
3. Add unit tests in `tests/test_evm_service.py` (happy, boundary, None propagation)
4. Export in the function's caller via import, never inline

### Adding a chart

1. Add builder function to the appropriate `charts/*.js` file
2. Start with `{ ..._chartDefaults(), ... }`
3. Use `_getPalette()[i]` for series colors
4. Use `_cssVar('--...')` for semantic/status colors
5. Register the chart ID in `CHARTS_PER_TAB` in `app.js`
6. Add mobile height to `style.css` breakpoints if the chart has a fixed container ID
