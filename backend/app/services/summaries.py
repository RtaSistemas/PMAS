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
    that was touched by the current ingestion batch.

    Replaces the former O(P×C) nested-loop approach with a single bulk
    aggregation query over the entire (pep_wbs_list × cycle_ids) space,
    followed by a single-pass upsert.
    """
    peps = [p for p in pep_wbs_list if p is not None]
    if not peps or not cycle_ids:
        return

    now = datetime.utcnow()

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
        .filter(
            TimesheetRecord.pep_wbs.in_(peps),
            TimesheetRecord.cycle_id.in_(cycle_ids),
        )
        .group_by(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            TimesheetRecord.cycle_id,
        )
        .all()
    )

    # Aggregate across pep_description variants for the same (pep_wbs, cycle_id)
    agg_map: dict[tuple, dict] = {}
    for r in rows:
        key = (r.pep_wbs, r.cycle_id)
        if key not in agg_map:
            agg_map[key] = {
                "pep_wbs":         r.pep_wbs,
                "pep_description": r.pep_description,
                "cycle_id":        r.cycle_id,
                "normal_hours":    0.0,
                "extra_hours":     0.0,
                "standby_hours":   0.0,
                "total_hours":     0.0,
                "normal_cost":     0.0,
                "extra_cost":      0.0,
                "standby_cost":    0.0,
                "total_cost":      0.0,
                "refreshed_at":    now,
            }
        a = agg_map[key]
        a["normal_hours"]  += r.normal_hours  or 0.0
        a["extra_hours"]   += r.extra_hours   or 0.0
        a["standby_hours"] += r.standby_hours or 0.0
        a["total_hours"]   += r.total_hours   or 0.0
        a["normal_cost"]   += r.normal_cost   or 0.0
        a["extra_cost"]    += r.extra_cost    or 0.0
        a["standby_cost"]  += r.standby_cost  or 0.0
        a["total_cost"]     = a["normal_cost"] + a["extra_cost"] + a["standby_cost"]

    # Touch pairs that had rows removed — rows not in agg_map but in the DB
    touched_pairs = {(p, c) for p in peps for c in cycle_ids}
    found_pairs   = set(agg_map.keys())
    deleted_pairs = touched_pairs - found_pairs

    for pep, cycle_id in deleted_pairs:
        db.query(PepCycleSummary).filter_by(
            pep_wbs=pep, cycle_id=cycle_id
        ).delete(synchronize_session=False)

    # Upsert remaining
    existing_rows = (
        db.query(PepCycleSummary)
        .filter(
            PepCycleSummary.pep_wbs.in_(peps),
            PepCycleSummary.cycle_id.in_(cycle_ids),
        )
        .all()
    )
    existing_map = {(e.pep_wbs, e.cycle_id): e for e in existing_rows}

    for key, a in agg_map.items():
        existing = existing_map.get(key)
        if existing:
            for k, v in a.items():
                setattr(existing, k, v)
        else:
            db.add(PepCycleSummary(**a))


def refresh_collaborator_cycle(
    db: Session,
    collaborator_ids: list[int],
    cycle_ids: list[int],
) -> None:
    """Recompute `collaborator_cycle_summary` for every (collaborator_id, cycle_id)
    pair that was touched by the current ingestion batch.

    Replaces the former O(C×K) nested-loop approach with a single bulk
    aggregation query, followed by a single-pass upsert.
    """
    if not collaborator_ids or not cycle_ids:
        return

    now = datetime.utcnow()

    rows = (
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
        .filter(
            TimesheetRecord.collaborator_id.in_(collaborator_ids),
            TimesheetRecord.cycle_id.in_(cycle_ids),
        )
        .group_by(TimesheetRecord.collaborator_id, TimesheetRecord.cycle_id)
        .all()
    )

    agg_map: dict[tuple, dict] = {}
    for r in rows:
        key = (r.collaborator_id, r.cycle_id)
        nc = r.normal_cost  or 0.0
        ec = r.extra_cost   or 0.0
        sc = r.standby_cost or 0.0
        agg_map[key] = {
            "collaborator_id": r.collaborator_id,
            "cycle_id":        r.cycle_id,
            "normal_hours":    r.normal_hours  or 0.0,
            "extra_hours":     r.extra_hours   or 0.0,
            "standby_hours":   r.standby_hours or 0.0,
            "total_hours":     r.total_hours   or 0.0,
            "normal_cost":     nc,
            "extra_cost":      ec,
            "standby_cost":    sc,
            "total_cost":      nc + ec + sc,
            "refreshed_at":    now,
        }

    touched_pairs = {(c, k) for c in collaborator_ids for k in cycle_ids}
    deleted_pairs = touched_pairs - set(agg_map.keys())

    for collab_id, cycle_id in deleted_pairs:
        db.query(CollaboratorCycleSummary).filter_by(
            collaborator_id=collab_id, cycle_id=cycle_id
        ).delete(synchronize_session=False)

    existing_rows = (
        db.query(CollaboratorCycleSummary)
        .filter(
            CollaboratorCycleSummary.collaborator_id.in_(collaborator_ids),
            CollaboratorCycleSummary.cycle_id.in_(cycle_ids),
        )
        .all()
    )
    existing_map = {(e.collaborator_id, e.cycle_id): e for e in existing_rows}

    for key, a in agg_map.items():
        existing = existing_map.get(key)
        if existing:
            for k, v in a.items():
                setattr(existing, k, v)
        else:
            db.add(CollaboratorCycleSummary(**a))


def backfill_summaries(db: Session) -> None:
    """Populate summary tables from existing TimesheetRecord data.

    Called once on startup when the tables are empty (e.g. first migration).
    Uses the legacy cost calculation (cost_per_hour × weighted hours) for rows
    that pre-date the frozen-cost columns, falling back gracefully.
    """
    pep_empty    = db.query(PepCycleSummary).count() == 0
    collab_empty = db.query(CollaboratorCycleSummary).count() == 0

    if not pep_empty and not collab_empty:
        return  # both tables already populated

    now = datetime.utcnow()

    # PEP × cycle grain — only if empty
    if pep_empty:
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

    # Collaborator × cycle grain — only if empty
    if collab_empty:
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
