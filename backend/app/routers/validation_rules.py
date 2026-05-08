from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import ValidationRule
from backend.app.schemas import ValidationRuleIn, ValidationRuleOut

router = APIRouter(
    prefix="/api/validation-rules",
    tags=["validation-rules"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ValidationRuleOut])
def list_rules(db: DbSession, _: CurrentUser):
    return db.query(ValidationRule).order_by(ValidationRule.order, ValidationRule.id).all()


@router.post("", response_model=ValidationRuleOut, status_code=201)
def create_rule(payload: ValidationRuleIn, db: DbSession, current_user: AdminUser):
    rule = ValidationRule(
        is_active=payload.is_active,
        is_system=False,
        order=payload.order,
        field=payload.field,
        operator=payload.operator,
        value=payload.value,
        action=payload.action,
        description=payload.description,
        created_by=current_user.username,
        created_at=datetime.utcnow(),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=ValidationRuleOut)
def update_rule(rule_id: int, payload: ValidationRuleIn, db: DbSession, current_user: AdminUser):
    rule = db.get(ValidationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    if rule.is_system:
        # System rules: only value and is_active are editable
        immutable = {
            "field": (rule.field, payload.field),
            "operator": (rule.operator, payload.operator),
            "action": (rule.action, payload.action),
            "order": (rule.order, payload.order),
        }
        changed = [k for k, (old, new) in immutable.items() if old != new]
        if changed:
            raise HTTPException(
                status_code=422,
                detail=f"Regras de sistema: apenas value e is_active são editáveis. Campos imutáveis alterados: {changed}",
            )
        rule.value = payload.value
        rule.is_active = payload.is_active
    else:
        rule.is_active = payload.is_active
        rule.order = payload.order
        rule.field = payload.field
        rule.operator = payload.operator
        rule.value = payload.value
        rule.action = payload.action
        rule.description = payload.description
    rule.updated_by = current_user.username
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: DbSession, _: AdminUser):
    rule = db.get(ValidationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    if rule.is_system:
        raise HTTPException(status_code=403, detail="Regras de sistema não podem ser excluídas.")
    db.delete(rule)
    db.commit()


@router.patch("/{rule_id}/toggle", response_model=ValidationRuleOut)
def toggle_rule(rule_id: int, db: DbSession, current_user: AdminUser):
    rule = db.get(ValidationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    rule.is_active = not rule.is_active
    rule.updated_by = current_user.username
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/reorder", response_model=list[ValidationRuleOut])
def reorder_rules(order_map: dict[int, int], db: DbSession, current_user: AdminUser):
    """Bulk update order field. Body: {rule_id: new_order, ...}"""
    rules = db.query(ValidationRule).filter(ValidationRule.id.in_(order_map.keys())).all()
    for rule in rules:
        rule.order = max(1, order_map[rule.id])
        rule.updated_by = current_user.username
        rule.updated_at = datetime.utcnow()
    db.commit()
    return db.query(ValidationRule).order_by(ValidationRule.order, ValidationRule.id).all()
