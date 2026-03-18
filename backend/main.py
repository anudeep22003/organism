from typing import AsyncGenerator

import socketio
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# for env variable loading (this automatically loads config)
from core import config  # noqa: F401
from core.api.routers import router as v1_router
from core.logging import setup_logging
from core.sockets import register_sio_handlers, sio


@asynccontextmanager
async def lifecycle_manager(app: FastAPI) -> AsyncGenerator[None, None]:
    # Setup logging first
    setup_logging(level="DEBUG", json_format=True)

    logger.debug("Starting FastAPI app")
    logger.debug("Checking environment variables loaded")

    # register socketio handlers
    register_sio_handlers()

    yield
    logger.info("Shutting down FastAPI app")


fastapi_app = FastAPI(lifespan=lifecycle_manager)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
