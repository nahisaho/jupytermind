"""Project resolution and notebook lifecycle management.

Implements DES-AIDS-003: project identifier validation (ADR-0005),
notebook creation/reuse, and a single-writer queue that serializes
concurrent notebook writes (ADR-0004).

Change: CHANGE-033
"""

from __future__ import annotations

import os
import re
import tempfile
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


# @id CODE-AIDS-152
# @implements REQ-AIDS-093
# @design DES-AIDS-093
def _discover_ancestor_projects_root(start: Path, name: str) -> Path | None:
    """Walk ``start`` and its ancestors for an existing ``name`` project root.

    Returns the nearest ancestor directory (including ``start`` itself) whose
    basename is exactly ``"projects"`` and which already contains a direct
    subdirectory named exactly ``name``, or ``None`` if no such ancestor
    exists. This lets a freshly started process/kernel whose own import-time
    cwd has already drifted inside an existing ``projects/<name>/...`` tree
    (GitHub #72) rediscover that same tree's root instead of recomputing
    ``<drifted cwd>/projects`` and silently recreating a nested
    ``projects/<name>/notebooks/projects/<name>`` path.
    """
    for candidate in (start, *start.parents):
        if candidate.name == "projects" and (candidate / name).is_dir():
            return candidate
    return None


def _default_projects_root(name: str | None = None) -> Path:
    """Resolve the stable default projects root.

    Prefers the ``AI_DATA_SCIENTIST_PROJECTS_ROOT`` environment variable when
    set (for callers that want to pin an explicit workspace root). Otherwise,
    when ``name`` is given, attempts to discover an existing ancestor
    ``projects`` directory that already contains ``name`` (REQ-AIDS-093),
    so a different process/kernel whose cwd has already drifted inside that
    tree resolves the same root. Falls back to ``<import-time cwd>/projects``,
    which stays constant for the lifetime of the process regardless of later
    ``os.chdir`` calls, when neither of the above applies.
    """
    env_root = os.environ.get(_PROJECTS_ROOT_ENV_VAR)
    if env_root:
        return Path(env_root).resolve()
    if name is not None:
        discovered = _discover_ancestor_projects_root(_IMPORT_TIME_CWD, name)
        if discovered is not None:
            return discovered.resolve()
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


class StablePathResolutionError(FileNotFoundError):
    """Raised when a path resolves under neither cwd nor the stable workspace root."""


@dataclass(frozen=True)
class ProjectHandle:
    """Resolved, validated project identity and its notebook path."""

    name: str
    root: Path
    notebook_path: Path
    data_dir: Path


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
    root = (
        Path(projects_root).resolve() if projects_root is not None else _default_projects_root(name)
    )
    project_dir = (root / name).resolve()
    if project_dir.parent != root:
        # Defense in depth: even a slug-valid name must stay inside projects_root.
        raise InvalidProjectNameError(f"'{name}' resolves outside the projects directory.")
    notebook_path = project_dir / "notebooks" / f"{name}.ipynb"
    data_dir = project_dir / "data"
    return ProjectHandle(
        name=name, root=project_dir, notebook_path=notebook_path, data_dir=data_dir
    )


# @id CODE-AIDS-055
# @implements REQ-AIDS-049
# @design DES-AIDS-037
def ensure_data_dir(handle: ProjectHandle) -> Path:
    """Create ``handle.data_dir`` (and any missing parents) if absent; return it."""
    handle.data_dir.mkdir(parents=True, exist_ok=True)
    return handle.data_dir


# @id CODE-AIDS-056
# @implements REQ-AIDS-047
# @design DES-AIDS-035
def resolve_stable_path(path: Path | str) -> Path:
    """Resolve ``path`` against cwd, falling back to the stable workspace root.

    Mirrors ``_default_projects_root``'s stability rule for any caller (such
    as ``notebook_audit.audit_notebook``) that receives a relative path which
    may have been computed against the workspace root but is later evaluated
    from a kernel whose working directory has drifted into a project's own
    notebook directory (REQ-AIDS-047).

    An absolute ``path`` is returned resolved as-is (existence is left to the
    caller, matching prior behavior). A relative ``path`` is first checked
    against the current working directory; if that candidate does not exist,
    it is re-checked against ``_IMPORT_TIME_CWD`` (the same stable base
    ``_default_projects_root`` anchors to). If neither candidate exists,
    ``StablePathResolutionError`` is raised naming both attempted locations.
    """
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.resolve()

    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    stable_candidate = (_IMPORT_TIME_CWD / candidate).resolve()
    if stable_candidate.exists():
        return stable_candidate

    raise StablePathResolutionError(
        f"Could not resolve '{path}' relative to the current working directory "
        f"({cwd_candidate}) or the stable workspace root ({stable_candidate})."
    )


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
# @implements REQ-AIDS-029 REQ-AIDS-059
# @design DES-AIDS-003
def enqueue_write(handle: ProjectHandle, cell_mutation) -> Path:
    """Serialize a notebook mutation through a per-notebook single-writer lock.

    ``cell_mutation`` is a callable receiving the loaded ``NotebookNode`` and
    mutating it in place (e.g. appending a cell). The notebook is re-read and
    re-written under the lock so every writer observes the latest on-disk
    state, guaranteeing no cell from a concurrent writer is lost, and the
    result always round-trips through ``nbformat.validate``.

    The write itself is atomic (GitHub #27): the mutated notebook is
    serialized to a string with ``nbformat.writes`` *before* anything on
    disk is touched, so a mutation that ``nbformat.validate`` accepts but
    that fails at JSON-serialization time (e.g. non-JSON-serializable
    metadata) raises without ever truncating or corrupting the existing
    file. The serialized string is then written to a temporary file in the
    same directory, flushed and fsynced, and atomically swapped into place
    with ``os.replace`` so a crash or error mid-write never leaves a
    partially written notebook on disk.

    **Concurrent-write risk with Jupyter MCP (GitHub #34, REQ-AIDS-059)**:
    this lock only serializes concurrent callers of this function within
    the current process; it does not coordinate with a separate Jupyter
    MCP session that has the same notebook file open in memory. If such an
    MCP session later saves its own in-memory copy, it can silently
    overwrite whatever this function already wrote to disk. Prefer routing
    writes through the active MCP session when one is open against this
    notebook, or pause MCP-side saves while calling this function directly.
    """
    lock = _lock_for(handle.notebook_path)
    with lock:
        notebook = nbformat.read(handle.notebook_path, as_version=4)
        cell_mutation(notebook)
        nbformat.validate(notebook)
        serialized = nbformat.writes(notebook)
        directory = handle.notebook_path.parent
        fd, tmp_name = tempfile.mkstemp(
            dir=directory, prefix=f".{handle.notebook_path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(serialized)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, handle.notebook_path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
    return handle.notebook_path
