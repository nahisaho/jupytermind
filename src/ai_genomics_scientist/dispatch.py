"""Method manifest & request dispatcher (DES-AGENOM-001 / REQ-AGENOM-001/002)."""

from __future__ import annotations

import importlib
import json
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy
import scipy

import ai_genomics_scientist.gene_set_enrichment as _gene_set_enrichment  # noqa: F401
import ai_genomics_scientist.sequence_alignment as _sequence_alignment  # noqa: F401
import ai_genomics_scientist.sequence_features as _sequence_features  # noqa: F401
import ai_genomics_scientist.splice_site_scoring as _splice_site_scoring  # noqa: F401
import ai_genomics_scientist.variant_effect as _variant_effect  # noqa: F401
import ai_genomics_scientist.differential_expression as _differential_expression  # noqa: F401
import ai_genomics_scientist.variant_pathogenicity as _variant_pathogenicity  # noqa: F401
import ai_genomics_scientist.acmg_classification as _acmg_classification  # noqa: F401
from ai_data_scientist.language_router import detect_language as _detect_language
from ai_genomics_scientist.evidence import record_run
from ai_genomics_scientist.validation import validate_parameters

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = REPO_ROOT / ".github" / "skills" / "ai-genomics-scientist" / "manifest.json"
_PER_ITEM_VALIDATED_MODULES = frozenset({"sequence-features"})
_PER_ITEM_BATCH_PARAM_NAMES = {"sequence-features": "sequences"}
_RUN_MODULE_PATHS = {
    "sequence-features": "ai_genomics_scientist.sequence_features",
    "variant-effect-annotation": "ai_genomics_scientist.variant_effect",
    "splice-site-strength": "ai_genomics_scientist.splice_site_scoring",
    "gene-set-enrichment": "ai_genomics_scientist.gene_set_enrichment",
    "pairwise-sequence-alignment": "ai_genomics_scientist.sequence_alignment",
    "differential-expression": "ai_genomics_scientist.differential_expression",
    "variant-pathogenicity": "ai_genomics_scientist.variant_pathogenicity",
    "acmg-amp-classification": "ai_genomics_scientist.acmg_classification",
}
_RUN_FUNCTION_NAMES = {
    "sequence-features": "run_sequence_features",
    "variant-effect-annotation": "run_variant_effect",
    "splice-site-strength": "run_splice_site_scoring",
    "gene-set-enrichment": "run_gene_set_enrichment",
    "pairwise-sequence-alignment": "run_sequence_alignment",
    "differential-expression": "run_differential_expression",
    "variant-pathogenicity": "run_variant_pathogenicity",
    "acmg-amp-classification": "run_acmg_classification",
}


