#!/usr/bin/env python3
"""
PMAS sample portfolio dataset generator — v2
Monthly cycles (Jan/2024 – Mai/2026), API-correct column names, realistic PEP codes.
"""

import csv
import os
from datetime import date, timedelta
from calendar import monthrange
from collections import defaultdict

OUT = "/home/user/PMAS/amostras"
os.makedirs(OUT, exist_ok=True)

TODAY = date(2026, 5, 9)
PT_MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def month_end(y, m):
    return date(y, m, monthrange(y, m)[1])


def month_label(y, m):
    return f"{PT_MONTHS[m - 1]}/{y}"


def workdays(start, end):
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


# ── Seniority & rate cards ────────────────────────────────────────────────────

RATES = {
    "Sênior":     {2024: 150.0, 2025: 165.0, 2026: 165.0},
    "Pleno":      {2024: 100.0, 2025: 110.0, 2026: 110.0},
    "Júnior":     {2024:  65.0, 2025:  72.0, 2026:  72.0},
    "Estagiário": {2024:  25.0, 2025:  28.0, 2026:  28.0},
}


def rate(seniority, d):
    return RATES[seniority][d.year]


# ── Collaborators ─────────────────────────────────────────────────────────────

COLLABS = {
    "João Silva":      {"seniority": "Sênior",     "since": date(2024,  1, 1)},
    "Maria Santos":    {"seniority": "Sênior",     "since": date(2024,  1, 1)},
    "Carlos Oliveira": {"seniority": "Pleno",      "since": date(2024,  1, 1)},
    "Ana Ferreira":    {"seniority": "Pleno",      "since": date(2024,  4, 1)},
    "Roberto Costa":   {"seniority": "Pleno",      "since": date(2024,  7, 1)},
    "Lucas Pereira":   {"seniority": "Júnior",     "since": date(2024,  1, 1)},
    "Fernanda Lima":   {"seniority": "Júnior",     "since": date(2024,  1, 1)},
    "Gabriel Souza":   {"seniority": "Júnior",     "since": date(2025,  4, 1)},
    "Amanda Torres":   {"seniority": "Estagiário", "since": date(2024, 10, 1)},
    "Pedro Carvalho":  {"seniority": "Estagiário", "since": date(2025,  1, 1)},
}


# ── Projects — pep_wbs uses realistic enterprise codes ───────────────────────

PROJECTS = [
    {"pep_wbs": "60IT-001-01", "name": "Transformação Digital",  "client": "Banco Nacional", "manager": "João Silva",      "budget_hours": 3200, "budget_cost": 480000, "status": "encerrado", "pep_start": date(2024,1,1),  "pep_end": date(2024,12,31)},
    {"pep_wbs": "60IT-002-01", "name": "App Mobile",             "client": "RetailMart",     "manager": "Maria Santos",    "budget_hours": 1600, "budget_cost": 160000, "status": "encerrado", "pep_start": date(2024,3,1),  "pep_end": date(2024, 9,30)},
    {"pep_wbs": "60IT-003-01", "name": "Migração Cloud",         "client": "TechCorp",       "manager": "Carlos Oliveira", "budget_hours": 2400, "budget_cost": 264000, "status": "encerrado", "pep_start": date(2024,6,1),  "pep_end": date(2025, 3,31)},
    {"pep_wbs": "60IT-004-01", "name": "Plataforma Analytics",   "client": "IndustriaX",     "manager": "João Silva",      "budget_hours": 4800, "budget_cost": 528000, "status": "encerrado", "pep_start": date(2024,1,1),  "pep_end": date(2025, 6,30)},
    {"pep_wbs": "60IT-005-01", "name": "Implantação ERP",        "client": "Grupo Delta",    "manager": "Maria Santos",    "budget_hours": 5600, "budget_cost": 616000, "status": "encerrado", "pep_start": date(2024,9,1),  "pep_end": date(2025,12,31)},
    {"pep_wbs": "60IT-006-01", "name": "Auditoria de Segurança", "client": "FinanceGroup",   "manager": "Carlos Oliveira", "budget_hours":  800, "budget_cost":  88000, "status": "encerrado", "pep_start": date(2025,1,1),  "pep_end": date(2025, 3,31)},
    {"pep_wbs": "60IT-007-01", "name": "Hub de Integrações API", "client": "LogiTrans",      "manager": "Ana Ferreira",    "budget_hours": 3200, "budget_cost": 352000, "status": "encerrado", "pep_start": date(2025,3,1),  "pep_end": date(2025,12,31)},
    {"pep_wbs": "60IT-008-01", "name": "Portal do Cliente",      "client": "Banco Nacional", "manager": "João Silva",      "budget_hours": 4800, "budget_cost": 528000, "status": "ativo",     "pep_start": date(2026,1,1),  "pep_end": date(2026,12,31)},
    {"pep_wbs": "60IT-009-01", "name": "Chatbot IA",             "client": "RetailMart",     "manager": "Gabriel Souza",   "budget_hours": 2400, "budget_cost": 288000, "status": "ativo",     "pep_start": date(2026,3,1),  "pep_end": date(2026,12,31)},
    {"pep_wbs": "60IT-010-01", "name": "Upgrade Infraestrutura", "client": "TechCorp",       "manager": "Roberto Costa",   "budget_hours": 3200, "budget_cost": 352000, "status": "ativo",     "pep_start": date(2026,1,1),  "pep_end": date(2026, 9,30)},
]
BY_PEP = {p["pep_wbs"]: p for p in PROJECTS}


