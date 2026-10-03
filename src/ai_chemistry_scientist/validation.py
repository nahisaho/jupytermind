"""Shared parameter & chemical-validity validator (DES-ACHEM-002 / REQ-ACHEM-003)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

ValidationResult = dict
ValidatorFn = Callable[[dict[str, Any]], ValidationResult]
BatchItemValidatorFn = Callable[[dict[str, Any]], ValidationResult]

_REGISTRY: dict[str, ValidatorFn] = {}
_BATCH_ITEM_REGISTRY: dict[str, BatchItemValidatorFn] = {}


def ok() -> ValidationResult:
    return {"ok": True}


def fail(parameter: str, constraint: str) -> ValidationResult:
    return {"ok": False, "parameter": parameter, "constraint": constraint}


# @id CODE-ACHEM-002
# @implements REQ-ACHEM-003
# @design DES-ACHEM-002
def register_validator(module_name: str, validator: ValidatorFn) -> None:
    """Register ``module_name``'s own documented atomic-validity validator."""
    _REGISTRY[module_name] = validator


# @id CODE-ACHEM-913
# @implements REQ-ACHEM-003
# @design DES-ACHEM-002
def register_batch_item_validator(module_name: str, validator: BatchItemValidatorFn) -> None:
    """Register ``module_name``'s own documented per-item validator."""
    _BATCH_ITEM_REGISTRY[module_name] = validator


# @id CODE-ACHEM-914
# @implements REQ-ACHEM-003
# @design DES-ACHEM-002
def validate_parameters(module_name: str, params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered atomic validator.

    Must run to completion before any descriptor computation, model fit, or
    similarity/score calculation for the module's whole run (REQ-ACHEM-003).
    """
    validator = _REGISTRY.get(module_name)
    if validator is None:
        return fail("module", f"no validator registered for module '{module_name}'")
    if not isinstance(params, dict):
        return fail("params", "must be a dict")
    return validator(params)


# @id CODE-ACHEM-915
# @implements REQ-ACHEM-003
# @design DES-ACHEM-002
def validate_batch_item(module_name: str, item_params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered per-item validator.

    Invoked once per batch item (REQ-ACHEM-010's per-item granularity); an
    invalid item is rejected without aborting computation of the rest of the
    batch.
    """
    validator = _BATCH_ITEM_REGISTRY.get(module_name)
    if validator is None:
        return fail("module", f"no batch-item validator registered for module '{module_name}'")
    return validator(item_params)
