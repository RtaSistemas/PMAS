# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PMAS** (Project Management Assistant System) is a timesheet management and analytics dashboard. Project managers upload CSV/XLSX timesheet exports and visualize employee work hours and costs. The system includes EVM financial tracking, a validation rule engine, quarantine workflow, baseline planning, per-user ACL, and full audit logging.

**Stack:** Python 3.11+ · FastAPI · SQLAlchemy · SQLite · Vanilla JS · Apache ECharts 5. The UI is fully in Portuguese (pt-BR).

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

406 tests across 15 test files. All use an in-memory SQLite database (StaticPool) — no `pmas.db` is touched.

## Sample Data

```bash
python amostras/generate_portfolio.py
```

Generates ready-to-import CSVs in `amostras/`: `ciclos.csv` (29 monthly cycles Jan/2024–Mai/2026), `projetos.csv` (10 PEPs with `60IT-XXX-01` codes), `rate_cards.csv`, and per-month timesheet CSVs in `amostras/timesheets/`.

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — Slim FastAPI app: CORS middleware, `include_router` for 16 router modules, static file mount, root redirect, startup hook (`init_db`).
- **`models.py`** — 15 SQLAlchemy ORM models:
  - `SeniorityLevel` — unique name, linked to RateCard and Collaborator
  - `RateCard` — hourly_rate with valid_from / valid_to date range per seniority level
  - `Collaborator` — unique name, optional `seniority_level_id` FK, linked to records
  - `Cycle` — billing period with `start_date`, `end_date`, `is_closed` and `is_active` flags
  - `TimesheetRecord` — core entity linking collaborator + cycle + PEP + 4 hour fields + `cost_per_hour` (frozen at ingestion via EVM freeze pattern)
  - `Project` — PEP registry with `budget_hours` and `budget_cost` for EVM tracking
  - `ProjectCyclePlan` — planned hours/cost per (project, cycle) for baseline S-curve
  - `User` — username, hashed_password, role (`admin`/`user`)
  - `GlobalConfig` — key/value store (logo path, UI theme overrides)
  - `AuditLog` — structured log: user, action, entity, old/new JSON snapshot
  - `UserProjectAccess` — per-user PEP whitelist (empty = access all)
  - `ValidationRule` — ordered, typed rules evaluated per row during ingestion
  - `UploadSession` — metadata record for each upload (filename, user, row counts, status)
  - `QuarantineRecord` — rows that failed validation, with review workflow (pending/approved/rejected)
  - `UserPreference` — per-user UI preferences (chart layout order, etc.)
- **`schemas.py`** — All Pydantic input/output models: `CycleIn/Out`, `ProjectIn/Out`, `SeniorityLevelIn/Out`, `RateCardIn/Out`, `CollaboratorSeniorityIn`, `ImportResultOut`, `UserCreateIn`, `UserOut`, `ValidationRuleIn/Out`, `QuarantineRecordOut`, `UploadSessionOut`, `AlertSummaryOut`, `UserPreferenceIn/Out`, `UIThemeIn/Out`, `ProjectCyclePlanIn/Out`, `ForecastOut`, and others.
- **`database.py`** — SQLite engine, `get_db()` dependency, `init_db()` (runs `create_all` + `_migrate_columns`). `_migrate_columns()` applies `ALTER TABLE` for columns added after the initial schema, upgrading existing `pmas.db` files safely on startup.
- **`services/ingestion.py`** — Parses CSV/XLSX with pandas. Multi-phase pipeline with a configurable validation rule engine.

### Backend Routers (`backend/app/routers/`)

| File | Prefix | Responsibility |
|---|---|---|
| `auth.py` | `/api` | `POST /token` — JWT login |
| `users.py` | `/api/users` | Admin CRUD for user accounts |
| `auditlog.py` | `/api` | `GET /audit-log` (admin) |
| `cycles.py` | `/api/cycles` | CRUD + CSV import/export for billing cycles |
| `projects.py` | `/api/projects` | CRUD + CSV import/export for projects/PEPs |
| `plans.py` | `/api/projects` | `/{id}/plans` CRUD, `GET /plans/export`, `POST /plans/import` — baseline S-curve |
| `dashboard.py` | `/api/dashboard` | Hour aggregation by collaborator; supports `date_from`/`date_to` |
| `reference.py` | `/api` | `/collaborators` and `/peps` for cascading filters |
| `analytics.py` | `/api` | `/portfolio-health` and `/trends` — includes `actual_cost`, `budget_cost`; supports `date_from`/`date_to` |
| `ratecard.py` | `/api` | `/seniority-levels`, `/rate-cards`, `/team`, `/team/{id}/seniority` — all with CSV import/export |
| `acl.py` | `/api/projects` | `/{id}/access` — per-user PEP whitelist management (admin) |
| `upload.py` | `/api` | `POST /upload-timesheet`, `GET /upload-history[/{id}]` |
| `quarantine.py` | `/api/quarantine` | List, review, approve, reject, delete quarantine records (admin) |
| `validation_rules.py` | `/api/validation-rules` | CRUD + toggle + reorder for the rule engine |
| `my.py` | `/api/my` | Per-user: preferences, upload history, quarantine view, budget alerts |
| `theme.py` | `/api/theme` | `GET/PUT` global UI theme, logo upload/delete |

