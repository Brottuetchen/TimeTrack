import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Assignment, Event, SourceType, Project, Milestone

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
def export_csv(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    source_type: Optional[SourceType] = Query(None),
    include_private: bool = Query(False),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Assignment)
        .join(Event)
        .options(joinedload(Assignment.event), joinedload(Assignment.project), joinedload(Assignment.milestone))
    )

    if start:
        query = query.filter(Event.timestamp_start >= start)
    if end:
        query = query.filter(Event.timestamp_start <= end)
    if source_type:
        query = query.filter(Event.source_type == source_type)
    if not include_private:
        query = query.filter(Event.is_private.is_(False))

    rows = []
    for assignment in query.all():
        event = assignment.event
        project = assignment.project
        milestone = assignment.milestone
        rows.append(
            {
                "date": event.timestamp_start.date().isoformat(),
                "start_time": event.timestamp_start.time().isoformat(timespec="seconds"),
                "end_time": event.timestamp_end.time().isoformat(timespec="seconds") if event.timestamp_end else "",
                "duration_minutes": (event.duration_seconds or 0) / 60,
                "source_type": event.source_type.value,
                "phone_number": event.phone_number or "",
                "contact_name": event.contact_name or "",
                "window_title": event.window_title or "",
                "process_name": event.process_name or "",
                "project_name": project.name if project else "",
                "milestone_name": milestone.name if milestone else "",
                "activity_type": assignment.activity_type or "",
                "comment": assignment.comment or "",
            }
        )

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "source_type",
            "phone_number",
            "contact_name",
            "window_title",
            "process_name",
            "project_name",
            "milestone_name",
            "activity_type",
            "comment",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/csv")
def export_projects_csv(db: Session = Depends(get_db)):
    """
    Export aller Projekte als CSV.
    Format: name, kunde, notizen
    """
    projects = db.query(Project).order_by(Project.name).all()

    rows = []
    for project in projects:
        rows.append({
            "name": project.name,
            "kunde": project.kunde or "",
            "notizen": project.notizen or "",
        })

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["name", "kunde", "notizen"])
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    filename = f"projects_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/milestones/csv")
def export_milestones_csv(project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """
    Export aller Milestones als CSV.
    Optional: Nur für ein bestimmtes Projekt.
    Format: project_name, name, soll_stunden, ist_stunden, bonus_relevant
    """
    query = db.query(Milestone).join(Project).options(joinedload(Milestone.project))

    if project_id is not None:
        query = query.filter(Milestone.project_id == project_id)

    milestones = query.order_by(Project.name, Milestone.name).all()

    rows = []
    for milestone in milestones:
        rows.append({
            "project_name": milestone.project.name if milestone.project else "",
            "name": milestone.name,
            "soll_stunden": milestone.soll_stunden or 0,
            "ist_stunden": milestone.ist_stunden or 0,
            "bonus_relevant": "ja" if milestone.bonus_relevant else "nein",
        })

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["project_name", "name", "soll_stunden", "ist_stunden", "bonus_relevant"]
    )
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    filename_suffix = f"_project_{project_id}" if project_id else ""
    filename = f"milestones{filename_suffix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
