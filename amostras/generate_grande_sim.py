#!/usr/bin/env python3
"""
PMAS — Grande Simulação — Gerador de Dataset Completo
======================================================
60 meses (Jan/2022–Dez/2026) · 17 projetos · 22 colaboradores
Gera CSVs separados por mês + arquivos de referência para importação.

Cenários EVM cobertos:
  ON TRACK    — 60IT-INF-01, 60IT-API-01
  BEHIND      — 60IT-TRF-01, 60IT-DAT-01, 60IT-MKT-01
  AHEAD       — 60IT-PLT-01, 60IT-IOT-01
  OVER BUDGET — 60IT-ERP-01 (encerrado 108%), 60IT-BI-01 (encerrado 111%)
  WARNING     — 60IT-SUP-01 (94%), 60IT-MOB-01 (encerrado 97%)
  COMPLETED   — 60IT-SEG-01, 60IT-CRM-01, 60IT-GOV-01, 60IT-RH-01
  RAMP-UP     — 60IT-CLD-01 (início Jan/2026)
  SPORADIC    — 60IT-INO-01 (lab interno)

Regras de ingestão cobertas:
  Q1 (data inválida), Q2 (data futura), Q4 (horas negativas),
  Q5 (horas em branco), Q6 (horas > 24), Q8 (colaborador vazio),
  I1 (fim de semana), I2 (carga semanal excessiva),
  I3 (colaborador sem senioridade), I4 (linha duplicada),
  N1 (novo colaborador auto-criado)

Uso:
  python amostras/generate_grande_sim.py
"""

import csv
import math
import os
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta

# ── Paths ─────────────────────────────────────────────────────────────────────
OUT    = os.path.join(os.path.dirname(__file__), "grande_sim")
TS_DIR = os.path.join(OUT, "timesheets")
os.makedirs(TS_DIR, exist_ok=True)

TODAY      = date(2026, 5, 28)
SIM_START  = date(2022, 1, 1)
SIM_END    = date(2026, 12, 31)

PT_MONTHS  = ["Jan","Fev","Mar","Abr","Mai","Jun",
               "Jul","Ago","Set","Out","Nov","Dez"]
