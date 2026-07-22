# Changelog

All notable changes to PMAS (Project Management Assistant System) are recorded in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses release tags for versioning.

---

## [2.1.0_PMAS] — 2026-07-22

Scalability, error handling, and Linux release build.

### Added

- **Scalability — SQLite pragma tuning**: `wal_autocheckpoint=100`, `cache_size=-64000` (64 MB), `temp_store=MEMORY`, `mmap_size=268435456` (256 MB) added to the engine `connect` event listener. WAL checkpoint frequency and memory-mapped I/O now tuned for analytical workloads.
- **Scalability — connection pool configuration**: `pool_size`, `max_overflow`, `pool_timeout`, and `pool_recycle` added to `create_engine()`, all configurable via env vars `PMAS_DB_POOL_SIZE` and `PMAS_DB_MAX_OVERFLOW`. Defaults: pool_size=5, max_overflow=10.
- **RFC 7807 Problem Details**: `HTTPException` and `RequestValidationError` now return `application/problem+json` responses with `type`, `title`, `status`, `detail`, and field-level `erros` array in Portuguese. Replaces FastAPI's default JSON error format.
- **Linux release build**: Re-enabled `ubuntu-latest` matrix entry in `.github/workflows/release.yml`. Pushing a `v*` tag now produces `pmas-linux-x64` alongside the existing Windows binary.

### Changed

- **Version** bumped from `2.0.2` → `2.1.0`.

---

## [2.0.3_PMAS] — 2026-06-17

Audit remediation release. All 8 findings from PMAS-AUDIT.md resolved. No new end-user features.

### Fixed

- **DI-01 (HIGH)** — NULL cost columns no longer silently drop rows from `/api/v2/runway` and `/api/v2/allocation`. `func.coalesce(..., 0.0)` applied to each cost column in both endpoints. Regression test added: `TestNullCostRegression`.
- **GR-2-01 (HIGH)** — `simulate.py` was computing EAC inline, violating GR-2. New `compute_eac_avg_rate(actual_cost, consumed_hours, remaining_hours)` function added to `services/evm.py`; `simulate.py` now delegates to it. Unit tests: `TestComputeEacAvgRate` (6 cases).
- **GR-2-02 (MEDIUM)** — `dashboard.js` was computing cumulative CPI client-side via `ev/ac` division, duplicating EVM logic. `forecast.py` now includes `cpi_cumulative` in every history entry (via `compute_cpi`); the frontend reads it directly. Regression tests: `TestCpiCumulativeInHistory`.
- **AR-01 (LOW)** — `dashboard.js` classified SPI(t) color using a hardcoded 0.8 threshold, inconsistent with the server's 0.9 threshold used for all other indicators. `forecast.py` now includes `spi_t_color` computed via `spi_color(spi_t)`; the frontend maps it to a CSS class. Regression tests: `TestSpiTColorInForecast`.
- **GR-3-01 (LOW)** — `charts/forecast.js` and `charts/portfolio.js` used `|| '#hex'` fallbacks (e.g. `_cssVar('--green') || '#22c55e'`). All 12 occurrences removed. `test_gr3_no_hex_in_chart_color_properties` extended to cover `charts/*.js` and `tabs/*.js`; new `test_gr3_no_hex_fallback_in_charts` detects `|| '#hex'` patterns.
- **AR-02 (LOW)** — Added clarifying comment in `notifications_svc.py` explaining that `compute_spi` is called with period-level values intentionally for per-cycle consecutive-risk detection.

### Performance

- **PF-01 (MEDIUM)** — Added `Index('ix_timesheet_record_date', TimesheetRecord.record_date)` to `models.py`. M013 migration in `database.py` adds the index to existing production databases on startup.
- **PF-02 (MEDIUM)** — `refresh_pep_cycle` and `refresh_collaborator_cycle` in `summaries.py` replaced O(P×C) nested-loop queries with a single bulk `GROUP BY` aggregation per call. Total SQL round-trips reduced from O(P×C) to O(1) per ingestion regardless of portfolio size. Also fixed a latent bug where `(col or 0)` Python expressions were evaluated at ORM object level (not SQL COALESCE).

### Tests

- 712 tests total (+14 new tests covering all 8 audit findings).
- No regressions.

---

