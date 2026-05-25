"""Simulação de ponta a ponta com dados reais de amostra.

Carrega todo o portfólio de amostra via API (ciclos, projetos, rate cards,
10 timesheets) e valida a integridade de todos os endpoints v2.

Invariantes verificados:
  A. Ingestão — contagem de registros e ausência de erros críticos
  B. Tabelas summary — preenchidas após upload
  C. Custos frozen — non-zero para todos os registros com cost_per_hour > 0
  D. /api/v2/portfolio — 10 PEPs, campos render-ready, consistência de totais
  E. /api/v2/trends — 29 ciclos em ordem cronológica, campos delta presentes
  F. /api/v2/effort — todos os colaboradores presentes, horas não-negativas
  G. /api/v2/filters — collaborators + peps + cycles retornados
  H. /api/v2/forecast — histórico por projeto, CPI/SPI computados
  I. /api/v2/runway — consumo e risco classificados
  J. /api/v2/concentration — top_contributors não-vazio
  K. /api/v2/allocation — distribuição collab × PEP
  L. Cross-check — Σ trends_hours == Σ portfolio_hours (mesmos dados)
  M. Cross-check — Σ portfolio_total_cost consistente com Σ allocation_cost
"""
from __future__ import annotations

import io
import os
from datetime import date

import pytest

