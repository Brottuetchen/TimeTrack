import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Assignment, Event, SourceType

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
