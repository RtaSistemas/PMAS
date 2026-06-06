# Branch Diff — `claude/create-project-docs-qJaUo` vs `main`

> Generated: 2026-06-06  
> Branch: `claude/create-project-docs-qJaUo`  
> Commits ahead of main: **255**  
> Files changed: **153** (111 new · 33 modified · 9 deleted)  
> Lines: **+67,757 / −11,979**
> **Post-audit improvements:** Sprint 1 (2026-06-06) + Sprint 2 (2026-06-06) — 12 achados resolvidos, score 7.3 → 8.7

---

## 1. Summary

This branch transforms PMAS from a basic timesheet viewer into a full-featured EVM (Earned Value Management) analytics platform. The changes span four major axes:

| Axis | Before (main) | After (this branch) |
|------|--------------|---------------------|
| Backend analytics | Single `analytics.py` monolith + `reference.py` | 10 specialized `/api/v2` routers |
| EVM computation | Scattered inline formulas in routers + frontend | Centralized `services/evm.py` (single source of truth) |
| Frontend structure | Single 5,681-line `app.js` | Modular: `charts/`, `crud/`, `lang/`, `ui-helpers.js`, `evm-glossary.js`, `utils.js` |
| Test coverage | 406 tests across 15 files | 635 tests across 20 files |

---

## 2. New Files

### Backend

