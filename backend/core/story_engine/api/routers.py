from fastapi import APIRouter

from .v2.router import router as v2_router

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])

router.include_router(v2_router)
