"""Packaging helpers for ai-scientist npm bootstrap regressions."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path


# @id CODE-AISCI-027
# @implements REQ-AISCI-025 REQ-AGENOM-080 REQ-AIMS-080 REQ-ASTRUCT-060
# @design DES-AISCI-020 DES-AGENOM-080 DES-AIMS-080 DES-ASTRUCT-060
def load_package_files(package_json_path: str | Path = "package.json") -> list[str]:
    """Return the npm package whitelist entries from package.json."""
    package_json = Path(package_json_path)
    return json.loads(package_json.read_text("utf-8"))["files"]


# @id CODE-AISCI-028
# @implements REQ-AISCI-025 REQ-AGENOM-080 REQ-AIMS-080 REQ-ASTRUCT-060
# @design DES-AISCI-020 DES-AGENOM-080 DES-AIMS-080 DES-ASTRUCT-060
def load_npm_pack_dry_run_paths(project_root: str | Path = ".") -> set[str]:
    """Return packed file paths reported by `npm pack --dry-run --json`."""
    result = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        check=True,
        capture_output=True,
        cwd=Path(project_root),
        text=True,
    )
    payload = json.loads(result.stdout)
    return {entry["path"] for pack in payload for entry in pack["files"]}


# @id CODE-AISCI-029
# @implements REQ-AISCI-025 REQ-AGENOM-080 REQ-AIMS-080 REQ-ASTRUCT-060
# @design DES-AISCI-020 DES-AGENOM-080 DES-AIMS-080 DES-ASTRUCT-060
def iter_skill_python_globs(package_files: Sequence[str]) -> dict[str, str]:
    """Map exact shipped skill entries to expected Python source globs."""
    mappings = {}
    for entry in package_files:
        if not entry.startswith(".github/skills/") or "/" in entry.removeprefix(".github/skills/"):
            continue
        slug = entry.removeprefix(".github/skills/")
        package_dir = Path("src") / slug.replace("-", "_")
        if (package_dir / "__init__.py").exists():
            mappings[entry] = f"{package_dir.as_posix()}/**/*.py"
    return mappings
