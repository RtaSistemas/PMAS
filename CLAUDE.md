# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PMAS** (Project Management Assistant System) is a timesheet management and analytics dashboard. Project managers upload CSV/XLSX timesheet exports and visualize employee work hours and costs. The system includes EVM financial tracking, a validation rule engine, quarantine workflow, baseline planning, per-user ACL, and full audit logging.

**Stack:** Python 3.11+ · FastAPI · SQLAlchemy · SQLite · Vanilla JS · Apache ECharts 5. The UI is fully in Portuguese (pt-BR).

> **Implementation patterns** — all coding conventions, design tokens, EVM formula rules, modal/pagination/CRUD/i18n/accessibility patterns are documented in [`docs/PATTERNS.md`](docs/PATTERNS.md). Read it before adding any feature.
> **Project documentation** — audit reports, sprint records, and the branch diff live in [`docs/`](docs/README.md).

## Golden Rules — Architectural Constraints

These rules are non-negotiable. They encode decisions made at the product level and must never be violated by any implementation, refactor, or feature addition.

**GR-1 — Data entry via ingestion only. Manual manipulation is forbidden.**
The only pathway for timesheet data to enter PMAS is through the established CSV/XLSX ingestion pipeline (`POST /api/upload-timesheet` → `ingest_file()`). The upstream legacy system (the client's timekeeping platform) is the single source of truth. PMAS is a read-and-analyze layer on top of it. Consequently:
- No `POST /api/timesheet-records` endpoint for individual row creation.
- No `PUT` / `PATCH` / `DELETE` on individual `TimesheetRecord` rows outside the quarantine workflow.
- Errors in imported data must be corrected at the source and re-imported, not patched in PMAS.
- The quarantine workflow (approve / reject) is the only in-system intervention allowed on ingested rows.

**GR-2 — EVM formulas live exclusively in `services/evm.py`.**
No router, no frontend script, and no test may re-implement an EVM formula. All EVM computation (CPI, SPI, EAC, TCPI, VAC, CV, SV, Earned Schedule, etc.) must call the functions in `services/evm.py`. This is the single source of truth for every financial metric.

**GR-3 — Chart data-series colors must use `_getPalette()`.**
Colors for data series in ECharts charts must come from `_getPalette()` (admin-configured palette). Semantic/status colors (health alerts, thresholds, peaks) may use `_cssVar()`. Hardcoded hex literals in chart options are forbidden.

## Running the Project

```bash
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Access the app at `http://127.0.0.1:8000`. No build step — the frontend is plain HTML + JS served as static files.

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

698 tests across 26 test files. All use an in-memory SQLite database (StaticPool) — no `pmas.db` is touched.

## Sample Data

```bash
python amostras/generate_portfolio.py
```

Generates ready-to-import CSVs in `amostras/`: `ciclos.csv` (29 monthly cycles Jan/2024–Mai/2026), `projetos.csv` (10 PEPs with `60IT-XXX-01` codes), `rate_cards.csv`, and per-month timesheet CSVs in `amostras/timesheets/`.

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — Slim FastAPI app: CORS middleware, rate limiting (slowapi), structured logging, `include_router` for the stable CRUD routers plus the full `/api/v2` analytics layer, static file mount, root redirect, lifespan hook (`init_db`).
- **`models.py`** — 22 SQLAlchemy ORM models:
  - `SeniorityLevel` — unique name, linked to RateCard and Collaborator
  - `RateCard` — hourly_rate with valid_from / valid_to date range per seniority level
  - `Collaborator` — unique name, optional `seniority_level_id` FK, linked to records
  - `Cycle` — billing period with `start_date`, `end_date`, `is_closed` and `is_active` flags
  - `TimesheetRecord` — core entity linking collaborator + cycle + PEP + 4 hour fields + `cost_per_hour` (frozen at ingestion via EVM freeze pattern)
  - `Project` — PEP registry with `budget_hours`/`budget_cost`, plus `start_date`, `planned_end_date`, `completion_date` and `status` (`em_andamento`/`encerrado`) for EVM tracking
  - `ProjectBaseline` — locked, approved budget revision per project (`is_active`, `locked_at`, `label`); authoritative budget when active
  - `BudgetRevision` — append-only history of budget changes (hours/cost), surfaced as the budget-history sparkline
  - `ProjectCyclePlan` — planned hours/cost (and optional `physical_pct`) per (project, cycle) for baseline S-curve
  - `User` — username, hashed_password, role (`admin`/`user`)
  - `GlobalConfig` — key/value store (logo path, UI theme overrides, `spi_warning_threshold`, `spi_risk_consecutive_cycles`)
  - `AuditLog` — structured log: user, action, entity, old/new JSON snapshot
  - `UserProjectAccess` — per-user PEP whitelist (empty = access all)
  - `ValidationRule` — ordered, typed rules evaluated per row during ingestion
  - `UploadSession` — metadata record for each upload (filename, user, row counts, status)
  - `QuarantineRecord` — rows that failed validation, with review workflow (pending/approved/rejected)
  - `UserPreference` — per-user UI preferences (chart layout order, etc.)
  - `PepCycleSummary` — pre-computed hours/cost per (pep_wbs, cycle); the fast path for v2 analytics, with raw `TimesheetRecord` aggregation as fallback
  - `CollaboratorCycleSummary` — pre-computed hours/cost per (collaborator, cycle)
  - `ThemePreset` — named UI theme presets (CRUD + CSV export/import)
  - `Notification` — bell-tray notification per user: `user_id`, `message`, `is_read`, `created_at`, `link`
  - `ProjectAlert` — permanent, lifecycle-managed alert per project: `alert_type`, `level`, `message`, `metric_value`, `consecutive_cycles`, `created_at`, `resolved_at`, `is_resolved`. Deduplication by `(project_id, alert_type)`; level changes resolve old and create new; auto-resolves when the triggering metric recovers
- **`schemas.py`** — All Pydantic input/output models: `CycleIn/Out`, `ProjectIn/Out`, `SeniorityLevelIn/Out`, `RateCardIn/Out`, `CollaboratorSeniorityIn`, `ImportResultOut`, `UserCreateIn`, `UserOut`, `ValidationRuleIn/Out`, `QuarantineRecordOut`, `UploadSessionOut`, `AlertSummaryOut`, `UserPreferenceIn/Out`, `UIThemeIn/Out`, `ProjectCyclePlanIn/Out`, `ForecastOut`, and others.
- **`database.py`** — SQLite engine, `get_db()` dependency, `init_db()` (runs `create_all` + `_migrate_columns`). `_migrate_columns()` applies `ALTER TABLE` for columns added after the initial schema, upgrading existing `pmas.db` files safely on startup.
- **`services/evm.py`** — **Single source of truth for every EVM formula.** No router or frontend may re-implement these. Provides `freeze_costs`, `compute_cpi`/`compute_cpi_ev`, `compute_spi`, `compute_ev_capped`, `compute_eac`/`compute_eac_schedule`, `compute_tcpi`, `compute_vac`, `compute_cv`, `compute_sv`, Earned Schedule (`compute_earned_schedule`, `compute_spi_t`, `compute_sv_t`, `compute_ieac_t`), `resolve_effective_budget` (active baseline > project fields), `classify_health`, `get_thresholds`, and the label/color helpers consumed render-ready by the frontend. Every function guards against division by zero (returns `None`). SPI/SV use an hours proxy (AgileEVM); EV is capped at BAC.
- **`services/ingestion.py`** — Parses CSV/XLSX with pandas. Multi-phase pipeline with a configurable validation rule engine. Freezes cost via `freeze_costs` from `evm.py`.
- **Other services** — `rule_engine.py` (per-row rule evaluation), `summaries.py` (maintains `PepCycleSummary`/`CollaboratorCycleSummary`), `quarantine_svc.py`, `upload_session_svc.py`, `theme_svc.py`.

### Backend Routers (`backend/app/routers/`)

| File | Prefix | Responsibility |
|---|---|---|
| `auth.py` | `/api` | `POST /token` — JWT login |
| `users.py` | `/api/users` | Admin CRUD for user accounts |
| `auditlog.py` | `/api` | `GET /audit-log` (admin) |
| `cycles.py` | `/api/cycles` | CRUD + CSV import/export for billing cycles |
| `projects.py` | `/api/projects` | CRUD + CSV import/export for projects/PEPs |
| `plans.py` | `/api/projects` | `/{id}/plans` CRUD, `GET /plans/export`, `POST /plans/import` — baseline S-curve (planned hours/cost per cycle) |
| `baselines.py` | `/api/projects` | `/{id}/baselines` — lock/activate budget baselines + `/{id}/budget-history` revision log |
| `dashboard.py` | `/api/dashboard` | Hour aggregation by collaborator; supports `date_from`/`date_to` |
| `ratecard.py` | `/api` | `/seniority-levels`, `/rate-cards`, `/team`, `/team/{id}/seniority` — all with CSV import/export |
| `acl.py` | `/api/projects` | `/{id}/access` — per-user PEP whitelist management (admin) |
| `upload.py` | `/api` | `POST /upload-timesheet`, `GET /upload-history[/{id}]` |
| `quarantine.py` | `/api/quarantine` | List, review, approve, reject, delete quarantine records (admin) |
| `validation_rules.py` | `/api/validation-rules` | CRUD + toggle + reorder for the rule engine |
| `my.py` | `/api/my` | Per-user: preferences, upload history, quarantine view, budget alerts, `GET /alerts` (ACL-filtered project alerts) |
| `notifications.py` | `/api/notifications` | Bell-tray CRUD: list, mark-read, mark-all-read, delete |
| `project_alerts.py` | `/api/project-alerts` | `GET /` (admin only) — list `ProjectAlert` rows with filters: `pep_wbs`, `alert_type`, `is_resolved`, `date_from`, `date_to`, `limit`, `offset` |
| `theme.py` | `/api/theme` | `GET/PUT` global UI theme, logo upload/delete |

### v2 Analytics Routers (`backend/app/routers/v2/`)

All analytics consumed by the frontend live under `/api/v2`. These responses are **render-ready**: every EVM number (CPI, SPI, EAC, TCPI, VAC, CV, SV, deltas, colors, labels) is computed server-side via `services/evm.py` so the frontend performs no EVM arithmetic. All v2 endpoints enforce the per-user PEP ACL via `_allowed_peps` and prefer `PepCycleSummary` with a raw `TimesheetRecord` fallback. The v1 `analytics`/`reference` routers were removed during the v2 migration.

| File | Prefix | Responsibility |
|---|---|---|
| `filters.py` | `/api/v2` | Cascading filter options (collaborators, PEPs, cycles) |
| `portfolio.py` | `/api/v2` | `/portfolio` — treemap + bullet (EVM-aware, hours/R$), `_allowed_peps` ACL helper reused by other v2 routers |
| `effort.py` | `/api/v2` | Hour aggregation by collaborator (Esforço da Equipe) |
| `trends.py` | `/api/v2` | Per-cycle trends line (hours + cost, period deltas) |
| `forecast.py` | `/api/v2` | Full EVM forecast per PEP — CPI/SPI/EAC/TCPI/VAC/CV/SV, Earned Schedule (ES/SPI(t)/SV(t)/IEAC(t)), S-curve history, uncertainty band; supports Physical Percent Complete and closed-project freeze |
| `allocation.py` | `/api/v2` | Hours allocation matrix (collaborator × PEP/cycle) |
| `concentration.py` | `/api/v2` | Contributor concentration risk (top-1 dependency) |
| `runway.py` | `/api/v2` | `/runway` — cycles-to-complete + SPI/CPI/risk per PEP, frozen-cost based |
| `over_allocation.py` | `/api/v2` | Over-allocation detection (collaborators exceeding capacity) with filters/sort/CSV |
| `simulate.py` | `/api/v2` | `POST /projects/{id}/simulate` — What-If scenario (velocity multiplier + extra hours → cycles-to-complete, projected EAC, burn-up) |
| `monte_carlo.py` | `/api/v2` | `GET /projects/{id}/monte-carlo` — N-iteration probabilistic completion forecast → P10/P50/P90 + histogram |

### Frontend (`frontend/`)

- **`index.html`** — Six top-level tabs: **Dashboard**, **Ciclos**, **Projetos**, **Equipe**, **Minha Área**, **Admin** (hidden unless admin). Dashboard contains a shared filter card (date range + MultiSelect dropdowns) and three analytics sub-tabs (Esforço da Equipe, Saúde do Portfólio, Previsão). Admin tab has sections for users, validation rules, quarantine, upload history, and audit log. **No `style=` inline attributes** — all presentation is in `style.css`.
- **`style.css`** — Dark slate/blue theme. Key selectors: analytics sub-tabs (sticky at `top: 3.25rem`), treemap legend, bullet chart thresholds, empty states, `.table-search-input`, budget alert badges (`.badge-budget.critical`/`.warning`), semaphore bar (`.semaphore-bar`, `.sem-dot`, `.sem-project` pill variants). Includes utility classes (`.pagination-bar`, `.chevron`, `.mb-0`–`.mb-4`, etc.) and element-specific rules targeting IDs — see `docs/PATTERNS.md` §5.
- **`multiselect.js`** — Self-contained `MultiSelect` component (cascading dropdowns for collaborator and PEP filters).
- **`app.js`** — Core globals only (≤800 lines):
  - **Auth:** JWT Bearer token stored in `sessionStorage`. `_getTokenPayload()` decodes it. `_isAdmin()` gates admin UI. `_bootApp()` is the central init called after login and on page load with a valid token.
  - **ECharts lifecycle:** `CHARTS_PER_TAB` registry, `_disposeTabCharts()` on sub-tab leave, `_getOrCreateChart()` on enter, single `ResizeObserver` on `<main>` for responsiveness.
  - **Core globals:** i18n (`_t`, `_locale`, `_applyI18n`), currency, modal utilities, table sort (`_makeSortable`, `_applySort`), theme helpers, tab navigation, sub-tab state toggle buttons.
  - **Auth/fetch:** `_authHeaders`, `apiFetch`, `apiFetchJSON`, `_friendlyError`, notify queue, `fmt`, login form, `_logout`, `_checkTokenExpiry`.
  - **Preferences/theme:** `_loadPreferences`, `_DENSITY_MAP`, `_THEME_PRESETS`, `_getPalette`, `_resolveSeriesColor`, `_loadTheme`.
- **`tabs/dashboard.js`** — Dashboard tab: filter state, MultiSelect instances, filter cascade helpers, `_renderActiveTab`, all analytics render functions (`_renderEffortTab`, `_renderPortfolioTab`, `_renderForecastTab`), collab detail panel, `_lastEffortData`/`_lastRunwayData` caches, `_evmMode` boolean, `_loadForecastAlerts` (inline alert card shown when a PEP is selected in the Forecast sub-tab).
- **`tabs/equipe.js`** — Team tab: `_anomalyMaxHours`, `_budgetWarning`, `_budgetCritical`, seniority CRUD, rate card CRUD, over-alloc table, `loadGlobalConfig`.
- **`tabs/admin.js`** — Admin tab: users CRUD, audit log, validation rules engine, quarantine table, session detail, theme editor, Central de Alertas (paginated `ProjectAlert` table with PEP/type/status filters).
- **`tabs/minha-area.js`** — Minha Área tab: user preferences, chart layout drag-to-reorder, personal upload history, personal quarantine view, budget alerts, Alertas sub-tab (ACL-filtered `ProjectAlert` list; hidden for admin users).
- **`tabs/header.js`** — `_updateHeaderUser`, `loadSemaphore` (macro traffic-light bar; clicking a pill drills to Portfolio), `_drillDownToPep`, `_refreshTabBadges`, `_initNotifications`.

### Ingestion Pipeline (`services/ingestion.py`)

`ingest_file()` is an orchestrator that calls six phase functions in sequence:

| Phase function | Responsibility |
|---|---|
| `_phase_load_and_validate(file_bytes, filename)` | Load CSV/XLSX with pandas, validate required columns exist → `DataFrame` |
| `_phase_authorize_peps(df, db, user_id, user_role)` | Filter rows to ACL-allowed PEPs for non-admin users |
| `_phase_prescan_dates(df, db)` | Pre-scan unique parseable dates; build cycle cache; auto-create quarantine cycles for dates with no active cycle |
| `_phase_validate_rows(df, db, rules, cycle_cache, collab_cache)` | Per-row structural checks (Q1/Q2/Q8) + `ValidationRule` engine; separates valid rows from quarantine buffer |
| `_phase_aggregate_rules(valid_rows, rules)` | Compute daily/weekly sums across valid rows; emit aggregate-rule warnings/infos |
| `_phase_upsert_records(db, valid_rows, extra_multiplier, standby_multiplier)` | Surgical `DELETE` by `(pep_wbs, cycle_id)` + bulk `INSERT` + cost freeze via `_lookup_rate` |

After the phases, `ingest_file()` persists `QuarantineRecord` rows, creates `UploadSession`, commits the transaction, and writes the `AuditLog` entry. The public signature and return dict are unchanged.

`_lookup_rate(db, collab, record_date)` freezes `cost_per_hour` at ingestion time by finding the `RateCard` matching the collaborator's seniority level and date range.

### Data Flow

1. **Upload:** `POST /api/upload-timesheet` → `ingest_file()` → `_lookup_rate()` freezes `cost_per_hour` → creates `Collaborator` + `Cycle` rows → inserts `TimesheetRecord` rows → records `UploadSession` + any `QuarantineRecord` rows → `notify_threshold_crossings()` + `notify_schedule_risk()` fire after every successful upload (create `Notification` and `ProjectAlert` rows as needed).
2. **Esforço da Equipe:** `/api/v2/effort?date_from=&date_to=` → `GROUP BY collaborator` → horizontal stacked/grouped bar chart + client-side CSV export.
3. **Saúde do Portfólio:** `/api/v2/portfolio?date_from=&date_to=` → `GROUP BY pep_wbs` → joined with `Project` → Treemap + Bullet Chart. Toggle Horas/R$ switches between `consumed_hours`/`budget_hours` and `actual_cost`/`budget_cost`.
4. **Tendências:** `/api/v2/trends?date_from=&date_to=` → `GROUP BY cycle` ordered by `start_date` (quarantine excluded) → Line chart (includes `actual_cost` per cycle).
5. **Previsão:** `/api/v2/forecast?pep_wbs=` (full EVM, render-ready) + `/api/projects/{id}/plans` baseline → per-cycle planned vs actual hours/cost → S-curve, burn-up, and EVM cards. What-If (`/simulate`) and Monte Carlo (`/monte-carlo`) panels layer scenario and probabilistic forecasts on top.

### Key Behaviors

- **PEP dual representation:** Each record stores `pep_wbs` (machine code) and `pep_description` (human label). Filters apply on either independently.
- **Quarantine cycles:** Dates outside any registered cycle auto-create a quarantine cycle — no data is silently dropped. Quarantine cycles are excluded from the Trends chart.
- **EVM freeze pattern:** `cost_per_hour` is resolved at ingestion time via `_lookup_rate()`. Rate changes after ingestion do NOT retroactively alter stored costs.
- **Velocity windows (averaging rules):** Three distinct rules govern how the system computes average hours/cost per cycle. They are intentionally different — do not standardize them without understanding the rationale:

  | Context | Window | File | Notes |
  |---------|--------|------|-------|
  | **Forecast** — projected completion + uncertainty band | last **3** cycles | `v2/forecast.py` | Reactive to recent rhythm; all cycles included in window |
  | **Runway** — avg/cycle column + cycles-to-complete | last **3** non-zero cycles | `v2/runway.py` | Zero-hour cycles excluded from denominator, kept in window |
  | **Simulate (What-If)** — `avg_velocity` baseline | last **min(6, N)** cycles | `v2/simulate.py` | Smoother base for scenario planning; zeros included |
  | **Monte Carlo** — Gaussian μ and σ | **all** cycles with h > 0 | `v2/monte_carlo.py` | Full history needed to model variance; windowing underestimates σ |
  | **Sparkline (frontend)** — avg3 reference line | last **3** non-zero cycles | `app.js` | Computed client-side from `fc.history`; aligns with Forecast |

  The UI tooltips (hover on "Média/ciclo", "Vel. histórica média", "Vel. média") document these rules in the glossary (`evm-glossary.js` keys `RunwayAvg`, `SimAvgVel`, `MCMeanVel`).
- **ValidationRule engine:** Ordered list of rules evaluated per row. Each rule has a `field`, `operator`, `value`, `action` (`quarantine`/`warn`/`reject`), and `is_active` flag. System rules cannot be deleted, only toggled.
- **UploadSession transparency:** Every upload creates an `UploadSession` (filename, uploader, timestamp, row counts by outcome). Accessible via `/api/upload-history` (admin) and `/api/my/upload-history` (own uploads only).
- **QuarantineRecord workflow:** Rows that fail validation land in quarantine with `status=pending`. Admin can approve (re-ingest) or reject. Users see their own quarantine rows via `/api/my/quarantine`.
- **Per-user ACL:** `UserProjectAccess` rows whitelist specific PEPs per user. Empty whitelist = access all. Enforced across every `/api/v2/*` analytics endpoint via the shared `_allowed_peps` helper (`v2/portfolio.py`), and in `/api/dashboard`.
- **Schema migration:** `_migrate_columns()` in `database.py` checks `PRAGMA table_info` and runs `ALTER TABLE` for new columns so production databases upgrade non-destructively.
- **ECharts management:** Charts are initialized only after their container is visible. `dispose()` is called when leaving a sub-tab. A single `ResizeObserver` on `<main>` handles all resize events.
- **Client-side CSV export:** "Exportar CSV" in Effort tab uses `_lastEffortData` cache, builds a CSV string, creates a `Blob` URL, and triggers download — no server round-trip. Seniority and rate card exports also use client-side cached arrays.
- **Budget alerts:** `_buildBudgetCell(p)` renders "Estourado" (≥100%) or "Atenção ≥90%" badges in the Projects table using `_consumedByPep` fetched in parallel with `/api/projects`.
- **Sticky analytics sub-nav:** `.analytics-tabs` uses `position: sticky; top: 3.25rem; z-index: 90` so the sub-tab menu floats below the fixed header when scrolling.
- **Semaphore classification:** Green = both `consumed/budget` ratios < 90%; Yellow = 90–99%; Red = ≥100%; Grey = no budget defined.
- **Expected CSV columns:** `Colaborador`, `Data`, `Horas totais (decimal)` (required); `Hora extra`, `Hora sobreaviso`, `Código PEP`, `PEP` (optional).

## Test Structure

| File | Tests | Coverage |
|---|---|---|
| `test_evm_service.py` | 104 | Pure-math unit tests for every function in `services/evm.py` (happy/boundary/None) |
| `test_full_sample.py` | 83 | End-to-end upload + analytics pipeline with full sample data |
| `test_ingestion.py` | 64 | CSV/XLSX parsing, quarantine, rule engine integration |
| `test_v2_endpoints.py` | 64 | All `/api/v2` analytics endpoints (filters, portfolio, effort, trends, forecast, allocation, concentration) |
| `test_ingestion_phases.py` | 44 | Unit tests per phase function (`_phase_load_and_validate`, `_phase_authorize_peps`, `_phase_prescan_dates`, `_phase_validate_rows`, `_phase_aggregate_rules`, `_phase_upsert_records`); includes regression tests for weekly alert deduplication |
| `test_ratecard.py` | 35 | SeniorityLevel, RateCard, team, rate lookup, EVM freeze |
| `test_rule_engine.py` | 32 | ValidationRule CRUD, toggle, reorder, per-row evaluation |
| `test_theme.py` | 30 | UI theme CRUD + theme presets |
| `test_projects.py` | 27 | CRUD de projetos + EVM fields (start/planned-end/completion dates, status) |
| `test_quarantine.py` | 23 | QuarantineRecord workflow (approve/reject/delete) |
| `test_runway_concentration.py` | 23 | `/api/v2/runway` + `/api/v2/concentration` (velocity window, SPI/CPI, top-1 risk) |
| `test_users.py` | 22 | User CRUD, password change, role enforcement |
| `test_evm_integrity.py` | 20 | EVM HTTP integration — render-ready responses, EV capped at BAC, CPI=EV/AC |
| `test_cycles.py` | 20 | CRUD de ciclos |
| `test_project_alerts.py` | 19 | `ProjectAlert` deduplication, auto-resolution, threshold triggers, admin endpoint filters, `GET /api/my/alerts` ACL |
| `test_notifications.py` | 15 | Bell-tray `Notification` CRUD, mark-read, mark-all-read, per-user visibility |
| `test_over_allocation.py` | 13 | `/api/v2/over-allocation` detection (filters, sort, CSV) |
| `test_upload_guards.py` | 11 | Upload rate-limiting and auth guards |
| `test_validation_rules.py` | 10 | ValidationRule API |
| `test_monte_carlo.py` | 8 | `/api/v2/.../monte-carlo` (P10/P50/P90, histogram, insufficient-data guard) |
| `test_simulate.py` | 7 | `/api/v2/.../simulate` What-If (velocity window, projected EAC, burn-up) |
| `test_golden_rules.py` | 7 | Golden rules enforcement: GR-3 no hardcoded hex, locale patterns, `crud/*.js` coverage |
| `test_summaries_status.py` | 6 | `PepCycleSummary` / `CollaboratorCycleSummary` staleness detection |
| `test_my.py` | 5 | `/api/my/*` per-user endpoints |
| `test_auth.py` | 5 | JWT login, token validation |
| `test_simulation.py` | 1 | End-to-end portfolio simulation smoke test on full sample data |
| **Total** | **698** | |

The `conftest.py` `clean_db` fixture wipes all rows **before** each test (setup phase, not teardown) so every test starts from a known empty state.

## Known Production Gaps

Audited items deliberately deferred. Do not implement without an explicit decision from the responsible party.

| # | Item | Where | What to do |
|---|---|---|---|
| P1 | `PMAS_SECRET_KEY` mandatory in production | `backend/app/deps.py:17-26` | If `PMAS_ENV=production` and the variable is not set, raise `RuntimeError` at startup instead of silently generating a random key |
| P2 | `/ready` liveness probe | `backend/app/main.py` | `GET /health` already returns `{"status":"ok","timestamp":...,"version":...}`. Add `GET /ready` that runs `SELECT 1` and returns 503 if the database is unreachable |
| P3 | Database backup script | `backup_pmas.sh` ✅ exists | Script implemented: `VACUUM INTO`, configurable paths via env vars, 30-day retention, restore procedure documented. Still needs a cron entry in production |
| P4 | Dependency lock file | `requirements-lock.txt` ✅ exists | Generated with `pip freeze`; use `pip install -r requirements-lock.txt` for reproducible deployments |
| P5 | systemd deployment unit | does not exist | `pmas.service` with `uvicorn --workers 2 --host 127.0.0.1`, `Restart=on-failure`, `EnvironmentFile=/opt/pmas/.env`, `PrivateTmp=true`; operating instructions (start/stop/logs/deploy new version) |

**Additional known risks** (non-blocking, but on record):
- HTTPS not enforced — the app must run behind a reverse proxy (nginx/caddy) with TLS; no internal redirect middleware
- Login brute force — `POST /api/token` is rate-limited at 30/minute but has no per-user lockout and no logging of authentication failures
- Rate limiting absent on write routes (`/projects`, `/cycles`, `/users`) beyond upload and login
- `must_change_password` enforced only in the frontend — no hard block in the backend
- Manual migrations (`_migrate_columns()`) with no versioning or rollback strategy
