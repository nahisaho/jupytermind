"""Skill invocation abstraction for sibling Copilot skills."""

from __future__ import annotations

from typing import Protocol


class SkillInvoker(Protocol):
    """Minimal sibling-skill invocation contract."""

    def invoke(self, skill_id: str, version: str, mode: str, payload: dict) -> dict: ...


class DefaultSkillInvoker:
    """Placeholder implementation for non-test Python execution contexts."""

    def invoke(self, skill_id: str, version: str, mode: str, payload: dict) -> dict:
        raise NotImplementedError(
            "Sibling skill invocation must be provided by the Copilot agent runtime. "
            "See .github/skills/ai-scientist/SKILL.md for the delegation contract."
        )
