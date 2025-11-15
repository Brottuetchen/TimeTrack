from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import schemas
from ..database import get_db
from ..models import Assignment, Event, Milestone, Project

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=List[schemas.AssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.event), joinedload(Assignment.project), joinedload(Assignment.milestone))
        .all()
    )
    return assignments


@router.post("", response_model=schemas.AssignmentRead, status_code=201)
def create_assignment(payload: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    _ensure_event_exists(payload.event_id, db)
    _ensure_project_exists(payload.project_id, db)
    if payload.milestone_id:
        _ensure_milestone_exists(payload.milestone_id, db)

    if db.query(Assignment).filter(Assignment.event_id == payload.event_id).first():
        raise HTTPException(status_code=400, detail="Event already assigned")

    assignment = Assignment(**payload.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    db.refresh(assignment.event)
    db.refresh(assignment.project)
    if assignment.milestone_id:
        db.refresh(assignment.milestone)
    return assignment


@router.put("/{assignment_id}", response_model=schemas.AssignmentRead)
def update_assignment(assignment_id: int, payload: schemas.AssignmentUpdate, db: Session = Depends(get_db)):
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if payload.project_id:
        _ensure_project_exists(payload.project_id, db)
    if payload.milestone_id:
        _ensure_milestone_exists(payload.milestone_id, db)

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(assignment, key, value)
    db.commit()
    db.refresh(assignment)
    return assignment


def _ensure_event_exists(event_id: int, db: Session):
    if not db.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found")


def _ensure_project_exists(project_id: int, db: Session):
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


def _ensure_milestone_exists(milestone_id: int, db: Session):
    if not db.get(Milestone, milestone_id):
        raise HTTPException(status_code=404, detail="Milestone not found")

