"""Method manifest & request dispatcher (DES-ACHEM-001 / REQ-ACHEM-001/002)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import rdkit

# Imported eagerly (not lazily inside `_resolve_run_function`) so each
# module's `register_validator`/`register_batch_item_validator` call runs
# before any `validate_parameters` lookup below.
import ai_chemistry_scientist.admet_prediction as _admet_prediction  # noqa: F401
import ai_chemistry_scientist.bioactivity_classification as _bioactivity_classification  # noqa: F401
import ai_chemistry_scientist.docking_score as _docking_score  # noqa: F401
import ai_chemistry_scientist.dose_response as _dose_response  # noqa: F401
import ai_chemistry_scientist.drug_likeness_rules as _drug_likeness_rules  # noqa: F401
import ai_chemistry_scientist.enzyme_kinetics as _enzyme_kinetics  # noqa: F401
import ai_chemistry_scientist.molecular_descriptors as _molecular_descriptors  # noqa: F401
import ai_chemistry_scientist.molecular_formula_mass as _molecular_formula_mass  # noqa: F401
import ai_chemistry_scientist.molecular_similarity as _molecular_similarity  # noqa: F401
import ai_chemistry_scientist.pharmacokinetics as _pharmacokinetics  # noqa: F401
import ai_chemistry_scientist.qsar_modeling as _qsar_modeling  # noqa: F401
import ai_chemistry_scientist.salt_standardization as _salt_standardization  # noqa: F401
import ai_chemistry_scientist.structural_alerts as _structural_alerts  # noqa: F401
import ai_chemistry_scientist.structure_format_conversion as _structure_format_conversion  # noqa: F401
from ai_chemistry_scientist.evidence import record_run
from ai_chemistry_scientist.validation import validate_parameters
from ai_data_scientist.language_router import detect_language as _detect_language

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = (
    REPO_ROOT / ".github" / "skills" / "ai-chemistry-scientist" / "manifest.json"
)

#: The one module whose handler wrapper skips the separate upfront
#: `validate_parameters` call, because its own `run_*` function interleaves
#: per-item validation with per-item computation (ADR-0026, DES-ACHEM-001).
_PER_ITEM_VALIDATED_MODULES = frozenset({"molecular-descriptors"})

#: the 3 curve-fitting modules whose `run_*` function raises `ValueError`
#: on a post-fit convergence/physicality failure (ADR-0117/ADR-0118),
#: distinct from the pre-fit `validate_parameters` dict-shape rejection.
_POST_FIT_VALUEERROR_MODULES = frozenset(
    {"dose-response-fitting", "pharmacokinetic-analysis", "enzyme-kinetics"}
)

#: modules whose raw result's `limitation_label_key` is substituted with the
#: matching `language`-specific text before `record_run` (DES-ACHEM-001).
_LIMITATION_LABEL_MODULES = frozenset(
    {
        "admet-prediction",
        "docking-score",
        "structural-alerts",
        "bioactivity-classification",
        "salt-removal",
    }
)

_RUN_MODULE_PATHS = {
    "molecular-descriptors": "ai_chemistry_scientist.molecular_descriptors",
    "admet-prediction": "ai_chemistry_scientist.admet_prediction",
    "qsar-modeling": "ai_chemistry_scientist.qsar_modeling",
    "molecular-similarity": "ai_chemistry_scientist.molecular_similarity",
    "docking-score": "ai_chemistry_scientist.docking_score",
    "drug-likeness-rules": "ai_chemistry_scientist.drug_likeness_rules",
    "structural-alerts": "ai_chemistry_scientist.structural_alerts",
    "molecular-formula-mass": "ai_chemistry_scientist.molecular_formula_mass",
    "bioactivity-classification": "ai_chemistry_scientist.bioactivity_classification",
    "salt-removal": "ai_chemistry_scientist.salt_standardization",
    "structure-format-conversion": "ai_chemistry_scientist.structure_format_conversion",
    "dose-response-fitting": "ai_chemistry_scientist.dose_response",
    "pharmacokinetic-analysis": "ai_chemistry_scientist.pharmacokinetics",
    "enzyme-kinetics": "ai_chemistry_scientist.enzyme_kinetics",
}
_RUN_FUNCTION_NAMES = {
    "molecular-descriptors": "run_molecular_descriptors",
    "admet-prediction": "run_admet_prediction",
    "qsar-modeling": "run_qsar_modeling",
    "molecular-similarity": "run_molecular_similarity",
    "docking-score": "run_docking_score",
    "drug-likeness-rules": "run_drug_likeness_rules",
    "structural-alerts": "run_structural_alerts",
    "molecular-formula-mass": "run_molecular_formula_mass",
    "bioactivity-classification": "run_bioactivity_classification",
    "salt-removal": "run_salt_removal",
    "structure-format-conversion": "run_structure_conversion",
    "dose-response-fitting": "run_dose_response_fit",
    "pharmacokinetic-analysis": "run_pharmacokinetics",
    "enzyme-kinetics": "run_enzyme_kinetics",
}


def load_manifest(manifest_path: Path | None = None) -> dict:
    """Load the static method-name-to-module manifest (DES-ACHEM-001)."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _matched_methods(request_text: str, manifest: dict) -> list[str]:
    # Collapse runs of whitespace so extra spacing between words in a
    # request (e.g. multi-space or tab-separated phrasing) still matches an
    # English candidate phrase (REQ-ACHEM-002); Japanese candidates have no
    # internal whitespace, so matching against the raw text is unaffected.
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


