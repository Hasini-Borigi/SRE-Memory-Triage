"""Vectorize Hindsight Memory Store integration using native async SDK methods."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.config import settings, mask_secret
from app.memory.base import MemoryStore

logger = logging.getLogger("incident_agent.memory.hindsight")


class HindsightMemoryStore(MemoryStore):
    """Hindsight memory integration for temporal, semantic, and graph agent memory."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        bank_id: Optional[str] = None,
    ):
        self.api_key = api_key or settings.HINDSIGHT_API_KEY
        self.base_url = base_url or settings.HINDSIGHT_BASE_URL
        self.bank_id = bank_id or settings.HINDSIGHT_BANK_ID
        self._client = None
        self._bank_ensured = False
        self._init_client()

    @property
    def name(self) -> str:
        return "hindsight"

    def _init_client(self):
        try:
            logger.info(
                "Initializing Hindsight client (base_url=%s, key=%s, bank_id=%s)",
                self.base_url,
                mask_secret(self.api_key),
                self.bank_id,
            )
            from hindsight_client import Hindsight

            self._client = Hindsight(
                base_url=self.base_url,
                api_key=self.api_key if self.api_key else None,
            )
        except Exception as e:
            logger.warning("Could not initialize Hindsight client: %s", str(e))
            self._client = None

    async def _ensure_bank(self):
        """Asynchronously ensure memory bank exists."""
        if not self._client or self._bank_ensured:
            return
        try:
            await self._client.acreate_bank(
                bank_id=self.bank_id,
                name="Incident Response Bank",
            )
            self._bank_ensured = True
            logger.info("Ensured Hindsight bank '%s' exists", self.bank_id)
        except Exception as e:
            # Bank already exists or managed
            self._bank_ensured = True
            logger.debug("Hindsight bank notice: %s", str(e))

    async def ping(self) -> bool:
        """Check if Hindsight service is reachable and responsive."""
        if not self._client or not self.api_key:
            return False
        try:
            await self._ensure_bank()
            res = await asyncio.wait_for(
                self._client.arecall(
                    bank_id=self.bank_id,
                    query="ping health check",
                ),
                timeout=settings.HINDSIGHT_TIMEOUT_SECONDS,
            )
            return res is not None
        except Exception as e:
            logger.warning("Hindsight ping check failed: %s", str(e))
            return False

    async def retain(
        self,
        item_id: str,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Retain incident facts and context into Hindsight memory bank."""
        if not self._client:
            return False

        await self._ensure_bank()
        meta_context = f"item_id:{item_id} | type:{memory_type}"
        clean_metadata = {"memory_type": memory_type, "item_id": item_id}
        if metadata:
            meta_context += " | " + " | ".join(f"{k}:{v}" for k, v in metadata.items() if v)
            for k, v in metadata.items():
                if v is not None:
                    clean_metadata[str(k)] = str(v)

        full_content = f"[{memory_type.upper()}: {item_id}]\n{content}\nContext: {meta_context}"

        for attempt in range(settings.HINDSIGHT_MAX_RETRIES + 1):
            try:
                await asyncio.wait_for(
                    self._client.aretain(
                        bank_id=self.bank_id,
                        content=full_content,
                        document_id=item_id,
                        metadata=clean_metadata,
                    ),
                    timeout=settings.HINDSIGHT_TIMEOUT_SECONDS,
                )
                logger.info("Successfully retained %s into Hindsight bank %s", item_id, self.bank_id)
                return True
            except Exception as e:
                logger.warning(
                    "Hindsight retain attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    settings.HINDSIGHT_MAX_RETRIES + 1,
                    item_id,
                    str(e),
                )
                if attempt < settings.HINDSIGHT_MAX_RETRIES:
                    await asyncio.sleep(0.5 * (attempt + 1))
        return False

    async def recall(
        self,
        query: str,
        limit: int = 5,
        filter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall relevant memories from Hindsight bank with similarity scores."""
        if not self._client:
            return []

        search_query = query
        if filter_type:
            search_query = f"[{filter_type.upper()}] {query}"

        for attempt in range(settings.HINDSIGHT_MAX_RETRIES + 1):
            try:
                raw_response = await asyncio.wait_for(
                    self._client.arecall(
                        bank_id=self.bank_id,
                        query=search_query,
                    ),
                    timeout=settings.HINDSIGHT_TIMEOUT_SECONDS,
                )

                parsed_results = []
                results_list = []
                if hasattr(raw_response, "results") and raw_response.results:
                    results_list = raw_response.results
                elif isinstance(raw_response, list):
                    results_list = raw_response

                for item in results_list:
                    text = getattr(item, "text", "") or getattr(item, "content", "") or str(item)
                    item_id = getattr(item, "id", f"hs-{len(parsed_results)+1}")
                    doc_id = getattr(item, "document_id", None)
                    meta = getattr(item, "metadata", {}) or {}

                    score = 0.85
                    scores_obj = getattr(item, "scores", None)
                    if scores_obj:
                        if hasattr(scores_obj, "final") and scores_obj.final is not None:
                            score = scores_obj.final
                        elif hasattr(scores_obj, "semantic") and scores_obj.semantic is not None:
                            score = scores_obj.semantic
                        elif hasattr(scores_obj, "hybrid") and scores_obj.hybrid is not None:
                            score = scores_obj.hybrid
                    elif hasattr(item, "score") and item.score is not None:
                        score = item.score

                    effective_id = doc_id or str(item_id)
                    parsed_results.append({
                        "id": effective_id,
                        "content": str(text),
                        "metadata": meta if isinstance(meta, dict) else {},
                        "similarity": round(float(score), 4),
                        "source": "hindsight",
                    })

                return parsed_results[:limit]
            except Exception as e:
                logger.warning(
                    "Hindsight recall attempt %d/%d failed: %s",
                    attempt + 1,
                    settings.HINDSIGHT_MAX_RETRIES + 1,
                    str(e),
                )
                if attempt < settings.HINDSIGHT_MAX_RETRIES:
                    await asyncio.sleep(0.5 * (attempt + 1))

        return []
