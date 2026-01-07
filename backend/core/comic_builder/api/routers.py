from fastapi import APIRouter

from .projects import router as projects_router
from .streamer import router as streamer_router

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])

router.include_router(projects_router)
router.include_router(streamer_router)
