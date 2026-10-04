"""Shared parameter validator (DES-ASTRUCT-002 / REQ-ASTRUCT-003)."""

from __future__ import annotations

import importlib
import math
from collections.abc import Callable, Mapping, Sequence
from numbers import Real
from typing import Any

ValidationResult = dict[str, Any]
ValidatorFn = Callable[[dict[str, Any]], ValidationResult]

_REGISTRY: dict[str, ValidatorFn] = {}
_VALIDATOR_MODULES = {
    "secondary-structure-heuristic": "ai_structural_biology_scientist.secondary_structure",
    "hydrophobicity-burial-heuristic": "ai_structural_biology_scientist.hydrophobicity",
    "protein-protein-docking-score": "ai_structural_biology_scientist.protein_docking_score",
    "structural-similarity-rmsd": "ai_structural_biology_scientist.structural_similarity",
    "residue-contact-map": "ai_structural_biology_scientist.contact_map",
}
_SEQUENCE_ALPHABET = "ACDEFGHIKLMNPQRSTVWY"
_COORDINATE_CONSTRAINT = "must be a list/tuple of exactly 3 finite real numbers"


def ok() -> ValidationResult:
    return {"ok": True}


def fail(parameter: str, constraint: str) -> ValidationResult:
    return {"ok": False, "parameter": parameter, "constraint": constraint}


def is_finite_real(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def validate_uppercase_sequence(
    params: dict[str, Any], parameter: str = "sequence"
) -> ValidationResult:
    sequence = params.get(parameter)
    if not isinstance(sequence, str) or sequence == "":
        return fail(parameter, f"must be a non-empty uppercase sequence over {_SEQUENCE_ALPHABET}")
    for index, residue in enumerate(sequence):
        if residue not in _SEQUENCE_ALPHABET:
            return fail(
                parameter,
                (
                    f"must contain only uppercase residues from {_SEQUENCE_ALPHABET}; "
                    f"first invalid character {residue!r} at index {index}"
                ),
            )
    return ok()


def validate_coordinate(
    coordinate: Any,
    *,
    parameter: str,
    constraint: str = _COORDINATE_CONSTRAINT,
) -> ValidationResult:
    if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 3:
        return fail(parameter, constraint)
    if any(not is_finite_real(value) for value in coordinate):
        return fail(parameter, constraint)
    return ok()


def _ensure_validator_registered(module_name: str) -> None:
    if module_name in _REGISTRY:
        return
    module_path = _VALIDATOR_MODULES.get(module_name)
    if module_path is not None:
        importlib.import_module(module_path)


# @id CODE-ASTRUCT-002
# @implements REQ-ASTRUCT-003
# @design DES-ASTRUCT-002
def register_validator(module_name: str, validator: ValidatorFn) -> None:
    """Register ``module_name``'s documented atomic validator."""
    if module_name in _REGISTRY:
        raise ValueError(  # noqa: TRY004
            f"validator already registered for module '{module_name}'"
        )
    _REGISTRY[module_name] = validator


# @id CODE-ASTRUCT-902
# @implements REQ-ASTRUCT-003
# @design DES-ASTRUCT-002
def validate_parameters(module_name: str, params: dict[str, Any]) -> ValidationResult:
    """Dispatch to ``module_name``'s registered atomic validator."""
    _ensure_validator_registered(module_name)
    validator = _REGISTRY.get(module_name)
    if validator is None:
        return fail("module", f"no validator registered for module '{module_name}'")
    if not isinstance(params, Mapping):
        return fail("params", "must be a dict")
    return validator(dict(params))
