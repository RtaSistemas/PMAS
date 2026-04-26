from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import DbSession
from backend.app.models import Collaborator, RateCard, SeniorityLevel
from backend.app.schemas import CollaboratorSeniorityIn, RateCardIn, SeniorityLevelIn

router = APIRouter(prefix="/api", tags=["ratecard"])


def _assert_no_overlap(db: Session, body: RateCardIn, exclude_id: int | None = None) -> None:
    q = db.query(RateCard).filter(
        RateCard.seniority_level_id == body.seniority_level_id,
        (RateCard.valid_to.is_(None)) | (RateCard.valid_to >= body.valid_from),
    )
    if body.valid_to is not None:
        q = q.filter(RateCard.valid_from <= body.valid_to)
    if exclude_id is not None:
        q = q.filter(RateCard.id != exclude_id)
    if q.first():
        raise HTTPException(
            status_code=409,
            detail="Período sobrepõe outro rate card existente para o mesmo nível.",
        )


# ---------------------------------------------------------------------------
# Seniority Levels
# ---------------------------------------------------------------------------

@router.get("/seniority-levels")
def list_seniority_levels(db: DbSession):
    levels = db.query(SeniorityLevel).order_by(SeniorityLevel.name).all()
    return [{"id": l.id, "name": l.name} for l in levels]


@router.post("/seniority-levels", status_code=201)
def create_seniority_level(body: SeniorityLevelIn, db: DbSession):
    if db.query(SeniorityLevel).filter(SeniorityLevel.name == body.name).first():
        raise HTTPException(status_code=409, detail="Nível de senioridade já cadastrado.")
    sl = SeniorityLevel(name=body.name)
    db.add(sl); db.commit(); db.refresh(sl)
    return {"id": sl.id, "name": sl.name}


@router.put("/seniority-levels/{level_id}")
def update_seniority_level(level_id: int, body: SeniorityLevelIn, db: DbSession):
    sl = db.get(SeniorityLevel, level_id)
    if not sl:
        raise HTTPException(status_code=404, detail="Nível não encontrado.")
    conflict = db.query(SeniorityLevel).filter(
        SeniorityLevel.name == body.name, SeniorityLevel.id != level_id
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Nome já em uso por outro nível.")
    sl.name = body.name
    db.commit(); db.refresh(sl)
    return {"id": sl.id, "name": sl.name}


@router.delete("/seniority-levels/{level_id}", status_code=204)
def delete_seniority_level(level_id: int, db: DbSession):
    sl = db.get(SeniorityLevel, level_id)
    if not sl:
        raise HTTPException(status_code=404, detail="Nível não encontrado.")
    in_use = db.query(Collaborator).filter(Collaborator.seniority_level_id == level_id).count()
    if in_use:
        raise HTTPException(
            status_code=409,
            detail=f"Nível em uso por {in_use} colaborador(es). Reatribua antes de excluir.",
        )
    db.delete(sl); db.commit()


# ---------------------------------------------------------------------------
# Rate Cards
# ---------------------------------------------------------------------------

@router.get("/rate-cards")
def list_rate_cards(db: DbSession, seniority_level_id: Optional[int] = None):
    q = db.query(RateCard)
    if seniority_level_id:
        q = q.filter(RateCard.seniority_level_id == seniority_level_id)
    cards = q.order_by(RateCard.seniority_level_id, RateCard.valid_from.desc()).all()
    return [
        {
            "id": c.id,
            "seniority_level_id": c.seniority_level_id,
            "seniority_level_name": c.seniority_level.name,
            "hourly_rate": c.hourly_rate,
            "valid_from": str(c.valid_from),
            "valid_to": str(c.valid_to) if c.valid_to else None,
        }
        for c in cards
    ]


@router.post("/rate-cards", status_code=201)
def create_rate_card(body: RateCardIn, db: DbSession):
    if body.valid_to and body.valid_to < body.valid_from:
        raise HTTPException(status_code=422, detail="valid_to não pode ser anterior a valid_from.")
    if not db.get(SeniorityLevel, body.seniority_level_id):
        raise HTTPException(status_code=404, detail="Nível de senioridade não encontrado.")
    _assert_no_overlap(db, body)
    card = RateCard(
        seniority_level_id=body.seniority_level_id,
        hourly_rate=body.hourly_rate,
        valid_from=body.valid_from,
        valid_to=body.valid_to,
    )
    db.add(card); db.commit(); db.refresh(card)
    return {"id": card.id}


@router.put("/rate-cards/{card_id}")
def update_rate_card(card_id: int, body: RateCardIn, db: DbSession):
    card = db.get(RateCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Rate card não encontrado.")
    if body.valid_to and body.valid_to < body.valid_from:
        raise HTTPException(status_code=422, detail="valid_to não pode ser anterior a valid_from.")
    _assert_no_overlap(db, body, exclude_id=card_id)
    card.seniority_level_id = body.seniority_level_id
    card.hourly_rate = body.hourly_rate
    card.valid_from = body.valid_from
    card.valid_to = body.valid_to
    db.commit(); db.refresh(card)
    return {"id": card.id}


@router.delete("/rate-cards/{card_id}", status_code=204)
def delete_rate_card(card_id: int, db: DbSession):
    card = db.get(RateCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Rate card não encontrado.")
    db.delete(card); db.commit()


# ---------------------------------------------------------------------------
# Team (collaborators + seniority)
# ---------------------------------------------------------------------------

@router.get("/team")
def list_team(db: DbSession):
    collabs = db.query(Collaborator).order_by(Collaborator.name).all()
    today = date.today()

    valid_cards = (
        db.query(RateCard)
        .filter(
            RateCard.valid_from <= today,
            (RateCard.valid_to.is_(None)) | (RateCard.valid_to >= today),
        )
        .order_by(RateCard.seniority_level_id, RateCard.valid_from.desc())
        .all()
    )
    rate_by_level: dict[int, float] = {}
    for rc in valid_cards:
        if rc.seniority_level_id not in rate_by_level:
            rate_by_level[rc.seniority_level_id] = rc.hourly_rate

    return [
        {
            "id": c.id,
            "name": c.name,
            "seniority_level_id": c.seniority_level_id,
            "seniority_level_name": c.seniority_level.name if c.seniority_level else None,
            "current_hourly_rate": rate_by_level.get(c.seniority_level_id) if c.seniority_level_id else None,
        }
        for c in collabs
    ]


@router.put("/team/{collab_id}/seniority")
def assign_seniority(collab_id: int, body: CollaboratorSeniorityIn, db: DbSession):
    collab = db.get(Collaborator, collab_id)
    if not collab:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado.")
    if body.seniority_level_id is not None and not db.get(SeniorityLevel, body.seniority_level_id):
        raise HTTPException(status_code=404, detail="Nível de senioridade não encontrado.")
    collab.seniority_level_id = body.seniority_level_id
    db.commit()
    return {"id": collab.id, "seniority_level_id": collab.seniority_level_id}