def load_manifest(manifest_path: Path | None = None) -> dict:
    """Load the static method-name-to-module manifest."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def _matched_methods(request_text: str, manifest: dict) -> list[str]:
    normalized_request = _normalize_text(request_text)
    matched: list[str] = []
    for method, entry in manifest.items():
        names = entry.get("names", {})
        candidates = list(names.get("en", [])) + list(names.get("ja", []))
        if any(_normalize_text(candidate) in normalized_request for candidate in candidates):
            matched.append(method)
    return matched


def extract_params(request_text: str | Mapping[str, Any]) -> dict | None:
    """Extract exactly one balanced top-level JSON object from ``request_text``."""
    if isinstance(request_text, Mapping):
        return dict(request_text)
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


def _no_params_outcome(language: str) -> dict:
    constraint = (
        "`request_text` に埋め込まれた `JSON` オブジェクトとして抽出可能でなければなりません"
        if language == "ja"
        else "must be extractable as a JSON object embedded in request_text"
    )
    return {
        "ok": False,
        "parameter": "params",
        "constraint": constraint,
        "language": language,
    }


def _handle_module(
    method: str, request_text: str, language: str, params: dict[str, Any] | None = None
) -> dict:
    resolved_params = params if params is not None else extract_params(request_text)
    if resolved_params is None:
        return _no_params_outcome(language)

    if method not in _PER_ITEM_VALIDATED_MODULES:
        validation = validate_parameters(method, resolved_params)
        if not validation["ok"]:
            return {
                "ok": False,
                "parameter": validation["parameter"],
                "constraint": validation["constraint"],
                "language": language,
            }
    else:
        # The per-item-validated module still needs its own batch container
        # (``sequences``) checked for basic shape before iterating it: a
        # missing key or a non-list value (e.g. a bare string, which Python
        # would otherwise iterate character-by-character) must be rejected
        # the same way an atomic module rejects a malformed parameter,
        # rather than crashing or silently producing bogus per-item results.
        batch_param_name = _PER_ITEM_BATCH_PARAM_NAMES[method]
        batch_value = resolved_params.get(batch_param_name)
        if not isinstance(batch_value, list):
            return {
                "ok": False,
                "parameter": batch_param_name,
                "constraint": "must be a list",
                "language": language,
            }

    result = _resolve_run_function(method)(**resolved_params)
    run_record = record_run(
        module_name=method,
        params=resolved_params,
        result=result,
        numpy_version=numpy.__version__,
        scipy_version=scipy.__version__,
    )
    return {"ok": True, "run_record": run_record}


# @id CODE-AGENOM-011
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_sequence_features(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the sequence-features module."""
    return _handle_module("sequence-features", request_text, language, params or None)


# @id CODE-AGENOM-021
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_variant_effect_annotation(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the variant-effect-annotation module."""
    return _handle_module("variant-effect-annotation", request_text, language, params or None)


# @id CODE-AGENOM-031
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_splice_site_strength(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the splice-site-strength module."""
    return _handle_module("splice-site-strength", request_text, language, params or None)


# @id CODE-AGENOM-041
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_gene_set_enrichment(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the gene-set-enrichment module."""
    return _handle_module("gene-set-enrichment", request_text, language, params or None)


# @id CODE-AGENOM-051
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_pairwise_sequence_alignment(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the pairwise-sequence-alignment module."""
    return _handle_module("pairwise-sequence-alignment", request_text, language, params or None)


# @id CODE-AGENOM-061
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_differential_expression(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the differential-expression module."""
    return _handle_module("differential-expression", request_text, language, params or None)


# @id CODE-AGENOM-071
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_variant_pathogenicity(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the variant-pathogenicity module."""
    return _handle_module("variant-pathogenicity", request_text, language, params or None)


# @id CODE-AGENOM-091
# @implements REQ-AGENOM-002 REQ-AGENOM-004
# @design DES-AGENOM-001
def handle_acmg_amp_classification(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the acmg-amp-classification module."""
    return _handle_module("acmg-amp-classification", request_text, language, params or None)


def _render_clarification(candidates: list[str], language: str) -> str:
    names = "、".join(candidates) if language == "ja" else ", ".join(candidates)
    if language == "ja":
        return f"{names} のどちらを意図していますか。明確にしてください。"
    return f"Did you mean {names}? Please clarify which method you want."


def _render_rejection(language: str) -> str:
    if language == "ja":
        return "対応する手法が要求から認識されませんでした。"
    return "No supported method was recognized in your request."


# @id CODE-AGENOM-006
# @implements REQ-AGENOM-001 REQ-AGENOM-002
# @design DES-AGENOM-001
def dispatch(
    request_text: str,
    language: str | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Classify ``request_text`` and dispatch to exactly one matched module."""
    if not isinstance(request_text, str):
        raise ValueError("request_text: must be a str")
    if language is not None and language not in {"en", "ja"}:
        raise ValueError("language: must be 'en' or 'ja' when explicitly supplied")

    detected_language = language or _detect_language(request_text)
    manifest = load_manifest(manifest_path)
    matched = _matched_methods(request_text, manifest)

    if len(matched) == 1:
        method = matched[0]
        entry = manifest[method]
        handler_module = importlib.import_module(entry["modulePath"])
        handler = getattr(handler_module, entry["functionName"])
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
