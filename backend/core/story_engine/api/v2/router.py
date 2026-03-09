from fastapi import APIRouter

from .character import router as character_router
from .projects import router as projects_router
from .story import router as story_router

router = APIRouter(prefix="/v2", tags=["comic", "builder", "v2"])

router.include_router(projects_router)
router.include_router(story_router)
router.include_router(character_router)
