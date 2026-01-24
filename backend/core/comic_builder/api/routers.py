from fastapi import APIRouter

from .phases import router as phases_router
from .projects import router as projects_router

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])

router.include_router(projects_router)
router.include_router(phases_router)
