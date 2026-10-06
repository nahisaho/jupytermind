"""Shared parameter & validity validator (DES-AGENOM-002 / REQ-AGENOM-003)."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Any

ValidationResult = dict[str, Any]
ValidatorFn = Callable[[dict[str, Any]], ValidationResult]
BatchItemValidatorFn = Callable[[dict[str, Any]], ValidationResult]

_REGISTRY: dict[str, ValidatorFn] = {}
_BATCH_ITEM_REGISTRY: dict[str, BatchItemValidatorFn] = {}
_VALIDATOR_MODULES = {
    "sequence-features": "ai_genomics_scientist.sequence_features",
    "variant-effect-annotation": "ai_genomics_scientist.variant_effect",
    "splice-site-strength": "ai_genomics_scientist.splice_site_scoring",
    "gene-set-enrichment": "ai_genomics_scientist.gene_set_enrichment",
    "pairwise-sequence-alignment": "ai_genomics_scientist.sequence_alignment",
    "differential-expression": "ai_genomics_scientist.differential_expression",
    "variant-pathogenicity": "ai_genomics_scientist.variant_pathogenicity",
}


def ok() -> ValidationResult:
    return {"ok": True}


def fail(parameter: str, constraint: str) -> ValidationResult:
    return {"ok": False, "parameter": parameter, "constraint": constraint}


def _ensure_validator_registered(module_name: str) -> None:
    if module_name in _REGISTRY and module_name in _BATCH_ITEM_REGISTRY:
        return
    module_path = _VALIDATOR_MODULES.get(module_name)
    if module_path is not None:
        importlib.import_module(module_path)


# @id CODE-AGENOM-002
# @implements REQ-AGENOM-003
# @design DES-AGENOM-002
def register_validator(module_name: str, validator: ValidatorFn) -> None:
    """Register ``module_name``'s atomic validator."""
    _REGISTRY[module_name] = validator


# @id CODE-AGENOM-003
# @implements REQ-AGENOM-003
# @design DES-AGENOM-002
def validate_parameters(module_name: str, params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered atomic validator."""
    _ensure_validator_registered(module_name)
    validator = _REGISTRY.get(module_name)
    if validator is None:
        return fail("module", f"no validator registered for module '{module_name}'")
    if not isinstance(params, Mapping):
        return fail("params", "must be a dict")
    return validator(dict(params))


# @id CODE-AGENOM-004
# @implements REQ-AGENOM-003
# @design DES-AGENOM-002
def register_batch_item_validator(module_name: str, validator: BatchItemValidatorFn) -> None:
    """Register ``module_name``'s per-item validator."""
    _BATCH_ITEM_REGISTRY[module_name] = validator


# @id CODE-AGENOM-005
# @implements REQ-AGENOM-003
# @design DES-AGENOM-002
def validate_batch_item(module_name: str, item_params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered per-item validator."""
    _ensure_validator_registered(module_name)
    validator = _BATCH_ITEM_REGISTRY.get(module_name)
    if validator is None:
        return fail("module", f"no batch-item validator registered for module '{module_name}'")
    if not isinstance(item_params, Mapping):
        return fail("params", "must be a dict")
    return validator(dict(item_params))
