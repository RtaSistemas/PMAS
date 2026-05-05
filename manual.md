# PMAS — Technical Software Manual

---

## 1. System Overview

**PMAS** (Project Management Assistant System) is a timesheet ingestion, cost tracking, and EVM analytics platform for project managers.

### Architecture

```
┌─────────────────────────────────────────────┐
│  Browser (Vanilla JS + Apache ECharts 5)    │
│  Single-page, 5 tabs, sessionStorage JWT    │
└────────────────┬────────────────────────────┘
                 │ HTTP / REST (Bearer token)
┌────────────────▼────────────────────────────┐
│  FastAPI  (Python 3.11+)                    │
│  11 routers · Pydantic v2 · python-jose JWT │
└────────────────┬────────────────────────────┘
                 │ SQLAlchemy ORM
┌────────────────▼────────────────────────────┐
│  SQLite (WAL mode, synchronous=NORMAL)      │
│  pmas.db — schema-migrated on startup       │
└─────────────────────────────────────────────┘
```

### Core Components

| Component | Location | Responsibility |
|---|---|---|
| Ingestion service | `services/ingestion.py` | Parse CSV/XLSX, resolve cycles, freeze `cost_per_hour` |
| Auth | `routers/auth.py` + `deps.py` | JWT HS256, 8h expiry, bcrypt |
| Dashboard | `routers/dashboard.py` | Hour aggregation, budget vs actual, PEP radar, collaborator timeline |
| Analytics | `routers/analytics.py` | Portfolio health, trends (CPI), allocation matrix, EVM forecast |
| Plans | `routers/plans.py` | Baseline planning: `ProjectCyclePlan` CRUD and CSV import/export |
| ACL | `routers/acl.py` | Delegated project upload permissions (`UserProjectAccess`) |
| RateCard | `routers/ratecard.py` | Seniority levels, rate cards, team, global config (multipliers + anomaly threshold) |
| Audit | `audit.py` + `routers/auditlog.py` | Append-only audit trail, all write endpoints |
| DB init | `database.py` → `init_db()` | `create_all` + `_migrate_columns()` + seed admin/config |

---

## 2. Business Rules

### Authentication & Authorization
- JWT HS256, 8-hour expiry; `PMAS_SECRET_KEY` env var (random ephemeral key if unset — logs warning)
- Two roles: `admin`, `user`. All API routes require auth; admin-only routes use `AdminUser` dependency
- `access_token` stored in `sessionStorage` (XSS mitigation)
- Default seed user: `admin / admin` (created only when `user` table is empty — change immediately)

### Cycles
- Non-quarantine cycles must not have overlapping date ranges
- `is_closed` cycles block non-admin timesheet uploads (raises `ClosedCycleError` → HTTP 403)
- Dates outside all registered cycles auto-create a quarantine cycle (month-scoped); quarantine cycles excluded from Trends and Forecast charts
- Cycles with records cannot be deleted
- `is_active = false` marks a cycle as inactive (cosmetic flag, does not block ingestion)

### Projects
- `pep_wbs` is a unique business key
- `status ∈ {ativo, suspenso, encerrado}`; ingestion into `suspenso`/`encerrado` projects is blocked (raises `LockedProjectError` → HTTP 422)
- `budget_hours` and `budget_cost` are optional; used for EVM metrics
- `manager_id` links the project to a `User` (auto-grants upload access for that user)
- `manager` is a free-text legacy field (kept alongside `manager_id`)

### Upload Authorization (PEP-level ACL)
- Admin users: unrestricted — all PEP codes accepted
- Non-admin users: upload is accepted only for PEPs where the user is the registered `manager_id` **or** has an explicit `UserProjectAccess` grant
- Rows for unauthorized PEPs are silently discarded before ingestion with a warning returned in `UploadOut.warnings`

### Rate Cards
- Each rate card is scoped to a `SeniorityLevel` + date range (`valid_from` / `valid_to`)
- `valid_to = NULL` means open-ended (current)
- Overlapping date ranges for the same seniority level are rejected (HTTP 409)
- `SeniorityLevel` with assigned collaborators cannot be deleted

### EVM / Cost Freeze Pattern
- `cost_per_hour` is resolved at ingestion time via `_lookup_rate()` and stored on `TimesheetRecord`
- Subsequent rate changes do **not** retroactively alter stored records
- `actual_cost = Σ cost_per_hour × (normal_h + extra_h × extra_multiplier + standby_h × standby_multiplier)`
- Global multipliers: `extra_hours_multiplier` (default 1.5), `standby_hours_multiplier` (default 1.0); singleton `GlobalConfig(id=1)`
- `anomaly_max_daily_hours` (default 24.0): threshold for the anomaly detector — configurable by admin