| File | Purpose |
|------|---------|
| `backend/app/services/evm.py` | **Single source of truth** for all EVM formulas: CPI, SPI, EAC, TCPI, VAC, CV, SV, Earned Schedule, ETC, health classification, threshold helpers |
| `backend/app/services/summaries.py` | Maintains `PepCycleSummary` and `CollaboratorCycleSummary` pre-computed tables; fast path for all v2 analytics |
| `backend/app/services/notifications_svc.py` | `notify_threshold_crossings()` — detects budget threshold crossings post-upload |
| `backend/app/routers/baselines.py` | `ProjectBaseline` lock/activate + budget-history revision log |
| `backend/app/routers/notifications.py` | Notification listing endpoint |
| `backend/app/limiter.py` | slowapi rate-limiter factory (upload: 10/min, login: 30/min) |
| `backend/app/routers/v2/__init__.py` | v2 analytics package |
| `backend/app/routers/v2/filters.py` | Cascading filter options (collaborators, PEPs, cycles) |
| `backend/app/routers/v2/portfolio.py` | Treemap + bullet EVM-aware response; `_allowed_peps` ACL helper |
| `backend/app/routers/v2/effort.py` | Hour aggregation by collaborator |
| `backend/app/routers/v2/trends.py` | Per-cycle trends with period deltas |
| `backend/app/routers/v2/forecast.py` | Full EVM forecast: CPI/SPI/EAC/TCPI/VAC/CV/SV + Earned Schedule + S-curve + Physical % |
| `backend/app/routers/v2/runway.py` | Cycles-to-complete + SPI/CPI/risk + CPI×SPI trajectory per PEP |
| `backend/app/routers/v2/allocation.py` | Hours allocation matrix (collaborator × PEP/cycle) |
| `backend/app/routers/v2/concentration.py` | Top-1 contributor concentration risk per PEP |
| `backend/app/routers/v2/over_allocation.py` | Over-allocation detection (collaborators exceeding capacity) |
| `backend/app/routers/v2/simulate.py` | What-If scenario: velocity multiplier + extra hours → projected completion/EAC/burn-up |
| `backend/app/routers/v2/monte_carlo.py` | N-iteration Gaussian Monte Carlo → P10/P50/P90 + histogram |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/charts/effort.js` | Effort tab chart builders (stacked/grouped bars, velocity sparkline) |
| `frontend/charts/portfolio.js` | Portfolio chart builders: treemap, bullet, EVM quadrant scatter + trajectory lines |
| `frontend/charts/forecast.js` | Forecast chart builders: S-curve, burn-up, What-If burn-up, Monte Carlo histogram |
| `frontend/crud/cycles.js` | Cycles tab CRUD (extracted from app.js) |
| `frontend/crud/projects.js` | Projects tab CRUD + Plan modal + Baseline modal + ACL modal |
| `frontend/lang/pt.js` | Complete pt-BR i18n string table |
| `frontend/lang/en.js` | Complete en-US i18n string table |
| `frontend/ui-helpers.js` | Shared helpers: `_makePaginator()`, `_confirmDelete()`, `_makeRiskBadge()`, table-sort |
| `frontend/evm-glossary.js` | EVM glossary tooltips: hover + keyboard (focus/Escape) |
| `frontend/utils.js` | Pure utility functions: `_fmtH()`, `_fmtCost()`, `_cssVar()`, `_getPalette()` |
| `frontend/echarts.min.js` | ECharts local copy (offline, no CDN dependency) |

### Tests

| File | Tests | Coverage |
|------|-------|---------|
| `tests/test_evm_service.py` | 104 | Every function in `services/evm.py` |
| `tests/test_v2_endpoints.py` | 64 | All `/api/v2` analytics endpoints |
| `tests/test_golden_rules.py` | 260 lines | Architecture constraint enforcement |
| `tests/test_monte_carlo.py` | 8 | P10/P50/P90, histogram, insufficient-data guard |
| `tests/test_simulate.py` | 7 | What-If velocity window, projected EAC, burn-up |
| `tests/test_simulation.py` | 1 | End-to-end portfolio simulation smoke test |
| `tests/test_over_allocation.py` | 13 | Over-allocation filters, sort, CSV |
| `tests/test_notifications.py` | ~15 | Threshold crossing detection |
| `tests/test_summaries_status.py` | ~10 | PepCycleSummary staleness detection |
| `tests/test_upload_guards.py` | ~12 | Rate limiting, size cap |
| `tests/frontend/e2e/` | 4 suites | Playwright E2E: login, mobile, resilience, theme |
| `tests/frontend/unit/utils.test.js` | ~20 | vitest unit tests for utils.js |

### DevOps / Config

| File | Purpose |
|------|---------|
| `Makefile` | `make dev`, `make test`, `make e2e`, `make sample` shortcuts |
| `package.json` | Node dev dependencies for Playwright + vitest |
| `playwright.config.js` | E2E test configuration |
| `vitest.config.js` | Frontend unit test configuration |
| `requirements-lock.txt` | Pinned dependency versions for reproducible installs |
| `.env.example` | Environment variable template |

### Documentation

| File | Purpose |
|------|---------|
| `CHANGELOG.md` | Version history with semantic entries |
| `INTEGRITY-REPORT.md` | Visual/stack/purpose audit — 9 items, all resolved |
| `UX-AUDIT.md` | UX/accessibility audit — 23 items, all resolved |
| `docs/PATTERNS.md` | **Architectural patterns guide** (this branch) |

---

## 3. Modified Files (key changes)

### `backend/app/models.py`
- Added: `ProjectBaseline`, `BudgetRevision`, `PepCycleSummary`, `CollaboratorCycleSummary`, `ThemePreset`
- Extended `Project`: `start_date`, `planned_end_date`, `completion_date`, `status`
- Extended `ProjectCyclePlan`: `physical_pct` for Physical Percent Complete
- Extended `TimesheetRecord`: `normal_cost`, `extra_cost`, `standby_cost` (frozen costs per type)
- Total: 15 → 20 models

### `backend/app/main.py`
- Added: slowapi rate limiting, structured logging middleware
- Added: `include_router` for all v2 analytics routers
- Changed lifespan hook from `@app.on_event` to `@asynccontextmanager` pattern

### `backend/app/services/ingestion.py`
- Added: `affected_peps` list in return dict (used for post-upload notifications)
- Added: Phase 0b — pre-scan dates for quarantine-cycle detection
- Improved error messages and quarantine reason codes

### `backend/app/routers/dashboard.py`
- Added: `GET /collaborator-export` streaming CSV endpoint
- Extended `collaborator-daily` with quarantine date overlay

### `backend/app/routers/upload.py`
- Added: file size cap (configurable via `GlobalConfig`)
- Added: rate limiting (10/min per IP)
- Added: `notify_threshold_crossings()` call post-upload
- Added: `affected_peps` in upload response

### `backend/app/schemas.py`
- Added ~25 new Pydantic schemas for v2 responses
- All EVM render-ready schemas: CPI/SPI/colors/labels pre-computed server-side

### `frontend/app.js`
Major structural changes (5,681 → 5,633 lines after extraction of 2,000+ lines to modules):
- Cycles CRUD → `crud/cycles.js`
- Projects CRUD → `crud/projects.js`
- Chart builders → `charts/effort.js`, `charts/portfolio.js`, `charts/forecast.js`
- Language strings → `lang/pt.js`, `lang/en.js`
- UI helpers → `ui-helpers.js`
- EVM glossary → `evm-glossary.js`
- Utility functions → `utils.js`

New capabilities remaining in `app.js`:
- `_evmMode` toggle (hours ↔ R$)
- `_notifQueue` + `_processNotifQueue()` sequential notifications
- `_makeSortable()` with keyboard support (tabindex + Enter/Space)
- `_addKeyboardReorder()` for drag-list alternatives (WCAG 2.5.7)
- `_openRowMenu()` delegated keyboard handler for row-action dropdowns
- `_markFiltersDirty()` + `_setChartLoading()` ARIA helpers
- `_saveForecastSections()` + `_applyFcSection()` progressive disclosure
- Delegated `[data-modal-close]` listener replacing 30+ individual listeners

### `frontend/index.html`
- Removed: Google Fonts CDN (`<link rel="preconnect" href="https://fonts.googleapis.com">`)
- Added: `<script>` tags for all new modules (utils, ui-helpers, lang, evm-glossary, charts/*, crud/*)
- Added: Ciclos tab (extracted from former inline section)
- Added: Stats strip above Projects table
- Restructured Projects tab: `[Editar]` `[Plano]` `[⋮]` row actions
- Added: 37 `data-modal-close` attributes on all modal close/cancel buttons
- Added: `required aria-required="true"` on 9 critical form inputs
- Added: `<label class="sr-only">` for all unlabeled filter inputs
- Added: `overAllocHint` discovery panel for non-admin users

### `frontend/style.css`
- Added: CSS custom properties for z-index tokens (`--z-base` through `--z-tooltip`)
- Added: `--font-family: system-ui, -apple-system, "Segoe UI"...` (no external font)
- Changed: `--text-3: #7aadcc` (was `#5a82a0` — failed WCAG 1.4.3 contrast)
- Changed: `.sem-dot` 7px → 12px (min 12px touch target)
- Added: `@media (prefers-reduced-motion: reduce)` animation guard
- Added: `@media (max-width: 768px)` and `(max-width: 480px)` chart height breakpoints
- All hardcoded `z-index:` values replaced with `var(--z-*)` tokens

