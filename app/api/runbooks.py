"""Runbooks API router."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.orm import Runbook
from app.models.schemas import RunbookCreate, RunbookResponse
from app.memory.factory import get_memory_store

router = APIRouter(prefix="/runbooks", tags=["Runbooks"])


def format_runbook_response(rb: Runbook) -> RunbookResponse:
    steps = json.loads(rb.steps) if isinstance(rb.steps, str) else rb.steps
    return RunbookResponse(
        id=rb.id,
        title=rb.title,
        service=rb.service,
        description=rb.description,
        steps=steps,
        times_suggested=rb.times_suggested,
        times_worked=rb.times_worked,
        success_rate=rb.success_rate,
        avg_mttr_min=rb.avg_mttr_min,
        created_at=rb.created_at,
    )


@router.get("", response_model=List[RunbookResponse])
def list_runbooks(db: Session = Depends(get_db)):
    """List all operating runbooks sorted by effectiveness."""
    runbooks = db.query(Runbook).order_by(Runbook.success_rate.desc(), Runbook.times_suggested.desc()).all()
    return [format_runbook_response(r) for r in runbooks]


@router.post("", response_model=RunbookResponse, status_code=201)
async def create_runbook(runbook_in: RunbookCreate, db: Session = Depends(get_db)):
    """Create a new operational runbook and index into semantic memory."""
    existing = db.query(Runbook).filter(Runbook.id == runbook_in.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Runbook with ID {runbook_in.id} already exists")

    rb = Runbook(
        id=runbook_in.id,
        title=runbook_in.title,
        service=runbook_in.service,
        description=runbook_in.description,
        steps=json.dumps(runbook_in.steps),
        times_suggested=0,
        times_worked=0,
        success_rate=1.0,
        avg_mttr_min=25.0,
    )
    db.add(rb)
    db.commit()
    db.refresh(rb)

    # Retain into semantic memory
    memory = get_memory_store()
    content = (
        f"Runbook: {rb.title} (ID: {rb.id})\n"
        f"Service: {rb.service}\n"
        f"Description: {rb.description}\n"
        f"Mitigation Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(runbook_in.steps))
    )
    try:
        await memory.retain(
            item_id=rb.id,
            content=content,
            memory_type="runbook",
            metadata={"service": rb.service, "title": rb.title},
        )
    except Exception:
        pass

    return format_runbook_response(rb)