# ── Monthly cycles: Jan/2024 → Mai/2026 (29 cycles) ──────────────────────────

CYCLES = []
y, m = 2024, 1
while (y, m) <= (2026, 5):
    s = date(y, m, 1)
    e = month_end(y, m)
    # Months that have fully elapsed are closed
    is_closed = e < date(2026, 5, 1)
    CYCLES.append({"name": month_label(y, m), "start_date": s, "end_date": e, "is_closed": is_closed})
    m = m + 1 if m < 12 else (y := y + 1, 1)[1]


# ── Quarter groupings for timesheet files ─────────────────────────────────────
# Each quarterly file covers 3 (or fewer) monthly cycles.

QUARTERS = [
    ("Q1/2024", date(2024,  1, 1), date(2024,  3, 31)),
    ("Q2/2024", date(2024,  4, 1), date(2024,  6, 30)),
    ("Q3/2024", date(2024,  7, 1), date(2024,  9, 30)),
    ("Q4/2024", date(2024, 10, 1), date(2024, 12, 31)),
    ("Q1/2025", date(2025,  1, 1), date(2025,  3, 31)),
    ("Q2/2025", date(2025,  4, 1), date(2025,  6, 30)),
    ("Q3/2025", date(2025,  7, 1), date(2025,  9, 30)),
    ("Q4/2025", date(2025, 10, 1), date(2025, 12, 31)),
    ("Q1/2026", date(2026,  1, 1), date(2026,  3, 31)),
    ("Q2/2026", date(2026,  4, 1), TODAY),
]


# ── Assignments: (collaborator, pep_wbs, hours_per_workday) ──────────────────