### Frontend (`frontend/`)

- **`index.html`** — Six top-level tabs: **Dashboard**, **Ciclos**, **Projetos**, **Equipe**, **Minha Área**, **Admin** (hidden unless admin). Dashboard contains a shared filter card (date range + MultiSelect dropdowns) and three analytics sub-tabs (Esforço da Equipe, Saúde do Portfólio, Previsão). Admin tab has sections for users, validation rules, quarantine, upload history, and audit log.
- **`style.css`** — Dark slate/blue theme. Key selectors: analytics sub-tabs (sticky at `top: 3.25rem`), treemap legend, bullet chart thresholds, empty states, `.table-search-input`, budget alert badges (`.badge-budget.critical`/`.warning`), semaphore bar (`.semaphore-bar`, `.sem-dot`, `.sem-project` pill variants).
- **`multiselect.js`** — Self-contained `MultiSelect` component (cascading dropdowns for collaborator and PEP filters).
- **`app.js`** — All client logic:
  - **Auth:** JWT Bearer token stored in `sessionStorage`. `_getTokenPayload()` decodes it. `_isAdmin()` gates admin UI. `_bootApp()` is the central init called after login and on page load with a valid token.
  - **Header:** `_updateHeaderUser()` shows the logged-in username where "Gestão de Projetos" appears.
  - **Semaphore:** `loadSemaphore()` fetches `/api/portfolio-health` (no filters) and renders a macro traffic-light bar — green/yellow/red/grey per project, with dot + count summary and pill per project.
  - **ECharts lifecycle:** `CHARTS_PER_TAB` registry, `_disposeTabCharts()` on sub-tab leave, `_getOrCreateChart()` on enter, single `ResizeObserver` on `<main>` for responsiveness.
  - **Analytics sub-tabs:** `_renderEffortTab()`, `_renderPortfolioTab()`, `_renderForecastTab()`. Chart builders: effort bars, treemap (EVM-aware), bullet chart (EVM-aware), trends line, S-curve forecast.
  - **`_evmMode` boolean** — toggles Portfolio tab between hours and R$ views.
  - **`_lastEffortData` cache** — used for client-side CSV export from Effort tab.
  - **Cycles CRUD:** `_allCycles` cache, real-time search (`cycleSearch`), CSV import/export.
  - **Projects CRUD:** `_allProjects` + `_consumedByPep` cache, real-time search (`projectSearch`), `_buildBudgetCell()` for alert badges, CSV import/export.
  - **Equipe tab:** seniority levels CRUD + CSV import/export, rate cards CRUD + CSV import/export, collaborator seniority assignment.
  - **Minha Área tab:** user preferences (chart layout drag-to-reorder), personal upload history, personal quarantine view, budget alerts.
  - **Admin tab:** user management, validation rule engine (ordered list + toggle), global quarantine table, upload history, audit log.
  - **i18n / theme:** `_t()` translation lookup, `_applyI18n()`, `_loadTheme()`, lang toggle (pt-BR / en).

### Ingestion Pipeline (`services/ingestion.py`)

`ingest_file()` runs a multi-phase pipeline:

| Phase | Description |
|---|---|
| **0** | Load file with pandas, validate required columns exist |
| **0b** | Pre-scan all unique parseable dates; if any date has no active cycle, check whether to auto-create quarantine |
| **1** | Per-row structural checks: **Q8** (invalid collaborator name) → quarantine; **Q1** (unparseable date) → quarantine; **Q2** (future date) → quarantine; active cycle lookup; hours parsing |
| **2** | Per-row `ValidationRule` engine evaluation — configurable action (quarantine / warn / reject) |
| **N1** | Resolve new collaborators (auto-create `Collaborator` rows) |
| **3** | Aggregate rules — compute daily/weekly sums across rows |
| **4** | Surgical `DELETE` by `(pep_wbs, cycle_id)` + `INSERT` fresh `TimesheetRecord` rows |
| **5** | Persist `QuarantineRecord` rows, create `UploadSession`, commit transaction |
| **6** | Write `AuditLog` entry |

