"""Method manifest & request dispatcher (DES-ASTRUCT-001 / REQ-ASTRUCT-001/002)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import ai_structural_biology_scientist.contact_map as _contact_map  # noqa: F401
import ai_structural_biology_scientist.hydrophobicity as _hydrophobicity  # noqa: F401
import ai_structural_biology_scientist.protein_docking_score as _protein_docking_score  # noqa: F401
import ai_structural_biology_scientist.secondary_structure as _secondary_structure  # noqa: F401
import ai_structural_biology_scientist.structural_similarity as _structural_similarity  # noqa: F401
from ai_data_scientist.language_router import detect_language as _detect_language
from ai_structural_biology_scientist.evidence import record_run
from ai_structural_biology_scientist.validation import validate_parameters

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = (
    REPO_ROOT / ".github" / "skills" / "ai-structural-biology-scientist" / "manifest.json"
)

_LIMITATION_LABEL_MODULES = frozenset(
    {"secondary-structure-heuristic", "protein-protein-docking-score"}
)
_RUN_MODULE_PATHS = {
    "secondary-structure-heuristic": "ai_structural_biology_scientist.secondary_structure",
    "hydrophobicity-burial-heuristic": "ai_structural_biology_scientist.hydrophobicity",
    "protein-protein-docking-score": "ai_structural_biology_scientist.protein_docking_score",
    "structural-similarity-rmsd": "ai_structural_biology_scientist.structural_similarity",
    "residue-contact-map": "ai_structural_biology_scientist.contact_map",
}
_RUN_FUNCTION_NAMES = {
    "secondary-structure-heuristic": "run_secondary_structure",
    "hydrophobicity-burial-heuristic": "run_hydrophobicity",
    "protein-protein-docking-score": "run_protein_docking_score",
    "structural-similarity-rmsd": "run_structural_similarity",
    "residue-contact-map": "run_contact_map",
}
_SUPPORTED_LANGUAGES = ("en", "ja")


def _require_manifest_string(entry: dict[str, Any], method: str, field_name: str) -> None:
    value = entry.get(field_name)
    if not isinstance(value, str) or value == "":
        raise ValueError(  # noqa: TRY004
            f"manifest entry '{method}' must define a string '{field_name}'"
        )


def _validate_manifest(manifest: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")  # noqa: TRY004

    for method, entry in manifest.items():
        if not isinstance(entry, dict):
            raise ValueError(f"manifest entry '{method}' must be a JSON object")  # noqa: TRY004
        _require_manifest_string(entry, method, "modulePath")
        _require_manifest_string(entry, method, "functionName")
        names = entry.get("names")
        if not isinstance(names, dict):
            raise ValueError(f"manifest entry '{method}' must define an object 'names'")  # noqa: TRY004
        for language in _SUPPORTED_LANGUAGES:
            candidates = names.get(language)
            if not isinstance(candidates, list) or any(
                not isinstance(candidate, str) or candidate == "" for candidate in candidates
            ):
                raise ValueError(  # noqa: TRY004
                    f"manifest entry '{method}' must define a list of non-empty strings at "
                    f"'names.{language}'"
                )
    return manifest


def load_manifest(manifest_path: Path | None = None) -> dict:
    """Load the static method-name-to-module manifest."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    return _validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def _matched_methods(request_text: str, manifest: dict) -> list[str]:
    lowered = " ".join(request_text.lower().split())
    matched = []
    for method, entry in manifest.items():
        names = entry.get("names", {})
        candidates = list(names.get("en", [])) + list(names.get("ja", []))
        if any(
            (candidate.lower() in lowered) if candidate.isascii() else (candidate in request_text)
            for candidate in candidates
        ):
            matched.append(method)
    return matched


# @id CODE-ASTRUCT-901
# @implements REQ-ASTRUCT-002
# @design DES-ASTRUCT-001
def extract_params(request_text: Any) -> dict[str, Any] | None:
    """Extract structured params or a single embedded JSON object from input."""
    if isinstance(request_text, dict):
        return dict(request_text)
    if not isinstance(request_text, str):
        return None
    start = request_text.find("{")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(request_text)):
        char = request_text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = request_text[start : index + 1]
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None


def _resolve_run_function(method: str):
    module = importlib.import_module(_RUN_MODULE_PATHS[method])
    return getattr(module, _RUN_FUNCTION_NAMES[method])


