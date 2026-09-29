"""API integration tests covering all required endpoints."""

import pytest
import json
from app.models.orm import Incident, Runbook


def test_health_endpoint(client):
    """GET /health must never leak secret keys and report active components."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data
    assert "memory_backend" in data
    assert "****" in data["groq_key_masked"]
    assert "****" in data["hindsight_key_masked"]


def test_incident_crud_lifecycle(client):
    """POST /incidents, GET /incidents, GET /incidents/{id}."""
    # Create incident
    payload = {
        "title": "API Gateway 504 Timeout on Checkout",
        "service": "api-gateway",
        "severity": "SEV1",
        "symptoms": "Upstream timed out connecting to payment service",
        "logs_snippet": "504 Gateway Time-out while reading upstream response",
    }
    create_res = client.post("/incidents", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    inc_id = created["id"]
    assert inc_id.startswith("INC-")
    assert created["status"] == "OPEN"

    # List incidents
    list_res = client.get("/incidents?service=api-gateway")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(i["id"] == inc_id for i in items)

    # Get single incident
    get_res = client.get(f"/incidents/{inc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inc_id


def test_analyze_incident(client, db_session):
    """POST /incidents/{id}/analyze returns confidence, root cause, runbook, and citations."""
    inc = Incident(
        id="INC-ANALYZE-01",
        title="High error rate on postgres-primary",
        service="postgres-primary",
        severity="SEV1",
        status="OPEN",
        symptoms="Connection pool exhausted",
    )
    db_session.merge(inc)
    db_session.commit()

    res = client.post("/incidents/INC-ANALYZE-01/analyze")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "INC-ANALYZE-01"
    assert "probable_root_cause" in data
    assert "confidence" in data
    assert "ranked_resolution_steps" in data
    assert "why_explanation" in data


def test_feedback_endpoint(client, db_session):
    """POST /incidents/{id}/feedback updates runbook effectiveness."""
    rb = Runbook(
        id="RB-FEED-01",
        title="Pool Fix",
        service="postgres-primary",
        description="Fix pool",
        steps=json.dumps(["Step 1"]),
        times_suggested=2,
        times_worked=1,
        success_rate=0.5,
    )
    db_session.merge(rb)

    inc = Incident(
        id="INC-FEED-01",
        title="Test Feed",
        service="postgres-primary",
        severity="SEV2",
        status="INVESTIGATING",
        symptoms="Pool full",
    )
    db_session.merge(inc)
    db_session.commit()

    feedback_payload = {
        "runbook_id": "RB-FEED-01",
        "helpful": True,
        "notes": "Fast mitigation",
    }
    res = client.post("/incidents/INC-FEED-01/feedback", json=feedback_payload)
    assert res.status_code == 200
    assert res.json()["helpful"] is True


def test_resolve_endpoint(client, db_session):
    """POST /incidents/{id}/resolve marks incident resolved and records MTTR."""
    inc = Incident(
        id="INC-RES-01",
        title="To Resolve",
        service="postgres-primary",
        severity="SEV1",
        status="INVESTIGATING",
        symptoms="Timeout",
    )
    db_session.merge(inc)
    db_session.commit()

    payload = {
        "root_cause": "Exhausted connection pool",
        "resolution_steps": ["Restarted worker pool", "Scaled PgBouncer"],
        "runbook_id": "RB-001",
        "time_to_resolve_min": 15,
        "outcome": "SUCCESS",
    }
    res = client.post("/incidents/INC-RES-01/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RESOLVED"
    assert data["time_to_resolve_min"] == 15


def test_runbooks_crud(client):
    """GET and POST /runbooks."""
    payload = {
        "id": "RB-API-01",
        "title": "API Gateway Reload",
        "service": "api-gateway",
        "description": "Reload Nginx gracefully",
        "steps": ["nginx -t", "nginx -s reload"],
    }
    create_res = client.post("/runbooks", json=payload)
    assert create_res.status_code == 201

    get_res = client.get("/runbooks")
    assert get_res.status_code == 200
    items = get_res.json()
    assert any(r["id"] == "RB-API-01" for r in items)


def test_postmortems_crud(client):
    """POST /postmortems."""
    payload = {
        "title": "Post-Mortem: Postgres Pool Saturation",
        "service": "postgres-primary",
        "summary": "Outage due to connection pool leak",
        "root_cause": "Missing client pool timeout",
        "lessons_learned": ["Enforce connection checkout timeouts"],
        "action_items": ["Audit pool configs"],
    }
    res = client.post("/postmortems", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("PM-")
    assert len(data["lessons_learned"]) > 0


def test_memory_search(client):
    """GET /memory/search?q=..."""
    res = client.get("/memory/search?q=postgres%20pool")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_analytics_endpoint(client):
    """GET /analytics returns aggregated metrics and trends."""
    res = client.get("/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_incidents" in data
    assert "avg_mttr_min" in data
    assert "mttr_trend" in data
    assert "top_root_causes" in data
    assert "runbook_success_rates" in data