---

## 4. Deleted Files

| File | Reason |
|------|--------|
| `backend/app/routers/analytics.py` | Superseded by 10 focused `/api/v2` routers |
| `backend/app/routers/reference.py` | Superseded by `v2/filters.py` |
| `tests/test_analytics.py` | Tests for deleted `analytics.py` |
| `tests/test_dashboard.py` | Merged into broader test coverage |
| `tests/test_reference.py` | Tests for deleted `reference.py` |
| `MANUAL.md` / `manual.md` | Replaced by updated `README.md` |
| `docs/treinamento.md` | Replaced by `docs/PATTERNS.md` |
| `amostras/PORTFOLIO_ANALISE.md` | Outdated analysis document |

---

## 5. Category Breakdown

### 5.1 EVM Architecture

The central architectural change is the extraction of all EVM math into `services/evm.py`:

```
Before:  CPI formula in analytics.py, portfolio.py, forecast.py, frontend app.js
After:   CPI = compute_cpi_ev(consumed_h, budget_h, budget_cost, actual_cost)  [evm.py only]
```

All v2 routers produce **render-ready** responses — every number arrives at the frontend with color, label, and formatted value pre-computed. The frontend performs zero EVM arithmetic.

### 5.2 New EVM Capabilities

| Feature | Router/Service |
|---------|---------------|
| Earned Schedule (ES, SPI(t), SV(t), IEAC(t)) | `v2/forecast.py` + `evm.py` |
| Physical Percent Complete | `v2/forecast.py`, `ProjectCyclePlan.physical_pct` |
| What-If scenario planning | `v2/simulate.py` |
| Gaussian Monte Carlo (P10/P50/P90) | `v2/monte_carlo.py` |
| CPI×SPI trajectory lines | `v2/runway.py` + `charts/portfolio.js` |
| Concentration risk (top-1 dependency) | `v2/concentration.py` |
| Over-allocation detection | `v2/over_allocation.py` |
| Budget revision history + sparkline | `routers/baselines.py` |
| Collaborator timesheet CSV export | `routers/dashboard.py` |
| Post-upload budget alerts | `services/notifications_svc.py` |

