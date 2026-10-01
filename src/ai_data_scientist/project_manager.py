"""Project resolution and notebook lifecycle management.

Implements DES-AIDS-003: project identifier validation (ADR-0005),
notebook creation/reuse, and a single-writer queue that serializes
concurrent notebook writes (ADR-0004).
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

import nbformat

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Captured once, at import time, before any skill code can os.chdir() into a
# notebook/dataset directory. This anchors resolve_project's default
# projects_root to a stable location (REQ-AIDS-044 / DES-AIDS-032), instead
# of re-resolving "projects" relative to whatever the cwd happens to be at
# call time (which previously created nested
# projects/<slug>/notebooks/projects/<slug> paths when the kernel cwd drifted
# into a project's own notebooks directory).
_IMPORT_TIME_CWD = Path.cwd()

_PROJECTS_ROOT_ENV_VAR = "AI_DATA_SCIENTIST_PROJECTS_ROOT"


def _default_projects_root() -> Path:
    """Resolve the stable default projects root.

    Prefers the ``AI_DATA_SCIENTIST_PROJECTS_ROOT`` environment variable when
    set (for callers that want to pin an explicit workspace root); otherwise
    falls back to ``<import-time cwd>/projects``, which stays constant for
    the lifetime of the process regardless of later ``os.chdir`` calls.
    """
    env_root = os.environ.get(_PROJECTS_ROOT_ENV_VAR)
    if env_root:
        return Path(env_root).resolve()
    return (_IMPORT_TIME_CWD / "projects").resolve()


def next_execution_count(notebook) -> int:
    """Compute the next monotonically increasing execution_count for ``notebook``.

    Shared by any writer that appends an "executed" code cell (mcp_gateway's
    run_and_record, visualization's record_chart) so every such cell carries
    a real, non-null, incrementing execution_count instead of leaving it
    unset (REQ-AIDS-009's evidentiary-cell acceptance criterion).
    """
    existing = [
        cell.get("execution_count") for cell in notebook.cells if cell.get("cell_type") == "code"
    ]
    return max((count for count in existing if isinstance(count, int)), default=0) + 1


class InvalidProjectNameError(ValueError):
    """Raised when a project name does not satisfy the ADR-0005 slug policy."""


@dataclass(frozen=True)
class ProjectHandle:
    """Resolved, validated project identity and its notebook path."""

    name: str
    root: Path
    notebook_path: Path


# A process-wide lock per notebook path, guaranteeing a single writer at a
# time regardless of how many callers invoke enqueue_write concurrently.
_write_locks: dict[Path, threading.Lock] = {}
_write_locks_guard = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    with _write_locks_guard:
        lock = _write_locks.get(path)
        if lock is None:
            lock = threading.Lock()
            _write_locks[path] = lock
        return lock


# @id CODE-AIDS-028
# @implements REQ-AIDS-028
# @design DES-AIDS-003
# @id CODE-AIDS-052
# @implements REQ-AIDS-044
# @design DES-AIDS-032
def resolve_project(name: str, projects_root: Path | str | None = None) -> ProjectHandle:
    """Validate ``name`` and resolve its on-disk project handle.

    Rejects path traversal / non-slug names before any filesystem access,
    per ADR-0005.

    When ``projects_root`` is omitted, the default root is stable across
    process working-directory changes: it honors the
    ``AI_DATA_SCIENTIST_PROJECTS_ROOT`` environment variable when set, and
    otherwise anchors to the directory this module was imported from, not
    the caller's current working directory at call time (REQ-AIDS-044).
    Passing an explicit ``projects_root`` is unchanged from before.
    """
    if not _SLUG_PATTERN.match(name):
        raise InvalidProjectNameError(
            f"'{name}' is not a valid project name. Allowed pattern: "
            f"lowercase ASCII letters, digits and single hyphens, e.g. 'sales-2024' "
            f"(プロジェクト名は小文字英数字とハイフンのみ使用できます: 例 'sales-2024')."
        )
    root = Path(projects_root).resolve() if projects_root is not None else _default_projects_root()
    project_dir = (root / name).resolve()
    if project_dir.parent != root:
        # Defense in depth: even a slug-valid name must stay inside projects_root.
        raise InvalidProjectNameError(f"'{name}' resolves outside the projects directory.")
    notebook_path = project_dir / "notebooks" / f"{name}.ipynb"
    return ProjectHandle(name=name, root=project_dir, notebook_path=notebook_path)


# @id CODE-AIDS-002
# @implements REQ-AIDS-002
# @design DES-AIDS-003
def ensure_notebook(handle: ProjectHandle) -> Path:
    """Create the project notebook if missing; otherwise reuse it."""
    handle.notebook_path.parent.mkdir(parents=True, exist_ok=True)
    if not handle.notebook_path.exists():
        notebook = nbformat.v4.new_notebook()
        with handle.notebook_path.open("w", encoding="utf-8") as fh:
            nbformat.write(notebook, fh)
    return handle.notebook_path


# @id CODE-AIDS-011
# @implements REQ-AIDS-011
# @design DES-AIDS-003
# @id CODE-AIDS-029
# @implements REQ-AIDS-029
# @design DES-AIDS-003
def enqueue_write(handle: ProjectHandle, cell_mutation) -> Path:
    """Serialize a notebook mutation through a per-notebook single-writer lock.

    ``cell_mutation`` is a callable receiving the loaded ``NotebookNode`` and
    mutating it in place (e.g. appending a cell). The notebook is re-read and
    re-written under the lock so every writer observes the latest on-disk
    state, guaranteeing no cell from a concurrent writer is lost, and the
    result always round-trips through ``nbformat.validate``.
    """
    lock = _lock_for(handle.notebook_path)
    with lock:
        notebook = nbformat.read(handle.notebook_path, as_version=4)
        cell_mutation(notebook)
        nbformat.validate(notebook)
        with handle.notebook_path.open("w", encoding="utf-8") as fh:
            nbformat.write(notebook, fh)
    return handle.notebook_path
