#!/usr/bin/env python3
"""
Portfolio dataset generator for PMAS system.
Generates complete sample data: cycles, projects, seniority/rate cards,
and quarterly timesheet CSVs with realistic data and intentional anomalies.
"""

import csv
import os
from datetime import date, timedelta
from collections import defaultdict

# ── Output directory ─────────────────────────────────────────────────────────
OUT = "/home/user/PMAS/amostras"
os.makedirs(OUT, exist_ok=True)

# ── Seniority levels and rates ────────────────────────────────────────────────
SENIORITY_RATES = {
    "Sênior":     {"2024": 150.0, "2025+": 165.0},
    "Pleno":      {"2024": 100.0, "2025+": 110.0},
    "Júnior":     {"2024":  65.0, "2025+":  72.0},
    "Estagiário": {"2024":  25.0, "2025+":  28.0},
}

def get_rate(seniority: str, record_date: date) -> float:
    rates = SENIORITY_RATES[seniority]
    return rates["2024"] if record_date.year == 2024 else rates["2025+"]

# ── Collaborators ─────────────────────────────────────────────────────────────
COLLABORATORS = {
    "João Silva":      {"seniority": "Sênior",     "first_active": date(2024,  1, 1)},
    "Maria Santos":    {"seniority": "Sênior",     "first_active": date(2024,  1, 1)},
    "Carlos Oliveira": {"seniority": "Pleno",      "first_active": date(2024,  1, 1)},
    "Ana Ferreira":    {"seniority": "Pleno",      "first_active": date(2024,  4, 1)},
    "Roberto Costa":   {"seniority": "Pleno",      "first_active": date(2024,  7, 1)},
    "Lucas Pereira":   {"seniority": "Júnior",     "first_active": date(2024,  1, 1)},
    "Fernanda Lima":   {"seniority": "Júnior",     "first_active": date(2024,  1, 1)},
    "Gabriel Souza":   {"seniority": "Júnior",     "first_active": date(2025,  4, 1)},
    "Amanda Torres":   {"seniority": "Estagiário", "first_active": date(2024, 10, 1)},
    "Pedro Carvalho":  {"seniority": "Estagiário", "first_active": date(2025,  1, 1)},
}

# ── Projects ──────────────────────────────────────────────────────────────────
PROJECTS = [
    {"pep": "PRJ-001", "name": "Transformação Digital",   "client": "Banco Nacional",  "manager": "João Silva",       "start": "2024-01", "end": "2024-12", "status": "encerrado", "budget_hours": 3200, "budget_cost": 480000},
    {"pep": "PRJ-002", "name": "App Mobile",              "client": "RetailMart",      "manager": "Maria Santos",     "start": "2024-03", "end": "2024-09", "status": "encerrado", "budget_hours": 1600, "budget_cost": 160000},
    {"pep": "PRJ-003", "name": "Migração Cloud",          "client": "TechCorp",        "manager": "Carlos Oliveira",  "start": "2024-06", "end": "2025-03", "status": "encerrado", "budget_hours": 2400, "budget_cost": 264000},
    {"pep": "PRJ-004", "name": "Plataforma Analytics",    "client": "IndustriaX",      "manager": "João Silva",       "start": "2024-01", "end": "2025-06", "status": "encerrado", "budget_hours": 4800, "budget_cost": 528000},
    {"pep": "PRJ-005", "name": "Implantação ERP",         "client": "Grupo Delta",     "manager": "Maria Santos",     "start": "2024-09", "end": "2025-12", "status": "encerrado", "budget_hours": 5600, "budget_cost": 616000},
    {"pep": "PRJ-006", "name": "Auditoria de Segurança",  "client": "FinanceGroup",    "manager": "Carlos Oliveira",  "start": "2025-01", "end": "2025-03", "status": "encerrado", "budget_hours":  800, "budget_cost":  88000},
    {"pep": "PRJ-007", "name": "Hub de Integrações API",  "client": "LogiTrans",       "manager": "Ana Ferreira",     "start": "2025-03", "end": "2025-12", "status": "encerrado", "budget_hours": 3200, "budget_cost": 352000},
    {"pep": "PRJ-008", "name": "Portal do Cliente",       "client": "Banco Nacional",  "manager": "João Silva",       "start": "2026-01", "end": "2026-12", "status": "ativo",     "budget_hours": 4800, "budget_cost": 528000},
    {"pep": "PRJ-009", "name": "Chatbot IA",              "client": "RetailMart",      "manager": "Gabriel Souza",    "start": "2026-03", "end": "2026-12", "status": "ativo",     "budget_hours": 2400, "budget_cost": 288000},
    {"pep": "PRJ-010", "name": "Upgrade Infraestrutura",  "client": "TechCorp",        "manager": "Roberto Costa",    "start": "2026-01", "end": "2026-09", "status": "ativo",     "budget_hours": 3200, "budget_cost": 352000},
]
PROJECTS_BY_PEP = {p["pep"]: p for p in PROJECTS}

# ── Cycles ────────────────────────────────────────────────────────────────────
CYCLES = [
    {"name": "Q1/2024", "start": date(2024,  1, 1), "end": date(2024,  3, 31)},
    {"name": "Q2/2024", "start": date(2024,  4, 1), "end": date(2024,  6, 30)},
    {"name": "Q3/2024", "start": date(2024,  7, 1), "end": date(2024,  9, 30)},
    {"name": "Q4/2024", "start": date(2024, 10, 1), "end": date(2024, 12, 31)},
    {"name": "Q1/2025", "start": date(2025,  1, 1), "end": date(2025,  3, 31)},
    {"name": "Q2/2025", "start": date(2025,  4, 1), "end": date(2025,  6, 30)},
    {"name": "Q3/2025", "start": date(2025,  7, 1), "end": date(2025,  9, 30)},
    {"name": "Q4/2025", "start": date(2025, 10, 1), "end": date(2025, 12, 31)},
    {"name": "Q1/2026", "start": date(2026,  1, 1), "end": date(2026,  3, 31)},
    {"name": "Q2/2026", "start": date(2026,  4, 1), "end": date(2026,  6, 30)},
]

