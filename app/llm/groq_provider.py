"""Groq LLM Provider with structured JSON output, model negotiation, and resilient fallback."""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from app.config import settings, mask_secret
from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider

logger = logging.getLogger("incident_agent.llm.groq")


class GroqLLMProvider(BaseLLMProvider):
    """Groq Cloud LLM provider featuring fast inference and structured JSON responses."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = settings.GROQ_API_KEY if api_key is None else api_key
        self.model = settings.GROQ_MODEL if model is None else model
        self._active_model = self.model
        self._client = None
        self._fallback = MockLLMProvider()
        self._init_client()

    @property
    def name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._active_model

    def _init_client(self):
        try:
            logger.info(
                "Initializing Groq client with model %s and key %s",
                self.model,
                mask_secret(self.api_key),
            )
            from groq import Groq

            if self.api_key:
                self._client = Groq(api_key=self.api_key)
            else:
                self._client = None
        except Exception as e:
            logger.warning("Could not instantiate Groq client: %s", str(e))
            self._client = None

    def _negotiate_model(self):
        """Find best accessible model if configured model 404s."""
        if not self._client:
            return
        try:
            model_list = self._client.models.list()
            available = [m.id for m in model_list.data]
            logger.info("Groq accessible models: %s", available)

            candidates = [
                self.model,
                "llama-3.3-70b-versatile",
                "openai/gpt-oss-120b",
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-20b",
            ]
            for c in candidates:
                if c in available:
                    self._active_model = c
                    logger.info("Selected Groq active model: %s", self._active_model)
                    return
            if available:
                self._active_model = available[0]
                logger.info("Selected first available Groq model: %s", self._active_model)
        except Exception as e:
            logger.warning("Model negotiation warning: %s", str(e))

    async def ping(self) -> bool:
        """Check if Groq API is responsive."""
        if not self._client or not self.api_key:
            return False
        try:
            self._negotiate_model()

            def _test_call():
                return self._client.chat.completions.create(
                    model=self._active_model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                )

            await asyncio.wait_for(
                asyncio.to_thread(_test_call),
                timeout=settings.GROQ_TIMEOUT_SECONDS,
            )
            return True
        except Exception as e:
            logger.warning("Groq ping failed: %s", str(e))
            return False

    async def analyze_incident(
        self,
        incident: Dict[str, Any],
        recalled_incidents: List[Dict[str, Any]],
        available_runbooks: List[Dict[str, Any]],
        recalled_lessons: List[str],
    ) -> Dict[str, Any]:
        """Use Groq for root cause analysis and resolution reasoning."""
        if not self._client:
            logger.info("Groq client not available, using deterministic fallback")
            return await self._fallback.analyze_incident(
                incident, recalled_incidents, available_runbooks, recalled_lessons
            )

        self._negotiate_model()

        system_prompt = (
            "You are an expert Site Reliability Engineering (SRE) Incident Response Agent with persistent memory.\n"
            "Analyze active production incidents, compare against recalled historical incidents, "
            "identify probable root causes, recommend vetted runbooks, and provide a concrete resolution plan.\n\n"
            "CRITICAL RULES:\n"
            "1. NEVER hallucinate past incidents. Only reference and cite past incident IDs provided in the RECALLED HISTORICAL INCIDENTS section.\n"
            "2. If no similar incidents exist, state so honestly and provide first-principles troubleshooting steps.\n"
            "3. Ground your confidence score (0.0 to 1.0) on the quality of historical memory match and symptoms alignment.\n"
            "4. Return strictly valid JSON conforming to the requested schema."
        )

        user_content = {
            "current_incident": {
                "title": incident.get("title"),
                "service": incident.get("service"),
                "severity": incident.get("severity"),
                "symptoms": incident.get("symptoms"),
                "logs_snippet": incident.get("logs_snippet"),
            },
            "recalled_historical_incidents": [
                {
                    "id": m.get("incident_id") or m.get("id"),
                    "title": m.get("title"),
                    "service": m.get("service"),
                    "root_cause": m.get("root_cause"),
                    "runbook_id": m.get("runbook_id"),
                    "score": m.get("score"),
                }
                for m in recalled_incidents
            ],
            "available_runbooks": [
                {
                    "id": rb.get("id"),
                    "title": rb.get("title"),
                    "service": rb.get("service"),
                    "steps": rb.get("steps"),
                    "success_rate": rb.get("success_rate"),
                }
                for rb in available_runbooks
            ],
            "recalled_lessons": recalled_lessons,
        }

        json_schema_prompt = (
            "Output must be a valid JSON object with the following keys:\n"
            "{\n"
            '  "probable_root_cause": "string explaining the most likely root cause",\n'
            '  "confidence": 0.88,\n'
            '  "why_explanation": "string explaining the rationale, explicitly citing past incident IDs if relevant",\n'
            '  "cited_incident_ids": ["INC-1001"],\n'
            '  "recommended_runbook_id": "RB-001" or null,\n'
            '  "ranked_resolution_steps": ["step 1", "step 2", "step 3"],\n'
            '  "is_novel_incident": false\n'
            "}"
        )

        for attempt in range(settings.GROQ_MAX_RETRIES + 1):
            try:
                def _call_groq():
                    return self._client.chat.completions.create(
                        model=self._active_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": (
                                    f"Analyze this incident:\n\n{json.dumps(user_content, indent=2)}\n\n"
                                    f"{json_schema_prompt}"
                                ),
                            },
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=1500,
                    )

                response = await asyncio.wait_for(
                    asyncio.to_thread(_call_groq),
                    timeout=settings.GROQ_TIMEOUT_SECONDS,
                )

                content = response.choices[0].message.content
                parsed = json.loads(content)
                logger.info("Successfully received analysis from Groq LLM (model=%s)", self._active_model)
                return parsed

            except Exception as e:
                logger.warning(
                    "Groq incident analysis attempt %d/%d failed: %s",
                    attempt + 1,
                    settings.GROQ_MAX_RETRIES + 1,
                    str(e),
                )
                if attempt < settings.GROQ_MAX_RETRIES:
                    await asyncio.sleep(0.5 * (attempt + 1))

        logger.warning("Groq failed after retries, falling back to mock provider")
        return await self._fallback.analyze_incident(
            incident, recalled_incidents, available_runbooks, recalled_lessons
        )

    async def extract_postmortem_lessons(
        self,
        content: str,
        service: str,
    ) -> Dict[str, Any]:
        """Extract structured lessons from postmortem using Groq."""
        if not self._client:
            return await self._fallback.extract_postmortem_lessons(content, service)

        self._negotiate_model()

        system_prompt = (
            "You are an SRE post-mortem analyzer. "
            "Extract a concise summary, root cause, key lessons learned, and action items. "
            "Return JSON with: summary (str), root_cause (str), lessons_learned (list of str), action_items (list of str)."
        )

        for attempt in range(settings.GROQ_MAX_RETRIES + 1):
            try:
                def _call_groq():
                    return self._client.chat.completions.create(
                        model=self._active_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Postmortem for service {service}:\n\n{content}"},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=1000,
                    )

                response = await asyncio.wait_for(
                    asyncio.to_thread(_call_groq),
                    timeout=settings.GROQ_TIMEOUT_SECONDS,
                )
                parsed = json.loads(response.choices[0].message.content)
                return parsed
            except Exception as e:
                logger.warning("Groq postmortem extraction failed: %s", str(e))
                if attempt < settings.GROQ_MAX_RETRIES:
                    await asyncio.sleep(0.5)

        return await self._fallback.extract_postmortem_lessons(content, service)