## [2.0.2_PMAS] — 2026-06-11

Stability and robustness release. No new end-user features; all changes harden the backend against misuse, data loss, and accidental misconfiguration.

### Added

- **`GET /ready` liveness probe** — runs `SELECT 1` against the database and returns `{"status":"ready"}` (200) or `{"detail":"Database unavailable."}` (503). Suitable for container orchestration health checks.
- **Rotating file log handler** — set `PMAS_LOG_FILE=/path/to/pmas.log` to write logs to a rotating file (10 MB × 5 backups) in addition to stdout. Console logging is unchanged when the variable is not set.
- **Security headers middleware** — every HTTP response now includes `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and a `Content-Security-Policy` restricting resource origins to `'self'`.
- **Rate limiting on write routes** — `@limiter.limit("30/minute")` applied to all POST / PUT / PATCH / DELETE handlers in `/api/projects`, `/api/cycles`, `/api/users`, and `/api/validation-rules`. Upload and login were already limited.
- **`must_change_password` backend enforcement** — `get_current_user` now raises HTTP 403 (`X-PMAS-Must-Change-Password: true`) when the user's flag is set, blocking access to all routes except `PATCH /api/users/{id}/password`. The password-change endpoint uses the new `get_current_user_allow_change` dependency, which bypasses the flag check to allow the forced update.
- **Notification deduplication (24-hour window)** — `create_notification()` in `notifications_svc.py` checks for an existing unread notification with the same `(user_id, message)` created within the last 24 hours before inserting a new row. Prevents bell-tray spam when the same alert condition persists across multiple uploads.
- **Schema migration version table** — `_migrate_columns()` in `database.py` now creates and consults a `schema_migration` table. Each migration step is keyed (M001–M012) and runs exactly once. Prevents `ALTER TABLE` races during multi-worker startup and provides a queryable history of applied migrations.
- **Login lockout** — after 5 consecutive failed login attempts the account is locked for 15 minutes (`locked_until` column on `User`). Successful login resets the counter. New columns (`failed_login_attempts INTEGER DEFAULT 0`, `locked_until DATETIME`) added via migration M012.

### Changed

- API `version` bumped to `2.0.2` in `main.py`.

---

## [2.0.1_PMAS] — 2026-06-08

UI polish and notification reliability release.

### Fixed

- **Pagination bar single line (P1):** Removed `overflow-x:auto` from `.pagination-bar` in
  `style.css`. The property created a faint scrollbar container that made the paginator appear
  on two lines. `flex-wrap:nowrap` was already set — the overflow rule was redundant and harmful.

- **Admin tab section order (P2):** Moved "Aparência do Sistema" card to the first position
  inside the Admin tab, above "Gestão de Usuários". System appearance is global configuration
  that should be immediately visible to admins.

- **Header semaphore hidden after page refresh (P4):** On page reload with a valid token,
  `app.js` line 729 called `_bootApp()` synchronously, before `tabs/header.js` (and other tab
  modules) had loaded. This caused a `ReferenceError` at `_updateHeaderUser()`, leaving the
  header username as `—` and the traffic-light semaphore permanently hidden. Fixed by replacing
  the direct `_bootApp()` call with `setTimeout(_bootApp, 0)`, which defers execution to after
  all `<script>` tags in `<body>` have evaluated.

- **Quarantine modal Reject button design (P5):** Changed `id="qrRejectBtn"` from `btn-primary`
  to `btn-danger` in `index.html`. The Approve and Reject actions were visually identical;
  Reject is a destructive action and must use the danger variant (transparent background, red
  border and text) to match the design system.

- **Bell not reflecting persistent alerts (P6):** In `notifications_svc.py`,
  `notify_threshold_crossings()` and `notify_schedule_risk()` only called
  `create_notification()` when `_upsert_project_alert()` returned `True` (new alert or level
  escalation). If an existing alert persisted at the same severity level across multiple
  uploads, no bell notification was sent — the ProjectAlert existed in Central de Alertas but
  was invisible to the bell. Removed the `if created:` guard so a notification is created on
  every upload that detects an active alert.

---

## [2.0.0RC_PMAS] — 2026-06-07

Predictive alerting release. PMAS reaches **Maturity Level 5** (Predictive) with proactive
schedule-risk detection and a persistent, queryable Alert Center. All 8 key management
decisions now have high confidence. Test suite at **698 tests** (zero failures).

### Added

- **`ProjectAlert` model** — permanent, lifecycle-managed alert record per project:
  `alert_type`, `level`, `message`, `metric_value`, `consecutive_cycles`, `created_at`,
  `resolved_at`, `is_resolved`. Deduplication: same (project, alert_type, level) → skip;
  level changes → resolves old, creates new. Auto-resolves on the next upload when the
  triggering metric recovers.
- **Schedule-risk detection (`notify_schedule_risk`)** — fires automatically after every
  successful upload. Detects collaborator SPI below the configurable threshold (default 0.85)
  for N consecutive cycles (default 2). Creates a `ProjectAlert` of type `schedule_risk` and
  delivers a bell-tray notification to all users with access to the affected PEP.
- **`GET /api/project-alerts`** (admin only) — lists all ProjectAlerts with filters: `pep_wbs`,
  `alert_type`, `is_resolved`, `date_from`, `date_to`, `limit`, `offset`.
- **`GET /api/my/alerts`** — per-user endpoint, ACL-filtered via `_allowed_peps`. Regular users
  see only alerts for PEPs they can access; admins see all.
- **Central de Alertas** (Admin tab) — paginated table with PEP, type, level, message, date and
  status filters. PEP dropdown populated dynamically from current data.
- **Alertas sub-tab** (Minha Área) — visible to non-admin users only (admins use the Admin tab
  to avoid redundancy). Paginated table with active/resolved filter and refresh button.
- **Forecast per-PEP alert card** — inline card inside the Forecast tab that loads
  automatically when a PEP is selected, showing its active and resolved alerts. Hidden when
  no alerts exist.
- **Alert level styles** in `style.css` — `.alert-level-warning` (amber), `.alert-level-error`
  (red), `.alert-level-info` (blue), `.alert-resolved` (dimmed row), `.forecast-alert-item`
  border variants.
- **`GlobalConfig` fields**: `spi_warning_threshold` (float, default 0.85) and
  `spi_risk_consecutive_cycles` (integer, default 2) — configurable without code changes.
  Safe `ALTER TABLE` migrations added to `_migrate_columns()`.
- **19 new tests** in `tests/test_project_alerts.py`: deduplication logic, auto-resolution,
  budget-warning trigger, overrun escalation, empty-list guard, admin endpoint filters,
  my-alerts ACL filtering with a real regular-user override.

### Fixed

- **`soma_semanal` alert fired N times per week** instead of once. `_phase_aggregate_rules`
  iterated over `daily_sums` (one entry per collaborator × day) and re-evaluated the weekly
  rule on every iteration, producing as many warnings as there were days with entries in the
  overloaded week. Fixed by splitting evaluation into two independent passes — daily rules
  over `daily_sums`, weekly rules over `weekly_sums` (one entry per collaborator × ISO week).
  The date shown in the weekly warning is now the **earliest day with actual data** in that
  week, pointing to a real timesheet entry (Option C). Two new regression tests confirm
  exactly one warning per week and correct first-day selection.

### Documentation

- **VALUE-AUDIT.html** updated to Maturity Level 5: verdict pill changed to 8/8 high-confidence
  decisions; "Previsão de Entrega" row upgraded from Moderada to Alta; maturity step 5 marked
  ✓; scope paragraph updated; Opportunity 1 marked as implemented; 15 evidence entries
  (previously 14, the gap entry replaced by the implementation entry).
- **`docs/README.md`** — VALUE-AUDIT description updated to Level 5, 8/8.
- API `version` bumped to `2.0.0RC` in `main.py`.

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

[2.0.0RC_PMAS]: #200rc_pmas--2026-06-07
[RC2.1]: #rc21--2026-06-06
[RC2.0]: #rc20--2026-06-03
[v1.4.8]: #v148--pagination-and-table-refinements
[v1.4.6 / v1.4.7]: #v146--v147--evm-metric-consistency-and-expert-review
[v1.4.4 / v1.4.5]: #v144--v145--architectural-consolidation-and-start-of-centralised-evm
[v1.4.1 → v1.4.3]: #v141--v143--accessibility-dynamic-treemap-and-evm-audit
[v1.4.0]: #v140--product-foundation
