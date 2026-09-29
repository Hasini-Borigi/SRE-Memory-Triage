"""Pydantic v2 schemas for requests, responses, and agent analysis."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Incident Schemas ----------------

class TimelineEvent(BaseModel):
    timestamp: str
    message: str
    level: str = "INFO"


class IncidentCreate(BaseModel):
    title: str = Field(...)
    service: str = Field(...)
    severity: str = Field("SEV2")  # SEV1, SEV2, SEV3
    symptoms: str = Field(...)
    logs_snippet: Optional[str] = Field(None)
    category: Optional[str] = Field(None)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    service: str
    severity: str
    status: str
    category: Optional[str] = None
    symptoms: str
    logs_snippet: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    root_cause: Optional[str] = None
    resolution_steps: Optional[List[str]] = None
    runbook_id: Optional[str] = None
    time_to_resolve_min: Optional[int] = None
    outcome: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class IncidentResolve(BaseModel):
    root_cause: Optional[str] = None
    resolution_steps: Optional[List[str]] = None
    runbook_id: Optional[str] = None
    time_to_resolve_min: Optional[int] = None
    outcome: Optional[str] = "SUCCESS"  # SUCCESS, MITIGATED, ESCALATED


# ---------------- Runbook Schemas ----------------

class RunbookCreate(BaseModel):
    id: str = Field(...)
    title: str = Field(...)
    service: str = Field(...)
    description: str = Field(...)
    steps: List[str] = Field(...)


class RunbookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    service: str
    description: str
    steps: List[str]
    times_suggested: int
    times_worked: int
    success_rate: float
    avg_mttr_min: float
    created_at: datetime


# ---------------- PostMortem Schemas ----------------

class PostMortemCreate(BaseModel):
    title: str
    service: str
    incident_id: Optional[str] = None
    content: Optional[str] = None  # Markdown or plain text
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    lessons_learned: Optional[List[str]] = None
    action_items: Optional[List[str]] = None


class PostMortemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    incident_id: Optional[str] = None
    service: str
    summary: str
    root_cause: str
    lessons_learned: List[str]
    action_items: Optional[List[str]] = None
    created_at: datetime


# ---------------- Feedback Schemas ----------------

class FeedbackCreate(BaseModel):
    runbook_id: Optional[str] = None
    helpful: bool  # True = helpful / thumbs up, False = thumbs down
    notes: Optional[str] = ""


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: str
    runbook_id: Optional[str] = None
    helpful: bool
    notes: Optional[str] = None
    created_at: datetime


# ---------------- Analysis & Triage Schemas ----------------

class ScoreBreakdown(BaseModel):
    vector_similarity: float
    service_match: float
    severity_match: float
    runbook_success_rate: float
    recency_factor: float
    final_score: float


class SimilarIncidentMatch(BaseModel):
    incident_id: str
    title: str
    service: str
    severity: str
    root_cause: Optional[str] = None
    runbook_id: Optional[str] = None
    score: float
    score_breakdown: ScoreBreakdown
    snippet: str


class IncidentClassification(BaseModel):
    service: str
    severity: str
    category: str


class AnalysisResponse(BaseModel):
    incident_id: str
    classification: IncidentClassification
    probable_root_cause: str
    confidence: float  # 0.0 - 1.0
    why_explanation: str
    cited_incident_ids: List[str]
    recommended_runbook: Optional[RunbookResponse] = None
    ranked_resolution_steps: List[str]
    similar_incidents: List[SimilarIncidentMatch]
    post_mortem_lessons: List[str]
    is_novel_incident: bool = False


# ---------------- Memory Search & Analytics ----------------

class MemorySearchResult(BaseModel):
    id: str
    type: str  # "incident", "runbook", "postmortem"
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    total_incidents: int
    open_incidents: int
    resolved_incidents: int
    avg_mttr_min: float
    mttr_trend: List[Dict[str, Any]]
    top_root_causes: List[Dict[str, Any]]
    runbook_success_rates: List[Dict[str, Any]]
    repeat_incident_rate: float


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str
    llm_status: str
    memory_backend: str
    memory_status: str
    groq_configured: bool
    hindsight_configured: bool
    groq_key_masked: str
    hindsight_key_masked: str
