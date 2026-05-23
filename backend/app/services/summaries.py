"""Pre-computed summary tables.

`refresh_pep_cycle` and `refresh_collaborator_cycle` are called at the end of
`ingest_file()`, inside the same transaction.  They are the *only* writers for
`pep_cycle_summary` and `collaborator_cycle_summary`.

No other code path should modify these tables directly.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import (
    CollaboratorCycleSummary,
    PepCycleSummary,
    TimesheetRecord,
)


def refresh_pep_cycle(
    db: Session,
    pep_wbs_list: list[str | None],
    cycle_ids: list[int],
) -> None:
    """Recompute `pep_cycle_summary` for every (pep_wbs, cycle_id) pair
    that was touched by the current ingestion batch."""
    now = datetime.utcnow()
    for pep in pep_wbs_list:
        if pep is None:
            continue
        for cycle_id in cycle_ids:
            rows = (
                db.query(
                    func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
                    func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
                    func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
                    func.sum(
                        TimesheetRecord.normal_hours
                        + TimesheetRecord.extra_hours
                        + TimesheetRecord.standby_hours
                    ).label("total_hours"),
                    func.sum(TimesheetRecord.normal_cost).label("normal_cost"),
                    func.sum(TimesheetRecord.extra_cost).label("extra_cost"),
                    func.sum(TimesheetRecord.standby_cost).label("standby_cost"),
                    func.sum(
                        (TimesheetRecord.normal_cost or 0)
                        + (TimesheetRecord.extra_cost or 0)
                        + (TimesheetRecord.standby_cost or 0)
                    ).label("total_cost"),
                    TimesheetRecord.pep_description,
                )
                .filter(
                    TimesheetRecord.pep_wbs == pep,
                    TimesheetRecord.cycle_id == cycle_id,
                )
                .group_by(TimesheetRecord.pep_description)
                .all()
            )

            if not rows:
                # No records left → delete summary row if it exists
                db.query(PepCycleSummary).filter_by(
                    pep_wbs=pep, cycle_id=cycle_id
                ).delete(synchronize_session=False)
                continue

            # Aggregate across all pep_description variants for this pep_wbs
            agg = {
                "normal_hours":  sum(r.normal_hours  or 0.0 for r in rows),
                "extra_hours":   sum(r.extra_hours   or 0.0 for r in rows),
                "standby_hours": sum(r.standby_hours or 0.0 for r in rows),
                "total_hours":   sum(r.total_hours   or 0.0 for r in rows),
                "normal_cost":   sum(r.normal_cost   or 0.0 for r in rows),
                "extra_cost":    sum(r.extra_cost    or 0.0 for r in rows),
                "standby_cost":  sum(r.standby_cost  or 0.0 for r in rows),
                "total_cost":    sum(r.total_cost    or 0.0 for r in rows),
                "pep_description": rows[0].pep_description,
                "refreshed_at":  now,
            }

            existing = (
                db.query(PepCycleSummary)
                .filter_by(pep_wbs=pep, cycle_id=cycle_id)
                .first()
            )
            if existing:
                for k, v in agg.items():
                    setattr(existing, k, v)
            else:
                db.add(PepCycleSummary(pep_wbs=pep, cycle_id=cycle_id, **agg))


def refresh_collaborator_cycle(
    db: Session,
    collaborator_ids: list[int],
    cycle_ids: list[int],
) -> None:
    """Recompute `collaborator_cycle_summary` for every (collaborator_id, cycle_id)
    pair that was touched by the current ingestion batch."""
    now = datetime.utcnow()
    for collab_id in collaborator_ids:
        for cycle_id in cycle_ids:
            row = (
                db.query(
                    func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
                    func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
                    func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
                    func.sum(
                        TimesheetRecord.normal_hours
                        + TimesheetRecord.extra_hours
                        + TimesheetRecord.standby_hours
                    ).label("total_hours"),
                    func.sum(TimesheetRecord.normal_cost).label("normal_cost"),
                    func.sum(TimesheetRecord.extra_cost).label("extra_cost"),
                    func.sum(TimesheetRecord.standby_cost).label("standby_cost"),
                    func.sum(
                        (TimesheetRecord.normal_cost or 0)
                        + (TimesheetRecord.extra_cost or 0)
                        + (TimesheetRecord.standby_cost or 0)
                    ).label("total_cost"),
                )
                .filter(
                    TimesheetRecord.collaborator_id == collab_id,
                    TimesheetRecord.cycle_id == cycle_id,
                )
                .first()
            )

            if row is None or row.total_hours is None:
                db.query(CollaboratorCycleSummary).filter_by(
                    collaborator_id=collab_id, cycle_id=cycle_id
                ).delete(synchronize_session=False)
                continue

            agg = {
                "normal_hours":  row.normal_hours  or 0.0,
                "extra_hours":   row.extra_hours   or 0.0,
                "standby_hours": row.standby_hours or 0.0,
                "total_hours":   row.total_hours   or 0.0,
                "normal_cost":   row.normal_cost   or 0.0,
                "extra_cost":    row.extra_cost    or 0.0,
                "standby_cost":  row.standby_cost  or 0.0,
                "total_cost":    row.total_cost    or 0.0,
                "refreshed_at":  now,
            }

            existing = (
                db.query(CollaboratorCycleSummary)
                .filter_by(collaborator_id=collab_id, cycle_id=cycle_id)
                .first()
            )
            if existing:
                for k, v in agg.items():
                    setattr(existing, k, v)
            else:
                db.add(CollaboratorCycleSummary(
                    collaborator_id=collab_id, cycle_id=cycle_id, **agg
                ))


def backfill_summaries(db: Session) -> None:
    """Populate summary tables from existing TimesheetRecord data.

    Called once on startup when the tables are empty (e.g. first migration).
    Uses the legacy cost calculation (cost_per_hour × weighted hours) for rows
    that pre-date the frozen-cost columns, falling back gracefully.
    """
    if db.query(PepCycleSummary).count() > 0:
        return  # already populated

    now = datetime.utcnow()

    # PEP × cycle grain
    rows = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            TimesheetRecord.cycle_id,
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(TimesheetRecord.normal_cost).label("normal_cost"),
            func.sum(TimesheetRecord.extra_cost).label("extra_cost"),
            func.sum(TimesheetRecord.standby_cost).label("standby_cost"),
        )
        .filter(TimesheetRecord.pep_wbs.isnot(None))
        .group_by(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            TimesheetRecord.cycle_id,
        )
        .all()
    )

    pep_cycle_agg: dict[tuple, dict] = {}
    for r in rows:
        key = (r.pep_wbs, r.cycle_id)
        if key not in pep_cycle_agg:
            pep_cycle_agg[key] = {
                "pep_wbs": r.pep_wbs,
                "pep_description": r.pep_description,
                "cycle_id": r.cycle_id,
                "normal_hours": 0.0,
                "extra_hours": 0.0,
                "standby_hours": 0.0,
                "total_hours": 0.0,
                "normal_cost": 0.0,
                "extra_cost": 0.0,
                "standby_cost": 0.0,
                "refreshed_at": now,
            }
        agg = pep_cycle_agg[key]
        agg["normal_hours"]  += r.normal_hours  or 0.0
        agg["extra_hours"]   += r.extra_hours   or 0.0
        agg["standby_hours"] += r.standby_hours or 0.0
        agg["total_hours"]   += r.total_hours   or 0.0
        agg["normal_cost"]   += r.normal_cost   or 0.0
        agg["extra_cost"]    += r.extra_cost    or 0.0
        agg["standby_cost"]  += r.standby_cost  or 0.0

    for agg in pep_cycle_agg.values():
        agg["total_cost"] = agg["normal_cost"] + agg["extra_cost"] + agg["standby_cost"]
        db.add(PepCycleSummary(**agg))

    # Collaborator × cycle grain
    collab_rows = (
        db.query(
            TimesheetRecord.collaborator_id,
            TimesheetRecord.cycle_id,
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(TimesheetRecord.normal_cost).label("normal_cost"),
            func.sum(TimesheetRecord.extra_cost).label("extra_cost"),
            func.sum(TimesheetRecord.standby_cost).label("standby_cost"),
        )
        .group_by(TimesheetRecord.collaborator_id, TimesheetRecord.cycle_id)
        .all()
    )

    for r in collab_rows:
        nc = r.normal_cost  or 0.0
        ec = r.extra_cost   or 0.0
        sc = r.standby_cost or 0.0
        db.add(CollaboratorCycleSummary(
            collaborator_id=r.collaborator_id,
            cycle_id=r.cycle_id,
            normal_hours=r.normal_hours  or 0.0,
            extra_hours=r.extra_hours   or 0.0,
            standby_hours=r.standby_hours or 0.0,
            total_hours=r.total_hours   or 0.0,
            normal_cost=nc,
            extra_cost=ec,
            standby_cost=sc,
            total_cost=nc + ec + sc,
            refreshed_at=now,
        ))

    db.commit()
