"""Project-scoped configuration for ai_scientist."""

from __future__ import annotations

import json
from pathlib import Path

from ai_scientist.project_handle import ResearchProjectHandle

DEFAULT_CONFIG_PATH = ".ai_scientist_project.json"


def _config_path(handle: ResearchProjectHandle) -> Path:
    return handle.root / DEFAULT_CONFIG_PATH


def load_project_config(handle: ResearchProjectHandle) -> dict:
    """Load project configuration, defaulting to an empty mapping."""
    path = _config_path(handle)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_project_config(handle: ResearchProjectHandle, config: dict) -> Path:
    """Persist project configuration atomically."""
    path = _config_path(handle)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)
    return path