TS_FIELDS  = ["Colaborador","Data","Horas totais (decimal)",
               "Hora extra","Hora sobreaviso","Código PEP","PEP"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def mlabel(y, m):
    return f"{PT_MONTHS[m-1]}/{y}"

def mend(y, m):
    return date(y, m, monthrange(y, m)[1])

def workdays(y, m, cap=None):
    """Workdays in month, optionally capped at 'cap' date."""
    s = date(y, m, 1)
    e = min(mend(y, m), cap or mend(y, m))
    if s > e:
        return []
    return [s + timedelta(days=i) for i in range((e - s).days + 1)
            if (s + timedelta(days=i)).weekday() < 5]

def iter_months(start, end):
    """Yield (year, month) from start to end inclusive."""
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m = m % 12 + 1
        if m == 1:
            y += 1

def scurve_weights(n, ramp=0.20, tail=0.20):
    """
    Return a list of n weights summing to 1.0 following an S-curve.
    ramp fraction: linearly increases; steady fraction: flat; tail: linearly decreases.
    """
    n_ramp  = max(1, round(n * ramp))
    n_tail  = max(1, round(n * tail))
    n_mid   = max(1, n - n_ramp - n_tail)
    weights = []
    for i in range(n_ramp):
        weights.append((i + 1) / n_ramp)
    for _ in range(n_mid):
        weights.append(1.0)
    for i in range(n_tail):
        weights.append(1.0 - (i + 1) / (n_tail + 1))
    # Normalize to sum=1
    total = sum(weights)
    return [w / total for w in weights]

# ── Rate cards (per year) ─────────────────────────────────────────────────────
RATES = {
    "Arquiteto":    {2022: 200, 2023: 220, 2024: 240, 2025: 260, 2026: 275},
    "Especialista": {2022: 160, 2023: 175, 2024: 190, 2025: 205, 2026: 215},
    "Sênior":       {2022: 120, 2023: 132, 2024: 145, 2025: 158, 2026: 165},
    "Pleno":        {2022:  80, 2023:  88, 2024:  97, 2025: 106, 2026: 112},
    "Júnior":       {2022:  50, 2023:  55, 2024:  61, 2025:  67, 2026:  71},
    "Trainee":      {2022:  25, 2023:  28, 2024:  31, 2025:  34, 2026:  36},
}

def get_rate(seniority, d):
    return RATES.get(seniority, {}).get(d.year, 0.0)

# ── Collaborators ─────────────────────────────────────────────────────────────
COLLABS = {
    # Arquiteto
    "Rodrigo Andrade":  {"seniority": "Arquiteto",    "since": date(2022, 1,  1)},
    "Beatriz Nunes":    {"seniority": "Arquiteto",    "since": date(2022, 7,  1)},
    # Especialista
    "Marcos Tavares":   {"seniority": "Especialista", "since": date(2022, 1,  1)},
    "Juliana Ramos":    {"seniority": "Especialista", "since": date(2022, 1,  1)},
    "Thiago Campos":    {"seniority": "Especialista", "since": date(2023, 4,  1)},
    # Sênior
    "João Silva":       {"seniority": "Sênior",       "since": date(2022, 1,  1)},
    "Maria Santos":     {"seniority": "Sênior",       "since": date(2022, 1,  1)},
    "Carlos Oliveira":  {"seniority": "Sênior",       "since": date(2022, 7,  1)},
    "Ana Ferreira":     {"seniority": "Sênior",       "since": date(2023, 1,  1)},
    "Roberto Costa":    {"seniority": "Sênior",       "since": date(2022, 1,  1)},
    # Pleno
    "Lucas Pereira":    {"seniority": "Pleno",        "since": date(2022, 1,  1)},
    "Fernanda Lima":    {"seniority": "Pleno",        "since": date(2022, 1,  1)},
    "Gabriel Souza":    {"seniority": "Pleno",        "since": date(2023, 7,  1)},
    "Amanda Torres":    {"seniority": "Pleno",        "since": date(2024, 1,  1)},
    "Rafael Gomes":     {"seniority": "Pleno",        "since": date(2022, 1,  1)},
    "Camila Barbosa":   {"seniority": "Pleno",        "since": date(2023, 4,  1)},
    # Júnior
    "Pedro Carvalho":   {"seniority": "Júnior",       "since": date(2022, 1,  1)},
    "Leticia Moreira":  {"seniority": "Júnior",       "since": date(2023, 1,  1)},
    "Diego Martins":    {"seniority": "Júnior",       "since": date(2023, 7,  1)},
    "Priscila Farias":  {"seniority": "Júnior",       "since": date(2024, 1,  1)},
    # Trainee
    "Vinícius Mendes":  {"seniority": "Trainee",      "since": date(2024, 1,  1)},
    "Sara Alves":       {"seniority": "Trainee",      "since": date(2024, 7,  1)},
}

# ── Projects ──────────────────────────────────────────────────────────────────
# budgets are computed in pass-2; placeholder here
PROJECTS_DEF = [
    # MEGA — 60 meses
    {"pep": "60IT-INF-01", "name": "Plataforma Core Enterprise",
     "client": "Banco Meridional",   "manager": "Rodrigo Andrade",
     "pstart": date(2022,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "on_track"},

    {"pep": "60IT-TRF-01", "name": "Transformação Digital 360°",
     "client": "GrupoVarejo S.A.",   "manager": "Beatriz Nunes",
     "pstart": date(2022,7,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "behind"},

    # LONG — 48 meses
    {"pep": "60IT-ERP-01", "name": "Implantação ERP Global",
     "client": "IndustriaMax",       "manager": "Marcos Tavares",
     "pstart": date(2022,1,1),  "pend": date(2025,12,31), "status": "encerrado",
     "completion_date": date(2025,12,31), "evm": "over_budget"},

    {"pep": "60IT-PLT-01", "name": "Migração de Plataforma",
     "client": "TechlogicBR",        "manager": "Juliana Ramos",
     "pstart": date(2023,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "ahead"},

    # MEDIUM-LONG — 30-36 meses
    {"pep": "60IT-SEG-01", "name": "Programa de Cibersegurança",
     "client": "FinanceSeguro",      "manager": "Thiago Campos",
     "pstart": date(2022,1,1),  "pend": date(2024,12,31), "status": "encerrado",
     "completion_date": date(2024,12,31), "evm": "completed"},

    {"pep": "60IT-CRM-01", "name": "CRM Enterprise",
     "client": "RetailPlus",         "manager": "João Silva",
     "pstart": date(2022,1,1),  "pend": date(2024,6,30),  "status": "encerrado",
     "completion_date": date(2024,6,30), "evm": "completed"},

    {"pep": "60IT-GOV-01", "name": "Governança & Compliance",
     "client": "Holding Alfa",       "manager": "Maria Santos",
     "pstart": date(2023,1,1),  "pend": date(2024,12,31), "status": "encerrado",
     "completion_date": date(2024,12,31), "evm": "completed"},

    {"pep": "60IT-SUP-01", "name": "Sustentação & Operações",
     "client": "MultiCliente",       "manager": "Roberto Costa",
     "pstart": date(2022,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "warning"},

    # MEDIUM — 24-36 meses
    {"pep": "60IT-DAT-01", "name": "Data Lakehouse",
     "client": "AnaliticosBR",       "manager": "Beatriz Nunes",
     "pstart": date(2024,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "behind"},

    {"pep": "60IT-RH-01", "name": "RH Digital",
     "client": "Capital Humano",     "manager": "Carlos Oliveira",
     "pstart": date(2023,7,1),  "pend": date(2024,12,31), "status": "encerrado",
     "completion_date": date(2024,12,31), "evm": "completed"},

    {"pep": "60IT-API-01", "name": "Gateway de APIs",
     "client": "EcossistemaTech",    "manager": "Ana Ferreira",
     "pstart": date(2024,7,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "on_track"},

    {"pep": "60IT-INO-01", "name": "Lab de Inovação",
     "client": "Interno",            "manager": "Rodrigo Andrade",
     "pstart": date(2024,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "sporadic"},

    # SHORT — 12-18 meses
    {"pep": "60IT-MOB-01", "name": "App Mobile B2C",
     "client": "ConsumerApp",        "manager": "Gabriel Souza",
     "pstart": date(2024,7,1),  "pend": date(2025,12,31), "status": "encerrado",
     "completion_date": date(2025,12,31), "evm": "warning"},

    {"pep": "60IT-MKT-01", "name": "Plataforma de Marketing",
     "client": "MídiaDigital",       "manager": "Camila Barbosa",
     "pstart": date(2025,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "behind"},

    {"pep": "60IT-BI-01",  "name": "BI & Analytics",
     "client": "DataDriven",         "manager": "Thiago Campos",
     "pstart": date(2025,1,1),  "pend": date(2025,12,31), "status": "encerrado",
     "completion_date": date(2025,12,31), "evm": "over_budget"},

    {"pep": "60IT-IOT-01", "name": "IoT Industrial",
     "client": "FábricaSmart",       "manager": "Lucas Pereira",
     "pstart": date(2025,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "ahead"},

    {"pep": "60IT-CLD-01", "name": "Cloud Migration",
     "client": "TechlogicBR",        "manager": "Juliana Ramos",
     "pstart": date(2026,1,1),  "pend": date(2026,12,31), "status": "ativo",
     "evm": "ramp_up"},
]
BY_PEP = {p["pep"]: p for p in PROJECTS_DEF}

# ── Budget scenario multipliers (budget = actual × factor) ───────────────────
# factor > 1  → on track / budget available
# factor < 1  → over budget
EVM_FACTOR = {
    "on_track":    1.13,   # 88% consumed
    "behind":      1.42,   # consumed but less than planned % (65-70%)
    "ahead":       1.35,   # 74% consumed, ahead
    "over_budget": 0.92,   # 109% consumed
    "completed":   1.06,   # 94% consumed, finished
    "warning":     1.04,   # 96% consumed
    "sporadic":    1.60,   # 62% consumed, underutilized
    "ramp_up":     2.80,   # only 36% consumed so far (new project)
}

# Cost budget as multiple of hours budget × average blended rate
# (calibrated per project based on team seniority mix)
COST_RATE = {
    "60IT-INF-01": 165,   # high — Arquiteto + Especialista heavy
    "60IT-TRF-01": 155,
    "60IT-ERP-01": 145,
    "60IT-PLT-01": 140,
    "60IT-SEG-01": 150,
    "60IT-CRM-01": 110,
    "60IT-GOV-01": 120,
    "60IT-SUP-01": 108,
    "60IT-DAT-01": 145,
    "60IT-RH-01":  115,
    "60IT-API-01": 120,
    "60IT-INO-01": 165,
    "60IT-MOB-01": 105,
    "60IT-MKT-01": 108,
    "60IT-BI-01":  145,
    "60IT-IOT-01": 110,
    "60IT-CLD-01": 135,
}

# ── Regular assignments: (pep, collab, date_start, date_end, daily_hours) ────
# daily_hours = hours this person spends on this project each workday
ASSIGNMENTS = [
    # ══ 60IT-INF-01: Plataforma Core Enterprise (Jan/2022 – Dez/2026) ══════
    # Phase 1 — Architecture & Foundation (Jan/2022–Dec/2022)
    ("60IT-INF-01", "Rodrigo Andrade",  date(2022,1,1),  date(2022,12,31), 5),
    ("60IT-INF-01", "Marcos Tavares",   date(2022,1,1),  date(2022,12,31), 4),
    ("60IT-INF-01", "João Silva",       date(2022,1,1),  date(2022,12,31), 4),
    ("60IT-INF-01", "Pedro Carvalho",   date(2022,7,1),  date(2022,12,31), 3),
    # Phase 2 — Full Development (Jan/2023–Dec/2024)
    ("60IT-INF-01", "Rodrigo Andrade",  date(2023,1,1),  date(2024,12,31), 5),
    ("60IT-INF-01", "Marcos Tavares",   date(2023,1,1),  date(2024,12,31), 5),
    ("60IT-INF-01", "Ana Ferreira",     date(2023,1,1),  date(2024,12,31), 4),
    ("60IT-INF-01", "Lucas Pereira",    date(2023,1,1),  date(2024,6,30),  4),
    ("60IT-INF-01", "Leticia Moreira",  date(2023,1,1),  date(2024,12,31), 3),
    ("60IT-INF-01", "Pedro Carvalho",   date(2023,1,1),  date(2024,12,31), 3),
    # Phase 3 — Integration & Testing (Jan/2025–Jun/2025)
    ("60IT-INF-01", "Rodrigo Andrade",  date(2025,1,1),  date(2025,6,30),  6),
    ("60IT-INF-01", "Ana Ferreira",     date(2025,1,1),  date(2025,6,30),  5),
    ("60IT-INF-01", "Amanda Torres",    date(2025,1,1),  date(2025,6,30),  4),
    ("60IT-INF-01", "Priscila Farias",  date(2025,1,1),  date(2025,6,30),  4),
    ("60IT-INF-01", "Vinícius Mendes",  date(2025,1,1),  date(2025,6,30),  3),
    # Phase 4 — Stabilization & Go-live (Jul/2025–Dez/2026)
    ("60IT-INF-01", "Rodrigo Andrade",  date(2025,7,1),  date(2026,12,31), 4),
    ("60IT-INF-01", "Ana Ferreira",     date(2025,7,1),  date(2026,12,31), 3),
    ("60IT-INF-01", "Amanda Torres",    date(2025,7,1),  date(2026,12,31), 3),
    ("60IT-INF-01", "Vinícius Mendes",  date(2025,7,1),  date(2026,12,31), 2),

    # ══ 60IT-TRF-01: Transformação Digital 360° (Jul/2022 – Dez/2026) ═══════
    # Phase 1 (Jul/2022–Jun/2023)
    ("60IT-TRF-01", "Beatriz Nunes",    date(2022,7,1),  date(2023,6,30),  5),
    ("60IT-TRF-01", "Juliana Ramos",    date(2022,7,1),  date(2023,6,30),  4),
    ("60IT-TRF-01", "Maria Santos",     date(2022,7,1),  date(2023,6,30),  4),
    ("60IT-TRF-01", "Rafael Gomes",     date(2022,7,1),  date(2023,3,31),  3),
    # Phase 2 (Jul/2023–Jun/2025) — behind schedule: smaller team than planned
    ("60IT-TRF-01", "Beatriz Nunes",    date(2023,7,1),  date(2025,6,30),  5),
    ("60IT-TRF-01", "Juliana Ramos",    date(2023,7,1),  date(2025,6,30),  4),
    ("60IT-TRF-01", "Gabriel Souza",    date(2023,7,1),  date(2025,6,30),  4),
    ("60IT-TRF-01", "Camila Barbosa",   date(2023,7,1),  date(2025,6,30),  3),
    # Phase 3 (Jul/2025–Dez/2026) — recovery sprint
    ("60IT-TRF-01", "Beatriz Nunes",    date(2025,7,1),  date(2026,12,31), 6),
    ("60IT-TRF-01", "Juliana Ramos",    date(2025,7,1),  date(2026,12,31), 5),
    ("60IT-TRF-01", "Thiago Campos",    date(2025,7,1),  date(2026,12,31), 4),
    ("60IT-TRF-01", "Diego Martins",    date(2025,7,1),  date(2026,12,31), 3),

    # ══ 60IT-ERP-01: Implantação ERP Global (Jan/2022 – Dez/2025) ═══════════
    # Phase 1 (Jan/2022–Jun/2023)
    ("60IT-ERP-01", "Marcos Tavares",   date(2022,1,1),  date(2023,6,30),  5),
    ("60IT-ERP-01", "João Silva",       date(2022,1,1),  date(2023,6,30),  4),
    ("60IT-ERP-01", "Fernanda Lima",    date(2022,1,1),  date(2023,12,31), 4),
    ("60IT-ERP-01", "Carlos Oliveira",  date(2022,7,1),  date(2023,12,31), 4),
    ("60IT-ERP-01", "Pedro Carvalho",   date(2022,1,1),  date(2022,12,31), 3),
    # Phase 2 (Jul/2023–Jun/2024)
    ("60IT-ERP-01", "Marcos Tavares",   date(2023,7,1),  date(2024,6,30),  5),
    ("60IT-ERP-01", "Thiago Campos",    date(2023,7,1),  date(2024,6,30),  5),
    ("60IT-ERP-01", "Carlos Oliveira",  date(2024,1,1),  date(2024,6,30),  4),
    ("60IT-ERP-01", "Leticia Moreira",  date(2023,7,1),  date(2024,6,30),  4),
    ("60IT-ERP-01", "Fernanda Lima",    date(2024,1,1),  date(2024,6,30),  4),
    # Phase 3 — Go-live (Jul/2024–Dez/2025): intense, over budget
    ("60IT-ERP-01", "Marcos Tavares",   date(2024,7,1),  date(2025,12,31), 7),
    ("60IT-ERP-01", "Thiago Campos",    date(2024,7,1),  date(2025,12,31), 6),
    ("60IT-ERP-01", "Carlos Oliveira",  date(2024,7,1),  date(2025,12,31), 5),
    ("60IT-ERP-01", "Fernanda Lima",    date(2024,7,1),  date(2025,12,31), 5),
    ("60IT-ERP-01", "Leticia Moreira",  date(2024,7,1),  date(2025,12,31), 4),
    ("60IT-ERP-01", "Diego Martins",    date(2024,7,1),  date(2025,12,31), 3),

    # ══ 60IT-PLT-01: Migração de Plataforma (Jan/2023 – Dez/2026) ═══════════
    # Phase 1 (Jan/2023–Jun/2024)
    ("60IT-PLT-01", "Juliana Ramos",    date(2023,1,1),  date(2024,6,30),  5),
    ("60IT-PLT-01", "Ana Ferreira",     date(2023,1,1),  date(2024,6,30),  4),
    ("60IT-PLT-01", "Rafael Gomes",     date(2023,1,1),  date(2024,6,30),  4),
    ("60IT-PLT-01", "Leticia Moreira",  date(2023,7,1),  date(2024,6,30),  3),
    # Phase 2 (Jul/2024–Dez/2025)
    ("60IT-PLT-01", "Juliana Ramos",    date(2024,7,1),  date(2025,12,31), 5),
    ("60IT-PLT-01", "Thiago Campos",    date(2024,7,1),  date(2025,12,31), 4),
    ("60IT-PLT-01", "Rafael Gomes",     date(2024,7,1),  date(2025,12,31), 4),
    ("60IT-PLT-01", "Diego Martins",    date(2024,7,1),  date(2025,12,31), 3),
    ("60IT-PLT-01", "Priscila Farias",  date(2024,7,1),  date(2025,12,31), 3),
    # Phase 3 (Jan/2026–Dez/2026)
    ("60IT-PLT-01", "Juliana Ramos",    date(2026,1,1),  date(2026,12,31), 5),
    ("60IT-PLT-01", "Rafael Gomes",     date(2026,1,1),  date(2026,12,31), 4),
    ("60IT-PLT-01", "Diego Martins",    date(2026,1,1),  date(2026,12,31), 3),

    # ══ 60IT-SEG-01: Cibersegurança (Jan/2022 – Dez/2024) ═══════════════════
    ("60IT-SEG-01", "Maria Santos",     date(2022,1,1),  date(2023,3,31),  4),
    ("60IT-SEG-01", "Carlos Oliveira",  date(2022,7,1),  date(2023,3,31),  4),
    ("60IT-SEG-01", "Pedro Carvalho",   date(2022,1,1),  date(2022,6,30),  3),
    ("60IT-SEG-01", "Thiago Campos",    date(2023,4,1),  date(2024,12,31), 5),
    ("60IT-SEG-01", "Fernanda Lima",    date(2023,4,1),  date(2024,12,31), 4),
    ("60IT-SEG-01", "Leticia Moreira",  date(2023,4,1),  date(2024,12,31), 3),

    # ══ 60IT-CRM-01: CRM Enterprise (Jan/2022 – Jun/2024) ════════════════════
    ("60IT-CRM-01", "João Silva",       date(2022,1,1),  date(2023,6,30),  4),
    ("60IT-CRM-01", "Rafael Gomes",     date(2022,1,1),  date(2023,6,30),  4),
    ("60IT-CRM-01", "Lucas Pereira",    date(2022,1,1),  date(2023,12,31), 3),
    ("60IT-CRM-01", "Camila Barbosa",   date(2023,4,1),  date(2024,6,30),  4),
    ("60IT-CRM-01", "Gabriel Souza",    date(2023,7,1),  date(2024,6,30),  3),
    ("60IT-CRM-01", "Diego Martins",    date(2023,7,1),  date(2024,6,30),  3),

    # ══ 60IT-GOV-01: Governança & Compliance (Jan/2023 – Dez/2024) ══════════
    ("60IT-GOV-01", "Maria Santos",     date(2023,1,1),  date(2024,12,31), 3),
    ("60IT-GOV-01", "Juliana Ramos",    date(2023,1,1),  date(2023,12,31), 3),
    ("60IT-GOV-01", "Carlos Oliveira",  date(2023,7,1),  date(2024,12,31), 3),
    ("60IT-GOV-01", "Amanda Torres",    date(2024,1,1),  date(2024,12,31), 2),

    # ══ 60IT-SUP-01: Sustentação & Operações (Jan/2022 – Dez/2026) ══════════
    ("60IT-SUP-01", "Roberto Costa",    date(2022,1,1),  date(2026,12,31), 3),
    ("60IT-SUP-01", "Rafael Gomes",     date(2022,1,1),  date(2026,12,31), 3),
    ("60IT-SUP-01", "Lucas Pereira",    date(2022,1,1),  date(2023,12,31), 2),
    ("60IT-SUP-01", "Diego Martins",    date(2023,7,1),  date(2026,12,31), 2),
    ("60IT-SUP-01", "Sara Alves",       date(2024,7,1),  date(2026,12,31), 2),

    # ══ 60IT-DAT-01: Data Lakehouse (Jan/2024 – Dez/2026) ═══════════════════
    ("60IT-DAT-01", "Beatriz Nunes",    date(2024,1,1),  date(2026,12,31), 5),
    ("60IT-DAT-01", "Thiago Campos",    date(2024,1,1),  date(2025,6,30),  4),
    ("60IT-DAT-01", "Amanda Torres",    date(2024,1,1),  date(2025,12,31), 3),
    ("60IT-DAT-01", "Priscila Farias",  date(2024,7,1),  date(2025,12,31), 3),
    ("60IT-DAT-01", "Thiago Campos",    date(2025,7,1),  date(2026,12,31), 4),
    ("60IT-DAT-01", "Vinícius Mendes",  date(2025,1,1),  date(2026,12,31), 2),
    ("60IT-DAT-01", "Sara Alves",       date(2024,7,1),  date(2025,12,31), 2),

    # ══ 60IT-RH-01: RH Digital (Jul/2023 – Dez/2024) ════════════════════════
    ("60IT-RH-01",  "Carlos Oliveira",  date(2023,7,1),  date(2024,12,31), 4),
    ("60IT-RH-01",  "Camila Barbosa",   date(2023,7,1),  date(2024,12,31), 4),
    ("60IT-RH-01",  "Leticia Moreira",  date(2023,7,1),  date(2024,12,31), 3),
    ("60IT-RH-01",  "Gabriel Souza",    date(2023,7,1),  date(2024,12,31), 3),

    # ══ 60IT-API-01: Gateway de APIs (Jul/2024 – Dez/2026) ══════════════════
    ("60IT-API-01", "Ana Ferreira",     date(2024,7,1),  date(2026,12,31), 4),
    ("60IT-API-01", "Gabriel Souza",    date(2024,7,1),  date(2025,12,31), 4),
    ("60IT-API-01", "Camila Barbosa",   date(2024,7,1),  date(2026,12,31), 3),
    ("60IT-API-01", "Diego Martins",    date(2024,7,1),  date(2025,6,30),  3),
    ("60IT-API-01", "Priscila Farias",  date(2025,1,1),  date(2026,12,31), 3),

    # ══ 60IT-INO-01: Lab de Inovação (Jan/2024 – Dez/2026) — esporádico ═════
    ("60IT-INO-01", "Rodrigo Andrade",  date(2024,1,1),  date(2026,12,31), 2),
    ("60IT-INO-01", "Beatriz Nunes",    date(2024,1,1),  date(2025,12,31), 2),
    ("60IT-INO-01", "Thiago Campos",    date(2024,1,1),  date(2025,6,30),  2),
    ("60IT-INO-01", "Vinícius Mendes",  date(2024,1,1),  date(2026,12,31), 2),

    # ══ 60IT-MOB-01: App Mobile B2C (Jul/2024 – Dez/2025) ═══════════════════
    ("60IT-MOB-01", "Gabriel Souza",    date(2024,7,1),  date(2025,12,31), 6),
    ("60IT-MOB-01", "Camila Barbosa",   date(2024,7,1),  date(2025,12,31), 5),
    ("60IT-MOB-01", "Diego Martins",    date(2024,7,1),  date(2025,12,31), 4),
    ("60IT-MOB-01", "Sara Alves",       date(2024,7,1),  date(2025,12,31), 3),

    # ══ 60IT-MKT-01: Plataforma de Marketing (Jan/2025 – Dez/2026) ══════════
    ("60IT-MKT-01", "Camila Barbosa",   date(2025,1,1),  date(2026,12,31), 5),
    ("60IT-MKT-01", "Fernanda Lima",    date(2025,1,1),  date(2026,12,31), 4),
    ("60IT-MKT-01", "Priscila Farias",  date(2025,7,1),  date(2026,12,31), 3),
    ("60IT-MKT-01", "Vinícius Mendes",  date(2025,7,1),  date(2026,12,31), 2),

    # ══ 60IT-BI-01: BI & Analytics (Jan/2025 – Dez/2025) — over budget ══════
    # Large team + crises → over budget
    ("60IT-BI-01",  "Thiago Campos",    date(2025,1,1),  date(2025,12,31), 6),
    ("60IT-BI-01",  "Ana Ferreira",     date(2025,1,1),  date(2025,6,30),  4),
    ("60IT-BI-01",  "Priscila Farias",  date(2025,1,1),  date(2025,12,31), 4),
    ("60IT-BI-01",  "Amanda Torres",    date(2025,1,1),  date(2025,12,31), 3),
    ("60IT-BI-01",  "Sara Alves",       date(2025,1,1),  date(2025,12,31), 3),

    # ══ 60IT-IOT-01: IoT Industrial (Jan/2025 – Dez/2026) — ahead ════════════
    ("60IT-IOT-01", "Lucas Pereira",    date(2025,1,1),  date(2026,12,31), 5),
    ("60IT-IOT-01", "Fernanda Lima",    date(2025,1,1),  date(2026,12,31), 4),
    ("60IT-IOT-01", "Diego Martins",    date(2025,1,1),  date(2026,12,31), 4),
    ("60IT-IOT-01", "Priscila Farias",  date(2025,7,1),  date(2026,12,31), 3),

    # ══ 60IT-CLD-01: Cloud Migration (Jan/2026 – Dez/2026) — ramp-up ════════
    ("60IT-CLD-01", "Juliana Ramos",    date(2026,1,1),  date(2026,12,31), 6),
    ("60IT-CLD-01", "Carlos Oliveira",  date(2026,1,1),  date(2026,12,31), 5),
    ("60IT-CLD-01", "Leticia Moreira",  date(2026,1,1),  date(2026,12,31), 4),
    ("60IT-CLD-01", "Vinícius Mendes",  date(2026,1,1),  date(2026,12,31), 3),
]

# ── Crisis months — extra hours (Hora extra = Sim) ────────────────────────────
# (pep, collab, year, month, extra_h_per_day, n_crisis_days)
CRISES = [
    # ERP Go-live sprint Nov-Dez/2025
    ("60IT-ERP-01", "Marcos Tavares",   2025, 11, 3.0, 10),
    ("60IT-ERP-01", "Marcos Tavares",   2025, 12, 3.5, 12),
    ("60IT-ERP-01", "Thiago Campos",    2025, 11, 2.5,  9),
    ("60IT-ERP-01", "Thiago Campos",    2025, 12, 3.0, 12),
    ("60IT-ERP-01", "Carlos Oliveira",  2025, 11, 2.0,  8),
    ("60IT-ERP-01", "Carlos Oliveira",  2025, 12, 2.5, 10),
    ("60IT-ERP-01", "Fernanda Lima",    2025, 12, 2.0,  8),
    # INF-01 Integration sprint Abr/2024
    ("60IT-INF-01", "Rodrigo Andrade",  2024,  4, 2.0,  8),
    ("60IT-INF-01", "Ana Ferreira",     2024,  4, 1.5,  6),
    # TRF-01 Regulatory deadline Mar/2025
    ("60IT-TRF-01", "Beatriz Nunes",    2025,  3, 2.5,  8),
    ("60IT-TRF-01", "Juliana Ramos",    2025,  3, 2.0,  8),
    ("60IT-TRF-01", "Thiago Campos",    2025,  3, 2.0,  6),
    # MOB-01 Launch sprint Nov/2025
    ("60IT-MOB-01", "Gabriel Souza",    2025, 11, 3.0, 10),
    ("60IT-MOB-01", "Camila Barbosa",   2025, 11, 2.5,  8),
    ("60IT-MOB-01", "Diego Martins",    2025, 11, 2.0,  7),
    # BI-01 Year-end crunch Dez/2025 — principal causa do over-budget
    ("60IT-BI-01",  "Thiago Campos",    2025, 11, 3.0, 12),
    ("60IT-BI-01",  "Thiago Campos",    2025, 12, 4.0, 15),
    ("60IT-BI-01",  "Priscila Farias",  2025, 11, 2.0, 10),
    ("60IT-BI-01",  "Priscila Farias",  2025, 12, 3.0, 12),
    ("60IT-BI-01",  "Amanda Torres",    2025, 12, 2.0, 10),
    # IOT-01 Factory launch sprint Feb/2026
    ("60IT-IOT-01", "Lucas Pereira",    2026,  2, 2.5,  8),
    ("60IT-IOT-01", "Diego Martins",    2026,  2, 2.0,  6),
    # INF-01 final sprint Mar/2026
    ("60IT-INF-01", "Rodrigo Andrade",  2026,  3, 2.0,  6),
    ("60IT-INF-01", "Ana Ferreira",     2026,  3, 1.5,  5),
    # PLT-01 migration go-live Feb/2026
    ("60IT-PLT-01", "Juliana Ramos",    2026,  2, 2.0,  7),
    ("60IT-PLT-01", "Thiago Campos",    2026,  2, 1.5,  6),
]

# ── Standby — Sobreaviso ──────────────────────────────────────────────────────
# SUP-01: Roberto + Rafael on-call every month
# IOT-01: Lucas + Diego on-call every month (factory monitoring)
# Structure: (pep, collab, pstart, pend, standby_days_per_month, standby_hours_each)
STANDBY_CONFIG = [
    ("60IT-SUP-01", "Roberto Costa",  date(2022,1,1), date(2026,12,31), 3, 2.0),
    ("60IT-SUP-01", "Rafael Gomes",   date(2022,1,1), date(2026,12,31), 2, 2.0),
    ("60IT-IOT-01", "Lucas Pereira",  date(2025,1,1), date(2026,12,31), 3, 3.0),
    ("60IT-IOT-01", "Diego Martins",  date(2025,7,1), date(2026,12,31), 2, 2.5),
    ("60IT-INF-01", "Rodrigo Andrade",date(2025,7,1), date(2026,12,31), 1, 2.0),
]

# ── Anomaly rows (ingestion rule validation) ──────────────────────────────────
# Distributed across 16 different months, covering all rules
ANOMALY_ROWS = {
    # Feb/2022 — I1 (fim de semana Sab 05/02) + I4 (duplicata)
    (2022, 2): [
        {"Colaborador": "Rodrigo Andrade", "Data": "05/02/2022",
         "Horas totais (decimal)": "5.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-INF-01", "PEP": "Plataforma Core Enterprise"},
        {"Colaborador": "Marcos Tavares",  "Data": "01/02/2022",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-INF-01", "PEP": "Plataforma Core Enterprise"},
    ],
    # Mai/2022 — Q5 (horas em branco)
    (2022, 5): [
        {"Colaborador": "João Silva",      "Data": "10/05/2022",
         "Horas totais (decimal)": "",     "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-CRM-01", "PEP": "CRM Enterprise"},
    ],
    # Ago/2022 — Q8 (colaborador vazio)
    (2022, 8): [
        {"Colaborador": "",                "Data": "15/08/2022",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-ERP-01", "PEP": "Implantação ERP Global"},
    ],
    # Nov/2022 — Q6 (horas > 24)
    (2022, 11): [
        {"Colaborador": "Fernanda Lima",   "Data": "07/11/2022",
         "Horas totais (decimal)": "25.5", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-ERP-01", "PEP": "Implantação ERP Global"},
    ],
    # Fev/2023 — Q4 (horas negativas) + I1 (Sáb 04/02/2023)
    (2023, 2): [
        {"Colaborador": "Pedro Carvalho",  "Data": "08/02/2023",
         "Horas totais (decimal)": "-3.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-INF-01", "PEP": "Plataforma Core Enterprise"},
        {"Colaborador": "Leticia Moreira", "Data": "04/02/2023",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-INF-01", "PEP": "Plataforma Core Enterprise"},
    ],
    # Jun/2023 — Q2 (data futura 2028)
    (2023, 6): [
        {"Colaborador": "Ana Ferreira",    "Data": "15/06/2028",
         "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-PLT-01", "PEP": "Migração de Plataforma"},
    ],
    # Set/2023 — Q1 (data impossível: dia 32)
    (2023, 9): [
        {"Colaborador": "Carlos Oliveira", "Data": "32/09/2023",
         "Horas totais (decimal)": "5.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-ERP-01", "PEP": "Implantação ERP Global"},
    ],
    # Dez/2023 — I2 (carga semanal excessiva 14+14h) + I3+N1 (sem senioridade)
    (2023, 12): [
        {"Colaborador": "Marcos Tavares",  "Data": "11/12/2023",
         "Horas totais (decimal)": "14.0", "Hora extra": "Sim", "Hora sobreaviso": "",
         "Código PEP": "60IT-ERP-01", "PEP": "Implantação ERP Global"},
        {"Colaborador": "Marcos Tavares",  "Data": "12/12/2023",
         "Horas totais (decimal)": "14.0", "Hora extra": "Sim", "Hora sobreaviso": "",
         "Código PEP": "60IT-ERP-01", "PEP": "Implantação ERP Global"},
        {"Colaborador": "Estágio Rotativo","Data": "04/12/2023",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-INF-01", "PEP": "Plataforma Core Enterprise"},
    ],
    # Abr/2024 — N1+I3 (Consultor sem senioridade)
    (2024, 4): [
        {"Colaborador": "Consultor Freelance", "Data": "08/04/2024",
         "Horas totais (decimal)": "8.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-DAT-01", "PEP": "Data Lakehouse"},
    ],
    # Ago/2024 — Q5 (horas em branco) + I4 (duplicata)
    (2024, 8): [
        {"Colaborador": "Amanda Torres",   "Data": "12/08/2024",
         "Horas totais (decimal)": "",     "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-DAT-01", "PEP": "Data Lakehouse"},
        {"Colaborador": "Gabriel Souza",   "Data": "01/08/2024",
         "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-MOB-01", "PEP": "App Mobile B2C"},
    ],
    # Dez/2024 — I1 (Sáb 07/12/2024) + Q8 (vazio)
    (2024, 12): [
        {"Colaborador": "Diego Martins",   "Data": "07/12/2024",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-API-01", "PEP": "Gateway de APIs"},
        {"Colaborador": "",                "Data": "10/12/2024",
         "Horas totais (decimal)": "5.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-DAT-01", "PEP": "Data Lakehouse"},
    ],
    # Mar/2025 — Q4 (negativo)
    (2025, 3): [
        {"Colaborador": "Sara Alves",      "Data": "05/03/2025",
         "Horas totais (decimal)": "-1.5", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-MOB-01", "PEP": "App Mobile B2C"},
    ],
    # Jul/2025 — Q2 (futura) + Q6 (>24h)
    (2025, 7): [
        {"Colaborador": "Vinícius Mendes", "Data": "20/07/2028",
         "Horas totais (decimal)": "3.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-DAT-01", "PEP": "Data Lakehouse"},
        {"Colaborador": "Diego Martins",   "Data": "14/07/2025",
         "Horas totais (decimal)": "26.0", "Hora extra": "Sim", "Hora sobreaviso": "",
         "Código PEP": "60IT-IOT-01", "PEP": "IoT Industrial"},
    ],
    # Out/2025 — Q1 (impossível) + I4 (duplicata)
    (2025, 10): [
        {"Colaborador": "Priscila Farias", "Data": "99/10/2025",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-MKT-01", "PEP": "Plataforma de Marketing"},
        {"Colaborador": "Camila Barbosa",  "Data": "01/10/2025",
         "Horas totais (decimal)": "5.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-MKT-01", "PEP": "Plataforma de Marketing"},
    ],
    # Fev/2026 — I3+N1 (terceirizado sem senioridade) + I2 (carga excessiva)
    (2026, 2): [
        {"Colaborador": "Técnico Terceirizado", "Data": "10/02/2026",
         "Horas totais (decimal)": "6.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-CLD-01", "PEP": "Cloud Migration"},
        {"Colaborador": "Juliana Ramos",   "Data": "09/02/2026",
         "Horas totais (decimal)": "12.0", "Hora extra": "Sim", "Hora sobreaviso": "",
         "Código PEP": "60IT-PLT-01", "PEP": "Migração de Plataforma"},
        {"Colaborador": "Juliana Ramos",   "Data": "10/02/2026",
         "Horas totais (decimal)": "12.0", "Hora extra": "Sim", "Hora sobreaviso": "",
         "Código PEP": "60IT-PLT-01", "PEP": "Migração de Plataforma"},
    ],
    # Abr/2026 — Q5 (branco) + I1 (Sáb 04/04/2026)
    (2026, 4): [
        {"Colaborador": "Carlos Oliveira", "Data": "14/04/2026",
         "Horas totais (decimal)": "",     "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-CLD-01", "PEP": "Cloud Migration"},
        {"Colaborador": "Leticia Moreira", "Data": "04/04/2026",
         "Horas totais (decimal)": "4.0", "Hora extra": "", "Hora sobreaviso": "",
         "Código PEP": "60IT-CLD-01", "PEP": "Cloud Migration"},
    ],
}

# ═════════════════════════════════════════════════════════════════════════════
# PASS 1 — compute actual consumption per project
# ═════════════════════════════════════════════════════════════════════════════

print("Calculando consumo real por projeto...")

pep_total_hours: dict[str, float] = defaultdict(float)
pep_total_cost:  dict[str, float] = defaultdict(float)

# Build crisis index: (pep, collab, y, m) → (extra_h, n_days)
crisis_idx: dict = {}
for pep, collab, y, m, extra_h, n_days in CRISES:
    crisis_idx[(pep, collab, y, m)] = (extra_h, n_days)

# Build standby index: (pep, collab, y, m) → (standby_days, standby_h)
standby_idx: dict = defaultdict(list)
for pep, collab, pstart, pend, days_pm, h_each in STANDBY_CONFIG:
    for y, m in iter_months(pstart, min(pend, TODAY)):
        standby_idx[(pep, collab, y, m)].append((days_pm, h_each))

# Compute hours from regular assignments
for pep, collab, astart, aend, hpd in ASSIGNMENTS:
    sen  = COLLABS.get(collab, {}).get("seniority", "")
    since = COLLABS.get(collab, {}).get("since", astart)
    eff_start = max(astart, since)
    eff_end   = min(aend, TODAY)
    if eff_start > eff_end:
        continue
    for y, m in iter_months(eff_start, eff_end):
        wd = workdays(y, m, cap=min(eff_end, mend(y, m)))
        for d in wd:
            if d < eff_start or d > eff_end:
                continue
            r = get_rate(sen, d)
            pep_total_hours[pep] += hpd
            pep_total_cost[pep]  += hpd * r

# Crisis extra hours
for pep, collab, y, m, extra_h, n_days in CRISES:
    if date(y, m, 1) > TODAY:
        continue
    sen = COLLABS.get(collab, {}).get("seniority", "")
    cap = min(mend(y, m), TODAY)
    wd  = workdays(y, m, cap=cap)
    days_used = min(n_days, len(wd))
    for d in wd[:days_used]:
        r = get_rate(sen, d)
        pep_total_hours[pep] += extra_h
        pep_total_cost[pep]  += extra_h * r

# Standby hours
for (pep, collab, y, m), entries in standby_idx.items():
    sen = COLLABS.get(collab, {}).get("seniority", "")
    cap = min(mend(y, m), TODAY)
    wd  = workdays(y, m, cap=cap)
    for (sdays, sh) in entries:
        days_used = min(sdays, len(wd))
        for d in wd[:days_used]:
            r = get_rate(sen, d)
            pep_total_hours[pep] += sh
            pep_total_cost[pep]  += sh * r * 0.33  # standby_multiplier

# ═════════════════════════════════════════════════════════════════════════════
# PASS 1b — compute budgets from scenario factors
# ═════════════════════════════════════════════════════════════════════════════

def round_budget(v, base=100):
    return round(v / base) * base

PROJECTS_FINAL = []
for p in PROJECTS_DEF:
    pep    = p["pep"]
    evm    = p["evm"]
    factor = EVM_FACTOR[evm]
    actual_h = pep_total_hours.get(pep, 0)
    actual_c = pep_total_cost.get(pep, 0)
    budget_h = max(round_budget(actual_h * factor, 100), 100)
    budget_c = max(round_budget(actual_c * factor * 1.05, 1000), 5000)
    PROJECTS_FINAL.append({**p, "budget_hours": budget_h, "budget_cost": budget_c})

BY_PEP_FINAL = {p["pep"]: p for p in PROJECTS_FINAL}

# ═════════════════════════════════════════════════════════════════════════════
# GENERATE REFERENCE FILES
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. Seniority levels CSV ───────────────────────────────────────────────────
def write_seniority():
    path = os.path.join(OUT, "niveis_senioridade.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name"])
        for level in RATES:
            w.writerow([level])
    print(f"  ✓ niveis_senioridade.csv ({len(RATES)} níveis)")

# ── 2. Rate cards CSV ─────────────────────────────────────────────────────────
def write_rate_cards():
    path = os.path.join(OUT, "rate_cards.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["seniority_level", "valid_from", "valid_to", "hourly_rate"])
        years = sorted({y for r in RATES.values() for y in r})
        for level, rates in RATES.items():
            for i, year in enumerate(years):
                valid_from = f"{year}-01-01"
                valid_to   = f"{year}-12-31" if i < len(years) - 1 else ""
                w.writerow([level, valid_from, valid_to, f"{rates[year]:.2f}"])
    n = len(RATES) * len(years)
    print(f"  ✓ rate_cards.csv ({n} entradas)")

# ── 3. Cycles CSV ─────────────────────────────────────────────────────────────
def write_cycles():
    path  = os.path.join(OUT, "ciclos.csv")
    count = 0
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "start_date", "end_date", "is_closed", "record_count"])
        for y, m in iter_months(SIM_START, SIM_END):
            s = date(y, m, 1)
            e = mend(y, m)
            closed = e < date(TODAY.year, TODAY.month, 1)
            w.writerow([mlabel(y, m), s.strftime("%Y-%m-%d"),
                        e.strftime("%Y-%m-%d"), "true" if closed else "false", 0])
            count += 1
    print(f"  ✓ ciclos.csv ({count} ciclos mensais)")

# ── 4. Projects CSV ───────────────────────────────────────────────────────────
def write_projects():
    path = os.path.join(OUT, "projetos.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["pep_wbs", "name", "client", "manager",
                    "budget_hours", "budget_cost", "status"])
        for p in PROJECTS_FINAL:
            w.writerow([p["pep"], p["name"], p["client"], p["manager"],
                        p["budget_hours"], int(p["budget_cost"]), p["status"]])
    print(f"  ✓ projetos.csv ({len(PROJECTS_FINAL)} projetos)")

# ═════════════════════════════════════════════════════════════════════════════
# GENERATE MONTHLY TIMESHEETS
# ═════════════════════════════════════════════════════════════════════════════

def generate_all_timesheets():
    total_files = 0
    total_rows  = 0
    total_anomalies = 0

    # Build assignment lookup: (pep, collab) → list of (astart, aend, hpd)
    assign_map: dict = defaultdict(list)
    for pep, collab, astart, aend, hpd in ASSIGNMENTS:
        assign_map[(pep, collab)].append((astart, aend, hpd))

    for y, m in iter_months(SIM_START, TODAY):
        wd      = workdays(y, m, cap=TODAY)
        if not wd:
            continue

        rows = []
        seen = set()  # for I4 deduplication detection (the duplicate IS added)

        # Regular assignment rows
        for pep, collab, astart, aend, hpd in ASSIGNMENTS:
            pinfo = BY_PEP.get(pep, {})
            pname = pinfo.get("name", pep)
            since  = COLLABS.get(collab, {}).get("since", astart)
            eff_s  = max(astart, since)
            eff_e  = aend
            for d in wd:
                if d < eff_s or d > eff_e:
                    continue
                key = (collab, d.strftime("%d/%m/%Y"), pep)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "Colaborador": collab,
                    "Data": d.strftime("%d/%m/%Y"),
                    "Horas totais (decimal)": str(float(hpd)),
                    "Hora extra": "",
                    "Hora sobreaviso": "",
                    "Código PEP": pep,
                    "PEP": pname,
                })

        # Crisis rows (extra hours)
        for pep, collab, cy, cm, extra_h, n_days in CRISES:
            if cy != y or cm != m:
                continue
            pname = BY_PEP.get(pep, {}).get("name", pep)
            days_used = min(n_days, len(wd))
            for d in wd[:days_used]:
                rows.append({
                    "Colaborador": collab,
                    "Data": d.strftime("%d/%m/%Y"),
                    "Horas totais (decimal)": str(extra_h),
                    "Hora extra": "Sim",
                    "Hora sobreaviso": "",
                    "Código PEP": pep,
                    "PEP": pname,
                })

        # Standby rows (sobreaviso)
        for pep, collab, pstart, pend, sdays, sh in STANDBY_CONFIG:
            if not (pstart <= date(y, m, 1) <= pend):
                continue
            pname = BY_PEP.get(pep, {}).get("name", pep)
            days_used = min(sdays, len(wd))
            for d in wd[:days_used]:
                rows.append({
                    "Colaborador": collab,
                    "Data": d.strftime("%d/%m/%Y"),
                    "Horas totais (decimal)": str(sh),
                    "Hora extra": "",
                    "Hora sobreaviso": "Sim",
                    "Código PEP": pep,
                    "PEP": pname,
                })

        data_count = len(rows)

        # Anomaly rows
        anomalies = ANOMALY_ROWS.get((y, m), [])
        rows.extend(anomalies)

        # Write CSV
        fname = f"{y}-{m:02d}.csv"
        path  = os.path.join(TS_DIR, fname)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=TS_FIELDS)
            w.writeheader()
            w.writerows(rows)

        total_files     += 1
        total_rows      += data_count
        total_anomalies += len(anomalies)

    print(f"  ✓ {total_files} arquivos mensais em timesheets/")
    print(f"    {total_rows:,} linhas de dados + {total_anomalies} anomalias")
    return total_files, total_rows

# ═════════════════════════════════════════════════════════════════════════════
# GENERATE BASELINE PLANS (S-curve)
# ═════════════════════════════════════════════════════════════════════════════

def generate_plans():
    path = os.path.join(OUT, "planos_baseline.csv")
    total_rows = 0

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["pep_wbs", "cycle_name", "planned_hours", "planned_cost"])

        for p in PROJECTS_FINAL:
            pep    = p["pep"]
            pstart = p["pstart"]
            pend   = p["pend"]
            budget_h = p["budget_hours"]
            budget_c = p["budget_cost"]
            blended  = budget_c / budget_h if budget_h > 0 else 0

            # Collect all cycles within project duration
            cyc = list(iter_months(pstart, pend))
            n   = len(cyc)
            if n == 0:
                continue

            weights = scurve_weights(n, ramp=0.20, tail=0.20)

            for i, (cy, cm) in enumerate(cyc):
                planned_h = round(budget_h * weights[i], 1)
                planned_c = round(planned_h * blended, 2)
                w.writerow([pep, mlabel(cy, cm), planned_h, planned_c])
                total_rows += 1

    print(f"  ✓ planos_baseline.csv ({total_rows} linhas de planejamento)")

# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY REPORT
# ═════════════════════════════════════════════════════════════════════════════

def print_summary():
    fmt_h = lambda v: f"{v:,.0f}".replace(",", ".")
    fmt_r = lambda v: f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print("\n" + "═" * 76)
    print("RESUMO DO PORTFÓLIO GERADO")
    print("═" * 76)
    hdr = f"{'PEP':<14} {'Nome':<30} {'Consumido':>10} {'Budget':>10} {'%':>6}  {'Cenário'}"
    print(hdr)
    print("─" * 76)

    grand_h = 0
    grand_c = 0
    for p in PROJECTS_FINAL:
        pep     = p["pep"]
        ah      = pep_total_hours.get(pep, 0)
        bh      = p["budget_hours"]
        pct     = ah / bh * 100 if bh else 0
        icon    = ("🔴" if pct >= 100 else "⚠️ " if pct >= 90 else "✅")
        evm     = p["evm"].replace("_", " ").upper()
        print(f"{pep:<14} {p['name'][:30]:<30} {fmt_h(ah):>8}h {fmt_h(bh):>8}h {pct:>5.1f}%  {icon} {evm}")
        grand_h += ah
        grand_c += pep_total_cost.get(pep, 0)

    print("─" * 76)
    print(f"{'TOTAL':>44} {fmt_h(grand_h):>8}h")
    print(f"{'CUSTO TOTAL':>44} {fmt_r(grand_c):>12}")
    print("═" * 76)

    print("\nCENÁRIOS EVM:")
    for evm, factor in EVM_FACTOR.items():
        peps = [p["pep"] for p in PROJECTS_FINAL if p["evm"] == evm]
        if peps:
            print(f"  {evm.upper():<15} — {', '.join(peps)}")

    print("\nREGRAS DE INGESTÃO COBERTAS:")
    rules = {
        "Q1": "Data com formato impossível (dia 32, dia 99)",
        "Q2": "Data futura",
        "Q4": "Horas negativas",
        "Q5": "Campo de horas em branco",
        "Q6": "Horas > 24h em um dia",
        "Q8": "Colaborador com nome vazio",
        "I1": "Lançamento em dia de fim de semana",
        "I2": "Carga semanal excessiva (14h+14h consecutivos)",
        "I3": "Colaborador sem senioridade cadastrada",
        "I4": "Linha duplicada filtrada na ingestão",
        "N1": "Novo colaborador detectado (auto-criação)",
    }
    for code, desc in rules.items():
        print(f"  {code}: {desc}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 60)
    print("PMAS — Grande Simulação — Gerador")
    print(f"Período: Jan/2022 – Dez/2026  (60 ciclos)")
    print(f"Dados:   Jan/2022 – Mai/2026  (53 meses)")
    print(f"Saída:   {OUT}")
    print("═" * 60)

    print("\n[1/5] Arquivos de referência...")
    write_seniority()
    write_rate_cards()
    write_cycles()
    write_projects()

    print("\n[2/5] Timesheets mensais...")
    n_files, n_rows = generate_all_timesheets()

    print("\n[3/5] Planos de baseline (S-curve)...")
    generate_plans()

    print("\n[4/5] Resumo...")
    print_summary()

    print("\n[5/5] Ordem de importação sugerida:")
    print("  1. niveis_senioridade.csv  → Admin › Equipe › Importar Níveis")
    print("  2. rate_cards.csv          → Admin › Equipe › Importar Rate Cards")
    print("  3. ciclos.csv              → Admin › Ciclos › Importar CSV")
    print("  4. projetos.csv            → Admin › Projetos › Importar CSV")
    print("  5. planos_baseline.csv     → Admin › Projetos › [cada PEP] › Importar Baseline")
    print("  6. timesheets/YYYY-MM.csv  → Upload Timesheet (mês a mês, Jan/2022 primeiro)")
    print(f"\n  Total: {n_files} arquivos de timesheet  ·  {n_rows:,} linhas de dados")
    print("\nConcluído.")