# ── Quarter assignments ───────────────────────────────────────────────────────
# Each assignment: (collaborator, pep_code, hours_per_workday)
ASSIGNMENTS = {
    "Q1/2024": [
        ("João Silva",      "PRJ-001", 7),
        ("Carlos Oliveira", "PRJ-001", 6),
        ("Lucas Pereira",   "PRJ-001", 6),
        ("Maria Santos",    "PRJ-004", 7),
        ("Ana Ferreira",    "PRJ-004", 6),
        ("Fernanda Lima",   "PRJ-004", 6),
    ],
    "Q2/2024": [
        ("João Silva",      "PRJ-001", 7),
        ("Carlos Oliveira", "PRJ-001", 6),
        ("Lucas Pereira",   "PRJ-002", 6),
        ("Maria Santos",    "PRJ-002", 7),
        ("Fernanda Lima",   "PRJ-002", 5),
        ("Ana Ferreira",    "PRJ-004", 6),
    ],
    "Q3/2024": [
        ("João Silva",      "PRJ-001", 7),
        ("Carlos Oliveira", "PRJ-003", 6),
        ("Roberto Costa",   "PRJ-003", 6),
        ("Lucas Pereira",   "PRJ-004", 6),
        ("Ana Ferreira",    "PRJ-004", 6),
        ("Maria Santos",    "PRJ-002", 7),
        ("Fernanda Lima",   "PRJ-002", 5),
    ],
    "Q4/2024": [
        ("João Silva",      "PRJ-001", 7),
        ("Lucas Pereira",   "PRJ-001", 6),
        ("Carlos Oliveira", "PRJ-003", 6),
        ("Roberto Costa",   "PRJ-003", 6),
        ("Ana Ferreira",    "PRJ-004", 6),
        ("Fernanda Lima",   "PRJ-004", 5),
        ("Maria Santos",    "PRJ-005", 7),
        ("Amanda Torres",   "PRJ-005", 5),
    ],
    "Q1/2025": [
        ("João Silva",      "PRJ-006", 7),
        ("Fernanda Lima",   "PRJ-006", 6),
        ("Roberto Costa",   "PRJ-003", 6),
        ("Carlos Oliveira", "PRJ-005", 6),
        ("Maria Santos",    "PRJ-005", 7),
        ("Amanda Torres",   "PRJ-005", 5),
        ("Ana Ferreira",    "PRJ-004", 6),
        ("Lucas Pereira",   "PRJ-004", 6),
        ("Pedro Carvalho",  "PRJ-004", 5),
    ],
    "Q2/2025": [
        ("João Silva",      "PRJ-007", 7),
        ("Roberto Costa",   "PRJ-007", 6),
        ("Gabriel Souza",   "PRJ-007", 5),
        ("Ana Ferreira",    "PRJ-004", 6),
        ("Lucas Pereira",   "PRJ-004", 6),
        ("Carlos Oliveira", "PRJ-005", 6),
        ("Maria Santos",    "PRJ-005", 7),
        ("Amanda Torres",   "PRJ-005", 5),
    ],
    "Q3/2025": [
        ("João Silva",      "PRJ-007", 7),
        ("Roberto Costa",   "PRJ-007", 6),
        ("Gabriel Souza",   "PRJ-007", 6),
        ("Pedro Carvalho",  "PRJ-007", 5),
        ("Carlos Oliveira", "PRJ-005", 7),
        ("Maria Santos",    "PRJ-005", 7),
        ("Amanda Torres",   "PRJ-005", 5),
        ("Fernanda Lima",   "PRJ-005", 6),
    ],
    "Q4/2025": [
        ("João Silva",      "PRJ-007", 7),
        ("Roberto Costa",   "PRJ-007", 6),
        ("Gabriel Souza",   "PRJ-007", 6),
        ("Fernanda Lima",   "PRJ-007", 5),
        ("Carlos Oliveira", "PRJ-005", 7),
        ("Maria Santos",    "PRJ-005", 7),
        ("Amanda Torres",   "PRJ-005", 5),
        ("Pedro Carvalho",  "PRJ-005", 5),
    ],
    "Q1/2026": [
        ("João Silva",      "PRJ-008", 7),
        ("Carlos Oliveira", "PRJ-008", 6),
        ("Lucas Pereira",   "PRJ-008", 6),
        ("Amanda Torres",   "PRJ-008", 5),
        ("Roberto Costa",   "PRJ-010", 7),
        ("Pedro Carvalho",  "PRJ-010", 5),
    ],
    "Q2/2026": [
        ("João Silva",      "PRJ-008", 7),
        ("Carlos Oliveira", "PRJ-008", 6),
        ("Lucas Pereira",   "PRJ-008", 6),
        ("Gabriel Souza",   "PRJ-009", 6),
        ("Fernanda Lima",   "PRJ-009", 5),
        ("Roberto Costa",   "PRJ-010", 7),
        ("Pedro Carvalho",  "PRJ-010", 5),
    ],
}

