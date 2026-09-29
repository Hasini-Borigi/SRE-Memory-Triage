"""ChromaDB Memory Store: Local embedding-based episodic and semantic memory."""

import os
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.memory.base import MemoryStore

logger = logging.getLogger("incident_agent.memory.chroma")


class ChromaMemoryStore(MemoryStore):
    """Local ChromaDB persistent memory backend with cosine similarity."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = None
        self._collection = None
        self._init_client()

    @property
    def name(self) -> str:
        return "chroma"

    def _init_client(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Default HNSW collection with cosine space
            self._collection = self._client.get_or_create_collection(
                name="incident_memory_store",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialized successfully at %s", self.persist_dir)
        except Exception as e:
            logger.warning("ChromaDB client initialization deferred or failed: %s", str(e))
            self._client = None
            self._collection = None

    async def ping(self) -> bool:
        """Verify ChromaDB collection availability."""
        try:
            if self._collection is None:
                self._init_client()
            if self._collection is not None:
                self._collection.count()
                return True
        except Exception as e:
            logger.warning("ChromaDB ping failed: %s", str(e))
        return False

    async def retain(
        self,
        item_id: str,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store an incident, runbook, or post-mortem in ChromaDB."""
        try:
            if self._collection is None:
                self._init_client()
            if self._collection is None:
                logger.error("ChromaDB collection unavailable for retain")
                return False

            meta = {
                "memory_type": memory_type,
                **(metadata or {}),
            }
            # Flatten any nested lists or dicts for chromadb metadata compatibility
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)

            self._collection.upsert(
                ids=[item_id],
                documents=[content],
                metadatas=[clean_meta],
            )
            logger.info("Retained item %s (type=%s) in ChromaDB", item_id, memory_type)
            return True
        except Exception as e:
            logger.error("Failed to retain item %s in ChromaDB: %s", item_id, str(e))
            return False

    async def recall(
        self,
        query: str,
        limit: int = 5,
        filter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall top-K most similar memories using cosine similarity."""
        try:
            if self._collection is None:
                self._init_client()
            if self._collection is None:
                logger.error("ChromaDB collection unavailable for recall")
                return []

            where_clause = {"memory_type": filter_type} if filter_type else None
            count = self._collection.count()
            if count == 0:
                logger.info("ChromaDB collection is empty, returning empty recall")
                return []

            actual_limit = min(limit, count)
            results = self._collection.query(
                query_texts=[query],
                n_results=actual_limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            recalled = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                docs = results["documents"][0] if results.get("documents") else []
                metas = results["metadatas"][0] if results.get("metadatas") else []
                distances = results["distances"][0] if results.get("distances") else []

                for i, item_id in enumerate(ids):
                    dist = distances[i] if i < len(distances) else 1.0
                    # Cosine distance to similarity: similarity = max(0.0, 1.0 - (dist / 2.0))
                    similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                    recalled.append({
                        "id": item_id,
                        "content": docs[i] if i < len(docs) else "",
                        "metadata": metas[i] if i < len(metas) else {},
                        "similarity": round(float(similarity), 4),
                        "source": "chroma",
                    })

            return recalled
        except Exception as e:
            logger.error("Error recalling from ChromaDB: %s", str(e))
            return []
