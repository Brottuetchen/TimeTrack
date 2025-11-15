import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .database import Base


class SourceType(str, enum.Enum):
    PHONE = "phone"
    WINDOW = "window"


class CallDirection(str, enum.Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    MISSED = "MISSED"
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    INTERNAL = "INTERNAL"


class CallSource(str, enum.Enum):
    BLUETOOTH_PBAP = "bluetooth_pbap"
    TEAMS = "teams"
    PLACETEL = "placetel"
    MANUAL = "manual"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(Enum(SourceType), nullable=False)
    timestamp_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    timestamp_end = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    is_private = Column(Boolean, nullable=False, default=False)

    phone_number = Column(String(64), nullable=True)
    contact_name = Column(String(128), nullable=True)
    direction = Column(Enum(CallDirection), nullable=True)

    window_title = Column(String(256), nullable=True)
    process_name = Column(String(128), nullable=True)

    machine_id = Column(String(64), nullable=True)
    device_id = Column(String(64), nullable=True)
    user_id = Column(String(64), nullable=True)

    assignments = relationship("Assignment", back_populates="event", uselist=True)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    kunde = Column(String(128), nullable=True)
    notizen = Column(Text, nullable=True)

    milestones = relationship("Milestone", back_populates="project")
    assignments = relationship("Assignment", back_populates="project")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(128), nullable=False)
    soll_stunden = Column(Float, nullable=True)
    ist_stunden = Column(Float, nullable=True)
    bonus_relevant = Column(Boolean, default=False)

    project = relationship("Project", back_populates="milestones")
    assignments = relationship("Assignment", back_populates="milestone")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, unique=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    activity_type = Column(String(64), nullable=True)
    comment = Column(Text, nullable=True)

    event = relationship("Event", back_populates="assignments")
    project = relationship("Project", back_populates="assignments")
    milestone = relationship("Milestone", back_populates="assignments")


class CallLog(Base):
    """
    Unified call log for all call sources (Bluetooth/PBAP, Teams, Placetel, manual).
    Stores call metadata with source tracking and deduplication via external_id.
    """
    __tablename__ = "calllogs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    source = Column(Enum(CallSource), nullable=False, index=True)
    external_id = Column(String(256), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    direction = Column(Enum(CallDirection), nullable=True)
    remote_number = Column(String(128), nullable=True)
    remote_name = Column(String(256), nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
