from fastapi import APIRouter

from .session import router as session_router
from .transcribe import router as transcribe_router

router = APIRouter(prefix="/api")
router.include_router(session_router)
router.include_router(transcribe_router)
