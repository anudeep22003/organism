from fastapi import APIRouter

from core.auth import auth_router

from .transcribe import router as transcribe_router

router = APIRouter(prefix="/api")
router.include_router(transcribe_router)
router.include_router(auth_router)
