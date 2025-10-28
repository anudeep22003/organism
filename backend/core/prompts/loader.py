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
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def load_prompt(file_name: str, key: str) -> str:
    """Load a prompt from a YAML file with caching.

    Args:
        file_name: Name of the YAML file (e.g., 'prompt_repo.yaml')
        key: Key in the YAML file (e.g., 'story_writing_prompt')

    Returns:
        The prompt string
    """
    prompt = load_yaml(file_name)[key]
    if isinstance(prompt, str):
        return prompt
    else:
        raise ValueError(f"Prompt {key} is not a string")


def load_prompt_list(file_name: str, key: str) -> list[str]:
    prompt_list = load_yaml(file_name)[key]
    if isinstance(prompt_list, list):
        return prompt_list
    else:
        raise ValueError(f"Prompt list {key} is not a list")


if __name__ == "__main__":
    print(load_prompt("manager.yaml", "task_list"))
