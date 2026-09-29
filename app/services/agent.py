"""Incident Response Agent orchestrating triage, memory recall, and LLM reasoning."""

import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.orm import Incident, Runbook, PostMortem
from app.models.schemas import (
    AnalysisResponse,
    IncidentClassification,
    RunbookResponse,
    SimilarIncidentMatch,
)
from app.services.retrieval import HybridRetrievalService

logger = logging.getLogger("incident_agent.services.agent")


class IncidentResponseAgent:
    """Core autonomous agent coordinating memory recall, classification, and triage reasoning."""

    def __init__(self, memory_store, llm_provider):
        self.memory = memory_store
        self.llm = llm_provider

    def classify_incident(self, incident: Incident) -> IncidentClassification:
        """Classify incident into service, severity tier, and operational category."""
        category = incident.category
        if not category:
            text = f"{incident.title} {incident.symptoms} {incident.service}".lower()
            if any(k in text for k in ["db", "postgres", "pool", "query", "deadlock", "table", "wal"]):
                category = "Database"
            elif any(k in text for k in ["redis", "cache", "memory", "oom", "evict"]):
                category = "Caching / In-Memory"
            elif any(k in text for k in ["cert", "tls", "ssl", "dns", "ingress", "gateway", "502", "504"]):
                category = "Networking & TLS"
            elif any(k in text for k in ["kafka", "queue", "lag", "partition", "broker"]):
                category = "Messaging & Queues"
            elif any(k in text for k in ["k8s", "crashloop", "pod", "deployment", "node"]):
                category = "Kubernetes / Compute"
            else:
                category = "Application Core"

        return IncidentClassification(
            service=incident.service,
            severity=incident.severity or "SEV2",
            category=category,
        )

    async def analyze_incident(
        self,
        incident_id: str,
        db: Session,
    ) -> AnalysisResponse:
        """Execute full incident triage pipeline with hybrid memory recall and LLM reasoning."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found")

        # 1. Classification
        classification = self.classify_incident(incident)
        if incident.category != classification.category:
            incident.category = classification.category
            db.commit()

        # 2. Hybrid Retrieval from Memory Store
        retrieval_service = HybridRetrievalService(memory_store=self.memory, db=db)
        incident_dict = {
            "id": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "symptoms": incident.symptoms,
            "logs_snippet": incident.logs_snippet or "",
        }
        similar_matches = await retrieval_service.retrieve_similar_incidents(
            current_incident=incident_dict,
            top_k=4,
            threshold=0.40,
        )

        # 3. Retrieve available runbooks
        all_runbooks = db.query(Runbook).all()
        runbooks_data = [
            {
                "id": rb.id,
                "title": rb.title,
                "service": rb.service,
                "description": rb.description,
                "steps": json.loads(rb.steps) if isinstance(rb.steps, str) else rb.steps,
                "success_rate": rb.success_rate,
                "times_suggested": rb.times_suggested,
                "times_worked": rb.times_worked,
                "avg_mttr_min": rb.avg_mttr_min,
                "created_at": rb.created_at,
            }
            for rb in all_runbooks
        ]

        # 4. Semantic recall for post-mortem lessons
        query_text = f"{incident.service} {incident.symptoms}"
        recalled_pms = await self.memory.recall(
            query=query_text,
            limit=3,
            filter_type="postmortem",
        )
        lessons_list = []
        for pm in recalled_pms:
            content = pm.get("content", "")
            if "Lessons Learned:" in content:
                lessons_part = content.split("Lessons Learned:")[1].split("Action Items:")[0]
                for line in lessons_part.strip().split("\n"):
                    clean = line.strip().lstrip("-").strip()
                    if clean:
                        lessons_list.append(clean)

        # 5. LLM Reasoning Call
        matches_payload = [
            {
                "incident_id": m.incident_id,
                "title": m.title,
                "service": m.service,
                "severity": m.severity,
                "root_cause": m.root_cause,
                "runbook_id": m.runbook_id,
                "score": m.score,
            }
            for m in similar_matches
        ]

        llm_result = await self.llm.analyze_incident(
            incident=incident_dict,
            recalled_incidents=matches_payload,
            available_runbooks=runbooks_data,
            recalled_lessons=lessons_list,
        )

        # 6. Format recommended runbook
        recommended_rb = None
        rec_rb_id = llm_result.get("recommended_runbook_id")
        if not rec_rb_id and similar_matches and similar_matches[0].runbook_id:
            rec_rb_id = similar_matches[0].runbook_id

        if rec_rb_id:
            matched_rb = next((rb for rb in runbooks_data if rb["id"] == rec_rb_id), None)
            if matched_rb:
                recommended_rb = RunbookResponse(
                    id=matched_rb["id"],
                    title=matched_rb["title"],
                    service=matched_rb["service"],
                    description=matched_rb["description"],
                    steps=matched_rb["steps"],
                    times_suggested=matched_rb["times_suggested"],
                    times_worked=matched_rb["times_worked"],
                    success_rate=matched_rb["success_rate"],
                    avg_mttr_min=matched_rb["avg_mttr_min"],
                    created_at=matched_rb["created_at"],
                )

        # Default resolution steps if LLM didn't provide
        ranked_steps = llm_result.get("ranked_resolution_steps", [])
        if not ranked_steps and recommended_rb:
            ranked_steps = recommended_rb.steps
        elif not ranked_steps:
            ranked_steps = [
                "Verify live telemetry and recent deployment logs",
                "Isolate degraded service instances",
                "Apply recommended configuration tuning or rollback",
                "Verify recovery across latency and error rate dashboards",
            ]

        # Ensure timeline event recorded on incident
        timeline = []
        if incident.timeline:
            try:
                timeline = json.loads(incident.timeline)
            except Exception:
                timeline = []
        timeline.append({
            "timestamp": incident.created_at.isoformat() if incident.created_at else "",
            "message": f"Agent performed memory-augmented triage. Confidence: {llm_result.get('confidence', 0.85):.0%}",
            "level": "INFO",
        })
        incident.timeline = json.dumps(timeline)
        incident.status = "INVESTIGATING"
        db.commit()

        return AnalysisResponse(
            incident_id=incident.id,
            classification=classification,
            probable_root_cause=llm_result.get(
                "probable_root_cause", "Underlying system saturation"
            ),
            confidence=float(llm_result.get("confidence", 0.85)),
            why_explanation=llm_result.get("why_explanation", ""),
            cited_incident_ids=llm_result.get("cited_incident_ids", []),
            recommended_runbook=recommended_rb,
            ranked_resolution_steps=ranked_steps,
            similar_incidents=similar_matches,
            post_mortem_lessons=lessons_list[:4],
            is_novel_incident=llm_result.get("is_novel_incident", len(similar_matches) == 0),
        )
