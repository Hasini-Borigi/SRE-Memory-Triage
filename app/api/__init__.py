"""API routers package."""

from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.runbooks import router as runbooks_router
from app.api.postmortems import router as postmortems_router
from app.api.memory import router as memory_router
from app.api.analytics import router as analytics_router

__all__ = [
    "health_router",
    "incidents_router",
    "runbooks_router",
    "postmortems_router",
    "memory_router",
    "analytics_router",
]
