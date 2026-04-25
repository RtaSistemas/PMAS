# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PMAS** (Project Management Assistant System) is a timesheet management and analytics dashboard. Project managers upload CSV/XLSX timesheet exports and visualize employee work hours through three analytics views: Team Effort, Portfolio Health, and Trends.

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

91 tests across 6 test files. All use an in-memory SQLite database (StaticPool) — no `pmas.db` is touched.

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — Slim FastAPI app (~80 lines): CORS middleware, `include_router` for the 5 router modules, static file mount, root redirect, startup hook (`init_db`), and the upload endpoint.
- **`models.py`** — Four SQLAlchemy ORM models:
  - `Collaborator` — unique name, linked to records
  - `Cycle` — billing period with `start_date`, `end_date`, `is_quarantine` flag
  - `TimesheetRecord` — core entity linking collaborator + cycle + PEP + 4 hour fields (`normal_hours`, `extra_hours`, `standby_hours`, `cost_per_hour`)
  - `Project` — PEP registry with `budget_hours` for EVM tracking
- **`schemas.py`** — Pydantic input models: `CycleIn`, `ProjectIn`.
- **`database.py`** — SQLite engine, `get_db()` dependency, `init_db()` (runs `create_all` + `_migrate_columns`). `_migrate_columns()` applies `ALTER TABLE` for columns added after the initial schema, so existing `pmas.db` files are upgraded safely on startup.
- **`services/ingestion.py`** — Parses CSV/XLSX with pandas. Auto-creates `Collaborator` and `Cycle` records. Creates quarantine cycles for dates outside any registered cycle. Deduplicates in-batch and across calls.

### Backend Routers (`backend/app/routers/`)

| File | Prefix | Responsibility |
|---|---|---|
| `cycles.py` | `/api/cycles` | CRUD for billing cycles |
| `projects.py` | `/api/projects` | CRUD for projects/PEPs |
| `dashboard.py` | `/api/dashboard` | Hour aggregation by collaborator |
| `reference.py` | `/api` | `/collaborators` and `/peps` for cascading filters |
| `analytics.py` | `/api` | `/portfolio-health` and `/trends` for analytics tabs |

### Frontend (`frontend/`)

- **`index.html`** — Three top-level tabs (Dashboard, Ciclos, Projetos). Dashboard contains a shared filter card and three analytics sub-tabs.
- **`style.css`** — Dark slate/blue theme. Includes styles for analytics sub-tabs, treemap legend, bullet chart thresholds, and empty states.
- **`multiselect.js`** — Self-contained `MultiSelect` component (cascading dropdowns).
- **`app.js`** — All client logic:
  - ECharts instance registry with `dispose()` on sub-tab switch and `ResizeObserver` for responsiveness
  - Three render functions: `_renderEffortTab()`, `_renderPortfolioTab()`, `_renderTrendsTab()`
  - Chart option builders: effort bars, budget comparison, treemap, bullet chart, trends line
  - Cycles and Projects CRUD (modals)
  - Upload and filter cascade logic

### Data Flow

1. **Upload:** `POST /api/upload-timesheet` → `ingest_file()` → creates `Collaborator` + `Cycle` rows → inserts `TimesheetRecord` rows.
2. **Esforço da Equipe:** `/api/dashboard[/{cycle_id}]` → `GROUP BY collaborator` → horizontal stacked/grouped bar chart.
3. **Saúde do Portfólio:** `/api/portfolio-health` → `GROUP BY pep_wbs` → joined with `Project` → Treemap + Bullet Chart.
4. **Tendências:** `/api/trends` → `GROUP BY cycle` ordered by `start_date` (quarantine excluded) → Line chart.

### Key Behaviors

- **PEP dual representation:** Each record stores `pep_wbs` (machine code) and `pep_description` (human label). Filters apply on either independently.
- **Quarantine cycles:** Dates outside any registered cycle auto-create a quarantine cycle — no data is silently dropped. Quarantine cycles are excluded from the Trends chart.
- **`cost_per_hour` placeholder:** Set to `0.0` on ingestion. Reserved for a future RateCard module that will freeze hourly costs at ingestion time for EVM financial tracking.
- **Schema migration:** `_migrate_columns()` in `database.py` checks `PRAGMA table_info` and runs `ALTER TABLE` for any new columns so that production databases are upgraded non-destructively.
- **ECharts management:** Charts are initialized only after their container is visible. `dispose()` is called when leaving a sub-tab. A single `ResizeObserver` on `<main>` handles all resize events.
- **Expected CSV columns:** `Colaborador`, `Data`, `Horas totais (decimal)` (required); `Hora extra`, `Hora sobreaviso`, `Código PEP`, `PEP` (optional).
