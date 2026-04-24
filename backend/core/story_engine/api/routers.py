from fastapi import APIRouter

from .router import router as v2_router

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])

router.include_router(v2_router)
