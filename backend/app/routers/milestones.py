from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Milestone

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("", response_model=List[schemas.MilestoneRead])
def list_milestones(project_id: int | None = Query(None), db: Session = Depends(get_db)):
    query = db.query(Milestone)
    if project_id is not None:
        query = query.filter(Milestone.project_id == project_id)
    return query.order_by(Milestone.name).all()


@router.post("", response_model=schemas.MilestoneRead, status_code=201)
def create_milestone(payload: schemas.MilestoneCreate, db: Session = Depends(get_db)):
    milestone = Milestone(**payload.dict())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.put("/{milestone_id}", response_model=schemas.MilestoneRead)
def update_milestone(milestone_id: int, payload: schemas.MilestoneCreate, db: Session = Depends(get_db)):
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for key, value in payload.dict().items():
        setattr(milestone, key, value)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()
    return None

