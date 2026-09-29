"""Analytics API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import AnalyticsResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    """Retrieve operational analytics, MTTR trend, and runbook success rates."""
    service = AnalyticsService(db=db)
    return service.get_system_analytics()
