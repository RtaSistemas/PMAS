"""GET /api/v2/filters — replaces /collaborators + /peps + cycles list.

Returns collaborators, PEPs, and cycles in one round-trip so the frontend
can populate all filter dropdowns without multiple requests.
"""
from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, TimesheetRecord
from backend.app.routers.v2.portfolio import _allowed_peps

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/filters", summary="Filtros disponíveis: colaboradores, PEPs e ciclos", response_model=dict)
def get_filters(db: DbSession, current_user=Depends(get_current_user)):
    allowed = _allowed_peps(db, current_user)

    collab_q = (
        db.query(Collaborator.id, Collaborator.name)
        .join(TimesheetRecord, TimesheetRecord.collaborator_id == Collaborator.id)
    )
    if allowed is not None:
        collab_q = collab_q.filter(TimesheetRecord.pep_wbs.in_(allowed))
    collaborators = collab_q.distinct().order_by(Collaborator.name).all()

    pep_q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
        )
        .filter(TimesheetRecord.pep_wbs.isnot(None))
    )
    if allowed is not None:
        pep_q = pep_q.filter(TimesheetRecord.pep_wbs.in_(allowed))
    pep_rows = pep_q.distinct().order_by(TimesheetRecord.pep_wbs).all()
    pep_grouped: dict[str, dict] = defaultdict(
        lambda: {"code": "", "descriptions": []}
    )
    for r in pep_rows:
        pep_grouped[r.pep_wbs]["code"] = r.pep_wbs
        if r.pep_description and r.pep_description not in pep_grouped[r.pep_wbs]["descriptions"]:
            pep_grouped[r.pep_wbs]["descriptions"].append(r.pep_description)

    cycles = (
        db.query(Cycle)
        .filter(Cycle.is_active == True)  # noqa: E712
        .order_by(Cycle.start_date)
        .all()
    )

    return {
        "collaborators": [{"id": r.id, "name": r.name} for r in collaborators],
        "peps": list(pep_grouped.values()),
        "cycles": [
            {
                "id": c.id,
                "name": c.name,
                "start_date": str(c.start_date),
                "end_date": str(c.end_date),
                "is_active": c.is_active,
                "is_closed": c.is_closed,
            }
            for c in cycles
        ],
    }
