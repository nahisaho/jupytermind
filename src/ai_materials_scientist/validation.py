"""Shared parameter & stability validator (DES-AIMS-002 / REQ-AIMS-003)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

ValidationResult = dict
ValidatorFn = Callable[[dict[str, Any]], ValidationResult]

_REGISTRY: dict[str, ValidatorFn] = {}


def _ok() -> ValidationResult:
    return {"ok": True}


def _fail(parameter: str, constraint: str) -> ValidationResult:
    return {"ok": False, "parameter": parameter, "constraint": constraint}


# @id CODE-AIMS-002
# @implements REQ-AIMS-003
# @design DES-AIMS-002
def check_finite_array(parameter: str, array: np.ndarray) -> ValidationResult:
    """Reject a numeric array containing any non-finite (NaN/Inf) value."""
    if not np.all(np.isfinite(array)):
        return _fail(parameter, "all elements must be finite (no NaN/Inf)")
    return _ok()


# @id CODE-AIMS-913
# @implements REQ-AIMS-003
# @design DES-AIMS-002
def check_positive_step_count(steps: int) -> ValidationResult:
    """Reject a step count that is not a positive integer."""
    if steps <= 0:
        return _fail("steps", "steps > 0")
    return _ok()


# @id CODE-AIMS-914
# @implements REQ-AIMS-003
# @design DES-AIMS-002
def check_positive_output_interval(output_every: int) -> ValidationResult:
    """Reject an output interval that is not a positive integer."""
    if output_every <= 0:
        return _fail("output_every", "output_every > 0")
    return _ok()


# @id CODE-AIMS-915
# @implements REQ-AIMS-003
# @design DES-AIMS-002
def register_validator(module_name: str, validator: ValidatorFn) -> None:
    """Register ``module_name``'s own documented-domain validator function."""
    _REGISTRY[module_name] = validator


# @id CODE-AIMS-916
# @implements REQ-AIMS-003
# @design DES-AIMS-002
def validate_parameters(module_name: str, params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered validator before any simulation step."""
    validator = _REGISTRY.get(module_name)
    if validator is None:
        return _fail("module", f"no validator registered for module '{module_name}'")
    return validator(params)