# @id CODE-ACHEM-916
# @implements REQ-ACHEM-002
# @design DES-ACHEM-001
def extract_params(request_text: str) -> dict | None:
    """Extract a module's structured ``params`` embedded in ``request_text``.

    Each handler wrapper's own documented extraction responsibility
    (DES-ACHEM-001): a calling context supplies structured parameters by
    embedding exactly one JSON object literal anywhere in ``request_text``
    (e.g. a natural-language instruction followed by
    ``{"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}``). Returns ``None`` when no
    balanced top-level JSON object is present or it fails to parse.
    """
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
    """Resolve each module's raw ``run_*`` compute function by method name."""
    module = importlib.import_module(_RUN_MODULE_PATHS[method])
    return getattr(module, _RUN_FUNCTION_NAMES[method])


def _localize_limitation_label(method: str, result: dict, language: str) -> dict:
    """Substitute `limitation_label_key` with its `language` text (DES-ACHEM-001)."""
    if method not in _LIMITATION_LABEL_MODULES:
        return result
    module_path = {
        "admet-prediction": "ai_chemistry_scientist.admet_prediction",
        "docking-score": "ai_chemistry_scientist.docking_score",
        "structural-alerts": "ai_chemistry_scientist.structural_alerts",
        "bioactivity-classification": "ai_chemistry_scientist.bioactivity_classification",
        "salt-removal": "ai_chemistry_scientist.salt_standardization",
    }[method]
    module = importlib.import_module(module_path)
    key = result["limitation_label_key"]
    assert key == module.LIMITATION_LABEL_KEY
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


def _handle_module(
    method: str, request_text: str, language: str, params: dict | None = None
) -> dict:
    """Shared handler-wrapper body for ``method`` (DES-ACHEM-001's `handle_<method>`).

    Extracts params from ``request_text``, validates (except for the
    per-item-validated module), computes via the raw `run_*` function,
    localizes limitation labels, and wraps the result into a RunRecord
    (DES-ACHEM-003) — a `ModuleOutcome`.
    """
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

    run_function = _resolve_run_function(method)
    if method in _POST_FIT_VALUEERROR_MODULES:
        try:
            result = run_function(**resolved_params)
        except ValueError as exc:
            parameter, _, constraint = str(exc).partition(": ")
            return {
                "ok": False,
                "parameter": parameter,
                "constraint": constraint,
                "language": language,
            }
    else:
        result = run_function(**resolved_params)
    result = _localize_limitation_label(method, result, language)

    extra_kwargs = {}
    if method == "qsar-modeling":
        import sklearn

        extra_kwargs["scikit_learn_version"] = sklearn.__version__

    run_record = record_run(
        module_name=method,
        params=resolved_params,
        result=result,
        rdkit_version=rdkit.__version__,
        **extra_kwargs,
    )
    return {"ok": True, "run_record": run_record}


