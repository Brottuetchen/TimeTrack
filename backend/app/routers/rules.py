"""
Assignment Rules Router - Verwaltet automatische Zuweisungs-Regeln (lokal).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession, joinedload

from ..database import get_db
from ..models import AssignmentRule, Project, Milestone
from .. import schemas

router = APIRouter(prefix="/rules", tags=["assignment-rules"])


@router.get("", response_model=List[schemas.AssignmentRuleRead])
def list_rules(
    user_id: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: DBSession = Depends(get_db),
):
    """
    Listet alle Assignment-Regeln eines Users.
    """
    query = db.query(AssignmentRule).options(
        joinedload(AssignmentRule.project),
        joinedload(AssignmentRule.milestone),
    )

    if user_id:
        query = query.filter(AssignmentRule.user_id == user_id)
    if enabled is not None:
        query = query.filter(AssignmentRule.enabled == enabled)

    rules = query.order_by(AssignmentRule.priority.desc()).all()
    return rules


@router.get("/{rule_id}", response_model=schemas.AssignmentRuleRead)
def get_rule(rule_id: int, db: DBSession = Depends(get_db)):
    """Einzelne Regel abrufen"""
    rule = db.query(AssignmentRule).options(
        joinedload(AssignmentRule.project),
        joinedload(AssignmentRule.milestone),
    ).filter(AssignmentRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("", response_model=schemas.AssignmentRuleRead, status_code=201)
def create_rule(payload: schemas.AssignmentRuleCreate, db: DBSession = Depends(get_db)):
    """
    Erstellt neue Assignment-Regel.
    Validiert dass Projekt/Milestone existieren.
    """
    # Validate project exists
    if payload.auto_project_id:
        project = db.get(Project, payload.auto_project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate milestone exists
    if payload.auto_milestone_id:
        milestone = db.get(Milestone, payload.auto_milestone_id)
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

    rule = AssignmentRule(**payload.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Refresh relationships
    if rule.auto_project_id:
        db.refresh(rule.project)
    if rule.auto_milestone_id:
        db.refresh(rule.milestone)

    return rule


@router.put("/{rule_id}", response_model=schemas.AssignmentRuleRead)
def update_rule(
    rule_id: int,
    payload: schemas.AssignmentRuleUpdate,
    db: DBSession = Depends(get_db),
):
    """
    Aktualisiert bestehende Regel.
    """
    rule = db.get(AssignmentRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Validate project if being updated
    if payload.auto_project_id:
        project = db.get(Project, payload.auto_project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate milestone if being updated
    if payload.auto_milestone_id:
        milestone = db.get(Milestone, payload.auto_milestone_id)
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)

    # Refresh relationships
    if rule.auto_project_id:
        db.refresh(rule.project)
    if rule.auto_milestone_id:
        db.refresh(rule.milestone)

    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: DBSession = Depends(get_db)):
    """
    Löscht eine Regel.
    """
    rule = db.get(AssignmentRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return None