def _localize_limitation_label(method: str, result: dict, language: str) -> dict:
    if method not in _LIMITATION_LABEL_MODULES:
        return result
    module = importlib.import_module(_RUN_MODULE_PATHS[method])
    text = module.LIMITATION_LABEL_TEXT[language]
    localized = dict(result)
    del localized["limitation_label_key"]
    localized["limitation_label"] = text
    return localized


def _no_params_outcome(language: str) -> dict:
    return {
        "ok": False,
        "parameter": "params",
        "constraint": "must be extractable as a JSON object embedded in request_text",
        "language": language,
    }


def _handle_module(method: str, request_text: str, language: str) -> dict:
    params = extract_params(request_text)
    if params is None:
        return _no_params_outcome(language)

    validation = validate_parameters(method, params)
    if not validation["ok"]:
        return {
            "ok": False,
            "parameter": validation["parameter"],
            "constraint": validation["constraint"],
            "language": language,
        }

    result = _resolve_run_function(method)(**params)
    result = _localize_limitation_label(method, result, language)
    run_record = record_run(
        module_name=method,
        params=params,
        result=result,
        numpy_version=np.__version__,
    )
    return {"ok": True, "run_record": run_record}


# @id CODE-ASTRUCT-011
# @implements REQ-ASTRUCT-002 REQ-ASTRUCT-003
# @design DES-ASTRUCT-001
def handle_secondary_structure(request_text: str, language: str) -> dict:
    """Handler wrapper for the secondary-structure module."""
    return _handle_module("secondary-structure-heuristic", request_text, language)


# @id CODE-ASTRUCT-021
# @implements REQ-ASTRUCT-002 REQ-ASTRUCT-003
# @design DES-ASTRUCT-001
def handle_hydrophobicity(request_text: str, language: str) -> dict:
    """Handler wrapper for the hydrophobicity module."""
    return _handle_module("hydrophobicity-burial-heuristic", request_text, language)


# @id CODE-ASTRUCT-031
# @implements REQ-ASTRUCT-002 REQ-ASTRUCT-003
# @design DES-ASTRUCT-001
def handle_protein_docking_score(request_text: str, language: str) -> dict:
    """Handler wrapper for the protein-docking module."""
    return _handle_module("protein-protein-docking-score", request_text, language)


# @id CODE-ASTRUCT-041
# @implements REQ-ASTRUCT-002 REQ-ASTRUCT-003
# @design DES-ASTRUCT-001
def handle_structural_similarity(request_text: str, language: str) -> dict:
    """Handler wrapper for the structural-similarity module."""
    return _handle_module("structural-similarity-rmsd", request_text, language)


# @id CODE-ASTRUCT-051
# @implements REQ-ASTRUCT-002 REQ-ASTRUCT-003
# @design DES-ASTRUCT-001
def handle_contact_map(request_text: str, language: str) -> dict:
    """Handler wrapper for the contact-map module."""
    return _handle_module("residue-contact-map", request_text, language)


def _render_clarification(candidates: list[str], language: str) -> str:
    names = "、".join(candidates) if language == "ja" else ", ".join(candidates)
    if language == "ja":
        return f"{names} のどちらを意図していますか。明確にしてください。"
    return f"Did you mean {names}? Please clarify which method you want."


def _render_rejection(language: str) -> str:
    if language == "ja":
        return "対応する手法が要求から認識されませんでした。"
    return "No supported method was recognized in your request."


# @id CODE-ASTRUCT-001
# @implements REQ-ASTRUCT-001 REQ-ASTRUCT-002
# @design DES-ASTRUCT-001
def dispatch(
    request_text: str,
    language: str | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Classify ``request_text`` and dispatch to exactly one matched module."""
    if not isinstance(request_text, str):
        raise ValueError("request_text: must be a str")  # noqa: TRY004
    if language is not None and language not in ("en", "ja"):
        raise ValueError("language: must be 'en' or 'ja' when explicitly supplied")

    detected_language = language or _detect_language(request_text)
    manifest = load_manifest(manifest_path)
    matched = _matched_methods(request_text, manifest)

    if len(matched) == 1:
        method = matched[0]
        entry = manifest[method]
        handler = getattr(importlib.import_module(entry["modulePath"]), entry["functionName"])
        return {
            "outcome": "dispatch",
            "module": method,
            "language": detected_language,
            "handler_result": handler(request_text, detected_language),
        }
    if len(matched) > 1:
        return {
            "outcome": "clarification",
            "candidates": matched,
            "language": detected_language,
            "clarification_question": _render_clarification(matched, detected_language),
        }
    return {
        "outcome": "rejected",
        "language": detected_language,
        "rejected_method": _render_rejection(detected_language),
    }
