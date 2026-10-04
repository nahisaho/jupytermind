"""Hydrophobicity / burial heuristic module (DES-ASTRUCT-020 / REQ-ASTRUCT-020)."""

from __future__ import annotations

from numbers import Integral

from ai_structural_biology_scientist.validation import (
    fail,
    is_finite_real,
    register_validator,
    validate_uppercase_sequence,
)

_MODULE_NAME = "hydrophobicity-burial-heuristic"
_KD_SCALE = {
    "A": 1.8,
    "R": -4.5,
    "N": -3.5,
    "D": -3.5,
    "C": 2.5,
    "Q": -3.5,
    "E": -3.5,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "L": 3.8,
    "K": -3.9,
    "M": 1.9,
    "F": 2.8,
    "P": -1.6,
    "S": -0.8,
    "T": -0.7,
    "W": -0.9,
    "Y": -1.3,
    "V": 4.2,
}


def _hydrophobicity_validator(params: dict) -> dict:
    """DES-ASTRUCT-002 registered atomic validator for this module."""
    if "sequence" not in params:
        return fail("sequence", "is required")
    sequence_validation = validate_uppercase_sequence(params)
    if not sequence_validation["ok"]:
        return sequence_validation

    window_size = params.get("window_size", 9)
    if (
        not isinstance(window_size, Integral)
        or isinstance(window_size, bool)
        or window_size < 1
        or window_size % 2 == 0
    ):
        return fail("window_size", "must be a positive odd integer")

    burial_threshold = params.get("burial_threshold", 1.5)
    if not is_finite_real(burial_threshold):
        return fail("burial_threshold", "must be a finite number")

    return {"ok": True}


register_validator(_MODULE_NAME, _hydrophobicity_validator)


# @id CODE-ASTRUCT-020
# @implements REQ-ASTRUCT-020
# @design DES-ASTRUCT-020
def run_hydrophobicity(
    sequence: str,
    window_size: int = 9,
    burial_threshold: float = 1.5,
) -> dict:
    """Compute the Kyte-Doolittle burial heuristic for ``sequence``."""
    validation = _hydrophobicity_validator(
        {
            "sequence": sequence,
            "window_size": window_size,
            "burial_threshold": burial_threshold,
        }
    )
    if not validation["ok"]:
        raise ValueError("parameters must already be validated by the handler wrapper")

    half_window = window_size // 2
    residues = []
    for position, residue in enumerate(sequence):
        start = max(0, position - half_window)
        stop = min(len(sequence), position + half_window + 1)
        window_values = [_KD_SCALE[window_residue] for window_residue in sequence[start:stop]]
        window_average = sum(window_values) / len(window_values)
        residues.append(
            {
                "position": position,
                "residue": residue,
                "kd_value": _KD_SCALE[residue],
                "window_average": window_average,
                "label": "buried" if window_average > burial_threshold else "exposed",
            }
        )
    return {"residues": residues}
