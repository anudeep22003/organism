from fastapi import APIRouter

from core.auth import auth_router

#! combine the comic_module_router and comic_router
from core.comic_builder.router import router as comic_builder_module_router

from .comic_builder import router as comic_builder_router
from .transcribe import router as transcribe_router

router = APIRouter(prefix="/api")
router.include_router(transcribe_router)
router.include_router(auth_router)
router.include_router(comic_builder_router)
router.include_router(comic_builder_module_router)
