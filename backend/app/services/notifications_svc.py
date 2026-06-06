from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Notification


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    level: str = "info",
) -> Notification:
    """Create a Notification and add it to the session. Caller must commit."""
    notif = Notification(user_id=user_id, message=message, level=level)
    db.add(notif)
    return notif


def notify_threshold_crossings(db: Session, pep_wbs_list: list[str]) -> None:
    """Create warning/error notifications for users with access to PEPs crossing budget thresholds.

    Called after each successful upload. Non-critical: exceptions are swallowed so they never block
    the upload response.
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
            User,
            UserProjectAccess,
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
            consumed_hours, actual_cost = row[0], (row[1] or 0.0)

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
            if health not in ("warning", "overrun"):
                continue

            ratio = round(consumed_hours / budget_hours * 100, 1)
            level = "warning" if health == "warning" else "error"
            label = project.name or pep
            status_label = "Atenção" if health == "warning" else "Estourado"
            msg = (
                f"Projeto '{label}' ({pep}): orçamento {ratio}% consumido ({status_label})."
            )

            admin_ids = {u.id for u in db.query(User).filter(User.role == "admin").all()}
            access_user_ids = {
                a.user_id
                for a in db.query(UserProjectAccess)
                .filter(UserProjectAccess.project_id == project.id)
                .all()
            }
            for uid in admin_ids | access_user_ids:
                create_notification(db, uid, msg, level=level)
    except Exception:
        pass  # Non-critical — never block the upload response
