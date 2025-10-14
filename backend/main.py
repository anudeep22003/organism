import os
from typing import AsyncGenerator

import socketio  # type: ignore[import-untyped]
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# for env variable laoding
from core import config  # noqa: F401
from core.api.routers import router as v1_router
from core.logging import setup_logging
from core.sockets import register_sio_handlers, sio

## SETTINGS
REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "BUCKET_NAME",
    "GITHUB_TOKEN",
]

## OPTIONAL ENV VARS (with defaults)
OPTIONAL_ENV_VARS = {
    "CLAUDE_MODEL": "claude-3-5-sonnet-20241022",
    "TEMP_DIR": None,  # Uses system default
    "OPERATION_TIMEOUT": "3600",  # 1 hour in seconds
}


# ## FUNCTIONS
def check_env_vars() -> bool:
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            return False
    return True


def set_default_env_vars() -> None:
    """Set default values for optional environment variables if not set."""
    for var, default_value in OPTIONAL_ENV_VARS.items():
        if default_value is not None and not os.getenv(var):
            os.environ[var] = default_value


@asynccontextmanager
async def lifecycle_manager(self) -> AsyncGenerator[None, None]:
    # Setup logging first
    setup_logging(level="DEBUG", json_format=True)

    logger.debug("Starting FastAPI app")
    logger.debug("Checking environment variables loaded")

    if not check_env_vars():
        raise ValueError("Missing required environment variables")

    # Set default values for optional environment variables
    set_default_env_vars()
    logger.debug("Environment variables configured")

    # register socketio handlers
    register_sio_handlers()

    yield
    logger.info("Shutting down FastAPI app")


fastapi_app = FastAPI(lifespan=lifecycle_manager)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
