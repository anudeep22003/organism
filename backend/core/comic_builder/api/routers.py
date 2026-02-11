from fastapi import APIRouter

from .phases import router as phases_router
from .projects import router as projects_router
from .v2.router import router as v2_router

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])

router.include_router(projects_router)
router.include_router(phases_router)
router.include_router(v2_router)
