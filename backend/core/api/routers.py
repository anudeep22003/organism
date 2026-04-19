from fastapi import APIRouter

from core.auth.router import router as auth_router
from core.auth_v2.router import router as google_auth_router
from core.story_engine.api.routers import router as story_engine_router

from .transcribe import router as transcribe_router

router = APIRouter(prefix="/api")
router.include_router(transcribe_router)
router.include_router(auth_router)
router.include_router(google_auth_router)
router.include_router(story_engine_router)
