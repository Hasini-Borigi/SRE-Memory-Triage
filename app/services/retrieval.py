"""Hybrid Retrieval and Explainable Scoring Engine."""

import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.orm import Incident, Runbook
from app.models.schemas import SimilarIncidentMatch, ScoreBreakdown


def calculate_recency_factor(created_at: Optional[datetime]) -> float:
    """Calculate recency score decaying smoothly over 180 days."""
    if not created_at:
        return 0.5
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
    # Exponential decay with half-life of ~60 days, floor at 0.1
    decay = math.exp(-0.0115 * age_days)
    return round(max(0.1, min(1.0, decay)), 4)


def calculate_service_match(target_service: str, candidate_service: str) -> float:
    """Match score based on service identity or category domain."""
    s1 = target_service.lower().strip()
    s2 = candidate_service.lower().strip()
    if s1 == s2:
        return 1.0
    # Partial token match (e.g. 'postgres' vs 'postgres-primary')
    tokens1 = set(s1.replace("-", "_").split("_"))
    tokens2 = set(s2.replace("-", "_").split("_"))
    if tokens1 & tokens2:
        return 0.7
    return 0.1


def calculate_severity_affinity(target_sev: str, candidate_sev: str) -> float:
    """Score affinity between severity tiers (SEV1, SEV2, SEV3)."""
    t = target_sev.upper().strip()
    c = candidate_sev.upper().strip()
    if t == c:
        return 1.0
    pairs = {("SEV1", "SEV2"), ("SEV2", "SEV1"), ("SEV2", "SEV3"), ("SEV3", "SEV2")}
    if (t, c) in pairs:
        return 0.7
    return 0.4


class HybridRetrievalService:
    """Retrieves candidates from memory and applies multi-factor explainable scoring."""

    def __init__(self, memory_store, db: Session):
        self.memory = memory_store
        self.db = db

    async def retrieve_similar_incidents(
        self,
        current_incident: Dict[str, Any],
        top_k: int = 5,
        threshold: float = 0.45,
    ) -> List[SimilarIncidentMatch]:
        """Perform hybrid search combining vector similarity, metadata matching, and runbook stats."""
        query_text = (
            f"Service: {current_incident.get('service')} | "
            f"Title: {current_incident.get('title')} | "
            f"Symptoms: {current_incident.get('symptoms')} | "
            f"Logs: {current_incident.get('logs_snippet', '')}"
        )

        # 1. Recall candidates from episodic memory store
        recalled_memories = await self.memory.recall(
            query=query_text,
            limit=top_k * 3,
            filter_type="incident",
        )

        # Build similarity lookup map
        sim_map = {}
        for mem in recalled_memories:
            item_id = mem.get("id")
            # In Hindsight, text might contain [INCIDENT: INC-xxx]
            sim_score = mem.get("similarity", 0.5)
            if item_id:
                sim_map[item_id] = sim_score
            content = mem.get("content", "")
            if "[INCIDENT:" in content:
                extracted_id = content.split("[INCIDENT:")[1].split("]")[0].strip()
                sim_map[extracted_id] = max(sim_map.get(extracted_id, 0.0), sim_score)

        # 2. Fetch all resolved/historical incidents from SQLite
        all_incidents = (
            self.db.query(Incident)
            .filter(Incident.id != current_incident.get("id"))
            .all()
        )

        # 3. Pre-fetch runbook effectiveness metrics
        runbooks = {rb.id: rb for rb in self.db.query(Runbook).all()}

        scored_candidates = []
        target_service = current_incident.get("service", "")
        target_severity = current_incident.get("severity", "SEV2")
        target_symptoms = current_incident.get("symptoms", "").lower()
        target_title = current_incident.get("title", "").lower()

        for inc in all_incidents:
            # Determine vector similarity
            vector_sim = sim_map.get(inc.id)
            if vector_sim is None:
                # Text token overlap fallback if vector recall didn't hit this specific record
                inc_text = f"{inc.title} {inc.symptoms} {inc.root_cause or ''}".lower()
                query_tokens = set(f"{target_title} {target_symptoms}".split())
                doc_tokens = set(inc_text.split())
                overlap = len(query_tokens & doc_tokens) / max(1, len(query_tokens))
                vector_sim = min(1.0, overlap * 1.5)

            # Metadata matches
            service_score = calculate_service_match(target_service, inc.service)
            severity_score = calculate_severity_affinity(target_severity, inc.severity)

            # Runbook effectiveness
            rb = runbooks.get(inc.runbook_id)
            if rb:
                runbook_score = max(0.2, min(1.0, rb.success_rate))
            else:
                runbook_score = 0.5

            # Recency factor
            recency_score = calculate_recency_factor(inc.created_at)

            # Hybrid Score Formulation:
            # 0.40 * vector_similarity + 0.20 * service_match + 0.15 * severity_match
            # + 0.15 * runbook_success_rate + 0.10 * recency_factor
            final_score = (
                0.40 * vector_sim
                + 0.20 * service_score
                + 0.15 * severity_score
                + 0.15 * runbook_score
                + 0.10 * recency_score
            )
            final_score = round(final_score, 4)

            breakdown = ScoreBreakdown(
                vector_similarity=round(vector_sim, 4),
                service_match=round(service_score, 4),
                severity_match=round(severity_score, 4),
                runbook_success_rate=round(runbook_score, 4),
                recency_factor=round(recency_score, 4),
                final_score=final_score,
            )

            snippet = inc.symptoms[:120] + ("..." if len(inc.symptoms) > 120 else "")

            scored_candidates.append(
                SimilarIncidentMatch(
                    incident_id=inc.id,
                    title=inc.title,
                    service=inc.service,
                    severity=inc.severity,
                    root_cause=inc.root_cause,
                    runbook_id=inc.runbook_id,
                    score=final_score,
                    score_breakdown=breakdown,
                    snippet=snippet,
                )
            )

        # Sort descending by final score
        scored_candidates.sort(key=lambda x: x.score, reverse=True)

        # Filter by threshold unless we need top results
        filtered = [c for c in scored_candidates if c.score >= threshold]
        if not filtered and scored_candidates and scored_candidates[0].score > 0.30:
            filtered = [scored_candidates[0]]

        return filtered[:top_k]