ASSIGNMENTS = {
    "Q1/2024": [
        ("João Silva",      "60IT-001-01", 7),
        ("Carlos Oliveira", "60IT-001-01", 6),
        ("Lucas Pereira",   "60IT-001-01", 6),
        ("Maria Santos",    "60IT-004-01", 7),
        ("Fernanda Lima",   "60IT-004-01", 6),
        ("Ana Ferreira",    "60IT-004-01", 4),  # no rate card yet → I3
    ],
    "Q2/2024": [
        ("João Silva",      "60IT-001-01", 7),
        ("Carlos Oliveira", "60IT-001-01", 6),
        ("Lucas Pereira",   "60IT-002-01", 6),
        ("Maria Santos",    "60IT-002-01", 7),
        ("Fernanda Lima",   "60IT-002-01", 5),
        ("Ana Ferreira",    "60IT-004-01", 6),
    ],
    "Q3/2024": [
        ("João Silva",      "60IT-001-01", 7),
        ("Carlos Oliveira", "60IT-003-01", 6),
        ("Roberto Costa",   "60IT-003-01", 6),  # N1: first appearance
        ("Lucas Pereira",   "60IT-004-01", 6),
        ("Ana Ferreira",    "60IT-004-01", 6),
        ("Maria Santos",    "60IT-002-01", 7),
        ("Fernanda Lima",   "60IT-002-01", 5),
    ],
    "Q4/2024": [
        ("João Silva",      "60IT-001-01", 7),
        ("Lucas Pereira",   "60IT-001-01", 6),
        ("Carlos Oliveira", "60IT-003-01", 6),
        ("Roberto Costa",   "60IT-003-01", 6),
        ("Ana Ferreira",    "60IT-004-01", 6),
        ("Fernanda Lima",   "60IT-004-01", 5),
        ("Maria Santos",    "60IT-005-01", 7),
        ("Amanda Torres",   "60IT-005-01", 5),  # N1: first appearance
    ],
    "Q1/2025": [
        ("João Silva",      "60IT-006-01", 7),
        ("Fernanda Lima",   "60IT-006-01", 6),
        ("Roberto Costa",   "60IT-003-01", 6),
        ("Carlos Oliveira", "60IT-005-01", 6),
        ("Maria Santos",    "60IT-005-01", 7),
        ("Amanda Torres",   "60IT-005-01", 5),
        ("Ana Ferreira",    "60IT-004-01", 6),
        ("Lucas Pereira",   "60IT-004-01", 6),
        ("Pedro Carvalho",  "60IT-004-01", 5),  # N1: first appearance
    ],
    "Q2/2025": [
        ("João Silva",      "60IT-007-01", 7),
        ("Roberto Costa",   "60IT-007-01", 6),
        ("Gabriel Souza",   "60IT-007-01", 5),  # N1: first appearance
        ("Ana Ferreira",    "60IT-004-01", 6),
        ("Lucas Pereira",   "60IT-004-01", 6),
        ("Carlos Oliveira", "60IT-005-01", 6),
        ("Maria Santos",    "60IT-005-01", 7),
        ("Amanda Torres",   "60IT-005-01", 5),
    ],
    "Q3/2025": [
        ("João Silva",      "60IT-007-01", 7),
        ("Roberto Costa",   "60IT-007-01", 6),
        ("Gabriel Souza",   "60IT-007-01", 6),
        ("Pedro Carvalho",  "60IT-007-01", 5),
        ("Carlos Oliveira", "60IT-005-01", 7),
        ("Maria Santos",    "60IT-005-01", 7),
        ("Amanda Torres",   "60IT-005-01", 5),
        ("Fernanda Lima",   "60IT-005-01", 6),
    ],
    "Q4/2025": [
        ("João Silva",      "60IT-007-01", 7),
        ("Roberto Costa",   "60IT-007-01", 6),
        ("Gabriel Souza",   "60IT-007-01", 6),
        ("Fernanda Lima",   "60IT-007-01", 5),
        ("Carlos Oliveira", "60IT-005-01", 7),
        ("Maria Santos",    "60IT-005-01", 7),
        ("Amanda Torres",   "60IT-005-01", 5),
        ("Pedro Carvalho",  "60IT-005-01", 5),
    ],
    "Q1/2026": [
        ("João Silva",      "60IT-008-01", 7),
        ("Carlos Oliveira", "60IT-008-01", 6),
        ("Lucas Pereira",   "60IT-008-01", 6),
        ("Amanda Torres",   "60IT-008-01", 5),
        ("Roberto Costa",   "60IT-010-01", 7),
        ("Pedro Carvalho",  "60IT-010-01", 5),
    ],
    "Q2/2026": [
        ("João Silva",      "60IT-008-01", 7),
        ("Carlos Oliveira", "60IT-008-01", 6),
        ("Lucas Pereira",   "60IT-008-01", 6),
        ("Gabriel Souza",   "60IT-009-01", 6),
        ("Fernanda Lima",   "60IT-009-01", 5),
        ("Roberto Costa",   "60IT-010-01", 7),
        ("Pedro Carvalho",  "60IT-010-01", 5),
    ],
}


# ── Anomaly rows (appended at end of each quarterly file) ────────────────────

