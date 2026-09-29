"""Tests for incident resolution and episodic memory write path."""

import pytest
import json
from datetime import datetime, timezone
from app.models.orm import Incident, Runbook
from app.models.schemas import IncidentResolve
from app.services.learning import LearningLoopService
from app.llm.mock_provider import MockLLMProvider
from app.memory.factory import get_memory_store


@pytest.mark.asyncio
async def test_resolve_incident_memory_write_path(db_session):
    """Verify that resolving an incident records outcome, updates MTTR, and retains into memory."""
    rb = Runbook(
        id="RB-RESOLVE-01",
        title="Resolve Test Runbook",
        service="payment-service",
        description="Test",
        steps=json.dumps(["Step A"]),
        times_suggested=5,
        times_worked=5,
        success_rate=1.0,
        avg_mttr_min=20.0,
    )
    db_session.merge(rb)

    inc = Incident(
        id="INC-RESOLVE-99",
        title="Live Outage to Resolve",
        service="payment-service",
        severity="SEV1",
        status="OPEN",
        symptoms="Checkout failing with 504",
        created_at=datetime.now(timezone.utc),
    )
    db_session.merge(inc)
    db_session.commit()

    memory = get_memory_store()
    service = LearningLoopService(memory_store=memory, llm_provider=MockLLMProvider())

    resolve_in = IncidentResolve(
        root_cause="Database connection pool starvation",
        resolution_steps=["Increased pool size to 50", "Killed idle connections"],
        runbook_id="RB-RESOLVE-01",
        time_to_resolve_min=14,
        outcome="SUCCESS",
    )

    resolved = await service.resolve_incident(
        incident_id="INC-RESOLVE-99",
        resolve_in=resolve_in,
        db=db_session,
    )

    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert resolved.time_to_resolve_min == 14
    assert resolved.outcome == "SUCCESS"
    assert resolved.root_cause == "Database connection pool starvation"

    # Verify retained item in memory
    retained = [item for item in getattr(memory, "retained_items", []) if item["id"] == "INC-RESOLVE-99"]
    assert len(retained) == 1
    assert retained[0]["type"] == "incident"
    assert "Database connection pool starvation" in retained[0]["content"]