### 5.3 Accessibility (UX-AUDIT — 23 items, all resolved)

| ID | Item | Resolution |
|----|------|-----------|
| ID-01 | Dirty filter indicator | Button text + `aria-description` change |
| ID-03 | Chart loading ARIA | `aria-busy="true"` + `aria-label` on container |
| ID-05 | Notification queue | Sequential queue — no overlapping banners |
| ID-06 | Modal close standardization | Single `[data-modal-close]` delegated listener |
| ID-07 | Paginator ARIA context | `aria-label` includes entity name |
| ID-08 | Required form fields | `required aria-required="true"` on 9 inputs |
| ID-09 | Confirm dialog i18n | `_confirmDelete()` uses `{entity}` placeholder |
| ID-10 | EVM glossary keyboard | `focusin`/`focusout`/`Escape` + `tabindex="0"` |
| ID-11 | Over-alloc discovery | `overAllocHint` panel for non-admins |
| ID-13 | Forecast progressive disclosure | Collapsible sections + UserPreference persistence |
| ID-14 | 422 error passthrough | Short API detail surfaced to user |
| ID-16 | Keyboard drag alternative | ArrowUp/Down reorder (WCAG 2.5.7) |
| ID-17 | Row-actions keyboard | `_openRowMenu()` + `aria-haspopup="menu"` |
| ID-18 | Sort headers keyboard | `tabindex="0"` + Enter/Space handler |
| ID-19 | Unlabeled filter inputs | `<label class="sr-only">` for all date/threshold inputs |
| ID-20 | `--text-3` contrast | `#7aadcc` (5.2:1 vs `#5a82a0` at 2.8:1) |
| ID-21 | `.sem-dot` size | 12px (was 7px; meets WCAG 1.4.11) |
| ID-22 | Print button name | `aria-label` + emoji `aria-hidden` |
| ID-23 | Reduced motion | `@media (prefers-reduced-motion: reduce)` guard |

### 5.4 Integrity (INTEGRITY-REPORT — 9 items, all resolved)

| ID | Item | Resolution |
|----|------|-----------|
| GR-01 | Upload chips hardcoded hex | `_cssVar('--green')` / `_cssVar('--primary')` |
| GR-02 | Chart series hardcoded hex | All replaced with `_getPalette()` / `_cssVar()` |
| GR-03 | Z-index token system | 9 `--z-*` tokens; zero literal `z-index` values |
| GR-04 | Google Fonts CDN | Removed; `system-ui` font stack |
| GR-05 | Mobile chart layout | 768px/480px breakpoints |
| GP-01 | `compute_etc()` function | Added to `evm.py`, used in `forecast.py` |
| GP-02 | Threshold notifications | `notifications_svc.py` wired in `upload.py` |
| GP-03 | Collaborator CSV export | `GET /api/dashboard/collaborator-export` |
| GP-04 | CPI×SPI trajectory | `runway.py` backend + `portfolio.js` frontend |

