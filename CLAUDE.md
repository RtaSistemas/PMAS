# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PMAS** (Project Management Assistant System) is a timesheet management and analytics dashboard. It allows project managers to upload CSV/XLSX timesheet exports and visualize employee work hours aggregated by project codes (PEPs/WBS).

**Stack:** Python 3 + FastAPI backend, Vanilla JS + Apache ECharts frontend, SQLite database. The UI is fully in Portuguese (pt-BR).

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Start the dev server (http://127.0.0.1:8000)
python -m uvicorn backend.app.main:app --reload
```

Access the app at `http://127.0.0.1:8000/frontend/index.html`. There is no build step — the frontend is plain HTML + JS.

No test suite or linting configuration exists in this project.

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app with all route definitions. Handles CORS for localhost, mounts static frontend files, and exposes the REST API under `/api/`.
- **`models.py`** — Three SQLAlchemy ORM models: `Collaborator`, `Cycle`, and `TimesheetRecord`. `TimesheetRecord` is the core entity linking collaborators, billing cycles, and PEP codes with three hour types (`normal_hours`, `extra_hours`, `standby_hours`).
- **`database.py`** — SQLite configuration (`pmas.db` in the project root). Uses `get_db()` as a FastAPI dependency for session injection. DB is auto-initialized on startup via `init_db()`.
- **`services/ingestion.py`** — Parses uploaded CSV/XLSX files using pandas. Dynamically creates `Collaborator` and `Cycle` records as needed. Creates "Quarantine" cycles for dates that fall outside any registered cycle (preserving all data).

### Frontend (`frontend/`)

- **`app.js`** — All client logic. Fetches data from `http://127.0.0.1:8000` (hardcoded). Implements cascading dropdowns (cycle → PEP code → PEP description → collaborator) with in-memory caching of PEP data. Renders an ECharts horizontal stacked bar chart (capped at 40 collaborators).
- **`index.html`** — Static HTML with embedded CSS. Dark theme using a slate/blue palette.

### Data Flow

1. User uploads a CSV/XLSX → `POST /api/upload-timesheet` → `ingest_file()` parses with pandas → creates/finds `Collaborator` + `Cycle` rows → inserts `TimesheetRecord` rows.
2. On dashboard load, the browser calls `/api/dashboard/{cycle_id}` (with optional filters) → SQL GROUP BY aggregates hours per collaborator/PEP → browser renders the chart.

### Key Behaviors

- **PEP dual representation:** Each record stores both `pep_wbs` (machine code, e.g. `60OP-03333`) and `pep_description` (human label, e.g. `COPEL-D | OMS`). Filters can be applied on either independently.
- **Quarantine cycles:** When ingested dates fall outside any existing cycle, a quarantine cycle is auto-created for that month so no data is silently dropped.
- **Expected CSV columns:** `Colaborador`, `Data`, `Horas totais (decimal)` (required); `Hora extra`, `Hora sobreaviso`, `Código PEP`, `PEP` (optional).
