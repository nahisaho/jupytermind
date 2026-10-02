"""Research workspace resolution for ai_scientist."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_data_scientist.project_manager import (
    InvalidProjectNameError,
    ProjectHandle,
    resolve_project,
)

PHASE_DIRECTORIES = {
    "planning": "planning",
    "literature": "literature",
    "design": "design",
    "manuscript": "manuscript",
    "review": "review",
    "reproducibility": "reproducibility",
    "presentation": "presentation",
}


@dataclass(frozen=True)
class ResearchProjectHandle:
    """Stable ai_scientist project paths derived from ai-data-scientist."""

    name: str
    root: Path
    notebook_path: Path
    planning_dir: Path
    literature_dir: Path
    design_dir: Path
    manuscript_dir: Path
    review_dir: Path
    reproducibility_dir: Path
    presentation_dir: Path


def _ensure_phase_dirs(handle: ProjectHandle) -> ResearchProjectHandle:
    phase_paths = {name: handle.root / directory for name, directory in PHASE_DIRECTORIES.items()}
    for path in phase_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return ResearchProjectHandle(
        name=handle.name,
        root=handle.root,
        notebook_path=handle.notebook_path,
        planning_dir=phase_paths["planning"],
        literature_dir=phase_paths["literature"],
        design_dir=phase_paths["design"],
        manuscript_dir=phase_paths["manuscript"],
        review_dir=phase_paths["review"],
        reproducibility_dir=phase_paths["reproducibility"],
        presentation_dir=phase_paths["presentation"],
    )


# @id CODE-AISCI-002
# @implements REQ-AISCI-002
# @design DES-AISCI-002
# @id CODE-AISCI-003
# @implements REQ-AISCI-003
# @design DES-AISCI-002
def resolve_research_project(
    name: str,
    projects_root: Path | str | None = None,
) -> ResearchProjectHandle:
    """Resolve the shared stable project handle and create ai_scientist dirs."""
    if not isinstance(name, str):
        raise InvalidProjectNameError(
            f"Project name must be a string, got {type(name).__name__} ({name!r})."
        )
    return _ensure_phase_dirs(resolve_project(name, projects_root=projects_root))
