"""SQLAlchemy ORM models for Incidents, Runbooks, PostMortems, and Feedback."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from app.models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Incident(Base):
    """Episodic record of an operational incident."""

    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    service = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # SEV1, SEV2, SEV3
    status = Column(String(30), default="OPEN", index=True)  # OPEN, INVESTIGATING, RESOLVED
    category = Column(String(100), nullable=True)  # Database, Network, Infrastructure, etc.

    symptoms = Column(Text, nullable=False)
    logs_snippet = Column(Text, nullable=True)
    timeline = Column(Text, nullable=True)  # JSON-serialized list of events

    # Resolution & Learning fields
    root_cause = Column(Text, nullable=True)
    resolution_steps = Column(Text, nullable=True)  # JSON-serialized list of steps
    runbook_id = Column(String(64), nullable=True, index=True)
    time_to_resolve_min = Column(Integer, nullable=True)
    outcome = Column(String(50), nullable=True)  # SUCCESS, MITIGATED, ESCALATED

    created_at = Column(DateTime, default=utc_now, index=True)
    resolved_at = Column(DateTime, nullable=True)


class Runbook(Base):
    """Semantic standard operating procedure with effectiveness tracking."""

    __tablename__ = "runbooks"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    service = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    steps = Column(Text, nullable=False)  # JSON-serialized list of strings

    # Effectiveness Memory metrics
    times_suggested = Column(Integer, default=0)
    times_worked = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)  # 0.0 - 1.0
    avg_mttr_min = Column(Float, default=30.0)

    created_at = Column(DateTime, default=utc_now)


class PostMortem(Base):
    """Semantic post-mortem document and extracted lessons."""

    __tablename__ = "post_mortems"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    incident_id = Column(String(64), nullable=True, index=True)
    service = Column(String(100), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    lessons_learned = Column(Text, nullable=False)  # JSON-serialized list of strings
    action_items = Column(Text, nullable=True)  # JSON-serialized list of strings

    created_at = Column(DateTime, default=utc_now)


class Feedback(Base):
    """Operator feedback on incident suggestions and runbooks."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), nullable=False, index=True)
    runbook_id = Column(String(64), nullable=True, index=True)
    helpful = Column(Boolean, nullable=False)  # True = Thumbs Up, False = Thumbs Down
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
