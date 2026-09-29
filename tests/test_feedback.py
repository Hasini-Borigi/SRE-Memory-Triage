"""Tests for feedback learning and runbook effectiveness updates."""

import pytest
import json
from app.models.orm import Incident, Runbook
from app.models.schemas import FeedbackCreate
from app.services.learning import LearningLoopService
from app.llm.mock_provider import MockLLMProvider
from app.memory.factory import get_memory_store


@pytest.mark.asyncio
async def test_feedback_thumbs_up_learning(db_session):
    """Test that thumbs up increases runbook success rate and times_worked."""
    rb = Runbook(
        id="RB-TEST-01",
        title="Test Runbook",
        service="payment-service",
        description="Test desc",
        steps=json.dumps(["Step 1"]),
        times_suggested=10,
        times_worked=5,
        success_rate=0.50,
        avg_mttr_min=30.0,
    )
    db_session.merge(rb)
    db_session.commit()

    memory = get_memory_store()
    service = LearningLoopService(memory_store=memory, llm_provider=MockLLMProvider())

    feedback_in = FeedbackCreate(
        runbook_id="RB-TEST-01",
        helpful=True,
        notes="Remediated the timeout in 5 minutes",
    )

    fb = await service.record_feedback(
        incident_id="INC-1001",
        feedback_in=feedback_in,
        db=db_session,
    )

    assert fb.id is not None
    assert fb.helpful is True

    # Verify runbook updated in SQLite
    updated_rb = db_session.query(Runbook).filter(Runbook.id == "RB-TEST-01").first()
    assert updated_rb.times_suggested == 11
    assert updated_rb.times_worked == 6
    assert updated_rb.success_rate == round(6 / 11, 3)


@pytest.mark.asyncio
async def test_feedback_thumbs_down_learning(db_session):
    """Test that thumbs down increments suggested but lowers success rate."""
    rb = Runbook(
        id="RB-TEST-02",
        title="Test Runbook 2",
        service="payment-service",
        description="Test desc",
        steps=json.dumps(["Step 1"]),
        times_suggested=10,
        times_worked=8,
        success_rate=0.80,
        avg_mttr_min=30.0,
    )
    db_session.merge(rb)
    db_session.commit()

    memory = get_memory_store()
    service = LearningLoopService(memory_store=memory, llm_provider=MockLLMProvider())

    feedback_in = FeedbackCreate(
        runbook_id="RB-TEST-02",
        helpful=False,
        notes="Did not resolve the connection leak",
    )

    fb = await service.record_feedback(
        incident_id="INC-1002",
        feedback_in=feedback_in,
        db=db_session,
    )

    assert fb.helpful is False

    updated_rb = db_session.query(Runbook).filter(Runbook.id == "RB-TEST-02").first()
    assert updated_rb.times_suggested == 11
    assert updated_rb.times_worked == 8
    assert updated_rb.success_rate == round(8 / 11, 3)
