"""Tests for hybrid retrieval scoring and ranking."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from app.models.orm import Incident, Runbook
from app.services.retrieval import (
    HybridRetrievalService,
    calculate_service_match,
    calculate_severity_affinity,
    calculate_recency_factor,
)
from app.memory.base import MemoryStore


class SimpleMemoryStore(MemoryStore):
    @property
    def name(self):
        return "mock_memory"

    async def ping(self):
        return True

    async def retain(self, item_id, content, memory_type, metadata=None):
        return True

    async def recall(self, query, limit=5, filter_type=None):
        return [
            {
                "id": "INC-1001",
                "content": "[INCIDENT: INC-1001] Postgres connection pool exhausted",
                "metadata": {"service": "postgres-primary"},
                "similarity": 0.95,
            }
        ]


@pytest.mark.asyncio
async def test_hybrid_scoring_formula(db_session):
    """Verify weights and ranking calculation."""
    # Ensure runbook exists
    rb = Runbook(
        id="RB-001",
        title="Postgres Pool Saturation",
        service="postgres-primary",
        description="Pool recovery",
        steps=json.dumps(["Terminate idle"]),
        times_suggested=10,
        times_worked=9,
        success_rate=0.90,
    )
    db_session.merge(rb)

    # Historical incident
    past_inc = Incident(
        id="INC-1001",
        title="Postgres connection timeout on payment-service",
        service="postgres-primary",
        severity="SEV1",
        status="RESOLVED",
        symptoms="Connection pool saturated",
        root_cause="Connection leak in error handler",
        runbook_id="RB-001",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    db_session.merge(past_inc)
    db_session.commit()

    retrieval_service = HybridRetrievalService(
        memory_store=SimpleMemoryStore(),
        db=db_session,
    )

    current_inc = {
        "id": "INC-TEST-NEW",
        "title": "DB connection timeouts after deploy on payment-service",
        "service": "postgres-primary",
        "severity": "SEV1",
        "symptoms": "Remaining connection slots are reserved for superuser",
    }

    results = await retrieval_service.retrieve_similar_incidents(
        current_incident=current_inc,
        top_k=3,
    )

    assert len(results) > 0
    top = results[0]
    assert top.incident_id == "INC-1001"
    assert top.runbook_id == "RB-001"
    assert top.score >= 0.80

    # Verify score breakdown elements
    b = top.score_breakdown
    assert b.service_match == 1.0  # Exact match on postgres-primary
    assert b.severity_match == 1.0  # Both SEV1
    assert b.vector_similarity >= 0.80
    assert b.runbook_success_rate == 0.90


def test_service_match():
    assert calculate_service_match("postgres-primary", "postgres-primary") == 1.0
    assert calculate_service_match("postgres-primary", "postgres-replica") == 0.7
    assert calculate_service_match("redis-cluster", "kafka-pipeline") == 0.1


def test_severity_affinity():
    assert calculate_severity_affinity("SEV1", "SEV1") == 1.0
    assert calculate_severity_affinity("SEV1", "SEV2") == 0.7
    assert calculate_severity_affinity("SEV1", "SEV3") == 0.4
