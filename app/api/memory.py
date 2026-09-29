"""Memory search API router for semantic memory inspection."""

from typing import List, Optional
from fastapi import APIRouter, Query
from app.models.schemas import MemorySearchResult
from app.memory.factory import get_memory_store

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/search", response_model=List[MemorySearchResult])
async def search_memory(
    q: str = Query(..., description="Query string for semantic/episodic memory search"),
    limit: int = Query(8, ge=1, le=25),
    filter_type: Optional[str] = Query(None, description="Filter by type (incident, runbook, postmortem)"),
):
    """Search the active memory bank (Hindsight or ChromaDB) directly."""
    memory = get_memory_store()
    results = await memory.recall(
        query=q,
        limit=limit,
        filter_type=filter_type,
    )

    out = []
    for r in results:
        meta = r.get("metadata", {})
        m_type = meta.get("memory_type", "incident")
        title = meta.get("title") or r.get("id")
        out.append(
            MemorySearchResult(
                id=str(r.get("id")),
                type=m_type,
                title=title,
                content=r.get("content", ""),
                score=r.get("similarity", 0.85),
                metadata=meta,
            )
        )
    return out
