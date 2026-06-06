# Changelog

All notable changes to PMAS (Project Management Assistant System) are recorded in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses release tags for versioning.

---

## [RC2.1] — 2026-06-06

Resilience and documentation release. Focused on frontend robustness, test suite hygiene, and codebase maintainability.

### Added

- **Global unhandled rejection handler:** `window.addEventListener('unhandledrejection', ...)` surfaces all unhandled Promise rejections via `notify()` and logs to the console — previously they were silent.
- **Session expiry warning:** `_checkTokenExpiry()` runs every 5 minutes and notifies the user when fewer than 10 minutes remain on the JWT.
- **Visibility-change refresh:** `document.addEventListener('visibilitychange', ...)` reloads cached data when the browser tab is brought back into focus after being hidden.
- **`frontend/crud/cycles.js`:** Billing-cycles CRUD extracted from `app.js` into its own file (~168 lines). Shares `window` scope with `app.js` (plain `<script>` tags, no bundler).
- **`frontend/crud/projects.js`:** Projects/PEPs CRUD + plans + baselines + ACL extracted from `app.js` into its own file (~615 lines). Fixed hardcoded `'pt-BR'` locale to use `_locale === 'pt' ? 'pt-BR' : 'en-US'`.
- **Playwright E2E tests (`tests/frontend/e2e/`):** resilience spec covering global error handler, `_logout()`, visibility listener, and `_checkTokenExpiry` registration.
- **`Makefile`:** `serve`, `test`, `test-backend`, `test-unit`, `test-e2e` targets.
- **`test_upload_guards.py`:** 11 tests for upload rate-limiting and auth guards.
- **Golden rules tests extended:** `test_golden_rules.py` now checks `crud/*.js` for GR-3 (no hardcoded hex) and locale patterns.

### Fixed

- **Critical test ordering bug:** `test_upload_guards.py` called `app.dependency_overrides.clear()` without saving and restoring the session-scoped override set by `conftest.py`. Tests running alphabetically after it received 401 Unauthorized. Fixed with save/restore pattern: `saved = dict(app.dependency_overrides)` before, `app.dependency_overrides.update(saved)` after.
- **Stale E2E test `login.spec.js:66`:** Test checked for `#cyclesTable` inside the Projetos tab, but the Ciclos/Projetos tab-split refactor moved cycles to a dedicated Ciclos tab. Updated to navigate to the correct tab.

### Documentation

- All documentation rewritten in English (official language from this release).
- `README.md` fully rewritten in English with updated architecture diagrams, test count, project structure, and frontend patterns.
- `CHANGELOG.md` rewritten in English.
- `CLAUDE.md` — "Pendências de Produção" section translated to "Known Production Gaps".
- Executed and obsolete internal report files removed from the repository.

---

## [RC2.0] — 2026-06-03

Consolidation release. The entire analytics layer (Portfolio Health, Trends, Forecast) is now served by a dedicated API with EVM numbers pre-computed server-side, eliminating formula divergences between screens. Projection tools (What-If, Monte Carlo, Runway, Earned Schedule) were added, and dozens of interface details polished.

Test suite grew from 406 to **590 tests** (all green), with **188 EVM-specific tests**.

### Added

- **Monte Carlo probabilistic forecast:** simulates thousands of completion scenarios and presents optimistic (P10), central (P50) and pessimistic (P90) milestones, with histogram and reference curve.
- **What-If simulation:** panel where the manager adjusts team velocity and overtime hours per cycle and instantly sees remaining cycles, projected completion cost, and the resulting burn-up curve.
- **Portfolio runway:** table estimating, per PEP, how many cycles remain to completion, average hours/cost per cycle, and schedule (SPI) and cost (CPI) risk.
- **Earned Schedule:** new time-based schedule indicators — Earned Schedule (ES), SPI(t), SV(t), and IEAC(t).
- **Physical Percent Complete:** option to enter real physical progress per cycle, used as the Earned Value basis when available (instead of the hours proxy).
- **Budget baseline:** lock an approved budget revision per project; when active, it becomes the authoritative budget in all analyses, with a banner and badge.
- **Budget revision history:** append-only log of all budget changes (hours/cost), shown as a sparkline.
- **Over-allocation detection:** identifies collaborators exceeding capacity in the period, with filters, sorting and CSV export.
- **Project dates and status:** projects now carry start date, planned end date, completion date and status (`em_andamento` / `encerrado`); completed projects have their metrics frozen at the final state.
- **Total trend line** optional in the team effort chart, and improved readability on indicator cards.
- **Standardised pagination** across all tables (Cycles, Projects/PEPs, Users, Audit Log, Import History, Quarantine, Seniority, Rate Card).
- **Extended EVM tooltip glossary** for new indicators (What-If, Monte Carlo, ES/SPI(t)/SV(t)/IEAC(t), velocity averages).
- Status filter and CSV export in Import History.

### Changed

