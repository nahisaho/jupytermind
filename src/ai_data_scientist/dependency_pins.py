"""Read declared dependency version specifiers from pyproject.toml.

Implements DES-AIDS-038 (REQ-AIDS-050): a minimal, dependency-free reader of
pyproject.toml's [project].dependencies array, used to assert the
jupyter-mcp-server / mcp version pins stay explicitly bounded on both sides
(no silent drift to an untested release whose negotiated MCP protocol
version is incompatible with the rest of the pinned stack).

Deliberately avoids a TOML-parsing library: stdlib ``tomllib`` only ships
from Python 3.11, and this project still supports 3.10, so the
``dependencies = [...]`` array is scanned as plain text instead.
"""

from __future__ import annotations

import re
from pathlib import Path

_PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"
_DEPENDENCY_LINE_PATTERN = re.compile(r'^\s*"([A-Za-z0-9_.-]+)([^"]*)"\s*,?\s*$')


def _normalize(name: str) -> str:
    """Normalize a package name per PEP 503 (case/separator-insensitive)."""
    return re.sub(r"[-_.]+", "-", name).lower()


# @id CODE-AIDS-059
# @implements REQ-AIDS-050
# @design DES-AIDS-038
def get_dependency_specifier(name: str, pyproject_path: Path = _PYPROJECT_PATH) -> str:
    """Return the raw dependency requirement string declared for ``name``.

    Scans ``pyproject_path``'s ``[project].dependencies`` array for the
    single entry whose package name matches ``name`` (case/separator
    insensitive), returning it verbatim including its version specifier
    (e.g. ``"jupyter-mcp-server>=2.2,<2.3"``).

    Raises ``KeyError`` if no dependency named ``name`` is declared.
    """
    target = _normalize(name)
    in_dependencies = False
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not in_dependencies:
            if stripped.startswith("dependencies"):
                in_dependencies = True
            continue
        if stripped.startswith("]"):
            break
        match = _DEPENDENCY_LINE_PATTERN.match(line)
        if not match:
            continue
        raw_name = match.group(1)
        if _normalize(raw_name) == target:
            return stripped.rstrip(",").strip('"')

    raise KeyError(
        f"No dependency named {name!r} declared in {pyproject_path}'s [project.dependencies]."
    )
