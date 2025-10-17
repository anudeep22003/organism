"""Centralized prompt loading utility."""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger

logger = logger.bind(name=__name__)

_PROMPT_CACHE: dict[str, dict[str, Any]] = {}

def load_yaml(file_name: str) -> dict[str, Any]:
    path = Path("core/prompts") / file_name
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_prompt(file_name: str, key: str) -> str:
    """Load a prompt from a YAML file with caching.

    Args:
        file_name: Name of the YAML file (e.g., 'prompt_repo.yaml')
        key: Key in the YAML file (e.g., 'story_writing_prompt')

    Returns:
        The prompt string
    """
    return load_yaml(file_name)[key]

def load_prompt_list(file_name: str, key: str) -> list[str]:
    return load_yaml(file_name)[key]

if __name__ == "__main__":
    print(load_prompt("manager.yaml", "task_list"))