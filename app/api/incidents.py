"""Incidents API router."""

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.orm import Incident
from app.models.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentResolve,
    FeedbackCreate,
    FeedbackResponse,
    AnalysisResponse,
)
from app.services.agent import IncidentResponseAgent
from app.services.learning import LearningLoopService
from app.llm.factory import get_llm_provider
from app.memory.factory import get_memory_store

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def format_incident_response(inc: Incident) -> IncidentResponse:
    """Format ORM Incident to Pydantic schema with parsed JSON fields."""
    timeline = None
    if inc.timeline:
        try:
            timeline = json.loads(inc.timeline) if isinstance(inc.timeline, str) else inc.timeline
        except Exception:
            timeline = []

    res_steps = None
    if inc.resolution_steps:
        try:
            res_steps = json.loads(inc.resolution_steps) if isinstance(inc.resolution_steps, str) else inc.resolution_steps
        except Exception:
            res_steps = [str(inc.resolution_steps)]

    return IncidentResponse(
        id=inc.id,
        title=inc.title,
        service=inc.service,
        severity=inc.severity,
        status=inc.status,
        category=inc.category,
        symptoms=inc.symptoms,
        logs_snippet=inc.logs_snippet,
        timeline=timeline,
        root_cause=inc.root_cause,
        resolution_steps=res_steps,
        runbook_id=inc.runbook_id,
        time_to_resolve_min=inc.time_to_resolve_min,
        outcome=inc.outcome,
        created_at=inc.created_at,
        resolved_at=inc.resolved_at,
    )


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(incident_in: IncidentCreate, db: Session = Depends(get_db)):
    """Create a new operational incident in OPEN state."""
    count = db.query(Incident).count()
    new_id = f"INC-{1000 + count + 1}"

    now = datetime.now(timezone.utc)
    initial_timeline = [
        {
            "timestamp": now.isoformat(),
            "message": f"Incident {new_id} reported on {incident_in.service} with severity {incident_in.severity}.",
            "level": "INFO",
        }
    ]

    inc = Incident(
        id=new_id,
        title=incident_in.title,
        service=incident_in.service,
        severity=incident_in.severity,
        status="OPEN",
        category=incident_in.category,
        symptoms=incident_in.symptoms,
        logs_snippet=incident_in.logs_snippet or "",
        timeline=json.dumps(initial_timeline),
        created_at=now,
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return format_incident_response(inc)


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    service: Optional[str] = Query(None, description="Filter by service"),
    severity: Optional[str] = Query(None, description="Filter by severity (SEV1, SEV2, SEV3)"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, INVESTIGATING, RESOLVED)"),
    db: Session = Depends(get_db),
):
    """List incidents with optional filters."""
    query = db.query(Incident)
    if service:
        query = query.filter(Incident.service.ilike(f"%{service}%"))
    if severity:
        query = query.filter(Incident.severity == severity.upper())
    if status:
        query = query.filter(Incident.status == status.upper())

    results = query.order_by(Incident.created_at.desc()).all()
    return [format_incident_response(i) for i in results]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Fetch single incident details."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return format_incident_response(inc)


@router.post("/{incident_id}/analyze", response_model=AnalysisResponse)
async def analyze_incident(incident_id: str, db: Session = Depends(get_db)):
    """Trigger agent triage pipeline using persistent memory recall and LLM reasoning."""
    agent = IncidentResponseAgent(
        memory_store=get_memory_store(),
        llm_provider=get_llm_provider(),
    )
    try:
        analysis = await agent.analyze_incident(incident_id=incident_id, db=db)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{incident_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    incident_id: str,
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
):
    """Submit operator thumbs up/down feedback on recommended runbooks."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    service = LearningLoopService(
        memory_store=get_memory_store(),
        llm_provider=get_llm_provider(),
    )
    feedback = await service.record_feedback(
        incident_id=incident_id,
        feedback_in=feedback_in,
        db=db,
    )
    return FeedbackResponse.model_validate(feedback)


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    resolve_in: IncidentResolve,
    db: Session = Depends(get_db),
):
    """Mark incident resolved, update runbook metrics, and retain episodic memory."""
    service = LearningLoopService(
        memory_store=get_memory_store(),
        llm_provider=get_llm_provider(),
    )
    incident = await service.resolve_incident(
        incident_id=incident_id,
        resolve_in=resolve_in,
        db=db,
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return format_incident_response(incident)