`_lookup_rate(db, collab, record_date)` freezes `cost_per_hour` at ingestion time by finding the `RateCard` matching the collaborator's seniority level and date range.

### Data Flow

1. **Upload:** `POST /api/upload-timesheet` → `ingest_file()` → `_lookup_rate()` freezes `cost_per_hour` → creates `Collaborator` + `Cycle` rows → inserts `TimesheetRecord` rows → records `UploadSession` + any `QuarantineRecord` rows.
2. **Esforço da Equipe:** `/api/dashboard[/{cycle_id}]?date_from=&date_to=` → `GROUP BY collaborator` → horizontal stacked/grouped bar chart + client-side CSV export.
3. **Saúde do Portfólio:** `/api/portfolio-health?date_from=&date_to=` → `GROUP BY pep_wbs` → joined with `Project` → Treemap + Bullet Chart. Toggle Horas/R$ switches between `consumed_hours`/`budget_hours` and `actual_cost`/`budget_cost`.
4. **Tendências:** `/api/trends?date_from=&date_to=` → `GROUP BY cycle` ordered by `start_date` (quarantine excluded) → Line chart (includes `actual_cost` per cycle).
5. **Previsão:** `/api/projects/{id}/plans` → per-cycle planned vs actual hours/cost → S-curve chart.

### Key Behaviors

- **PEP dual representation:** Each record stores `pep_wbs` (machine code) and `pep_description` (human label). Filters apply on either independently.
- **Quarantine cycles:** Dates outside any registered cycle auto-create a quarantine cycle — no data is silently dropped. Quarantine cycles are excluded from the Trends chart.
- **EVM freeze pattern:** `cost_per_hour` is resolved at ingestion time via `_lookup_rate()`. Rate changes after ingestion do NOT retroactively alter stored costs.
- **ValidationRule engine:** Ordered list of rules evaluated per row. Each rule has a `field`, `operator`, `value`, `action` (`quarantine`/`warn`/`reject`), and `is_active` flag. System rules cannot be deleted, only toggled.
- **UploadSession transparency:** Every upload creates an `UploadSession` (filename, uploader, timestamp, row counts by outcome). Accessible via `/api/upload-history` (admin) and `/api/my/upload-history` (own uploads only).
- **QuarantineRecord workflow:** Rows that fail validation land in quarantine with `status=pending`. Admin can approve (re-ingest) or reject. Users see their own quarantine rows via `/api/my/quarantine`.
- **Per-user ACL:** `UserProjectAccess` rows whitelist specific PEPs per user. Empty whitelist = access all. Enforced in `/api/portfolio-health` and `/api/dashboard`.
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
| `test_full_sample.py` | 108 | End-to-end upload + analytics pipeline |
| `test_ingestion.py` | 65 | CSV/XLSX parsing, quarantine, rule engine integration |
| `test_analytics.py` | 36 | portfolio-health, trends, EVM cost |
| `test_ratecard.py` | 35 | SeniorityLevel, RateCard, team, rate lookup, EVM freeze |
| `test_rule_engine.py` | 32 | ValidationRule CRUD, toggle, reorder, per-row evaluation |
| `test_quarantine.py` | 23 | QuarantineRecord workflow (approve/reject/delete) |
| `test_users.py` | 22 | User CRUD, password change, role enforcement |
| `test_cycles.py` | 20 | CRUD de ciclos |
| `test_projects.py` | 16 | CRUD de projetos |
| `test_reference.py` | 13 | `/collaborators` and `/peps` filter endpoints |
| `test_dashboard.py` | 11 | Hour aggregation, ACL filtering |
| `test_validation_rules.py` | 10 | ValidationRule API |
| `test_auth.py` | 5 | JWT login, token validation |
| `test_my.py` | 5 | `/api/my/*` per-user endpoints |
| `test_theme.py` | 5 | UI theme CRUD |
| **Total** | **406** | |

The `conftest.py` `clean_db` fixture wipes all rows **before** each test (setup phase, not teardown) so every test starts from a known empty state.