# ── Anomaly rows per quarter ──────────────────────────────────────────────────
ANOMALY_ROWS = {
    "Q1/2024": [
        # Weekend date (Saturday 06/01/2024) → I1 info/warning
        {"Colaborador": "Ana Ferreira",    "Data": "06/01/2024", "Horas totais (decimal)": "4.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-004", "PEP": "Plataforma Analytics"},
        # Duplicate of first normal João Silva row → I4 skipped
        {"Colaborador": "João Silva",      "Data": "02/01/2024", "Horas totais (decimal)": "7.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-001", "PEP": "Transformação Digital"},
    ],
    "Q2/2024": [
        # Invalid hours (empty) → Q5 quarantine
        {"Colaborador": "Carlos Oliveira", "Data": "15/04/2024", "Horas totais (decimal)": "",     "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-001", "PEP": "Transformação Digital"},
        # Duplicate of first normal Maria Santos row → I4 skipped
        {"Colaborador": "Maria Santos",    "Data": "02/04/2024", "Horas totais (decimal)": "7.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-002", "PEP": "App Mobile"},
    ],
    "Q3/2024": [
        # Empty collaborator name → Q8 quarantine
        {"Colaborador": "",                "Data": "10/07/2024", "Horas totais (decimal)": "6.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-003", "PEP": "Migração Cloud"},
        # Extra hours row for Roberto Costa
        {"Colaborador": "Roberto Costa",   "Data": "12/07/2024", "Horas totais (decimal)": "3.0",  "Hora extra": "Sim",  "Hora sobreaviso": "",    "Código PEP": "PRJ-003", "PEP": "Migração Cloud"},
    ],
    "Q4/2024": [
        # Hours > 24h → Q6 quarantine
        {"Colaborador": "Amanda Torres",   "Data": "02/10/2024", "Horas totais (decimal)": "25.0", "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
        # Standby row
        {"Colaborador": "Maria Santos",    "Data": "04/10/2024", "Horas totais (decimal)": "2.0",  "Hora extra": "",     "Hora sobreaviso": "Sim", "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
    ],
    "Q1/2025": [
        # Negative hours → Q4 quarantine
        {"Colaborador": "Pedro Carvalho",  "Data": "08/01/2025", "Horas totais (decimal)": "-2.0", "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-004", "PEP": "Plataforma Analytics"},
        # Weekend (Saturday 04/01/2025) → I1 info
        {"Colaborador": "Carlos Oliveira", "Data": "04/01/2025", "Horas totais (decimal)": "5.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
    ],
    "Q2/2025": [
        # Future date → Q2 quarantine
        {"Colaborador": "Gabriel Souza",   "Data": "15/04/2027", "Horas totais (decimal)": "6.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-007", "PEP": "Hub de Integrações API"},
        # Extra hours for busy month
        {"Colaborador": "João Silva",      "Data": "10/04/2025", "Horas totais (decimal)": "3.0",  "Hora extra": "Sim",  "Hora sobreaviso": "",    "Código PEP": "PRJ-007", "PEP": "Hub de Integrações API"},
    ],
    "Q3/2025": [
        # Invalid date format → Q1 quarantine
        {"Colaborador": "Fernanda Lima",   "Data": "99/07/2025", "Horas totais (decimal)": "6.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
        # High daily hours - two entries same day totaling > 24h (Q7 scenario)
        {"Colaborador": "Carlos Oliveira", "Data": "15/07/2025", "Horas totais (decimal)": "14.0", "Hora extra": "Sim",  "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
        {"Colaborador": "Carlos Oliveira", "Data": "15/07/2025", "Horas totais (decimal)": "12.0", "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
    ],
    "Q4/2025": [
        # Weekend (Saturday 04/10/2025) → I1 info
        {"Colaborador": "Pedro Carvalho",  "Data": "04/10/2025", "Horas totais (decimal)": "4.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-005", "PEP": "Implantação ERP"},
        # Duplicate → I4 skipped
        {"Colaborador": "João Silva",      "Data": "02/10/2025", "Horas totais (decimal)": "7.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-007", "PEP": "Hub de Integrações API"},
    ],
    "Q1/2026": [
        # New collaborator with no rate → N1 info + I3 warning
        {"Colaborador": "Estagiário Novo", "Data": "15/01/2026", "Horas totais (decimal)": "6.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-008", "PEP": "Portal do Cliente"},
        # Extra hours
        {"Colaborador": "João Silva",      "Data": "09/01/2026", "Horas totais (decimal)": "2.0",  "Hora extra": "Sim",  "Hora sobreaviso": "",    "Código PEP": "PRJ-008", "PEP": "Portal do Cliente"},
    ],
    "Q2/2026": [
        # Standby row
        {"Colaborador": "Roberto Costa",   "Data": "03/04/2026", "Horas totais (decimal)": "1.5",  "Hora extra": "",     "Hora sobreaviso": "Sim", "Código PEP": "PRJ-010", "PEP": "Upgrade Infraestrutura"},
        # Weekend (Saturday 05/04/2026) → I1 info
        {"Colaborador": "Lucas Pereira",   "Data": "05/04/2026", "Horas totais (decimal)": "3.0",  "Hora extra": "",     "Hora sobreaviso": "",    "Código PEP": "PRJ-008", "PEP": "Portal do Cliente"},
    ],
}

# ── Helper functions ──────────────────────────────────────────────────────────
FIELDS = ["Colaborador", "Data", "Horas totais (decimal)", "Hora extra", "Hora sobreaviso", "Código PEP", "PEP"]
TODAY = date(2026, 5, 9)

def workdays_in_range(start: date, end: date) -> list:
    """Return list of Mon-Fri dates in [start, end] (inclusive)."""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

def is_weekend_date_str(date_str: str) -> bool:
    """Check if a DD/MM/YYYY date string falls on a weekend."""
    try:
        d = date(int(date_str[6:10]), int(date_str[3:5]), int(date_str[0:2]))
        return d.weekday() >= 5
    except Exception:
        return False

def classify_anomaly(row: dict) -> str:
    """Classify an anomaly row as: quarantine, info, extra, standby, or normal."""
    hours_str = row.get("Horas totais (decimal)", "")
    data_str = row.get("Data", "")
    collab = row.get("Colaborador", "")

    # Empty collaborator
    if not collab.strip():
        return "quarantine"
    # Empty hours
    if not hours_str.strip():
        return "quarantine"
    # Invalid date format
    try:
        date(int(data_str[6:10]), int(data_str[3:5]), int(data_str[0:2]))
    except Exception:
        return "quarantine"
    # Future date (beyond today 2026-05-09)
    try:
        d = date(int(data_str[6:10]), int(data_str[3:5]), int(data_str[0:2]))
        if d > TODAY:
            return "quarantine"
    except Exception:
        return "quarantine"
    # Negative or >24h hours
    try:
        h = float(hours_str)
        if h < 0 or h > 24:
            return "quarantine"
    except Exception:
        return "quarantine"
    # Weekend
    if is_weekend_date_str(data_str):
        return "info_weekend"
    # Extra or standby
    if row.get("Hora extra") == "Sim":
        return "extra"
    if row.get("Hora sobreaviso") == "Sim":
        return "standby"
    # Likely duplicate (same collab/date/pep as something normal)
    return "possible_duplicate"


# ── Analytics tracking structures ─────────────────────────────────────────────
# stats[quarter][pep][collaborator] = dict
stats = defaultdict(lambda: defaultdict(lambda: defaultdict(
    lambda: {"normal_h": 0.0, "extra_h": 0.0, "sobreaviso_h": 0.0, "cost": 0.0}
)))
cumulative_hours = defaultdict(float)
cumulative_cost  = defaultdict(float)

# ── Generate quarterly timesheet CSVs ─────────────────────────────────────────
def generate_quarter(cycle: dict) -> list:
    """Generate all normal rows for one quarter and track stats."""
    quarter = cycle["name"]
    start   = cycle["start"]
    end     = min(cycle["end"], TODAY)  # cap Q2/2026 at today

    workdays = workdays_in_range(start, end)
    rows = []

    for collab, pep_code, hours_per_day in ASSIGNMENTS.get(quarter, []):
        pep_name = PROJECTS_BY_PEP[pep_code]["name"]
        seniority = COLLABORATORS[collab]["seniority"]
        collab_first_active = COLLABORATORS[collab]["first_active"]

        for d in workdays:
            if d < collab_first_active:
                continue

            rate = get_rate(seniority, d)
            row = {
                "Colaborador":            collab,
                "Data":                   d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": str(float(hours_per_day)),
                "Hora extra":             "",
                "Hora sobreaviso":        "",
                "Código PEP":             pep_code,
                "PEP":                    pep_name,
            }
            rows.append(row)
            # Track analytics
            stats[quarter][pep_code][collab]["normal_h"] += hours_per_day
            stats[quarter][pep_code][collab]["cost"]     += hours_per_day * rate
            cumulative_hours[pep_code] += hours_per_day
            cumulative_cost[pep_code]  += hours_per_day * rate

    # ── Baked-in extra/standby rows (part of normal data section) ─────────────
    # Q4/2024: extra hours for PRJ-005 kickoff (Maria Santos first week)
    if quarter == "Q4/2024":
        extra_dates = [d for d in workdays if d <= date(2024, 10, 11)][:3]
        for d in extra_dates:
            rate = get_rate("Sênior", d)
            rows.append({
                "Colaborador":            "Maria Santos",
                "Data":                   d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": "2.0",
                "Hora extra":             "Sim",
                "Hora sobreaviso":        "",
                "Código PEP":             "PRJ-005",
                "PEP":                    "Implantação ERP",
            })
            stats[quarter]["PRJ-005"]["Maria Santos"]["extra_h"] += 2.0
            stats[quarter]["PRJ-005"]["Maria Santos"]["cost"]    += 2.0 * rate
            cumulative_hours["PRJ-005"] += 2.0
            cumulative_cost["PRJ-005"]  += 2.0 * rate

    # Q3/2025: standby rows for PRJ-005 production incident (Maria Santos)
    if quarter == "Q3/2025":
        standby_dates = [d for d in workdays if date(2025, 8, 4) <= d <= date(2025, 8, 8)][:3]
        for d in standby_dates:
            rate = get_rate("Sênior", d)
            rows.append({
                "Colaborador":            "Maria Santos",
                "Data":                   d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": "2.0",
                "Hora extra":             "",
                "Hora sobreaviso":        "Sim",
                "Código PEP":             "PRJ-005",
                "PEP":                    "Implantação ERP",
            })
            stats[quarter]["PRJ-005"]["Maria Santos"]["sobreaviso_h"] += 2.0
            stats[quarter]["PRJ-005"]["Maria Santos"]["cost"]         += 2.0 * rate
            cumulative_hours["PRJ-005"] += 2.0
            cumulative_cost["PRJ-005"]  += 2.0 * rate

    return rows


# ── Main: generate all files ──────────────────────────────────────────────────
print("=" * 60)
print("PMAS Portfolio Dataset Generator")
print("=" * 60)
print()

generated_files = {}
for cycle in CYCLES:
    q     = cycle["name"]
    rows  = generate_quarter(cycle)
    anomaly = ANOMALY_ROWS.get(q, [])
    all_rows = rows + anomaly

    safe_name = q.replace("/", "_")
    fpath = os.path.join(OUT, f"timesheet_{safe_name}.csv")

    with open(fpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    generated_files[q] = fpath
    n_lines = len(all_rows)
    print(f"  Generated: timesheet_{safe_name}.csv  ({len(rows)} normal + {len(anomaly)} anomaly = {n_lines} data rows)")

print()

# ── Reference CSVs ─────────────────────────────────────────────────────────────
# 1. Cycles
cycles_path = os.path.join(OUT, "ciclos.csv")
with open(cycles_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Nome", "Data Início", "Data Fim"])
    writer.writeheader()
    for c in CYCLES:
        writer.writerow({"Nome": c["name"], "Data Início": c["start"].strftime("%d/%m/%Y"), "Data Fim": c["end"].strftime("%d/%m/%Y")})
print(f"  Generated: ciclos.csv ({len(CYCLES)} cycles)")

# 2. Projects
projects_path = os.path.join(OUT, "projetos.csv")
with open(projects_path, "w", newline="", encoding="utf-8") as f:
    fields = ["Código PEP", "Nome", "Cliente", "Gerente", "Início", "Fim", "Status", "Budget Horas", "Budget Custo (R$)"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for p in PROJECTS:
        writer.writerow({
            "Código PEP":        p["pep"],
            "Nome":              p["name"],
            "Cliente":           p["client"],
            "Gerente":           p["manager"],
            "Início":            p["start"],
            "Fim":               p["end"],
            "Status":            p["status"],
            "Budget Horas":      p["budget_hours"],
            "Budget Custo (R$)": p["budget_cost"],
        })
print(f"  Generated: projetos.csv ({len(PROJECTS)} projects)")

# 3. Seniority + Rate Card
ratecard_path = os.path.join(OUT, "senioridade_rate_card.csv")
with open(ratecard_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Nível de Senioridade", "Período Vigência", "Taxa Horária (R$/h)"])
    writer.writeheader()
    for seniority, rates in SENIORITY_RATES.items():
        writer.writerow({"Nível de Senioridade": seniority, "Período Vigência": "2024-01-01 a 2024-12-31", "Taxa Horária (R$/h)": rates["2024"]})
        writer.writerow({"Nível de Senioridade": seniority, "Período Vigência": "2025-01-01 em diante",     "Taxa Horária (R$/h)": rates["2025+"]})
print(f"  Generated: senioridade_rate_card.csv ({len(SENIORITY_RATES)*2} rate card entries)")

# 4. Special demo files
ciclo_fechado_path = os.path.join(OUT, "timesheet_ciclo_fechado_demo.csv")
with open(ciclo_fechado_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    for d in [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17)]:
        writer.writerow({
            "Colaborador": "João Silva", "Data": d.strftime("%d/%m/%Y"),
            "Horas totais (decimal)": "7.0", "Hora extra": "", "Hora sobreaviso": "",
            "Código PEP": "PRJ-001", "PEP": "Transformação Digital",
        })
print("  Generated: timesheet_ciclo_fechado_demo.csv (3 data rows)")

projeto_encerrado_path = os.path.join(OUT, "timesheet_projeto_encerrado_demo.csv")
with open(projeto_encerrado_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    for d in [date(2024, 2, 15), date(2024, 2, 16), date(2024, 2, 17)]:
        writer.writerow({
            "Colaborador": "Carlos Oliveira", "Data": d.strftime("%d/%m/%Y"),
            "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "",
            "Código PEP": "PRJ-001", "PEP": "Transformação Digital",
        })
print("  Generated: timesheet_projeto_encerrado_demo.csv (3 data rows)")

print()
print("=" * 60)
print("ANALYTICS SUMMARY")
print("=" * 60)

# ── Build quarter summary dicts ───────────────────────────────────────────────
quarter_summaries = {}
grand_total_hours = 0.0
grand_total_cost  = 0.0

for cycle in CYCLES:
    q = cycle["name"]
    q_stats = stats[q]
    anomaly_rows_q = ANOMALY_ROWS.get(q, [])

    total_normal_h = 0.0
    total_extra_h  = 0.0
    total_sb_h     = 0.0
    total_cost     = 0.0
    pep_data = defaultdict(lambda: {"hours": 0.0, "cost": 0.0, "by_collab": {}})
    seniority_data = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})

    for pep_code, collab_data in q_stats.items():
        for collab, cdata in collab_data.items():
            total_normal_h += cdata["normal_h"]
            total_extra_h  += cdata["extra_h"]
            total_sb_h     += cdata["sobreaviso_h"]
            total_cost     += cdata["cost"]

            pep_data[pep_code]["hours"] += cdata["normal_h"] + cdata["extra_h"] + cdata["sobreaviso_h"]
            pep_data[pep_code]["cost"]  += cdata["cost"]
            pep_data[pep_code]["by_collab"][collab] = cdata

            seniority = COLLABORATORS[collab]["seniority"]
            seniority_data[seniority]["hours"] += cdata["normal_h"] + cdata["extra_h"] + cdata["sobreaviso_h"]
            seniority_data[seniority]["cost"]  += cdata["cost"]

    grand_total_hours += total_normal_h + total_extra_h + total_sb_h
    grand_total_cost  += total_cost

    # Classify anomaly rows
    n_quarantine    = sum(1 for r in anomaly_rows_q if classify_anomaly(r) == "quarantine")
    n_info_weekend  = sum(1 for r in anomaly_rows_q if classify_anomaly(r) == "info_weekend")
    n_dup           = sum(1 for r in anomaly_rows_q if classify_anomaly(r) == "possible_duplicate")
    n_extra_anomaly = sum(1 for r in anomaly_rows_q if classify_anomaly(r) == "extra")
    n_sb_anomaly    = sum(1 for r in anomaly_rows_q if classify_anomaly(r) == "standby")

    quarter_summaries[q] = {
        "total_normal_h":  total_normal_h,
        "total_extra_h":   total_extra_h,
        "total_sb_h":      total_sb_h,
        "total_cost":      total_cost,
        "pep_data":        dict(pep_data),
        "seniority_data":  dict(seniority_data),
        "n_quarantine":    n_quarantine,
        "n_info_weekend":  n_info_weekend,
        "n_dup":           n_dup,
        "n_extra_anomaly": n_extra_anomaly,
        "n_sb_anomaly":    n_sb_anomaly,
        "anomaly_rows":    anomaly_rows_q,
    }

    print(f"\n{q}:")
    print(f"  Normal: {total_normal_h:.0f}h | Extra: {total_extra_h:.0f}h | Sobreaviso: {total_sb_h:.0f}h | Custo: R${total_cost:,.2f}")
    print(f"  Anomalias: {n_quarantine} quarentena, {n_info_weekend} fim-de-semana, {n_dup} duplicata, {n_extra_anomaly} hora-extra, {n_sb_anomaly} sobreaviso")
    for pep_code, pdata in sorted(pep_data.items()):
        pname = PROJECTS_BY_PEP[pep_code]["name"]
        print(f"    {pep_code} ({pname}): {pdata['hours']:.0f}h, R${pdata['cost']:,.2f}")


print()
print("=" * 60)
print("CUMULATIVE BUDGET CONSUMPTION")
print("=" * 60)

for p in PROJECTS:
    pep = p["pep"]
    ch  = cumulative_hours[pep]
    cc  = cumulative_cost[pep]
    bh  = p["budget_hours"]
    bc  = p["budget_cost"]
    pct_h = ch / bh * 100 if bh else 0
    pct_c = cc / bc * 100 if bc else 0
    flag_h = " [ESTOURADO]" if pct_h >= 100 else (" [ATENCAO]" if pct_h >= 90 else "")
    flag_c = " [ESTOURADO]" if pct_c >= 100 else (" [ATENCAO]" if pct_c >= 90 else "")
    print(f"  {pep} ({p['name'][:22]:22s}): {ch:7.0f}h / {bh}h = {pct_h:6.1f}%{flag_h} | R${cc:>11,.0f} / R${bc:,} = {pct_c:.1f}%{flag_c}")


# ── Generate PORTFOLIO_ANALISE.md ─────────────────────────────────────────────
print()
print("=" * 60)
print("Generating PORTFOLIO_ANALISE.md ...")

md_lines = []

def mdl(s=""):
    md_lines.append(s)

mdl("# Análise do Portfólio PMAS — Relatório Completo")
mdl()
mdl(f"> **Data de geração:** 09/05/2026  |  **Período do portfólio:** Janeiro/2024 – Maio/2026")
mdl()
mdl("---")
mdl()
mdl("## 1. Visão Geral do Portfólio")
mdl()
mdl("O portfólio PMAS abrange 10 projetos distribuídos ao longo de 10 trimestres (Q1/2024 a Q2/2026). "
    "Os dados foram gerados sinteticamente para fins de demonstração e validação do sistema, "
    "contemplando cenários realistas de alocação de equipe, variação de taxas horárias, "
    "estouro de orçamento e anomalias de ingestão.")
mdl()

# Grand totals
grand_budget_hours = sum(p["budget_hours"] for p in PROJECTS)
grand_budget_cost  = sum(p["budget_cost"]  for p in PROJECTS)
pct_portfolio_h = grand_total_hours / grand_budget_hours * 100 if grand_budget_hours else 0
pct_portfolio_c = grand_total_cost  / grand_budget_cost  * 100 if grand_budget_cost  else 0

mdl("| Indicador | Valor |")
mdl("|---|---|")
mdl(f"| Total de projetos | 10 (7 encerrados, 3 ativos) |")
mdl(f"| Total de ciclos | 10 trimestres |")
mdl(f"| Colaboradores | 10 |")
mdl(f"| Horas totais registradas | **{grand_total_hours:,.0f} h** |")
mdl(f"| Custo total estimado | **R$ {grand_total_cost:,.2f}** |")
mdl(f"| Budget total do portfólio (horas) | {grand_budget_hours:,} h |")
mdl(f"| Budget total do portfólio (custo) | R$ {grand_budget_cost:,} |")
mdl(f"| Consumo médio (horas) | {pct_portfolio_h:.1f}% |")
mdl(f"| Consumo médio (custo) | {pct_portfolio_c:.1f}% |")
mdl()

mdl("---")
mdl()
mdl("## 2. Níveis de Senioridade e Tabela de Taxas")
mdl()
mdl("| Nível | Taxa 2024 (R$/h) | Taxa 2025+ (R$/h) | Variação |")
mdl("|---|---|---|---|")
for seniority, rates in SENIORITY_RATES.items():
    var = (rates["2025+"] - rates["2024"]) / rates["2024"] * 100
    mdl(f"| {seniority} | R$ {rates['2024']:.2f} | R$ {rates['2025+']:.2f} | +{var:.1f}% |")
mdl()

mdl("---")
mdl()
mdl("## 3. Tabela de Projetos")
mdl()
mdl("| PEP | Nome | Cliente | Gerente | Início | Fim | Status | Budget Horas | Budget Custo | Consumido (h) | Consumido (R$) | % Horas | % Custo |")
mdl("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for p in PROJECTS:
    pep = p["pep"]
    ch  = cumulative_hours[pep]
    cc  = cumulative_cost[pep]
    bh  = p["budget_hours"]
    bc  = p["budget_cost"]
    pct_h = ch / bh * 100 if bh else 0
    pct_c = cc / bc * 100 if bc else 0
    flag = " ⚠️" if pct_h >= 90 and pct_h < 100 else (" 🔴" if pct_h >= 100 else "")
    mdl(f"| {pep} | {p['name']} | {p['client']} | {p['manager']} | {p['start']} | {p['end']} | {p['status']} | {bh:,} h | R$ {bc:,} | {ch:.0f} h | R$ {cc:,.0f} | {pct_h:.1f}%{flag} | {pct_c:.1f}% |")
mdl()

mdl("---")
mdl()
mdl("## 4. Ciclos (Trimestres)")
mdl()
mdl("| Ciclo | Início | Fim | Dias Úteis | Horas Totais | Custo Total |")
mdl("|---|---|---|---|---|---|")
for cycle in CYCLES:
    q = cycle["name"]
    qs = quarter_summaries[q]
    effective_end = min(cycle["end"], TODAY)
    wd = len(workdays_in_range(cycle["start"], effective_end))
    total_h = qs["total_normal_h"] + qs["total_extra_h"] + qs["total_sb_h"]
    mdl(f"| {q} | {cycle['start'].strftime('%d/%m/%Y')} | {effective_end.strftime('%d/%m/%Y')} | {wd} | {total_h:.0f} h | R$ {qs['total_cost']:,.2f} |")
mdl()

mdl("---")
mdl()
mdl("## 5. Análise por Trimestre")
mdl()

ANOMALY_DESCRIPTIONS = {
    "Q1/2024": [
        ("I1 – Dia inválido (fim de semana)",    "Ana Ferreira, 06/01/2024 (sábado). Registra aviso mas insere normalmente."),
        ("I4 – Linha duplicada",                  "João Silva, 02/01/2024, PRJ-001. Linha idêntica à primeira entrada normal — ignorada na segunda ingestão."),
    ],
    "Q2/2024": [
        ("Q5 – Horas vazias",                    "Carlos Oliveira, 15/04/2024, PRJ-001. Campo `Horas totais (decimal)` vazio → quarentena."),
        ("I4 – Linha duplicada",                  "Maria Santos, 02/04/2024, PRJ-002. Idêntica à primeira entrada normal — ignorada."),
    ],
    "Q3/2024": [
        ("Q8 – Colaborador vazio",               "Linha sem nome de colaborador, 10/07/2024. Campo `Colaborador` em branco → quarentena."),
        ("Hora extra válida",                     "Roberto Costa, 12/07/2024, PRJ-003. Hora extra marcada — inserida normalmente com flag."),
    ],
    "Q4/2024": [
        ("Q6 – Horas > 24h",                     "Amanda Torres, 02/10/2024, 25,0h. Valor acima de 24 horas em um único registro → quarentena."),
        ("Hora sobreaviso válida",               "Maria Santos, 04/10/2024, PRJ-005. Sobreaviso de 2h — inserido normalmente."),
    ],
    "Q1/2025": [
        ("Q4 – Horas negativas",                 "Pedro Carvalho, 08/01/2025, -2,0h. Valor negativo → quarentena."),
        ("I1 – Dia inválido (fim de semana)",    "Carlos Oliveira, 04/01/2025 (sábado). Aviso gerado, inserção normal."),
    ],
    "Q2/2025": [
        ("Q2 – Data futura",                     "Gabriel Souza, 15/04/2027. Data muito além do presente → quarentena."),
        ("Hora extra válida",                     "João Silva, 10/04/2025, PRJ-007. 3h extra marcadas — inseridas normalmente."),
    ],
    "Q3/2025": [
        ("Q1 – Formato de data inválido",        "Fernanda Lima, 99/07/2025. Dia=99 impossível → erro de parse → quarentena."),
        ("Q7 – Horas diárias > 24h (agregado)", "Carlos Oliveira, 15/07/2025: duas entradas no mesmo dia (14h extra + 12h normal = 26h). "
                                                  "Cada linha individualmente ≤ 24h, mas o agregado diário ultrapassa. Gera alerta Q7."),
    ],
    "Q4/2025": [
        ("I1 – Dia inválido (fim de semana)",    "Pedro Carvalho, 04/10/2025 (sábado). Aviso gerado, inserção normal."),
        ("I4 – Linha duplicada",                  "João Silva, 02/10/2025, PRJ-007. Idêntica à primeira entrada normal — ignorada."),
    ],
    "Q1/2026": [
        ("N1 + I3 – Colaborador sem taxa",       "Estagiário Novo, 15/01/2026. Colaborador desconhecido criado automaticamente, "
                                                  "mas sem RateCard associado → custo zerado + aviso I3 (sem taxa configurada)."),
        ("Hora extra válida",                     "João Silva, 09/01/2026, PRJ-008. 2h extra — inseridas normalmente."),
    ],
    "Q2/2026": [
        ("Hora sobreaviso válida",               "Roberto Costa, 03/04/2026, PRJ-010. Sobreaviso de 1,5h — inserido normalmente."),
        ("I1 – Dia inválido (fim de semana)",    "Lucas Pereira, 05/04/2026 (sábado). Aviso gerado, inserção normal."),
    ],
}

for cycle in CYCLES:
    q   = cycle["name"]
    qs  = quarter_summaries[q]
    assignments_q = ASSIGNMENTS.get(q, [])
    active_peps = sorted(set(pep for _, pep, _ in assignments_q))

    mdl(f"### 5.{CYCLES.index(cycle)+1}. {q}")
    mdl()

    mdl(f"**Período:** {cycle['start'].strftime('%d/%m/%Y')} – {min(cycle['end'], TODAY).strftime('%d/%m/%Y')}")
    mdl()
    mdl(f"**Projetos ativos neste trimestre:** {', '.join(active_peps)}")
    mdl()

    total_h = qs["total_normal_h"] + qs["total_extra_h"] + qs["total_sb_h"]
    mdl(f"**Resumo do trimestre:** {total_h:.0f} h registradas | {qs['total_extra_h']:.0f} h extra | {qs['total_sb_h']:.0f} h sobreaviso | R$ {qs['total_cost']:,.2f}")
    mdl()

    # Collaborator hours table
    mdl("#### Alocação de colaboradores")
    mdl()
    mdl("| Colaborador | Senioridade | PEP | Horas Normais | Horas Extra | Sobreaviso | Taxa (R$/h) | Custo Estimado |")
    mdl("|---|---|---|---|---|---|---|---|")

    for pep_code, collab_data in sorted(qs.get("pep_data", {}).items()):
        for collab, cdata in sorted(collab_data.get("by_collab", {}).items()):
            seniority = COLLABORATORS[collab]["seniority"]
            # Determine representative rate for the quarter
            sample_date = cycle["start"]
            rate = get_rate(seniority, sample_date)
            normal_h = cdata["normal_h"]
            extra_h  = cdata["extra_h"]
            sb_h     = cdata["sobreaviso_h"]
            cost     = cdata["cost"]
            if normal_h + extra_h + sb_h > 0:
                mdl(f"| {collab} | {seniority} | {pep_code} | {normal_h:.0f} h | {extra_h:.0f} h | {sb_h:.0f} h | R$ {rate:.0f} | R$ {cost:,.2f} |")

    mdl()

    # Per-project totals + cumulative budget consumption
    mdl("#### Consumo por projeto (acumulado até o trimestre)")
    mdl()
    mdl("| PEP | Nome | Horas Trimestre | Custo Trimestre | Horas Acumuladas | Budget Horas | % Horas | Status |")
    mdl("|---|---|---|---|---|---|---|---|")
    for pep_code in active_peps:
        pdata = qs.get("pep_data", {}).get(pep_code, {"hours": 0.0, "cost": 0.0})
        p     = PROJECTS_BY_PEP[pep_code]
        # Cumulative up to end of this quarter: use cumulative_hours as of END of all quarters
        # We'll compute per-quarter cumulative from stats
        cum_h_to_q = sum(
            sum(cd["normal_h"] + cd["extra_h"] + cd["sobreaviso_h"]
                for cd in stats[c["name"]][pep_code].values())
            for c in CYCLES[:CYCLES.index(cycle)+1]
        )
        bh    = p["budget_hours"]
        pct_h = cum_h_to_q / bh * 100 if bh else 0
        status = "Estourado 🔴" if pct_h >= 100 else ("Atenção ⚠️" if pct_h >= 90 else "OK ✅")
        mdl(f"| {pep_code} | {p['name']} | {pdata['hours']:.0f} h | R$ {pdata['cost']:,.2f} | {cum_h_to_q:.0f} h | {bh:,} h | {pct_h:.1f}% | {status} |")

    mdl()

    # Seniority breakdown
    mdl("#### Distribuição por senioridade")
    mdl()
    mdl("| Senioridade | Horas | Custo |")
    mdl("|---|---|---|")
    for seniority, sdata in sorted(qs.get("seniority_data", {}).items()):
        if sdata["hours"] > 0:
            mdl(f"| {seniority} | {sdata['hours']:.0f} h | R$ {sdata['cost']:,.2f} |")
    mdl()

    # Anomaly notes
    anomaly_desc = ANOMALY_DESCRIPTIONS.get(q, [])
    if anomaly_desc:
        mdl("#### Anomalias de ingestão")
        mdl()
        mdl("As seguintes linhas foram intencionalmente incluídas no arquivo CSV para demonstrar o comportamento do sistema de ingestão:")
        mdl()
        for title, desc in anomaly_desc:
            mdl(f"- **{title}:** {desc}")
        mdl()
        mdl(f"> Resumo: {qs['n_quarantine']} linha(s) para quarentena · {qs['n_info_weekend']} aviso(s) de fim de semana · {qs['n_dup']} duplicata(s) ignorada(s) · {qs['n_extra_anomaly']} hora(s) extra · {qs['n_sb_anomaly']} sobreaviso(s)")
        mdl()

    mdl("---")
    mdl()


mdl("## 6. Arquivos de Demonstração de Cenários Especiais")
mdl()
mdl("### 6.1. `timesheet_ciclo_fechado_demo.csv`")
mdl()
mdl("Contém 3 registros de João Silva em PRJ-001 com datas 15–17/01/2024 (dentro do Q1/2024).")
mdl()
mdl("**Cenário:** Se o ciclo Q1/2024 já estiver marcado como *fechado* no sistema, ")
mdl("a tentativa de importação deste arquivo deve gerar o alerta **W1 – Ciclo fechado**, ")
mdl("impedindo a inserção de novos registros naquele período sem autorização explícita do gestor.")
mdl()
mdl("### 6.2. `timesheet_projeto_encerrado_demo.csv`")
mdl()
mdl("Contém 3 registros de Carlos Oliveira em PRJ-001 com datas 15–17/02/2024.")
mdl()
mdl("**Cenário:** Se o projeto PRJ-001 (Transformação Digital) estiver com status *encerrado*, ")
mdl("a importação deve gerar o alerta **W3 – Projeto encerrado**, evitando que novas horas ")
mdl("sejam creditadas a um projeto já finalizado.")
mdl()
mdl("---")
mdl()
mdl("## 7. Resumo Final do Portfólio")
mdl()
mdl("### 7.1. Totais gerais")
mdl()
mdl("| Métrica | Valor |")
mdl("|---|---|")
mdl(f"| Horas normais totais | {sum(quarter_summaries[c['name']]['total_normal_h'] for c in CYCLES):,.0f} h |")
mdl(f"| Horas extra totais | {sum(quarter_summaries[c['name']]['total_extra_h'] for c in CYCLES):,.0f} h |")
mdl(f"| Horas sobreaviso totais | {sum(quarter_summaries[c['name']]['total_sb_h'] for c in CYCLES):,.0f} h |")
mdl(f"| **Horas totais** | **{grand_total_hours:,.0f} h** |")
mdl(f"| **Custo total estimado** | **R$ {grand_total_cost:,.2f}** |")
mdl(f"| Budget total (horas) | {grand_budget_hours:,} h |")
mdl(f"| Budget total (custo) | R$ {grand_budget_cost:,} |")
mdl(f"| Consumo do portfólio (horas) | {pct_portfolio_h:.1f}% |")
mdl(f"| Consumo do portfólio (custo) | {pct_portfolio_c:.1f}% |")
mdl()

mdl("### 7.2. Status de orçamento por projeto")
mdl()
mdl("| PEP | Nome | Status Projeto | Horas Consumidas | Budget Horas | % Horas | Custo Consumido | Budget Custo | % Custo | Alerta |")
mdl("|---|---|---|---|---|---|---|---|---|---|")
projects_over_budget = []
for p in PROJECTS:
    pep = p["pep"]
    ch  = cumulative_hours[pep]
    cc  = cumulative_cost[pep]
    bh  = p["budget_hours"]
    bc  = p["budget_cost"]
    pct_h = ch / bh * 100 if bh else 0
    pct_c = cc / bc * 100 if bc else 0
    if pct_h >= 100:
        alert = "🔴 Estourado"
        projects_over_budget.append(p["name"])
    elif pct_h >= 90:
        alert = "⚠️ Atenção"
    else:
        alert = "✅ OK"
    mdl(f"| {pep} | {p['name']} | {p['status']} | {ch:.0f} h | {bh:,} h | {pct_h:.1f}% | R$ {cc:,.0f} | R$ {bc:,} | {pct_c:.1f}% | {alert} |")
mdl()

if projects_over_budget:
    mdl(f"> **Projetos com orçamento estourado:** {', '.join(projects_over_budget)}")
    mdl()

mdl("### 7.3. Anomalias de ingestão por trimestre")
mdl()
mdl("| Trimestre | Quarentena | Fim de Semana | Duplicatas | Horas Extra (anomalia) | Sobreaviso (anomalia) | Total |")
mdl("|---|---|---|---|---|---|---|")
total_q = total_iw = total_dup = total_ex = total_sb = 0
for cycle in CYCLES:
    q = cycle["name"]
    qs = quarter_summaries[q]
    q_n  = qs["n_quarantine"]
    iw_n = qs["n_info_weekend"]
    d_n  = qs["n_dup"]
    ex_n = qs["n_extra_anomaly"]
    sb_n = qs["n_sb_anomaly"]
    tot  = q_n + iw_n + d_n + ex_n + sb_n
    total_q   += q_n;  total_iw  += iw_n
    total_dup += d_n;  total_ex  += ex_n
    total_sb  += sb_n
    mdl(f"| {q} | {q_n} | {iw_n} | {d_n} | {ex_n} | {sb_n} | {tot} |")
mdl(f"| **Total** | **{total_q}** | **{total_iw}** | **{total_dup}** | **{total_ex}** | **{total_sb}** | **{total_q+total_iw+total_dup+total_ex+total_sb}** |")
mdl()

mdl("### 7.4. Participação por nível de senioridade (portfólio completo)")
mdl()
mdl("| Senioridade | Horas Totais | % do Total | Custo Total | % do Custo |")
mdl("|---|---|---|---|---|")
seniority_grand = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
for cycle in CYCLES:
    for seniority, sdata in quarter_summaries[cycle["name"]].get("seniority_data", {}).items():
        seniority_grand[seniority]["hours"] += sdata["hours"]
        seniority_grand[seniority]["cost"]  += sdata["cost"]
for seniority in ["Sênior", "Pleno", "Júnior", "Estagiário"]:
    sdata = seniority_grand[seniority]
    pct_h = sdata["hours"] / grand_total_hours * 100 if grand_total_hours else 0
    pct_c = sdata["cost"]  / grand_total_cost  * 100 if grand_total_cost  else 0
    mdl(f"| {seniority} | {sdata['hours']:,.0f} h | {pct_h:.1f}% | R$ {sdata['cost']:,.2f} | {pct_c:.1f}% |")
mdl()

mdl("---")
mdl()
mdl("*Documento gerado automaticamente pelo script `generate_portfolio.py`. "
    "Os dados são sintéticos e destinados exclusivamente a fins de demonstração do sistema PMAS.*")

# Write the markdown file
md_path = os.path.join(OUT, "PORTFOLIO_ANALISE.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")

print(f"  Generated: PORTFOLIO_ANALISE.md ({len(md_lines)} lines)")
print()
print("=" * 60)
print("ALL FILES GENERATED SUCCESSFULLY")
print("=" * 60)

# Final file list with line counts
import subprocess
all_generated = [
    cycles_path, projects_path, ratecard_path,
    ciclo_fechado_path, projeto_encerrado_path, md_path,
] + list(generated_files.values())

print()
for fp in sorted(all_generated):
    with open(fp, encoding="utf-8") as f:
        lc = sum(1 for _ in f)
    print(f"  {os.path.basename(fp):55s} {lc:5d} lines")
