import os
from typing import AsyncGenerator

import socketio
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.api.routers import router as v1_router
from core.config import settings
from core.logging import setup_logging
from core.sockets import register_sio_handlers, sio


@asynccontextmanager
async def lifecycle_manager(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(level="DEBUG", json_format=True)
    logger.info(
        "StoryEngine starting",
        project=settings.gcp_project_id,
        region=settings.gcp_region,
    )
    register_sio_handlers()
    yield
    logger.info("StoryEngine shutting down")


fastapi_app = FastAPI(lifespan=lifecycle_manager)

# CORS_ORIGINS is a comma-separated list of allowed origins.
# Defaults to localhost:5173 for local dev — no .env.local change needed.
# In Cloud Run, injected as a plain env var from infra/components/cloudrun.py.
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fastapi_app.include_router(v1_router)


@fastapi_app.get("/")
async def index() -> dict[str, str]:
    return {
        "message": "Hello World",
    }


app = socketio.ASGIApp(sio, fastapi_app)


@fastapi_app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for extension to test server connectivity."""
    return {"status": "ok", "message": "Server is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8085, reload=True)