ANOMALY_ROWS = {
    "Q1/2024": [
        # I1 – weekend date (Saturday 06/01/2024)
        {"Colaborador": "Ana Ferreira",    "Data": "06/01/2024", "Horas totais (decimal)": "4.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-004-01", "PEP": "Plataforma Analytics"},
        # I4 – exact duplicate of first João Silva row
        {"Colaborador": "João Silva",      "Data": "02/01/2024", "Horas totais (decimal)": "7.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
    ],
    "Q2/2024": [
        # Q5 – horas em branco
        {"Colaborador": "Carlos Oliveira", "Data": "15/04/2024", "Horas totais (decimal)": "",     "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
        # I4 – duplicate Maria Santos
        {"Colaborador": "Maria Santos",    "Data": "02/04/2024", "Horas totais (decimal)": "7.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-002-01", "PEP": "App Mobile"},
    ],
    "Q3/2024": [
        # Q8 – colaborador vazio
        {"Colaborador": "",                "Data": "10/07/2024", "Horas totais (decimal)": "6.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-003-01", "PEP": "Migração Cloud"},
        # Extra hours – Roberto Costa (válido, computado)
        {"Colaborador": "Roberto Costa",   "Data": "12/07/2024", "Horas totais (decimal)": "3.0",  "Hora extra": "Sim", "Hora sobreaviso": "",    "Código PEP": "60IT-003-01", "PEP": "Migração Cloud"},
    ],
    "Q4/2024": [
        # Q6 – horas > 24h
        {"Colaborador": "Amanda Torres",   "Data": "02/10/2024", "Horas totais (decimal)": "25.0", "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
        # Hora sobreaviso – válido
        {"Colaborador": "Maria Santos",    "Data": "04/10/2024", "Horas totais (decimal)": "2.0",  "Hora extra": "",    "Hora sobreaviso": "Sim", "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
    ],
    "Q1/2025": [
        # Q4 – horas negativas
        {"Colaborador": "Pedro Carvalho",  "Data": "08/01/2025", "Horas totais (decimal)": "-2.0", "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-004-01", "PEP": "Plataforma Analytics"},
        # I1 – fim de semana (Saturday 04/01/2025)
        {"Colaborador": "Carlos Oliveira", "Data": "04/01/2025", "Horas totais (decimal)": "5.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
    ],
    "Q2/2025": [
        # Q2 – data futura (2027)
        {"Colaborador": "Gabriel Souza",   "Data": "15/04/2027", "Horas totais (decimal)": "6.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-007-01", "PEP": "Hub de Integrações API"},
        # Hora extra – válido
        {"Colaborador": "João Silva",      "Data": "10/04/2025", "Horas totais (decimal)": "3.0",  "Hora extra": "Sim", "Hora sobreaviso": "",    "Código PEP": "60IT-007-01", "PEP": "Hub de Integrações API"},
    ],
    "Q3/2025": [
        # Q1 – data inválida (dia 99)
        {"Colaborador": "Fernanda Lima",   "Data": "99/07/2025", "Horas totais (decimal)": "6.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
        # I2 – alta carga semanal (14h em um único dia, acima de 24h acumulado com próxima linha → I2 no nível semanal)
        {"Colaborador": "Carlos Oliveira", "Data": "15/07/2025", "Horas totais (decimal)": "14.0", "Hora extra": "Sim", "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
        {"Colaborador": "Carlos Oliveira", "Data": "16/07/2025", "Horas totais (decimal)": "12.0", "Hora extra": "Sim", "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
    ],
    "Q4/2025": [
        # I1 – fim de semana (Saturday 04/10/2025)
        {"Colaborador": "Pedro Carvalho",  "Data": "04/10/2025", "Horas totais (decimal)": "4.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-005-01", "PEP": "Implantação ERP"},
        # I4 – duplicate João Silva
        {"Colaborador": "João Silva",      "Data": "02/10/2025", "Horas totais (decimal)": "7.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-007-01", "PEP": "Hub de Integrações API"},
    ],
    "Q1/2026": [
        # N1 + I3 – novo colaborador sem senioridade cadastrada
        {"Colaborador": "Estagiário Novo", "Data": "15/01/2026", "Horas totais (decimal)": "6.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-008-01", "PEP": "Portal do Cliente"},
        # Hora extra – válido
        {"Colaborador": "João Silva",      "Data": "09/01/2026", "Horas totais (decimal)": "2.0",  "Hora extra": "Sim", "Hora sobreaviso": "",    "Código PEP": "60IT-008-01", "PEP": "Portal do Cliente"},
    ],
    "Q2/2026": [
        # Hora sobreaviso – válido
        {"Colaborador": "Roberto Costa",   "Data": "03/04/2026", "Horas totais (decimal)": "1.5",  "Hora extra": "",    "Hora sobreaviso": "Sim", "Código PEP": "60IT-010-01", "PEP": "Upgrade Infraestrutura"},
        # I1 – fim de semana (Saturday 05/04/2026)
        {"Colaborador": "Lucas Pereira",   "Data": "05/04/2026", "Horas totais (decimal)": "3.0",  "Hora extra": "",    "Hora sobreaviso": "",    "Código PEP": "60IT-008-01", "PEP": "Portal do Cliente"},
    ],
}

FIELDS = ["Colaborador", "Data", "Horas totais (decimal)", "Hora extra", "Hora sobreaviso", "Código PEP", "PEP"]


# ── Analytics accumulators ────────────────────────────────────────────────────

cum_h = defaultdict(float)   # pep_wbs → cumulative hours
cum_c = defaultdict(float)   # pep_wbs → cumulative cost


# ── Generate reference CSVs ───────────────────────────────────────────────────

def write_ciclos():
    path = f"{OUT}/ciclos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "start_date", "end_date", "is_closed", "record_count"])
        for c in CYCLES:
            w.writerow([
                c["name"],
                c["start_date"].strftime("%Y-%m-%d"),
                c["end_date"].strftime("%Y-%m-%d"),
                "true" if c["is_closed"] else "false",
                0,
            ])
    print(f"Cycles: {path}  ({len(CYCLES)} monthly cycles)")


def write_projetos():
    path = f"{OUT}/projetos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pep_wbs", "name", "client", "manager", "budget_hours", "budget_cost", "status"])
        for p in PROJECTS:
            w.writerow([p["pep_wbs"], p["name"], p["client"], p["manager"],
                        p["budget_hours"], p["budget_cost"], p["status"]])
    print(f"Projects: {path}")


def write_rate_cards():
    path = f"{OUT}/senioridade_rate_card.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seniority_level", "valid_from", "valid_to", "hourly_rate"])
        for sen, periods in RATES.items():
            w.writerow([sen, "2024-01-01", "2024-12-31", f"{periods[2024]:.2f}"])
            w.writerow([sen, "2025-01-01", "",            f"{periods[2025]:.2f}"])
    print(f"Rate cards: {path}")


# ── Generate quarterly timesheet CSVs ─────────────────────────────────────────

def generate_timesheet(qname, qstart, qend):
    end = min(qend, TODAY)
    wd = workdays(qstart, end)
    rows = []
    q_stats = defaultdict(lambda: defaultdict(lambda: {"h": 0.0, "c": 0.0}))

    for collab, pep_wbs, hpd in ASSIGNMENTS.get(qname, []):
        p = BY_PEP[pep_wbs]
        sen = COLLABS[collab]["seniority"]
        since = COLLABS[collab]["since"]
        for d in wd:
            if d < since:
                continue
            r = rate(sen, d)
            rows.append({
                "Colaborador":            collab,
                "Data":                   d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": str(float(hpd)),
                "Hora extra":             "",
                "Hora sobreaviso":        "",
                "Código PEP":             pep_wbs,
                "PEP":                    p["name"],
            })
            q_stats[pep_wbs][collab]["h"] += hpd
            q_stats[pep_wbs][collab]["c"] += hpd * r
            cum_h[pep_wbs] += hpd
            cum_c[pep_wbs] += hpd * r

    # Baked-in extra/standby in Q4/2024 kickoff week (Maria Santos, PRJ-005)
    if qname == "Q4/2024":
        first3 = [d for d in wd if d <= date(2024, 10, 11)][:3]
        for d in first3:
            r = rate("Sênior", d)
            rows.append({
                "Colaborador": "Maria Santos", "Data": d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": "2.0", "Hora extra": "Sim", "Hora sobreaviso": "",
                "Código PEP": "60IT-005-01", "PEP": "Implantação ERP",
            })
            q_stats["60IT-005-01"]["Maria Santos"]["h"] += 2
            q_stats["60IT-005-01"]["Maria Santos"]["c"] += 2 * r
            cum_h["60IT-005-01"] += 2
            cum_c["60IT-005-01"] += 2 * r

    # Baked-in standby in Q3/2025 (Roberto Costa, PRJ-007 production incident)
    if qname == "Q3/2025":
        incident_dates = [date(2025, 8, 23), date(2025, 8, 24)]
        for d in incident_dates:
            r = rate("Pleno", d)
            rows.append({
                "Colaborador": "Roberto Costa", "Data": d.strftime("%d/%m/%Y"),
                "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "Sim",
                "Código PEP": "60IT-007-01", "PEP": "Hub de Integrações API",
            })
            q_stats["60IT-007-01"]["Roberto Costa"]["h"] += 4
            q_stats["60IT-007-01"]["Roberto Costa"]["c"] += 4 * r
            cum_h["60IT-007-01"] += 4
            cum_c["60IT-007-01"] += 4 * r

    data_rows = len(rows)
    anomalies = ANOMALY_ROWS.get(qname, [])
    rows.extend(anomalies)

    fname = f"timesheet_{qname.replace('/', '_')}.csv"
    path = f"{OUT}/{fname}"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"  {qname}: {path}  ({data_rows} data rows, {len(anomalies)} anomaly rows)")
    return q_stats


# ── Generate demo files ───────────────────────────────────────────────────────

def write_demo_files():
    # Closed cycle demo: upload rows for Jan/2024 (which will be closed) → W1
    path = f"{OUT}/timesheet_ciclo_fechado_demo.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows([
            {"Colaborador": "João Silva",      "Data": "07/01/2024", "Horas totais (decimal)": "7.0", "Hora extra": "", "Hora sobreaviso": "", "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
            {"Colaborador": "Carlos Oliveira", "Data": "08/01/2024", "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "", "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
            {"Colaborador": "Lucas Pereira",   "Data": "09/01/2024", "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "", "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
        ])
    print(f"Demo (ciclo fechado): {path}")

    # Encerrado project demo: upload for PRJ-001 after it ended → W3
    path = f"{OUT}/timesheet_projeto_encerrado_demo.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows([
            {"Colaborador": "João Silva",   "Data": "05/01/2026", "Horas totais (decimal)": "7.0", "Hora extra": "", "Hora sobreaviso": "", "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
            {"Colaborador": "Ana Ferreira", "Data": "06/01/2026", "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "", "Código PEP": "60IT-001-01", "PEP": "Transformação Digital"},
        ])
    print(f"Demo (projeto encerrado): {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

print("Generating reference CSVs...")
write_ciclos()
write_projetos()
write_rate_cards()

print("\nGenerating quarterly timesheets...")
all_q_stats = {}
for qname, qstart, qend in QUARTERS:
    all_q_stats[qname] = generate_timesheet(qname, qstart, qend)

write_demo_files()

print("\nGenerating PORTFOLIO_ANALISE.md...")

# ── Build MD ──────────────────────────────────────────────────────────────────

def fmt_r(v): return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_h(v): return f"{v:,.0f}".replace(",", ".")
def pct(a, b): return f"{a/b*100:.1f}%" if b else "—"


md_lines = []
A = md_lines.append

A("# Análise de Portfólio — PMAS Sample Dataset")
A("")
A("> **Referência:** Portfólio fictício para demonstração e testes do PMAS.")
A(f"> **Período:** Janeiro/2024 – Maio/2026 (data base: {TODAY.strftime('%d/%m/%Y')}).")
A("> **Escopo:** 10 projetos · 10 colaboradores · 29 ciclos mensais.")
A("")
A("---")
A("")

# ── Reference tables ──────────────────────────────────────────────────────────
A("## Estrutura de Referência")
A("")
A("### Colaboradores e Senioridade")
A("")
A("| Colaborador       | Nível       | Ativo desde  |")
A("|-------------------|-------------|--------------|")
for name, c in COLLABS.items():
    A(f"| {name:<17} | {c['seniority']:<11} | {PT_MONTHS[c['since'].month-1]}/{c['since'].year}        |")

A("")
A("### Tarifas Horárias")
A("")
A("| Nível       | 2024 (R$/h) | 2025+ (R$/h) |")
A("|-------------|-------------|--------------|")
for sen, r in RATES.items():
    A(f"| {sen:<11} | {r[2024]:>11.2f} | {r[2025]:>12.2f} |")

A("")
A("### Portfólio de Projetos")
A("")
A("| PEP WBS      | Nome                    | Cliente       | Gerente        | Budget Horas | Budget Custo     | Status    |")
A("|--------------|-------------------------|---------------|----------------|-------------:|------------------:|-----------|")
for p in PROJECTS:
    A(f"| {p['pep_wbs']:<12} | {p['name']:<23} | {p['client']:<13} | {p['manager']:<14} | {p['budget_hours']:>12,} | {fmt_r(p['budget_cost']):>17} | {p['status']:<9} |")

A("")
A("### Ciclos Mensais")
A("")
A("| Ciclo    | Início     | Fim        | Fechado |")
A("|----------|------------|------------|---------|")
for c in CYCLES:
    A(f"| {c['name']:<8} | {c['start_date']} | {c['end_date']} | {'Sim' if c['is_closed'] else 'Não'}     |")

A("")
A("---")
A("")

# ── Quarter details ───────────────────────────────────────────────────────────

Q_ANOMALY_DESC = {
    "Q1/2024": [("I1", "1 lançamento em fim de semana (Ana Ferreira 06/01)"),
                ("I3", "Ana Ferreira sem senioridade cadastrada — cost_per_hour não congelado"),
                ("I4", "1 linha duplicada filtrada (João Silva 02/01)")],
    "Q2/2024": [("Q5", "Carlos Oliveira 15/04 — campo de horas vazio → quarentena"),
                ("I4", "1 linha duplicada filtrada (Maria Santos 02/04)")],
    "Q3/2024": [("Q8", "Linha com nome de colaborador vazio (10/07) → quarentena"),
                ("N1", "Roberto Costa: novo colaborador detectado na ingestão")],
    "Q4/2024": [("Q6", "Amanda Torres 02/10 — horas > 24h → quarentena"),
                ("N1", "Amanda Torres: nova colaboradora"),
                ("I4", "Linhas duplicadas filtradas")],
    "Q1/2025": [("Q4", "Pedro Carvalho 08/01 — horas negativas → quarentena"),
                ("N1", "Pedro Carvalho: novo colaborador"),
                ("I1", "1 lançamento em fim de semana (Carlos Oliveira 04/01)")],
    "Q2/2025": [("Q2", "Gabriel Souza 15/04/2027 — data futura → quarentena"),
                ("N1", "Gabriel Souza: novo colaborador (aparição válida em 10/04)")],
    "Q3/2025": [("Q1", "Fernanda Lima 99/07/2025 — data inválida → quarentena"),
                ("I2", "Carlos Oliveira: 26h em dois dias consecutivos (15–16/07) — carga semanal elevada")],
    "Q4/2025": [("I1", "Pedro Carvalho 04/10 — fim de semana"),
                ("I4", "1 linha duplicada filtrada (João Silva 02/10)")],
    "Q1/2026": [("N1", "Estagiário Novo: colaborador desconhecido → info de novo cadastro"),
                ("I3", "Estagiário Novo sem senioridade — cost_per_hour não congelado")],
    "Q2/2026": [("I1", "Lucas Pereira 05/04 — fim de semana (sábado)"),
                ("I4", "1 linha duplicada filtrada")],
}

# Track running cumulative for MD
running_h = defaultdict(float)
running_c = defaultdict(float)

for qname, qstart, qend in QUARTERS:
    cap = min(qend, TODAY)
    A(f"## {qname} — {PT_MONTHS[qstart.month-1]}/{qstart.year} a {PT_MONTHS[cap.month-1]}/{cap.year}")
    A("")
    if cap < qend:
        A(f"*Ciclo parcial — dados até {cap.strftime('%d/%m/%Y')}.*")
        A("")

    qs = all_q_stats.get(qname, {})
    total_h = sum(v["h"] for pep in qs.values() for v in pep.values())
    total_c = sum(v["c"] for pep in qs.values() for v in pep.values())

    # Update running cumulative
    for pep, collabs in qs.items():
        for collab, vals in collabs.items():
            running_h[pep] += vals["h"]
            running_c[pep] += vals["c"]

    A("### Horas e Custos")
    A("")
    A("| Métrica           | Valor           |")
    A("|-------------------|-----------------|")
    A(f"| Horas registradas | {fmt_h(total_h)} h        |")
    A(f"| Custo estimado    | {fmt_r(total_c)}   |")
    A("")

    A("### Distribuição por PEP")
    A("")
    A("| PEP WBS      | Projeto               | Horas Q  | Custo Q          | Acum. H  | % Budget H |")
    A("|--------------|------------------------|----------:|------------------:|----------:|-----------:|")
    for p in PROJECTS:
        pep = p["pep_wbs"]
        if pep not in qs:
            continue
        qh = sum(v["h"] for v in qs[pep].values())
        qc = sum(v["c"] for v in qs[pep].values())
        bh = p["budget_hours"]
        A(f"| {pep:<12} | {p['name']:<22} | {fmt_h(qh):>8} h | {fmt_r(qc):>17} | {fmt_h(running_h[pep]):>8} h | {pct(running_h[pep], bh):>10} |")

    A("")
    A("### Apontamentos de Ingestão")
    A("")
    A("| Código | Tipo       | Descrição                                                                   |")
    A("|--------|------------|-----------------------------------------------------------------------------|")
    anomalies = Q_ANOMALY_DESC.get(qname, [])
    if anomalies:
        for code, desc in anomalies:
            tipo = "Quarentena" if code.startswith("Q") else "Info"
            A(f"| {code:<6} | {tipo:<10} | {desc:<75} |")
    else:
        A("| —      | —          | Nenhuma anomalia neste ciclo                                                |")
    A("")
    A("---")
    A("")

# ── Final summary ─────────────────────────────────────────────────────────────

A("## Resumo Consolidado")
A("")
A("### Status Final dos Projetos")
A("")
A("| PEP WBS      | Nome                    | Horas Consumidas | Budget H  | % H    | Custo Total      | Budget R$       | % R$   | Status EVM   |")
A("|--------------|-------------------------|----------------:|----------:|-------:|-----------------:|---------------:|-------:|--------------|")
for p in PROJECTS:
    pep = p["pep_wbs"]
    ch = running_h.get(pep, 0)
    cc = running_c.get(pep, 0)
    bh = p["budget_hours"]
    bc = p["budget_cost"]
    ph = ch/bh*100 if bh else 0
    pc = cc/bc*100 if bc else 0
    status = ("🔴 ESTOURO" if ph >= 100 or pc >= 100 else
              "⚠ ATENÇÃO" if ph >= 90 or pc >= 90 else
              "✅ OK")
    A(f"| {pep:<12} | {p['name']:<23} | {fmt_h(ch):>16} h | {bh:>9,} h | {ph:>6.1f}% | {fmt_r(cc):>16} | {fmt_r(bc):>14} | {pc:>6.1f}% | {status:<12} |")

A("")
grand_h = sum(running_h.values())
grand_c = sum(running_c.values())
A(f"**Total geral:** {fmt_h(grand_h)} h registradas · {fmt_r(grand_c)} custo estimado")
A("")

A("### Cenários de Ingestão Cobertos")
A("")
A("| Código | Arquivo              | Cenário                                       |")
A("|--------|----------------------|-----------------------------------------------|")
scenarios = [
    ("Q1", "timesheet_Q3_2025.csv",            "Data com formato impossível (99/07/2025)"),
    ("Q2", "timesheet_Q2_2025.csv",            "Data futura (15/04/2027)"),
    ("Q4", "timesheet_Q1_2025.csv",            "Horas negativas (-2.0)"),
    ("Q5", "timesheet_Q2_2024.csv",            "Campo de horas em branco"),
    ("Q6", "timesheet_Q4_2024.csv",            "Horas > 24h em um único dia (25.0)"),
    ("Q8", "timesheet_Q3_2024.csv",            "Nome de colaborador vazio"),
    ("I1", "Q1/Q1-2025/Q4-2025/Q2-2026",       "Lançamento em dia de fim de semana"),
    ("I2", "timesheet_Q3_2025.csv",            "Carga semanal > 60h (Carlos Oliveira)"),
    ("I3", "timesheet_Q1_2024.csv + Q1/2026",  "Colaborador sem senioridade cadastrada"),
    ("I4", "Todos os quarters",                "Linha duplicada filtrada"),
    ("N1", "Q3/2024 a Q2/2025 + Q1/2026",      "Novo colaborador detectado na ingestão"),
    ("W1", "timesheet_ciclo_fechado_demo.csv", "Upload para ciclo fechado"),
    ("W3", "timesheet_projeto_encerrado_demo.csv", "PEP de projeto encerrado"),
]
for code, arquivo, desc in scenarios:
    A(f"| {code:<6} | {arquivo:<20} | {desc:<45} |")

A("")
A("---")
A(f"*Gerado automaticamente por `generate_portfolio.py` em {TODAY.strftime('%d/%m/%Y')}.*")

md_path = f"{OUT}/PORTFOLIO_ANALISE.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")
print(f"Analysis: {md_path}  ({len(md_lines)} lines)")

print("\nDone. All files in:", OUT)
