# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PMAS** (Project Management Assistant System) is a timesheet management and analytics dashboard. Project managers upload CSV/XLSX timesheet exports and visualize employee work hours and costs through three analytics views: Team Effort, Portfolio Health, and Trends. The system includes a RateCard module for EVM financial tracking.

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

117 tests across 7 test files. All use an in-memory SQLite database (StaticPool) — no `pmas.db` is touched.

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — Slim FastAPI app: CORS middleware, `include_router` for 6 router modules, static file mount, root redirect, startup hook (`init_db`), and the upload endpoint.
- **`models.py`** — Six SQLAlchemy ORM models:
  - `SeniorityLevel` — unique name, linked to RateCard and Collaborator
  - `RateCard` — hourly_rate with valid_from / valid_to date range per seniority level
  - `Collaborator` — unique name, optional `seniority_level_id` FK, linked to records
  - `Cycle` — billing period with `start_date`, `end_date`, `is_quarantine` flag
  - `TimesheetRecord` — core entity linking collaborator + cycle + PEP + 4 hour fields + `cost_per_hour` (frozen at ingestion via EVM freeze pattern)
  - `Project` — PEP registry with `budget_hours` and `budget_cost` for EVM tracking
- **`schemas.py`** — Pydantic input models: `CycleIn`, `ProjectIn`, `SeniorityLevelIn`, `RateCardIn`, `CollaboratorSeniorityIn`.
- **`database.py`** — SQLite engine, `get_db()` dependency, `init_db()` (runs `create_all` + `_migrate_columns`). `_migrate_columns()` applies `ALTER TABLE` for columns added after the initial schema, upgrading existing `pmas.db` files safely on startup.
- **`services/ingestion.py`** — Parses CSV/XLSX with pandas. Auto-creates `Collaborator` and `Cycle` records. Creates quarantine cycles for dates outside any registered cycle. Deduplicates in-batch and across calls. Uses `_lookup_rate()` to freeze `cost_per_hour` at ingestion time (EVM pattern).

### Backend Routers (`backend/app/routers/`)

| File | Prefix | Responsibility |
|---|---|---|
| `cycles.py` | `/api/cycles` | CRUD for billing cycles |
| `projects.py` | `/api/projects` | CRUD for projects/PEPs (includes `budget_cost`) |
| `dashboard.py` | `/api/dashboard` | Hour aggregation by collaborator; supports `date_from`/`date_to` |
| `reference.py` | `/api` | `/collaborators` and `/peps` for cascading filters |
| `analytics.py` | `/api` | `/portfolio-health` and `/trends` — includes `actual_cost`, `budget_cost`; supports `date_from`/`date_to` |
| `ratecard.py` | `/api` | `/seniority-levels`, `/rate-cards`, `/team`, `/team/{id}/seniority` |

### Frontend (`frontend/`)

- **`index.html`** — Four top-level tabs (Dashboard, Ciclos, Projetos, Equipe). Dashboard contains a shared filter card (with date range inputs) and three analytics sub-tabs.
- **`style.css`** — Dark slate/blue theme. Includes styles for analytics sub-tabs, treemap legend, bullet chart thresholds, empty states, table search input (`.table-search-input`), and budget alert badges (`.badge-budget.critical`, `.badge-budget.warning`).
- **`multiselect.js`** — Self-contained `MultiSelect` component (cascading dropdowns).
- **`app.js`** — All client logic:
  - ECharts instance registry with `dispose()` on sub-tab switch and `ResizeObserver` for responsiveness
  - Three render functions: `_renderEffortTab()`, `_renderPortfolioTab()`, `_renderTrendsTab()`
  - Chart option builders: effort bars, budget comparison, treemap (EVM-aware), bullet chart (EVM-aware), trends line
  - `_evmMode` boolean — toggles Portfolio tab between hours and R$ views
  - `_lastEffortData` cache — used for client-side CSV export
  - Cycles CRUD with `_allCycles` cache and real-time search (`cycleSearch`)
  - Projects CRUD with `_allProjects` + `_consumedByPep` cache, real-time search (`projectSearch`), and `_buildBudgetCell()` for alert badges
  - Equipe tab: seniority levels CRUD, rate cards CRUD, collaborator seniority assignment
  - Upload and filter cascade logic

### Data Flow

1. **Upload:** `POST /api/upload-timesheet` → `ingest_file()` → `_lookup_rate()` freezes `cost_per_hour` → creates `Collaborator` + `Cycle` rows → inserts `TimesheetRecord` rows.
2. **Esforço da Equipe:** `/api/dashboard[/{cycle_id}]?date_from=&date_to=` → `GROUP BY collaborator` → horizontal stacked/grouped bar chart + CSV export.
3. **Saúde do Portfólio:** `/api/portfolio-health?date_from=&date_to=` → `GROUP BY pep_wbs` → joined with `Project` → Treemap + Bullet Chart. Toggle Horas/R$ switches between `consumed_hours`/`budget_hours` and `actual_cost`/`budget_cost`.
4. **Tendências:** `/api/trends?date_from=&date_to=` → `GROUP BY cycle` ordered by `start_date` (quarantine excluded) → Line chart (includes `actual_cost` per cycle).

### Key Behaviors

- **PEP dual representation:** Each record stores `pep_wbs` (machine code) and `pep_description` (human label). Filters apply on either independently.
- **Quarantine cycles:** Dates outside any registered cycle auto-create a quarantine cycle — no data is silently dropped. Quarantine cycles are excluded from the Trends chart.
- **EVM freeze pattern:** `cost_per_hour` is resolved at ingestion time via `_lookup_rate(db, collab, record_date)` — looks up `RateCard` matching collaborator's seniority level and record date. Rate changes after ingestion do NOT retroactively alter stored costs.
- **Schema migration:** `_migrate_columns()` in `database.py` checks `PRAGMA table_info` and runs `ALTER TABLE` for new columns (`cost_per_hour` on `timesheet_record`, `seniority_level_id` on `collaborator`, `budget_cost` on `project`) so production databases upgrade non-destructively.
- **ECharts management:** Charts are initialized only after their container is visible. `dispose()` is called when leaving a sub-tab. A single `ResizeObserver` on `<main>` handles all resize events.
- **Client-side CSV export:** "Exportar CSV" button in Effort tab uses `_lastEffortData` cache, builds a CSV string, creates a `Blob` URL, and triggers download — no server round-trip.
- **Budget alerts:** Projects table calls `/api/portfolio-health` in parallel with `/api/projects` to build `_consumedByPep`. `_buildBudgetCell(p)` renders "Estourado" (≥100%) or "Atenção ≥90%" badges inline.
- **Expected CSV columns:** `Colaborador`, `Data`, `Horas totais (decimal)` (required); `Hora extra`, `Hora sobreaviso`, `Código PEP`, `PEP` (optional).

## Test Structure

| File | Tests | Coverage |
|---|---|---|
| `test_cycles.py` | 16 | CRUD de ciclos |
| `test_projects.py` | 15 | CRUD de projetos |
| `test_dashboard.py` | 9 | Agregação do dashboard |
| `test_ingestion.py` | 18 | Ingestão CSV/XLSX |
| `test_reference.py` | 12 | Endpoints de referência |
| `test_analytics.py` | 16 | portfolio-health e trends |
| `test_ratecard.py` | 26 | SeniorityLevel, RateCard, team, rate lookup, EVM freeze |
| **Total** | **117** | |

The `conftest.py` `clean_db` fixture wipes all rows **before** each test (setup phase, not teardown) so every test starts from a known empty state.
