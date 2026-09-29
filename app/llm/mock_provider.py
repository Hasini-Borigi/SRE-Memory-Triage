"""Deterministic and realistic Mock LLM Provider for offline resilience and tests."""

import logging
from typing import Dict, Any, List
from app.llm.base import BaseLLMProvider

logger = logging.getLogger("incident_agent.llm.mock")


class MockLLMProvider(BaseLLMProvider):
    """Fallback LLM provider with high-fidelity deterministic incident reasoning."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "deterministic-mock-v1"

    async def ping(self) -> bool:
        return True

    async def analyze_incident(
        self,
        incident: Dict[str, Any],
        recalled_incidents: List[Dict[str, Any]],
        available_runbooks: List[Dict[str, Any]],
        recalled_lessons: List[str],
    ) -> Dict[str, Any]:
        """Perform deterministic analysis based on recalled memory."""
        symptoms = incident.get("symptoms", "").lower()
        title = incident.get("title", "").lower()
        service = incident.get("service", "")

        # Check if we have strong historical matches
        if recalled_incidents and len(recalled_incidents) > 0:
            top_match = recalled_incidents[0]
            top_id = top_match.get("incident_id") or top_match.get("id", "INC-PREV")
            top_cause = top_match.get("root_cause") or "Historical failure pattern"
            runbook_id = top_match.get("runbook_id")

            # Find matching runbook steps if available
            steps = []
            if runbook_id:
                for rb in available_runbooks:
                    if rb.get("id") == runbook_id:
                        steps = rb.get("steps", [])
                        break

            if not steps:
                steps = [
                    "Inspect service logs and connection metrics",
                    "Verify replica status and network latency",
                    "Apply emergency rollback or restart saturated worker instances",
                    "Monitor error rate stabilization over 10-minute window",
                ]

            return {
                "probable_root_cause": f"Probable root cause matching historical pattern: {top_cause}",
                "confidence": round(min(0.96, max(0.72, top_match.get("score", 0.85))), 2),
                "why_explanation": (
                    f"Recalled past incident {top_id} on service '{service}' with similar symptoms. "
                    f"Prior root cause was verified as '{top_cause}'. "
                    f"Applying historical mitigation protocol which successfully resolved {top_id}."
                ),
                "cited_incident_ids": [top_id],
                "recommended_runbook_id": runbook_id,
                "ranked_resolution_steps": steps,
                "is_novel_incident": False,
            }

        # Novel incident protocol
        return {
            "probable_root_cause": "Novel incident detected: Anomaly in service metrics without prior direct match.",
            "confidence": 0.45,
            "why_explanation": (
                "No similar historical incidents exist in persistent memory bank. "
                "Initiating standard first-principles troubleshooting protocol for "
                f"service '{service}'."
            ),
            "cited_incident_ids": [],
            "recommended_runbook_id": None,
            "ranked_resolution_steps": [
                f"Triage {service} health endpoints and inspect error distribution",
                "Verify recent deployment changes, image tags, and environment variables",
                "Check upstream dependencies, network connectivity, and resource saturation",
                "Engage service on-call engineer and prepare diagnostic heap dump or connection trace",
            ],
            "is_novel_incident": True,
        }

    async def extract_postmortem_lessons(
        self,
        content: str,
        service: str,
    ) -> Dict[str, Any]:
        """Extract structured lessons from postmortem text."""
        return {
            "summary": f"Post-mortem analysis for {service} incident: Service degradation mitigated.",
            "root_cause": "Resource starvation triggered by unindexed queries and connection pool leaks.",
            "lessons_learned": [
                "Always enforce strict connection pool checkout timeouts",
                "Deploy proactive alerting on connection pool saturation >= 80%",
                "Implement circuit breaker failover for cascading database dependencies",
            ],
            "action_items": [
                "Audit connection pool configurations across all microservices",
                "Add automated pgbouncer pool utilization dashboard to Datadog",
                "Conduct quarterly failover game day for primary database failover",
            ],
        }