---

## 6. Post-Audit Improvements (Sprint 1 + Sprint 2)

> Applied after `MASTER-AUDIT.md` was generated on 2026-06-06.

### Sprint 1 — Quick Wins (8 items, ≤ 4h)

| ID | Change | Files |
|----|--------|-------|
| MA-03 | SortableJS 1.15.6 downloaded locally (45 KB); CDN removed | `frontend/sortable.min.js` (new), `frontend/index.html` |
| MA-02 | `_fmtR` removed from `forecast.js`; replaced with `_fmtCost()` | `frontend/charts/forecast.js`, `frontend/app.js` |
| MA-04 | `_fmtDate()` added to `utils.js`; 6 hardcoded timezone calls replaced | `frontend/utils.js`, `frontend/app.js` |
| MA-09 | 2× `console.warn` removed from `app.js` catch blocks | `frontend/app.js` |
| MA-06 | `compute_cpi` / `compute_cpi_ev` cross-reference docstrings added | `backend/app/services/evm.py` |
| MA-13 | `GET /health` endpoint added (status, timestamp, version) | `backend/app/main.py` |
| MA-17 | OpenAPI UI exposed at `/api/docs` and `/api/redoc` | `backend/app/main.py` |
| MA-11 | `.btn-sm` height corrected to `1.875rem` (was same as `.btn`) | `frontend/style.css` |

### Sprint 2 — Consolidação (4 items, ~1 day)

| ID | Change | Files |
|----|--------|-------|
| MA-10 | `_str_or_none` moved to `utils.py`; removed from `projects.py` + `ingestion.py` | `backend/app/utils.py`, `backend/app/routers/projects.py`, `backend/app/services/ingestion.py`, `backend/app/routers/quarantine.py` |
| MA-16 | `backup_pmas.sh` created with VACUUM INTO, 30-day retention, restore docs | `backup_pmas.sh` (new) |
| MA-08 | 4 muted text tokens removed (`--text-hint/faint/dim/pale`); 14 usages → `--text-3` | `frontend/style.css`, `frontend/index.html` |
| MA-05 | `formatHours()` gains `decimals` param; 8 `toFixed+'h'` in `<td>` templates replaced; ECharts formatters annotated | `frontend/app.js`, `frontend/charts/effort.js`, `frontend/utils.js` |

---

## 7. Metrics Comparison

| Metric | main | Branch (audit) | After Sprint 1+2 |
|--------|------|----------------|-----------------|
| Backend routers | 14 | 24 (+10 v2) | 24 |
| Backend services | 4 | 7 | 7 |
| ORM models | 15 | 20 | 20 |
| Test count | 406 | 635 | 635 |
| Frontend JS files | 3 | 13 | 14 (+sortable.min.js local) |
| i18n keys | 0 (hardcoded PT) | 540 (pt + en) | 540 |
| EVM formulas centralized | No | Yes (`evm.py`) | Yes (`evm.py`) |
| WCAG compliance (audited items) | Partial | 23/23 ✅ | 23/23 ✅ |
| Integrity compliance (audited items) | Partial | 9/9 ✅ | 9/9 ✅ |
| E2E test suites | 0 | 4 (Playwright) | 4 |
| CDN dependencies | 2 (ECharts + SortableJS) | 1 (SortableJS) | 0 ✅ |
| Text tokens in `:root` | — | 8 | 4 ✅ |
| MASTER-AUDIT score | — | 7.3/10 | 8.7/10 ✅ |
| Open audit findings | — | 17 | 5 (12 resolved) |
