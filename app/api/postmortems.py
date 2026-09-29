"""Post-mortems API router."""

import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.orm import PostMortem
from app.models.schemas import PostMortemCreate, PostMortemResponse
from app.services.learning import LearningLoopService
from app.llm.factory import get_llm_provider
from app.memory.factory import get_memory_store

router = APIRouter(prefix="/postmortems", tags=["PostMortems"])


def format_pm_response(pm: PostMortem) -> PostMortemResponse:
    lessons = json.loads(pm.lessons_learned) if isinstance(pm.lessons_learned, str) else pm.lessons_learned
    actions = json.loads(pm.action_items) if pm.action_items and isinstance(pm.action_items, str) else pm.action_items
    return PostMortemResponse(
        id=pm.id,
        title=pm.title,
        incident_id=pm.incident_id,
        service=pm.service,
        summary=pm.summary,
        root_cause=pm.root_cause,
        lessons_learned=lessons,
        action_items=actions,
        created_at=pm.created_at,
    )


@router.get("", response_model=List[PostMortemResponse])
def list_postmortems(db: Session = Depends(get_db)):
    """List all ingested post-mortems and preventative lessons."""
    pms = db.query(PostMortem).order_by(PostMortem.created_at.desc()).all()
    return [format_pm_response(p) for p in pms]


@router.post("", response_model=PostMortemResponse, status_code=201)
async def create_postmortem(pm_in: PostMortemCreate, db: Session = Depends(get_db)):
    """Ingest, parse, and retain a post-mortem document into semantic memory."""
    service = LearningLoopService(
        memory_store=get_memory_store(),
        llm_provider=get_llm_provider(),
    )
    pm = await service.ingest_postmortem(pm_in=pm_in, db=db)
    return format_pm_response(pm)