- **All analytics migrated to API v2:** Effort, Portfolio, Trends and Forecast screens now consume `/api/v2/*` endpoints. Responses arrive render-ready — all EVM indices (CPI, SPI, EAC, TCPI, VAC, CV, SV) are computed once on the server.
- **Single source of truth for EVM:** all Earned Value formulas centralised in a single backend module, eliminating duplicate calculations and cross-screen divergences. The frontend no longer recalculates any EVM index.
- **Portfolio semaphore** migrated to API v2; clicking a project pill now filters the Portfolio tab to that PEP.
- Forecast tab information architecture reorganised (card and panel order; baseline management moved to the Projects tab).
- Variance indicators (deltas) repositioned as badges in the upper corner of portfolio cards.
- EVM quadrant chart axes capped at 2.0 for better readability.
- Velocity window rules documented and standardised across Forecast, Runway, What-If and Monte Carlo (each uses its own window, by design).

### Fixed

- Schedule Variance (SV) card in Forecast was formatted as currency (R$) when the value is in hours.
- Variance indicators stopped appearing on overtime/standby cards when the prior period was zero — fixed.
- P10/P50/P90 percentile representation in the Monte Carlo histogram corrected; labels scaled to avoid overlap.
- Personal quarantine panel (My Area) now correctly filters by review status.
- Various UX adjustments in Portfolio and Forecast charts and cards (fonts, colours, spacing, labels, theme-compliant colours).
- Removed leftover moving-average line from the Trends (Hour Burn) chart.

### Security

- Per-PEP access control (ACL) applied consistently to all v2 analytics endpoints and to budget history/quarantine.

---

## [v1.4.8] — Pagination and table refinements

### Added
- Pagination across all data tables (Cycles, Projects/PEPs, Users, Audit Log, History, Seniority, Rate Card), centralised in a single component.
- Status filter and CSV export in Import History.
- Collapse/expand button on the Dashboard filter card.

### Fixed
- Baseline modal widened for better readability.
- Projects table column order standardised; quarantine pagination standardised.
- Duplicates within the same file now recorded as info (not error).

---

## [v1.4.6 / v1.4.7] — EVM metric consistency and expert review

### Changed
- Expert review (EVM/UX/implementation) addressed across four fronts: mathematical foundation, metric consistency, nomenclature, and UX polish.
- Schedule Variance (SV) and SPI now computed in hours, not currency.

### Added
- Custom theme presets with CRUD and CSV import/export.
- "SPI frozen boundary" logic extracted to the EVM module (reused between Forecast and Runway).

### Removed
- Internal working documents (reports and proposals) that did not belong in the product repository.

---

## [v1.4.4 / v1.4.5] — Architectural consolidation and start of centralised EVM

### Changed
- EVM formulas and budget resolution centralised in a single service module.
- Health classification (green/yellow/red) moved from frontend to backend.
- Frontend modularised: chart builders (Effort, Portfolio, Forecast), EVM glossary and UX helpers split into separate files; table CRUD standardised.

---

## [v1.4.1 → v1.4.3] — Accessibility, dynamic treemap and EVM audit

### Added
- Full EVM audit and associated corrections: CV, TCPI, VAC and ETC added to Forecast; inline CPI in Portfolio Health; per-cycle SPI history.
- Accessibility (WCAG): keyboard navigation in MultiSelect, alternative text for charts, ARIA roles on tabs and colour tokens.
- Planning baseline (S-curve) with CSV import/export, modal, badge and banner.
- Dynamic treemap height proportional to the number of PEPs.

### Fixed
- Correct weighting of overtime/standby hours in the Earned Value numerator.
- Earned Value capped at budget (BAC), ensuring CPI < 1 for over-budget projects.

---

## [v1.4.0] — Product foundation

### Added
- CSV/XLSX timesheet import with a multi-phase ingestion pipeline and configurable validation rule engine.
- Quarantine workflow for rows that fail validation (approve/reject) and automatic quarantine cycles for dates outside registered periods.
- EVM Freeze pattern: cost per hour frozen at import time.
- CRUD for Cycles, Projects/PEPs, Seniority and Rate Cards, all with CSV import/export.
- Analytics: Team Effort, Portfolio Health (treemap + bullet, hours/R$), Trends and Forecast (S-curve).
- JWT authentication with bcrypt, per-PEP access control (ACL), admin/user roles and full audit log.
- My Area (preferences, personal history, personal quarantine, budget alerts), configurable UI theme and i18n support (pt-BR / en).

---

[RC2.1]: #rc21--2026-06-06
[RC2.0]: #rc20--2026-06-03
[v1.4.8]: #v148--pagination-and-table-refinements
[v1.4.6 / v1.4.7]: #v146--v147--evm-metric-consistency-and-expert-review
[v1.4.4 / v1.4.5]: #v144--v145--architectural-consolidation-and-start-of-centralised-evm
[v1.4.1 → v1.4.3]: #v141--v143--accessibility-dynamic-treemap-and-evm-audit
[v1.4.0]: #v140--product-foundation