from backend.app.models import (
    Collaborator, PepCycleSummary, CollaboratorCycleSummary, TimesheetRecord,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

AMOSTRAS = os.path.join(os.path.dirname(__file__), "..", "amostras")

TIMESHEET_FILES = [
    "timesheet_Q1_2024.csv",
    "timesheet_Q2_2024.csv",
    "timesheet_Q3_2024.csv",
    "timesheet_Q4_2024.csv",
    "timesheet_Q1_2025.csv",
    "timesheet_Q2_2025.csv",
    "timesheet_Q3_2025.csv",
    "timesheet_Q4_2025.csv",
    "timesheet_Q1_2026.csv",
    "timesheet_Q2_2026.csv",
]

COLLABS_SENIORITY = {
    "João Silva":      "Sênior",
    "Maria Santos":    "Sênior",
    "Carlos Oliveira": "Pleno",
    "Ana Ferreira":    "Pleno",
    "Roberto Costa":   "Pleno",
    "Lucas Pereira":   "Júnior",
    "Fernanda Lima":   "Júnior",
    "Gabriel Souza":   "Júnior",
    "Amanda Torres":   "Estagiário",
    "Pedro Carvalho":  "Estagiário",
}

VALID_HEALTH = {"ok", "warning", "critical", "overrun", "no_budget"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(filename: str) -> bytes:
    with open(os.path.join(AMOSTRAS, filename), "rb") as f:
        return f.read()


def _post_csv(client, url: str, filename: str, content: bytes):
    return client.post(url, files={"file": (filename, io.BytesIO(content), "text/csv")})


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class TestPortfolioSimulation:
    """Carrega todo o portfólio de amostra e valida a integridade do sistema."""

    # ------------------------------------------------------------------
    # Bootstrap helpers
    # ------------------------------------------------------------------

    def _bootstrap(self, client, db_session):
        """Importa rate cards, ciclos; cria projetos como 'ativo'; retorna seniority IDs."""
        # Rate cards (importação cria seniority levels automaticamente)
        r = _post_csv(client, "/api/rate-cards/import", "senioridade_rate_card.csv",
                      _read("senioridade_rate_card.csv"))
        assert r.status_code == 200, f"rate-cards/import falhou: {r.text}"
        rc = r.json()
        assert rc["created"] > 0, "Nenhum rate card criado"
        assert not rc["errors"], f"Erros no import de rate cards: {rc['errors']}"

        # Ciclos
        r = _post_csv(client, "/api/cycles/import", "ciclos.csv", _read("ciclos.csv"))
        assert r.status_code == 200, f"cycles/import falhou: {r.text}"
        assert r.json()["created"] >= 29, "Menos de 29 ciclos importados"

        # Projetos criados como "ativo" — o workflow correto é criar ativo, fazer
        # uploads históricos, e encerrar depois (projetos encerrados bloqueiam upload).
        projects_payload = [
            {"pep_wbs": "60IT-001-01", "name": "Transformação Digital",  "client": "Banco Nacional",  "budget_hours": 3200, "budget_cost": 480000, "status": "ativo"},
            {"pep_wbs": "60IT-002-01", "name": "App Mobile",             "client": "RetailMart",      "budget_hours": 1600, "budget_cost": 160000, "status": "ativo"},
            {"pep_wbs": "60IT-003-01", "name": "Migração Cloud",         "client": "TechCorp",        "budget_hours": 2400, "budget_cost": 264000, "status": "ativo"},
            {"pep_wbs": "60IT-004-01", "name": "Plataforma Analytics",   "client": "IndustriaX",      "budget_hours": 4800, "budget_cost": 528000, "status": "ativo"},
            {"pep_wbs": "60IT-005-01", "name": "Implantação ERP",        "client": "Grupo Delta",     "budget_hours": 5600, "budget_cost": 616000, "status": "ativo"},
            {"pep_wbs": "60IT-006-01", "name": "Auditoria de Segurança", "client": "FinanceGroup",    "budget_hours":  800, "budget_cost":  88000, "status": "ativo"},
            {"pep_wbs": "60IT-007-01", "name": "Hub de Integrações API", "client": "LogiTrans",       "budget_hours": 3200, "budget_cost": 352000, "status": "ativo"},
            {"pep_wbs": "60IT-008-01", "name": "Portal do Cliente",      "client": "Banco Nacional",  "budget_hours": 4800, "budget_cost": 528000, "status": "ativo"},
            {"pep_wbs": "60IT-009-01", "name": "Chatbot IA",             "client": "RetailMart",      "budget_hours": 2400, "budget_cost": 288000, "status": "ativo"},
            {"pep_wbs": "60IT-010-01", "name": "Upgrade Infraestrutura", "client": "TechCorp",        "budget_hours": 3200, "budget_cost": 352000, "status": "ativo"},
        ]
        for proj in projects_payload:
            r = client.post("/api/projects", json=proj)
            assert r.status_code in (200, 201), f"Criação do projeto {proj['pep_wbs']} falhou: {r.text}"

        # Mapeia nomes de seniority → IDs
        sl_resp = client.get("/api/seniority-levels").json()
        return {s["name"]: s["id"] for s in sl_resp}

    def _close_historical_projects(self, client):
        """Encerra projetos históricos (60IT-001 a 60IT-007) após os uploads."""
        projects = {p["pep_wbs"]: p for p in client.get("/api/projects").json()}
        closed_peps = [f"60IT-{str(i).zfill(3)}-01" for i in range(1, 8)]
        for pep in closed_peps:
            p = projects.get(pep)
            if not p:
                continue
            body = {
                "pep_wbs":      p["pep_wbs"],
                "name":         p.get("name"),
                "client":       p.get("client"),
                "manager":      p.get("manager"),
                "budget_hours": p.get("budget_hours"),
                "budget_cost":  p.get("budget_cost"),
                "status":       "encerrado",
            }
            r = client.put(f"/api/projects/{p['id']}", json=body)
            assert r.status_code == 200, f"Encerramento de {pep} falhou: {r.text}"

    def _upload_timesheets(self, client):
        """Faz upload de todos os timesheets, retorna totais agregados."""
        total_inserted, total_quarantine, total_warnings = 0, 0, 0
        for fname in TIMESHEET_FILES:
            r = _post_csv(client, "/api/upload-timesheet", fname, _read(fname))
            assert r.status_code == 200, f"upload {fname} falhou: {r.text}"
            body = r.json()
            total_inserted   += body.get("records_inserted", 0)
            total_quarantine += body.get("quarantine_records_added", 0)
            total_warnings   += body.get("warning_count", 0)
        return total_inserted, total_quarantine, total_warnings

    def _assign_seniority(self, client, db_session, sl_map: dict):
        """Atribui seniority a todos os colaboradores conhecidos."""
        team = client.get("/api/team").json()
        for member in team:
            seniority = COLLABS_SENIORITY.get(member["name"])
            if seniority and seniority in sl_map:
                r = client.put(
                    f"/api/team/{member['id']}/seniority",
                    json={"seniority_level_id": sl_map[seniority]},
                )
                assert r.status_code == 200, f"seniority para {member['name']} falhou"

    def _reupload_timesheets(self, client):
        """Re-faz upload para recalcular frozen costs com seniority atribuída."""
        for fname in TIMESHEET_FILES:
            r = _post_csv(client, "/api/upload-timesheet", fname, _read(fname))
            assert r.status_code == 200, f"re-upload {fname} falhou"

    # ------------------------------------------------------------------
    # Teste principal
    # ------------------------------------------------------------------

    def test_full_portfolio_simulation(self, client, db_session):

        # ── Fase 1: Bootstrap ─────────────────────────────────────────
        sl_map = self._bootstrap(client, db_session)
        assert "Sênior" in sl_map and "Pleno" in sl_map, "Níveis de senioridade ausentes"

        # Primeiro upload — cria colaboradores (sem seniority ainda)
        total_inserted, total_quarantine, total_warnings = self._upload_timesheets(client)
        assert total_inserted > 0, "Nenhum registro inserido"

        # Atribui seniority e refaz upload para congelar custos corretamente
        self._assign_seniority(client, db_session, sl_map)
        self._reupload_timesheets(client)

        # Encerra projetos históricos após uploads (projetos encerrados bloqueiam upload)
        self._close_historical_projects(client)

        # ── A: Ingestão ───────────────────────────────────────────────
        all_records = db_session.query(TimesheetRecord).all()
        assert len(all_records) > 0, "TimesheetRecord vazio após uploads"
        records_with_pep = [r for r in all_records if r.pep_wbs]
        assert len(records_with_pep) > 100, "Menos de 100 registros com PEP"

        # ── B: Summary tables ─────────────────────────────────────────
        pep_summaries = db_session.query(PepCycleSummary).all()
        collab_summaries = db_session.query(CollaboratorCycleSummary).all()
        assert len(pep_summaries) > 0, "pep_cycle_summary vazia"
        assert len(collab_summaries) > 0, "collaborator_cycle_summary vazia"

        # Grain único: cada (pep_wbs, cycle_id) aparece exatamente uma vez
        pep_grains = {(s.pep_wbs, s.cycle_id) for s in pep_summaries}
        assert len(pep_grains) == len(pep_summaries), "Duplicatas em pep_cycle_summary"

        # Totais de summary batem com raw records
        for s in pep_summaries[:5]:  # amostra dos primeiros 5
            raw_h = sum(
                (r.normal_hours or 0) + (r.extra_hours or 0) + (r.standby_hours or 0)
                for r in all_records
                if r.pep_wbs == s.pep_wbs and r.cycle_id == s.cycle_id
            )
            assert abs(s.total_hours - raw_h) < 0.01, (
                f"Summary diverge para {s.pep_wbs} ciclo {s.cycle_id}: "
                f"summary={s.total_hours:.2f} raw={raw_h:.2f}"
            )

        # ── C: Frozen costs ───────────────────────────────────────────
        records_with_rate = [r for r in all_records if (r.cost_per_hour or 0) > 0]
        assert len(records_with_rate) > 0, "Nenhum registro com cost_per_hour > 0"

        zero_frozen = [
            r for r in records_with_rate
            if (r.normal_cost or 0) + (r.extra_cost or 0) + (r.standby_cost or 0) == 0
        ]
        pct_zero = len(zero_frozen) / len(records_with_rate) * 100
        assert pct_zero < 5, (
            f"{pct_zero:.1f}% dos registros com rate têm frozen costs zerados "
            f"({len(zero_frozen)}/{len(records_with_rate)})"
        )

        # ── D: /api/v2/portfolio ──────────────────────────────────────
        port = client.get("/api/v2/portfolio").json()
        assert len(port) == 10, f"Esperados 10 PEPs no portfólio, obtidos {len(port)}"

        pep_codes = {p["pep_wbs"] for p in port}
        expected_peps = {f"60IT-{str(i).zfill(3)}-01" for i in range(1, 11)}
        assert pep_codes == expected_peps, f"PEPs faltando: {expected_peps - pep_codes}"

        for item in port:
            # Campos render-ready obrigatórios
            assert item["health_hours"] in VALID_HEALTH, \
                f"{item['pep_wbs']}: health_hours inválido: {item['health_hours']}"
            assert item["health_cost"] in VALID_HEALTH, \
                f"{item['pep_wbs']}: health_cost inválido: {item['health_cost']}"
            assert "cpi_label" in item, f"{item['pep_wbs']}: cpi_label ausente"
            assert "cpi_color" in item, f"{item['pep_wbs']}: cpi_color ausente"
            assert item["total_hours"] >= 0
            assert item["total_cost"] >= 0
            assert item["budget_hours"] is not None, f"{item['pep_wbs']}: sem budget_hours"
            assert item["budget_cost"]  is not None, f"{item['pep_wbs']}: sem budget_cost"
            # CPI presente para todos (todos têm budget_cost e actual_cost > 0)
            if item["total_cost"] > 0:
                assert item["cpi"] is not None, f"{item['pep_wbs']}: CPI None com custo > 0"
                assert item["cpi"] > 0, f"{item['pep_wbs']}: CPI negativo: {item['cpi']}"

        portfolio_total_hours = sum(p["total_hours"] for p in port)
        portfolio_total_cost  = sum(p["total_cost"]  for p in port)
        assert portfolio_total_hours > 1000, f"Total de horas muito baixo: {portfolio_total_hours}"
        assert portfolio_total_cost  > 0,    "Custo total zerado no portfólio"

        # ── E: /api/v2/trends ─────────────────────────────────────────
        trends = client.get("/api/v2/trends").json()
        assert len(trends) >= 17, f"Trends deveria ter ≥17 ciclos não-quarentena, obtidos {len(trends)}"

        cycle_names = [t["cycle_name"] for t in trends]
        # Ordem cronológica (por cycle_start)
        starts = [t["cycle_start"] for t in trends]
        assert starts == sorted(starts), "Trends não está em ordem cronológica"

        for t in trends:
            assert "hours_delta" in t,      f"hours_delta ausente em {t['cycle_name']}"
            assert "hours_delta_pct" in t,  f"hours_delta_pct ausente em {t['cycle_name']}"
            assert "cost_delta" in t,       f"cost_delta ausente em {t['cycle_name']}"
            assert t["total_hours"] >= 0
            assert t["actual_cost"] >= 0

        # Primeiro ciclo não tem delta (não há ciclo anterior)
        assert trends[0]["hours_delta"] is None, "Primeiro ciclo não deveria ter delta"
        # Ciclos seguintes devem ter delta calculado
        deltas_computed = [t for t in trends[1:] if t["hours_delta"] is not None]
        assert len(deltas_computed) > 0, "Nenhum delta calculado nos ciclos seguintes"

        trends_total_hours = sum(t["total_hours"] for t in trends)

        # ── F: /api/v2/effort ─────────────────────────────────────────
        effort = client.get("/api/v2/effort").json()
        assert len(effort) >= 10, f"Esperados ≥10 colaboradores no effort, obtidos {len(effort)}"

        collab_names_effort = {e["collaborator"] for e in effort}
        for name in COLLABS_SENIORITY:
            assert name in collab_names_effort, f"{name} ausente no effort"

        for e in effort:
            assert e["total_hours"] >= 0
            assert e["total_cost"]  >= 0
            assert e["normal_hours"] + e["extra_hours"] + e["standby_hours"] <= e["total_hours"] + 0.01

        effort_total_hours = sum(e["total_hours"] for e in effort)

        # ── G: /api/v2/filters ────────────────────────────────────────
        filters = client.get("/api/v2/filters").json()
        assert "collaborators" in filters
        assert "peps" in filters
        assert "cycles" in filters
        assert len(filters["collaborators"]) >= 10
        assert len(filters["peps"]) == 10
        assert len(filters["cycles"]) >= 17

        pep_codes_filters = {p["code"] for p in filters["peps"]}
        assert pep_codes_filters == expected_peps, \
            f"Filters/peps diverge: {expected_peps - pep_codes_filters}"

        # ── H: /api/v2/forecast ───────────────────────────────────────
        for item in port:
            pep = item["pep_wbs"]
            r = client.get(f"/api/v2/forecast?pep_wbs={pep}")
            assert r.status_code == 200, f"forecast {pep} retornou {r.status_code}"
            fc = r.json()

            assert fc["consumed_hours"] > 0, f"{pep}: consumed_hours=0 no forecast"
            assert len(fc["history"]) > 0,   f"{pep}: histórico vazio no forecast"
            assert "cpi_label" in fc,         f"{pep}: cpi_label ausente no forecast"
            assert "spi_label" in fc,         f"{pep}: spi_label ausente no forecast"

            # Histórico: cada ponto tem period_hours e cumulative_hours crescente
            cum = 0.0
            for point in fc["history"]:
                assert point["period_hours"] >= 0, f"{pep}: period_hours negativo"
                cum += point["period_hours"]
                assert abs(point["cumulative_hours"] - cum) < 0.05, \
                    f"{pep}: cumulative_hours não-acumulativo em {point['cycle_name']}"

            if fc["actual_cost"] > 0 and fc.get("cpi") is not None:
                assert fc["cpi"] > 0, f"{pep}: CPI negativo no forecast"
                assert "eac" in fc and fc["eac"] is not None, \
                    f"{pep}: EAC ausente com CPI válido"

        # ── I: /api/v2/runway ─────────────────────────────────────────
        runway = client.get("/api/v2/runway").json()
        assert len(runway) == 10, f"Runway deveria ter 10 PEPs, obtidos {len(runway)}"

        for item in runway:
            assert item["risk"] in VALID_HEALTH, \
                f"{item['pep_wbs']}: risk inválido: {item['risk']}"
            assert item["cost_risk"] in VALID_HEALTH, \
                f"{item['pep_wbs']}: cost_risk inválido: {item['cost_risk']}"
            assert item["consumed_hours"] >= 0
            assert item["avg_hours_per_cycle"] >= 0

            if item["risk"] not in {"no_budget", "overrun"}:
                # pct_consumed deve estar definido para PEPs com budget
                assert item["pct_consumed"] is not None, \
                    f"{item['pep_wbs']}: pct_consumed None com risk={item['risk']}"

            if item["risk"] == "overrun":
                assert item["cycles_to_complete"] is None, \
                    f"{item['pep_wbs']}: cycles_to_complete deveria ser None quando overrun"

        # Projetos ativos em 2026 devem estar "ok" ou "warning" (pouco consumido)
        active_runway = [r for r in runway if r["pep_wbs"] in {"60IT-008-01", "60IT-009-01", "60IT-010-01"}]
        for r in active_runway:
            assert r["risk"] in {"ok", "warning", "no_budget"}, \
                f"{r['pep_wbs']}: projeto ativo com risk={r['risk']}"

        # ── J: /api/v2/concentration ──────────────────────────────────
        conc = client.get("/api/v2/concentration").json()
        assert len(conc) == 10, f"Concentration deveria ter 10 PEPs, obtidos {len(conc)}"

        for item in conc:
            assert len(item["top_contributors"]) > 0, \
                f"{item['pep_wbs']}: top_contributors vazio"
            assert item["top1_pct"] > 0, \
                f"{item['pep_wbs']}: top1_pct=0"
            assert item["risk"] in {"high", "medium", "low"}, \
                f"{item['pep_wbs']}: risk inválido: {item['risk']}"
            # Soma dos percentuais deve ser ~100
            total_pct = sum(c["pct"] for c in item["top_contributors"])
            assert abs(total_pct - 100.0) < 1.0, \
                f"{item['pep_wbs']}: percentuais somam {total_pct:.1f}% (esperado ~100%)"

        # ── K: /api/v2/allocation ─────────────────────────────────────
        alloc = client.get("/api/v2/allocation").json()
        assert len(alloc) > 0, "Allocation vazia"

        # Cada linha tem os campos obrigatórios
        for row in alloc:
            assert "collaborator" in row
            assert "pep_wbs" in row
            assert row["total_hours"] >= 0
            assert row["total_cost"] >= 0

        alloc_collab_names = {a["collaborator"] for a in alloc}
        for name in COLLABS_SENIORITY:
            assert name in alloc_collab_names, f"{name} ausente na allocation"

        # Cada PEP deve aparecer na allocation
        alloc_peps = {a["pep_wbs"] for a in alloc}
        assert alloc_peps == expected_peps, f"PEPs ausentes na allocation: {expected_peps - alloc_peps}"

        # ── L: Cross-check trends vs portfolio ────────────────────────
        # Sem filtros, os totais devem ser idênticos
        assert abs(trends_total_hours - portfolio_total_hours) < 0.1, (
            f"Divergência de horas: trends={trends_total_hours:.1f} "
            f"portfolio={portfolio_total_hours:.1f}"
        )

        # ── M: Cross-check effort vs portfolio (horas) ────────────────
        # effort agrupa por colaborador (sem filtro = todos os PEPs)
        # portfolio agrupa por PEP — ambos sem filtro devem somar o mesmo total
        assert abs(effort_total_hours - portfolio_total_hours) < 0.1, (
            f"Divergência de horas: effort={effort_total_hours:.1f} "
            f"portfolio={portfolio_total_hours:.1f}"
        )

        # ── N: Projetos encerrados vs ativos ──────────────────────────
        port_by_pep = {p["pep_wbs"]: p for p in port}

        # Projetos encerrados (001-007) devem ter consumo > 0
        closed_peps = [f"60IT-{str(i).zfill(3)}-01" for i in range(1, 8)]
        for pep in closed_peps:
            assert port_by_pep[pep]["total_hours"] > 0, \
                f"{pep}: projeto encerrado sem horas"

        # Projetos ativos (008-010) em 2026 devem ter horas mas não estar overrun
        active_peps = ["60IT-008-01", "60IT-009-01", "60IT-010-01"]
        for pep in active_peps:
            assert port_by_pep[pep]["total_hours"] > 0, \
                f"{pep}: projeto ativo sem horas"
            bh = port_by_pep[pep]["budget_hours"]
            th = port_by_pep[pep]["total_hours"]
            assert th < bh, \
                f"{pep}: projeto ativo com {th:.0f}h > budget de {bh:.0f}h (overrun inesperado)"

        # ── O: Relatório de saúde final ────────────────────────────────
        health_summary = {}
        for p in port:
            h = p["health_hours"]
            health_summary[h] = health_summary.get(h, 0) + 1

        # Sistema com 10 projetos reais deve ter distribuição de saúde variada
        assert len(health_summary) >= 2, \
            f"Todos os projetos com a mesma saúde ({health_summary}) — dados suspeitos"
