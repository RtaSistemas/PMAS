from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from backend.app.models import Notification
from backend.app.utils import now_br

_DEDUP_WINDOW_HOURS = 24


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    level: str = "info",
) -> Notification:
    """Create a Notification, skipping if an identical unread one was sent in the last 24 h."""
    cutoff = now_br() - timedelta(hours=_DEDUP_WINDOW_HOURS)
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.message == message,
            Notification.is_read == False,  # noqa: E712
            Notification.created_at >= cutoff,
        )
        .first()
    )
    if existing:
        return existing
    notif = Notification(user_id=user_id, message=message, level=level)
    db.add(notif)
    return notif


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_notif_recipients(db: Session, project_id: int) -> set[int]:
    """Return user IDs that should receive alerts for a project (admins + ACL users)."""
    from backend.app.models import User, UserProjectAccess
    admin_ids = {u.id for u in db.query(User).filter(User.role == "admin").all()}
    access_ids = {
        a.user_id
        for a in db.query(UserProjectAccess)
        .filter(UserProjectAccess.project_id == project_id)
        .all()
    }
    return admin_ids | access_ids


def _upsert_project_alert(
    db: Session,
    project_id: int,
    pep_wbs: str,
    alert_type: str,
    level: str,
    message: str,
    metric_value: float | None = None,
    consecutive_cycles: int | None = None,
) -> bool:
    """Create a ProjectAlert if none is active for (project_id, alert_type).

    If an active alert exists with a different level (e.g., warning → error),
    resolves the old one and creates a new one.

    Returns True when a new alert was created (caller should also send a Notification).
    """
    from backend.app.models import ProjectAlert
    existing = (
        db.query(ProjectAlert)
        .filter(
            ProjectAlert.project_id == project_id,
            ProjectAlert.alert_type == alert_type,
            ProjectAlert.is_resolved == False,  # noqa: E712
        )
        .first()
    )
    if existing:
        if existing.level == level:
            return False  # already active at same severity — no duplicate
        # severity changed — resolve old, fall through to create new
        existing.is_resolved = True
        existing.resolved_at = now_br()

    db.add(ProjectAlert(
        project_id=project_id,
        pep_wbs=pep_wbs,
        alert_type=alert_type,
        level=level,
        message=message,
        metric_value=metric_value,
        consecutive_cycles=consecutive_cycles,
    ))
    return True


def _resolve_project_alerts(db: Session, project_id: int, *alert_types: str) -> None:
    """Mark active alerts of given types as resolved for a project."""
    from backend.app.models import ProjectAlert
    db.query(ProjectAlert).filter(
        ProjectAlert.project_id == project_id,
        ProjectAlert.alert_type.in_(alert_types),
        ProjectAlert.is_resolved == False,  # noqa: E712
    ).update({"is_resolved": True, "resolved_at": now_br()}, synchronize_session=False)


# ── Public notification functions ─────────────────────────────────────────────

def notify_threshold_crossings(db: Session, pep_wbs_list: list[str]) -> None:
    """Create budget alert notifications and ProjectAlert records for PEPs crossing thresholds.

    Called after each successful upload. Non-critical: exceptions are swallowed so they
    never block the upload response. Also auto-resolves alerts when budget recovers.
    """
    if not pep_wbs_list:
        return
    try:
        from sqlalchemy import func

        from backend.app.models import (
            GlobalConfig,
            PepCycleSummary,
            Project,
            ProjectBaseline,
        )
        from backend.app.services.evm import (
            classify_health,
            get_thresholds,
            resolve_effective_budget,
        )

        cfg = db.get(GlobalConfig, 1)
        warning_threshold, critical_threshold = get_thresholds(cfg)

        for pep in pep_wbs_list:
            row = (
                db.query(
                    func.sum(PepCycleSummary.total_hours),
                    func.sum(PepCycleSummary.total_cost),
                )
                .filter(PepCycleSummary.pep_wbs == pep)
                .one_or_none()
            )
            if not row or not row[0]:
                continue
            consumed_hours = row[0]

            project = db.query(Project).filter(Project.pep_wbs == pep).first()
            if not project:
                continue

            baseline = (
                db.query(ProjectBaseline)
                .filter(
                    ProjectBaseline.project_id == project.id,
                    ProjectBaseline.is_active == True,  # noqa: E712
                )
                .first()
            )
            budget_hours, _ = resolve_effective_budget(project, baseline)
            if not budget_hours:
                continue

            health = classify_health(consumed_hours, budget_hours, warning_threshold, critical_threshold)

            if health == "ok":
                _resolve_project_alerts(db, project.id, "budget_warning", "budget_overrun")
                continue

            if health not in ("warning", "overrun"):
                continue

            ratio = round(consumed_hours / budget_hours * 100, 1)
            alert_type = "budget_warning" if health == "warning" else "budget_overrun"
            level = "warning" if health == "warning" else "error"
            label = project.name or pep
            status_label = "Atenção" if health == "warning" else "Estourado"
            msg = (
                f"Projeto '{label}' ({pep}): orçamento {ratio}% consumido ({status_label})."
            )

            _upsert_project_alert(
                db, project.id, pep, alert_type, level, msg, metric_value=ratio / 100
            )
            for uid in _get_notif_recipients(db, project.id):
                create_notification(db, uid, msg, level=level)
    except Exception:
        pass  # Non-critical — never block the upload response