### EVM Formulas
- `EV = (consumed_hours / budget_hours) × budget_cost`
- `CPI = EV / actual_cost`
- `EAC = budget_cost / CPI`
- `PV = (cumulative_planned_hours / budget_hours) × budget_cost`
- `SPI = EV / PV` (requires baseline planned hours per cycle)
- `SV = EV − PV`
- `avg_hours_per_cycle` = mean of the last 3 historical cycles for the PEP
- `estimated_cycles_to_complete = remaining_hours / avg_hours_per_cycle`

### Ingestion Deduplication
- **Layer 1 (auth filter):** rows for unauthorized PEPs are dropped before any write
- **Layer 2 (RBAC):** non-admins cannot write to closed cycles → 403
- **Layer 3 (surgical DELETE):** unit of replacement is `(pep_wbs, cycle_id)` — all existing records for that PEP+cycle block are deleted before inserting the new file's rows. For null-pep rows the scope is `(collaborator_id, cycle_id, pep_wbs IS NULL)`. This means uploading PEP-A never touches PEP-B rows in the same cycle.
- **Intra-batch dedup key:** `(collaborator_id, cycle_id, record_date, pep_wbs, pep_description, hour_type, start_time)`

### Anomaly Detection
After each successful ingestion, `_detect_anomalies()` checks for:
1. Records on weekends
2. Collaborators with total daily hours exceeding `anomaly_max_daily_hours`
3. PEP codes with no matching `Project` row

Warnings are returned in `UploadOut.warnings` and each one is also logged as a separate `AuditLog` row with `action="anomaly"`.

### Audit Log
- Every write operation appends an `AuditLog` row via `log_audit()` before the caller's `db.commit()`
- `username` is denormalized at write time; `user_id` FK has `ON DELETE SET NULL`
- Known `action` values: `create`, `update`, `delete`, `import`, `anomaly`, `grant_access`, `revoke_access`
- Readable only by admin via `GET /api/audit-log`

---

## 3. System Flows

### Authentication Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as FastAPI
    participant DB as SQLite

    B->>A: POST /api/token {username, password}
    A->>DB: SELECT user WHERE username=?
    DB-->>A: User row
    A->>A: bcrypt.verify(password, hashed)
    alt valid
        A-->>B: {access_token, token_type}
        B->>B: sessionStorage.setItem('access_token', ...)
    else invalid
        A-->>B: 401 Unauthorized
    end
```

### Timesheet Ingestion Flow

```mermaid
flowchart TD
    U[Upload CSV/XLSX] --> LD[Load DataFrame\npandas]
    LD --> V{Required cols?}
    V -- missing --> E1[422 Error]
    V -- ok --> AF[Auth filter\nnon-admin: drop unauthorized PEP rows]
    AF --> P1[Pass 1: resolve\nCollaborator + Cycle rows]
    P1 --> QC{Date in cycle?}
    QC -- no --> QQ[Create quarantine cycle]
    QC -- yes --> RBAC{user role?}
    QQ --> RBAC
    RBAC -- non-admin + closed cycle --> E2[403 ClosedCycleError]
    RBAC -- ok --> PL{PEP status check}
    PL -- encerrado/suspenso --> E3[422 LockedProjectError]
    PL -- ok --> DEL[DELETE existing records\nfor affected pep_wbs×cycle blocks]
    DEL --> INS[INSERT TimesheetRecord rows\nwith frozen cost_per_hour]
    INS --> AUD[log_audit import + anomaly entries\ndb.commit]
    AUD --> R[UploadOut response]
```

### Rate Lookup at Ingestion

```mermaid
flowchart LR
    C[Collaborator] --> SL{seniority_level_id?}
    SL -- null --> Z[cost_per_hour = 0.0]
    SL -- set --> Q[SELECT RateCard\nWHERE seniority_level_id=?\nAND valid_from <= record_date\nAND valid_to IS NULL OR valid_to >= record_date\nORDER BY valid_from DESC LIMIT 1]
    Q -- found --> R[hourly_rate]
    Q -- not found --> Z
