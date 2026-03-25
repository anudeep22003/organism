import os

from dotenv import load_dotenv
from loguru import logger

logger = logger.bind(name=__name__)


def is_running_in_cloudrun() -> bool:
    return os.getenv("K_SERVICE") is not None


if not is_running_in_cloudrun():
    load_dotenv(override=True, dotenv_path=".env.local")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "DB URL NOT SET")
FAL_API_KEY = os.getenv("FAL_API_KEY", "")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("GCP_REGION", "")
GCP_STORAGE_BUCKET = os.getenv("GCP_STORAGE_BUCKET", "")


if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is not set")
    raise ValueError("OPENAI_API_KEY is not set")

if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY is not set")
    raise ValueError("ANTHROPIC_API_KEY is not set")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set")
    raise ValueError("DATABASE_URL is not set")

if not FAL_API_KEY:
    logger.error("FAL_API_KEY is not set")
    raise ValueError("FAL_API_KEY is not set")

if not GCP_PROJECT_ID:
    logger.error("GCP_PROJECT_ID is not set")
    raise ValueError("GCP_PROJECT_ID is not set")

if not GCP_REGION:
    logger.error("GCP_REGION is not set")
    raise ValueError("GCP_REGION is not set")

if not GCP_STORAGE_BUCKET:
    logger.error("GCP_STORAGE_BUCKET is not set")
    raise ValueError("GCP_STORAGE_BUCKET is not set")
