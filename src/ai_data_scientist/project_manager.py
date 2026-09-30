"""Project resolution and notebook lifecycle management.

Implements DES-AIDS-003: project identifier validation (ADR-0005),
notebook creation/reuse, and a single-writer queue that serializes
concurrent notebook writes (ADR-0004).
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path

import nbformat

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


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
def resolve_project(name: str, projects_root: Path | str = "projects") -> ProjectHandle:
    """Validate ``name`` and resolve its on-disk project handle.

    Rejects path traversal / non-slug names before any filesystem access,
    per ADR-0005.
    """
    if not _SLUG_PATTERN.match(name):
        raise InvalidProjectNameError(
            f"'{name}' is not a valid project name. Allowed pattern: "
            f"lowercase ASCII letters, digits and single hyphens, e.g. 'sales-2024' "
            f"(プロジェクト名は小文字英数字とハイフンのみ使用できます: 例 'sales-2024')."
        )
    root = Path(projects_root).resolve()
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