# @id CODE-ACHEM-011
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_molecular_descriptors(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the molecular-descriptors module (DES-ACHEM-010)."""
    return _handle_module("molecular-descriptors", request_text, language, params or None)


# @id CODE-ACHEM-021
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_admet_prediction(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the admet-prediction module (DES-ACHEM-020)."""
    return _handle_module("admet-prediction", request_text, language, params or None)


# @id CODE-ACHEM-031
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_qsar_modeling(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the qsar-modeling module (DES-ACHEM-030)."""
    return _handle_module("qsar-modeling", request_text, language, params or None)


# @id CODE-ACHEM-041
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_molecular_similarity(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the molecular-similarity module (DES-ACHEM-040)."""
    return _handle_module("molecular-similarity", request_text, language, params or None)


# @id CODE-ACHEM-051
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_docking_score(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the docking-score module (DES-ACHEM-050)."""
    return _handle_module("docking-score", request_text, language, params or None)


# @id CODE-ACHEM-061
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_drug_likeness_rules(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the drug-likeness-rules module (DES-ACHEM-060)."""
    return _handle_module("drug-likeness-rules", request_text, language, params or None)


# @id CODE-ACHEM-071
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_structural_alerts(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the structural-alerts module (DES-ACHEM-070)."""
    return _handle_module("structural-alerts", request_text, language, params or None)


# @id CODE-ACHEM-081
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_molecular_formula_mass(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the molecular-formula-mass module (DES-ACHEM-080)."""
    return _handle_module("molecular-formula-mass", request_text, language, params or None)


# @id CODE-ACHEM-091
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_bioactivity_classification(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the bioactivity-classification module (DES-ACHEM-090)."""
    return _handle_module("bioactivity-classification", request_text, language, params or None)


# @id CODE-ACHEM-101
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_salt_removal(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the salt-removal module (DES-ACHEM-100)."""
    return _handle_module("salt-removal", request_text, language, params or None)


# @id CODE-ACHEM-111
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_structure_format_conversion(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the structure-format-conversion module (DES-ACHEM-110)."""
    return _handle_module("structure-format-conversion", request_text, language, params or None)


# @id CODE-ACHEM-121
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_dose_response_fitting(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the dose-response-fitting module (DES-ACHEM-120)."""
    return _handle_module("dose-response-fitting", request_text, language, params or None)


# @id CODE-ACHEM-131
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_pharmacokinetic_analysis(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the pharmacokinetic-analysis module (DES-ACHEM-130)."""
    return _handle_module("pharmacokinetic-analysis", request_text, language, params or None)


# @id CODE-ACHEM-141
# @implements REQ-ACHEM-002 REQ-ACHEM-003
# @design DES-ACHEM-001
def handle_enzyme_kinetics(request_text: str, language: str, **params) -> dict:
    """Handler wrapper for the enzyme-kinetics module (DES-ACHEM-140)."""
    return _handle_module("enzyme-kinetics", request_text, language, params or None)


# @id CODE-ACHEM-001
# @implements REQ-ACHEM-001 REQ-ACHEM-002
# @design DES-ACHEM-001
def dispatch(
    request_text: str,
    language: str | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Classify ``request_text`` and dispatch to exactly one matched module.

    ``language`` may be supplied explicitly; otherwise it is detected from
    ``request_text`` (REQ-ACHEM-001) and propagated into the result so every
    downstream (module handler, clarification, rejection) path can render
    its user-facing text in that language.
    """
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
        handler_module = importlib.import_module(entry["modulePath"])
        handler = getattr(handler_module, entry["functionName"])
        handler_result = handler(request_text, detected_language)
        return {
            "outcome": "dispatch",
            "module": method,
            "language": detected_language,
            "handler_result": handler_result,
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


def _render_clarification(candidates: list[str], language: str) -> str:
    """Render a single-sentence clarification question in ``language``.

    Method names (e.g. ``molecular-descriptors``) are the only permitted
    non-``language`` tokens, per REQ-ACHEM-001's acceptance.
    """
    names = "、".join(candidates) if language == "ja" else ", ".join(candidates)
    if language == "ja":
        return f"{names} のどちらを意図していますか。明確にしてください。"
    return f"Did you mean {names}? Please clarify which method you want."


def _render_rejection(language: str) -> str:
    """Render a single-sentence rejection message in ``language``."""
    if language == "ja":
        return "対応する手法が要求から認識されませんでした。"
    return "No supported method was recognized in your request."
