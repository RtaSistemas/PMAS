"""Regression tests for bugs found while reviewing the cycle 2 changes (cycle 3)."""
from __future__ import annotations

from sqlalchemy import event

from backend.app.models import Collaborator
from backend.app.services.ingestion import ingest_file
from tests.test_audit_analytics import _collab, _cycles, _project, _rec


# ---------------------------------------------------------------------------
# R1 - new collaborators must not trigger a full collaborator scan each
# ---------------------------------------------------------------------------

def test_new_collaborators_do_not_scan_whole_table_per_name(db_session, sample_cycle):
    for i in range(30):
        db_session.add(Collaborator(name=f"Existente {i}"))
    db_session.commit()

    unfiltered_selects: list[str] = []

    def _count(conn, cursor, statement, parameters, context, executemany):
        s = " ".join(statement.lower().split())
        if "from collaborator" in s and s.startswith("select") and " where " not in s:
            unfiltered_selects.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", _count)
    try:
        rows = "".join(f"Novo Nome {i};12/01/2026;8;AA-0001\n" for i in range(25))
        data = ("Colaborador;Data;Horas totais (decimal);Código PEP\n" + rows).encode()
        ingest_file(data, "a.csv", db_session)
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    # One scan (legacy-name index) is fine; one per new collaborator is not.
    assert len(unfiltered_selects) <= 3, len(unfiltered_selects)
    assert db_session.query(Collaborator).count() == 55


def test_legacy_unnormalized_collaborator_is_still_reused(db_session, sample_cycle):
    db_session.add(Collaborator(name="Maria  Souza"))  # double space, legacy row
    db_session.commit()
    data = "Colaborador;Data;Horas totais (decimal);Código PEP\nMaria Souza;12/01/2026;8;AA-0001\n".encode()
    ingest_file(data, "a.csv", db_session)
    assert db_session.query(Collaborator).count() == 1


# ---------------------------------------------------------------------------
# R2 - uncertainty band must bracket the estimate when idle cycles are in the window
# ---------------------------------------------------------------------------

def test_forecast_band_brackets_estimate_with_idle_cycle(client, db_session):
    cs = _cycles(db_session, 3)
    a = _collab(db_session)
    _project(db_session, "AA-0001", bh=1000, bc=100000)
    _rec(db_session, cs[0], a, "AA-0001", 100)
    _rec(db_session, cs[2], a, "AA-0001", 100)  # cycle 2 idle

    d = client.get("/api/v2/forecast?pep_wbs=AA-0001").json()
    est = d["estimated_cycles_to_complete"]
    assert est is not None
    assert d["est_cycles_optimistic"] <= est <= d["est_cycles_pessimistic"]
