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
BUCKET_NAME = os.getenv("BUCKET_NAME", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", "100"))

if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY is not set")
    raise ValueError("ANTHROPIC_API_KEY is not set")

if not BUCKET_NAME:
    logger.error("BUCKET_NAME is not set")
    raise ValueError("BUCKET_NAME is not set")

if not GITHUB_TOKEN:
    logger.error("GITHUB_TOKEN is not set")
    raise ValueError("GITHUB_TOKEN is not set")