```

### Analytics Data Flow

```mermaid
flowchart LR
    TR[(TimesheetRecord)] --> PH[portfolio-health\nGROUP BY pep_wbs]
    TR --> TRD[trends\nGROUP BY cycle ordered by start_date\nno quarantine]
    TR --> AL[allocation\nGROUP BY collaborator × pep_wbs]
    TR --> FC[forecast\nGROUP BY cycle for pep_wbs\ncumulative burn + EVM]
    PH --> PRJ[(Project)]
    FC --> PRJ
    FC --> PCP[(ProjectCyclePlan)]
    PH --> FE[Frontend\nTreemap + Bullet chart]
    TRD --> FE2[Frontend\nLine chart + CPI]
    AL --> FE3[Frontend\nHeatmap matrix]
    FC --> FE4[Frontend\nS-curve + KPI cards]
```

### Audit Write Pattern

```mermaid
sequenceDiagram
    participant H as Handler
    participant DB as Session
    participant AL as AuditLog table

    H->>DB: db.flush()  # stage main entity
    H->>DB: log_audit(db, user, action, entity, entity_id, detail)
    note over DB: db.add(AuditLog(...)) — not committed yet
    H->>DB: db.commit()  # atomically writes both
    DB-->>AL: INSERT audit_log row
```

---

## 4. Data Models / Structures

### Entity Relationship

```mermaid
erDiagram
    SeniorityLevel ||--o{ RateCard : "has"
    SeniorityLevel ||--o{ Collaborator : "assigned to"
    Collaborator ||--o{ TimesheetRecord : "creates"
    Cycle ||--o{ TimesheetRecord : "scopes"
    Cycle ||--o{ ProjectCyclePlan : "scopes"
    Project }o--o{ TimesheetRecord : "referenced by pep_wbs"
    Project ||--o{ ProjectCyclePlan : "has baseline"
    Project ||--o{ UserProjectAccess : "grants"
    User ||--o{ AuditLog : "generates (SET NULL on delete)"
    User ||--o{ Project : "manages (manager_id)"
    User ||--o{ UserProjectAccess : "receives"
```

### Tables

**`seniority_level`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| name | VARCHAR | UNIQUE NOT NULL |

**`rate_card`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| seniority_level_id | INTEGER | FK → seniority_level, NOT NULL |
| hourly_rate | FLOAT | NOT NULL |
| valid_from | DATE | NOT NULL |
| valid_to | DATE | NULL = open-ended |

**`collaborator`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| name | VARCHAR | UNIQUE NOT NULL INDEX |
| seniority_level_id | INTEGER | FK → seniority_level, NULL |

**`cycle`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| name | VARCHAR | NOT NULL |
| start_date | DATE | NOT NULL |
| end_date | DATE | NOT NULL |
| is_quarantine | BOOLEAN | NOT NULL DEFAULT false |
| is_closed | BOOLEAN | NOT NULL DEFAULT false |
| is_active | BOOLEAN | NOT NULL DEFAULT true |

**`timesheet_record`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| collaborator_id | INTEGER | FK NOT NULL |
| cycle_id | INTEGER | FK NOT NULL |
| record_date | DATE | NOT NULL |
| pep_wbs | VARCHAR | INDEX, NULL |
| pep_description | VARCHAR | INDEX, NULL |
| normal_hours | FLOAT | NOT NULL DEFAULT 0 |
| extra_hours | FLOAT | NOT NULL DEFAULT 0 |
| standby_hours | FLOAT | NOT NULL DEFAULT 0 |
| cost_per_hour | FLOAT | NOT NULL DEFAULT 0 — frozen at ingestion |

Composite index: `(cycle_id, collaborator_id)`

**`project`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| pep_wbs | VARCHAR | UNIQUE NOT NULL INDEX |
| name | VARCHAR | NULL |
| client | VARCHAR | NULL |
| manager | VARCHAR | NULL (free-text, legacy) |
| manager_id | INTEGER | FK → user ON DELETE SET NULL, NULL |
| budget_hours | FLOAT | NULL |
| budget_cost | FLOAT | NULL |
| status | VARCHAR | NOT NULL DEFAULT 'ativo' ∈ {ativo,suspenso,encerrado} |

**`project_cycle_plan`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| project_id | INTEGER | FK → project ON DELETE CASCADE, NOT NULL |
| cycle_id | INTEGER | FK → cycle ON DELETE CASCADE, NOT NULL |
| planned_hours | FLOAT | NOT NULL |

Unique index: `(project_id, cycle_id)`

**`user`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| username | VARCHAR | UNIQUE NOT NULL INDEX |
| hashed_password | VARCHAR | NOT NULL (bcrypt) |
| role | VARCHAR | NOT NULL DEFAULT 'user' ∈ {admin,user} |

**`user_project_access`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| user_id | INTEGER | FK → user ON DELETE CASCADE, NOT NULL |
| project_id | INTEGER | FK → project ON DELETE CASCADE, NOT NULL |

Unique index: `(user_id, project_id)`

**`global_config`** (singleton id=1)

| Column | Type | Default |
|---|---|---|
| extra_hours_multiplier | FLOAT | 1.5 |
| standby_hours_multiplier | FLOAT | 1.0 |
| anomaly_max_daily_hours | FLOAT | 24.0 |

**`audit_log`**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK |
| user_id | INTEGER | FK → user ON DELETE SET NULL, NULL |
| username | VARCHAR | denormalized, NULL |
| action | VARCHAR | NOT NULL |
| entity | VARCHAR | NOT NULL INDEX |
| entity_id | INTEGER | NULL |
| detail | VARCHAR | NULL, JSON string |
| timestamp | DATETIME | NOT NULL (UTC) |

---

## 5. Tech Stack & Setup

### Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | HTTP framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM + schema management |
| `pydantic` v2 | Request/response validation |
| `python-jose[cryptography]` | JWT encode/decode |
| `bcrypt` | Password hashing |
| `pandas` | CSV/XLSX parsing |
| `openpyxl` | XLSX support for pandas |

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PMAS_SECRET_KEY` | Recommended | JWT signing key (hex string). If unset, random key generated per process — sessions invalidated on restart |

### Setup

```bash
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload
# App: http://127.0.0.1:8000
# Swagger: http://127.0.0.1:8000/docs
```

- Database: `pmas.db` created at project root (dev) or adjacent to executable (frozen)
- `init_db()` runs on startup: `create_all` → `_migrate_columns()` → seed `admin/admin` user → seed `GlobalConfig`
- `_migrate_columns()` applies `ALTER TABLE` for: `cost_per_hour` (timesheet_record), `seniority_level_id` (collaborator), `budget_cost` + `manager_id` (project), `is_closed` + `is_active` (cycle), `anomaly_max_daily_hours` (global_config) — safe to run on existing databases

### Test

```bash
pip install pytest httpx
pytest tests/ -v        # 294 tests, in-memory SQLite StaticPool
```

---

## 6. Core Modules / API

### Endpoints Reference

#### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/token` | None | Login; returns `{access_token}` (OAuth2 form) |

#### Upload
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/upload-timesheet` | user | Ingest CSV/XLSX ≤20MB; returns `UploadOut` |

#### Cycles `/api/cycles`
| Method | Path | Auth | Body/Params |
|---|---|---|---|
| GET | `` | user | — → `list[CycleOut]` |
| POST | `` | user | `CycleIn` → `CycleOut 201` |
| PUT | `/{cycle_id}` | user | `CycleIn` → `CycleOut` |
| PATCH | `/{cycle_id}/toggle-status` | **admin** | — → `CycleOut` |
| POST | `/import` | user | CSV file → `ImportResultOut` |
| DELETE | `/{cycle_id}` | user | 204; 409 if records exist |

#### Projects `/api/projects`
| Method | Path | Auth | Body/Params |
|---|---|---|---|
| GET | `` | user | — → `list[ProjectOut]` |
| POST | `` | user | `ProjectIn` → `ProjectOut 201` |
| PUT | `/{project_id}` | user | `ProjectIn` → `ProjectOut` |
| POST | `/import` | user | CSV → `ImportResultOut` |
| DELETE | `/{project_id}` | user | 204 |

#### Project Plans `/api/projects` (plans router)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/{project_id}/plans` | user | List baseline plans for a project |
| PUT | `/{project_id}/plans/{cycle_id}` | user | Upsert planned hours for a cycle |
| DELETE | `/{project_id}/plans/{cycle_id}` | user | Delete a plan entry |
| GET | `/{project_id}/plans/export` | user | Download baseline as CSV |
| POST | `/plans/import` | user | Bulk import baseline from CSV (`pep_wbs`, `cycle_name`, `planned_hours`) |

#### Project ACL `/api/projects` (acl router)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/{project_id}/access` | user | List users with explicit upload access |
| POST | `/{project_id}/access` | **admin** | Grant access (`{user_id}`) → `UserProjectAccessOut 201` |
| DELETE | `/{project_id}/access/{user_id}` | **admin** | Revoke access; 204 |

#### Dashboard `/api/dashboard`
| Method | Path | Query params |
|---|---|---|
| GET | `` | `pep_wbs[]`, `pep_description[]`, `collaborator_id[]`, `date_from`, `date_to` |
| GET | `/{cycle_id}` | same + cycle scoped |
| GET | `/pep-radar` | `cycle_id[]`, `pep_wbs[]`, `pep_description[]`, `collaborator_id[]`, `date_from`, `date_to` → top-12 PEPs by hours |
| GET | `/collaborator-timeline` | `collaborator_name` + filters → hours per cycle |

#### Reference `/api`
| Method | Path | Query params |
|---|---|---|
| GET | `/collaborators` | `cycle_id`, `pep_code`, `pep_description` |
| GET | `/peps` | `cycle_id`, `collaborator_id` |

#### Analytics `/api`
| Method | Path | Query params | Notes |
|---|---|---|---|
| GET | `/portfolio-health` | `cycle_id[]`, `pep_wbs[]`, `pep_description[]`, `collaborator_id[]`, `date_from`, `date_to` | Joined with `Project`; includes `actual_cost`, sorted by `consumed_hours` desc |
| GET | `/trends` | `pep_wbs[]`, `pep_description[]`, `collaborator_id[]`, `date_from`, `date_to` | Chronological by cycle; quarantine excluded; includes `actual_cost` and per-cycle `cpi` |
| GET | `/allocation` | `cycle_id[]`, `collaborator_id[]`, `pep_wbs[]`, `pep_description[]`, `date_from`, `date_to` | Collaborator × PEP matrix |
| GET | `/forecast` | `pep_wbs` (required), `date_from`, `date_to` | EVM: CPI, EAC, SPI, SV, burn history, projected completion cycle |

#### RateCard `/api`
| Method | Path | Auth |
|---|---|---|
| GET/POST | `/seniority-levels` | user |
| PUT/DELETE | `/seniority-levels/{level_id}` | user |
| GET/POST | `/rate-cards` | user |
| PUT/DELETE | `/rate-cards/{card_id}` | user |
| GET | `/team` | user |
| PUT | `/team/bulk-seniority` | **admin** |
| PUT | `/team/{collab_id}/seniority` | user |
| GET/PUT | `/config` | GET: user, PUT: **admin** |

#### Users `/api/users`
| Method | Path | Auth |
|---|---|---|
| GET | `` | **admin** |
| POST | `` | **admin** |
| PATCH | `/{user_id}/password` | user (own) / admin (any) |
| DELETE | `/{user_id}` | **admin** |

#### Audit Log `/api`
| Method | Path | Auth | Query params |
|---|---|---|---|
| GET | `/audit-log` | **admin** | `entity`, `action`, `limit` (≤500, default 100), `offset` |

---

### Key Service Functions

| Function | Module | Signature summary |
|---|---|---|
| `ingest_file` | `services/ingestion.py` | `(bytes, filename, Session, user_role, user_id?) → dict` — full ingestion pipeline |
| `_lookup_rate` | `services/ingestion.py` | `(Session, Collaborator, date) → float` — EVM rate freeze |
| `_resolve_cycle` | `services/ingestion.py` | `(Session, date) → (Cycle, created: bool)` — auto-quarantine |
| `_detect_anomalies` | `services/ingestion.py` | `(DataFrame, set[str], Session, max_daily_hours) → list[str]` — weekend/over-limit/unregistered PEP checks |
| `_parse_date` | `services/ingestion.py` | handles `date`, Excel serial int, string with `dayfirst=True` |
| `_authorized_peps` | `services/ingestion.py` | `(Session, user_id, user_role, set[str]) → set[str]` — ACL filter |
| `log_audit` | `audit.py` | `(Session, User, action, entity, entity_id?, detail?) → None` |
| `init_db` | `database.py` | `create_all` + migrate + seed — called in lifespan |
| `_migrate_columns` | `database.py` | `PRAGMA table_info` + `ALTER TABLE` for post-initial columns |
| `get_current_user` | `deps.py` | JWT decode → `User`; used as `Depends` on all routers |
| `require_admin` | `deps.py` | Wraps `get_current_user`; 403 if `role != admin` |

### Expected CSV Columns (timesheet upload)

| Column | Required | Notes |
|---|---|---|
| `Colaborador` | Yes | Auto-creates `Collaborator` row if absent |
| `Data` | Yes | `dayfirst=True` string, or Excel serial int |
| `Horas totais (decimal)` | Yes | Float |
| `Hora extra` | No | `sim/yes/s/y/true/1` → `extra_hours` |
| `Hora sobreaviso` | No | same truth values → `standby_hours` |
| `Código PEP` | No | → `pep_wbs` |
| `PEP` | No | → `pep_description` |
| `Hora Inicial [H]` | No | Part of intra-batch dedup key |
