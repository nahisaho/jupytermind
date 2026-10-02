"""Phase manifest loading and repo-local skill registry verification."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILL_DIR = REPO_ROOT / ".github" / "skills" / "ai-scientist"
DEFAULT_MANIFEST_PATH = DEFAULT_SKILL_DIR / "manifest.json"
VENDORED_PATH = REPO_ROOT / ".github" / "skills" / "VENDORED.md"


class ManifestVerificationError(ValueError):
    """Manifest verification failed."""


def _import_handler(module_path: str, function_name: str) -> None:
    module = importlib.import_module(module_path)
    handler = getattr(module, function_name)
    if not callable(handler):
        raise ManifestVerificationError(f"{module_path}.{function_name} is not callable")


def _validate_skill_dependencies(phase: str, payload):
    if phase == "peer-review":
        if not isinstance(payload, dict) or set(payload) != {"ja", "en"}:
            raise ManifestVerificationError("peer-review skillDependencies must contain ja and en")
        return
    if not isinstance(payload, list):
        raise ManifestVerificationError(f"{phase}: skillDependencies must be a list")


def _load_vendored_versions() -> dict[str, str]:
    text = VENDORED_PATH.read_text(encoding="utf-8")
    versions: dict[str, str] = {}
    for skill_id, version in re.findall(r"\| `([^`]+)` \| [^|]+ \| `([^`]+)` \|", text):
        versions[skill_id] = version.removeprefix("v")
    return versions


def scan_repo_skill_registry() -> dict[str, str | None]:
    """Scan repo-local vendored skills as the verifiable startup registry."""
    versions = _load_vendored_versions()
    registry: dict[str, str | None] = {}
    skills_dir = REPO_ROOT / ".github" / "skills"
    for skill_path in skills_dir.glob("*/SKILL.md"):
        lines = skill_path.read_text(encoding="utf-8").splitlines()
        name_line = next((line for line in lines if line.startswith("name: ")), None)
        if name_line is not None:
            skill_id = name_line.split(":", 1)[1].strip()
            registry[skill_id] = versions.get(skill_id)
    return registry


# @id CODE-AISCI-023
# @implements REQ-AISCI-023
# @design DES-AISCI-015
def load_phase_manifest(path: Path | str = DEFAULT_MANIFEST_PATH) -> dict:
    """Load the machine-readable ai_scientist phase manifest."""
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    for phase, entry in manifest.items():
        module_path = entry.get("modulePath")
        function_name = entry.get("functionName")
        if not module_path or not function_name:
            raise ManifestVerificationError(f"{phase}: missing modulePath or functionName")
        _validate_skill_dependencies(phase, entry.get("skillDependencies", []))
        _import_handler(module_path, function_name)
    return manifest


def verify_manifest_against_registry(manifest: dict, registry: dict[str, str | None]) -> None:
    """Verify every declared dependency exists in the startup registry scan."""
    for phase, entry in manifest.items():
        dependencies = entry.get("skillDependencies", [])
        phase_dependencies = (
            dependencies.values() if isinstance(dependencies, dict) else dependencies
        )
        for dependency in phase_dependencies:
            skill_id = dependency["skillId"]
            version = dependency["version"]
            if registry.get(skill_id) != version:
                raise ManifestVerificationError(
                    f"{phase}: missing registry entry for {skill_id}@{version}"
                )
