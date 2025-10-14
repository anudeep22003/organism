"""Centralized prompt loading utility."""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger

logger = logger.bind(name=__name__)

_PROMPT_CACHE: dict[str, dict[str, Any]] = {}


def load_prompt(file_name: str, key: str) -> str:
    """Load a prompt from a YAML file with caching.

    Args:
        file_name: Name of the YAML file (e.g., 'prompt_repo.yaml')
        key: Key in the YAML file (e.g., 'story_writing_prompt')

    Returns:
        The prompt string
    """
    if file_name not in _PROMPT_CACHE:
        path = Path("core/prompts") / file_name
        with open(path, "r") as f:
            _PROMPT_CACHE[file_name] = yaml.safe_load(f)

    return _PROMPT_CACHE[file_name][key]
