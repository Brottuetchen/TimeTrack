from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import CallDirection, SourceType


class EventBase(BaseModel):
    timestamp_start: datetime = Field(default_factory=datetime.utcnow)
    timestamp_end: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    machine_id: Optional[str] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None


class PhoneEventCreate(EventBase):
    source_type: SourceType = Field(default=SourceType.PHONE, const=True)
    phone_number: Optional[str] = None
    contact_name: Optional[str] = None
    direction: Optional[CallDirection] = None


class WindowEventCreate(EventBase):
    source_type: SourceType = Field(default=SourceType.WINDOW, const=True)
    window_title: str
    process_name: str


class EventRead(BaseModel):
    id: int
    source_type: SourceType
    timestamp_start: datetime
    timestamp_end: Optional[datetime]
    duration_seconds: Optional[int]
    phone_number: Optional[str]
    contact_name: Optional[str]
    direction: Optional[CallDirection]
    window_title: Optional[str]
    process_name: Optional[str]
    machine_id: Optional[str]
    device_id: Optional[str]
    user_id: Optional[str]

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str
    kunde: Optional[str] = None
    notizen: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int

    class Config:
        orm_mode = True


class MilestoneBase(BaseModel):
    project_id: int
    name: str
    soll_stunden: Optional[float] = None
    ist_stunden: Optional[float] = None
    bonus_relevant: bool = False


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneRead(MilestoneBase):
    id: int

    class Config:
        orm_mode = True


class AssignmentBase(BaseModel):
    event_id: int
    project_id: int
    milestone_id: Optional[int] = None
    activity_type: Optional[str] = None
    comment: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    project_id: Optional[int] = None
    milestone_id: Optional[int] = None
    activity_type: Optional[str] = None
    comment: Optional[str] = None


class AssignmentRead(BaseModel):
    id: int
    event: EventRead
    project: ProjectRead
    milestone: Optional[MilestoneRead]
    activity_type: Optional[str]
    comment: Optional[str]

    class Config:
        orm_mode = True