def notify_schedule_risk(db: Session, pep_wbs_list: list[str]) -> None:
    """Create schedule-risk notifications for PEPs with consecutive low SPI cycles.

    Requires ProjectCyclePlan (baseline) to compute SPI. PEPs without a plan are skipped.
    Non-critical: exceptions are swallowed so they never block the upload response.
    Also auto-resolves alerts when SPI recovers.
    """
    if not pep_wbs_list:
        return
    try:
        from backend.app.models import (
            Cycle,
            GlobalConfig,
            PepCycleSummary,
            Project,
            ProjectCyclePlan,
        )
        from backend.app.services.evm import compute_spi

        cfg = db.get(GlobalConfig, 1)
        spi_threshold = float(getattr(cfg, "spi_warning_threshold", 0.85) or 0.85)
        consecutive_n = int(getattr(cfg, "spi_risk_consecutive_cycles", 2) or 2)

        for pep in pep_wbs_list:
            project = db.query(Project).filter(Project.pep_wbs == pep).first()
            if not project:
                continue

            rows = (
                db.query(PepCycleSummary, ProjectCyclePlan, Cycle)
                .join(Cycle, Cycle.id == PepCycleSummary.cycle_id)
                .join(
                    ProjectCyclePlan,
                    (ProjectCyclePlan.cycle_id == PepCycleSummary.cycle_id)
                    & (ProjectCyclePlan.project_id == project.id),
                )
                .filter(PepCycleSummary.pep_wbs == pep)
                .filter(Cycle.is_active == True)  # noqa: E712
                .order_by(Cycle.start_date.desc())
                .limit(consecutive_n)
                .all()
            )

            if len(rows) < consecutive_n:
                continue

            spi_values: list[float] = []
            for summary, plan, _cycle in rows:
                if not plan.planned_hours:
                    break
                # Intentional period-level use: for consecutive-cycle risk detection
                # we want to know if each individual cycle was behind plan, not the
                # cumulative SPI.  compute_spi performs actual/planned regardless of
                # whether the inputs are period or cumulative, so this is correct.
                spi = compute_spi(plan.planned_hours, summary.total_hours)
                if spi is None:
                    break
                spi_values.append(spi)

            if len(spi_values) < consecutive_n:
                continue

            all_at_risk = all(s < spi_threshold for s in spi_values)

            if not all_at_risk:
                _resolve_project_alerts(db, project.id, "schedule_risk")
                continue

            avg_spi = round(sum(spi_values) / len(spi_values), 2)
            label = project.name or pep
            msg = (
                f"Projeto '{label}' ({pep}): SPI médio {avg_spi} nos últimos "
                f"{consecutive_n} ciclos — ritmo atual projeta atraso. "
                f"Sugestão: revisar alocação da equipe ou atualizar o plano de ciclos."
            )

            _upsert_project_alert(
                db, project.id, pep, "schedule_risk", "warning", msg,
                metric_value=avg_spi, consecutive_cycles=consecutive_n,
            )
            for uid in _get_notif_recipients(db, project.id):
                create_notification(db, uid, msg, level="warning")
    except Exception:
        pass  # Non-critical — never block the upload response
