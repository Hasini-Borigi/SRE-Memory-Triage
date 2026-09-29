"""Learning loop service: Feedback processing, post-mortem ingestion, and memory retention."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.orm import Incident, Runbook, PostMortem, Feedback
from app.models.schemas import IncidentResolve, FeedbackCreate, PostMortemCreate

logger = logging.getLogger("incident_agent.services.learning")


def utc_now():
    return datetime.now(timezone.utc)


class LearningLoopService:
    """Manages effectiveness memory updates, feedback loops, and knowledge retention."""

    def __init__(self, memory_store, llm_provider):
        self.memory = memory_store
        self.llm = llm_provider

    async def record_feedback(
        self,
        incident_id: str,
        feedback_in: FeedbackCreate,
        db: Session,
    ) -> Feedback:
        """Process thumbs up/down feedback, adjust runbook weights, and retain outcome."""
        feedback = Feedback(
            incident_id=incident_id,
            runbook_id=feedback_in.runbook_id,
            helpful=feedback_in.helpful,
            notes=feedback_in.notes or "",
        )
        db.add(feedback)

        # Update runbook effectiveness statistics
        if feedback_in.runbook_id:
            runbook = db.query(Runbook).filter(Runbook.id == feedback_in.runbook_id).first()
            if runbook:
                runbook.times_suggested += 1
                if feedback_in.helpful:
                    runbook.times_worked += 1
                # Recalculate success rate
                runbook.success_rate = round(
                    runbook.times_worked / max(1, runbook.times_suggested), 3
                )
                logger.info(
                    "Updated runbook %s stats: suggested=%d, worked=%d, rate=%.2f",
                    runbook.id,
                    runbook.times_suggested,
                    runbook.times_worked,
                    runbook.success_rate,
                )

        db.commit()
        db.refresh(feedback)

        # Retain feedback into memory backend
        feedback_content = (
            f"Operator Feedback on Incident {incident_id}: "
            f"Runbook {feedback_in.runbook_id or 'General'} was marked "
            f"{'SUCCESSFUL/HELPFUL (Thumbs Up)' if feedback_in.helpful else 'UNHELPFUL/INEFFECTIVE (Thumbs Down)'}. "
            f"Notes: {feedback_in.notes or 'None'}"
        )
        try:
            await self.memory.retain(
                item_id=f"FEEDBACK-{feedback.id}",
                content=feedback_content,
                memory_type="feedback",
                metadata={
                    "incident_id": incident_id,
                    "runbook_id": feedback_in.runbook_id or "",
                    "helpful": feedback_in.helpful,
                },
            )
        except Exception as e:
            logger.warning("Failed to retain feedback in memory: %s", str(e))

        return feedback

    async def resolve_incident(
        self,
        incident_id: str,
        resolve_in: IncidentResolve,
        db: Session,
    ) -> Optional[Incident]:
        """Resolve incident, compute MTTR, update runbook metrics, and retain episodic memory."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None

        now = utc_now()
        incident.status = "RESOLVED"
        incident.resolved_at = now

        # Calculate or set MTTR
        if resolve_in.time_to_resolve_min is not None:
            incident.time_to_resolve_min = resolve_in.time_to_resolve_min
        elif incident.created_at:
            created = incident.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            delta = now - created
            incident.time_to_resolve_min = max(5, int(delta.total_seconds() / 60))
        else:
            incident.time_to_resolve_min = 25

        if resolve_in.root_cause:
            incident.root_cause = resolve_in.root_cause
        if resolve_in.runbook_id:
            incident.runbook_id = resolve_in.runbook_id
        if resolve_in.outcome:
            incident.outcome = resolve_in.outcome
        if resolve_in.resolution_steps:
            incident.resolution_steps = json.dumps(resolve_in.resolution_steps)

        # Update runbook MTTR tracking
        if incident.runbook_id:
            runbook = db.query(Runbook).filter(Runbook.id == incident.runbook_id).first()
            if runbook and incident.time_to_resolve_min:
                # Weighted running average
                runbook.avg_mttr_min = round(
                    (runbook.avg_mttr_min * 0.7) + (incident.time_to_resolve_min * 0.3), 1
                )

        db.commit()
        db.refresh(incident)

        # Retain resolved incident into Episodic Memory
        episodic_content = (
            f"Resolved Incident: {incident.title}\n"
            f"Service: {incident.service} | Severity: {incident.severity}\n"
            f"Symptoms: {incident.symptoms}\n"
            f"Root Cause: {incident.root_cause or 'Underlying hardware/software fault'}\n"
            f"Runbook Used: {incident.runbook_id or 'None'}\n"
            f"Resolution Steps: {incident.resolution_steps or 'Standard triage'}\n"
            f"Time To Resolve: {incident.time_to_resolve_min} minutes\n"
            f"Outcome: {incident.outcome or 'SUCCESS'}"
        )

        try:
            await self.memory.retain(
                item_id=incident.id,
                content=episodic_content,
                memory_type="incident",
                metadata={
                    "service": incident.service,
                    "severity": incident.severity,
                    "runbook_id": incident.runbook_id or "",
                    "root_cause": incident.root_cause or "",
                    "status": "RESOLVED",
                },
            )
            logger.info("Successfully retained resolved incident %s into memory", incident.id)
        except Exception as e:
            logger.error("Error retaining resolved incident %s in memory: %s", incident.id, str(e))

        return incident

    async def ingest_postmortem(
        self,
        pm_in: PostMortemCreate,
        db: Session,
    ) -> PostMortem:
        """Parse raw post-mortem markdown/text into structured lessons and retain into semantic memory."""
        summary = pm_in.summary
        root_cause = pm_in.root_cause
        lessons = pm_in.lessons_learned
        action_items = pm_in.action_items

        # If raw text was provided, parse through LLM
        if pm_in.content and (not summary or not root_cause or not lessons):
            extracted = await self.llm.extract_postmortem_lessons(
                content=pm_in.content,
                service=pm_in.service,
            )
            summary = summary or extracted.get("summary", "Post-mortem investigation completed.")
            root_cause = root_cause or extracted.get("root_cause", "Root cause identified.")
            lessons = lessons or extracted.get("lessons_learned", [])
            action_items = action_items or extracted.get("action_items", [])

        summary = summary or f"Post-mortem for {pm_in.service}"
        root_cause = root_cause or "Investigated service anomaly"
        lessons = lessons or ["Maintain proactive health monitors", "Keep runbooks updated"]
        action_items = action_items or ["Review monitoring thresholds"]

        # Generate unique ID
        count = db.query(PostMortem).count()
        pm_id = f"PM-{count + 1:03d}"

        pm = PostMortem(
            id=pm_id,
            title=pm_in.title,
            incident_id=pm_in.incident_id,
            service=pm_in.service,
            summary=summary,
            root_cause=root_cause,
            lessons_learned=json.dumps(lessons),
            action_items=json.dumps(action_items),
        )
        db.add(pm)
        db.commit()
        db.refresh(pm)

        # Retain into Semantic Memory
        semantic_content = (
            f"Post-Mortem: {pm.title} (ID: {pm.id})\n"
            f"Service: {pm.service}\n"
            f"Summary: {summary}\n"
            f"Root Cause: {root_cause}\n"
            f"Lessons Learned:\n" + "\n".join(f"- {item}" for item in lessons) + "\n"
            f"Action Items:\n" + "\n".join(f"- {item}" for item in action_items)
        )

        try:
            await self.memory.retain(
                item_id=pm.id,
                content=semantic_content,
                memory_type="postmortem",
                metadata={"service": pm.service, "title": pm.title},
            )
            logger.info("Retained post-mortem %s into semantic memory", pm.id)
        except Exception as e:
            logger.error("Error retaining post-mortem %s: %s", pm.id, str(e))

        return pm
