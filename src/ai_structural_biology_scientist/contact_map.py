"""Residue contact-map heuristic module (DES-ASTRUCT-050 / REQ-ASTRUCT-050)."""

from __future__ import annotations

import math
from numbers import Integral

from ai_structural_biology_scientist.validation import (
    fail,
    is_finite_real,
    register_validator,
    validate_coordinate,
)

_MODULE_NAME = "residue-contact-map"
_COORDINATE_CONSTRAINT = "must be a finite numeric 3-element sequence"


def _contact_map_validator(params: dict) -> dict:
    """DES-ASTRUCT-002 registered atomic validator for this module."""
    if "coordinates" not in params:
        return fail("coordinates", "is required")

    coordinates = params["coordinates"]
    if not isinstance(coordinates, list):
        return fail("coordinates", "must be a list")
    if len(coordinates) < 2:
        return fail("coordinates", "must contain at least 2 coordinates")
    for index, coordinate in enumerate(coordinates):
        coordinate_validation = validate_coordinate(
            coordinate,
            parameter=f"coordinates[{index}]",
            constraint=_COORDINATE_CONSTRAINT,
        )
        if not coordinate_validation["ok"]:
            return coordinate_validation

    distance_threshold_a = params.get("distance_threshold_A", 8.0)
    if not is_finite_real(distance_threshold_a) or distance_threshold_a <= 0:
        return fail("distance_threshold_A", "must be > 0")

    min_sequence_separation = params.get("min_sequence_separation", 3)
    if (
        not isinstance(min_sequence_separation, Integral)
        or isinstance(min_sequence_separation, bool)
        or min_sequence_separation < 1
    ):
        return fail("min_sequence_separation", "must be an integer >= 1")

    return {"ok": True}


register_validator(_MODULE_NAME, _contact_map_validator)


# @id CODE-ASTRUCT-050
# @implements REQ-ASTRUCT-050
# @design DES-ASTRUCT-050
def run_contact_map(
    coordinates: list,
    distance_threshold_A: float = 8.0,
    min_sequence_separation: int = 3,
) -> dict:
    """Compute the C-alpha contact-map heuristic."""
    validation = _contact_map_validator(
        {
            "coordinates": coordinates,
            "distance_threshold_A": distance_threshold_A,
            "min_sequence_separation": min_sequence_separation,
        }
    )
    if not validation["ok"]:
        raise ValueError("parameters must already be validated by the handler wrapper")

    contact_matrix = [[False for _ in coordinates] for _ in coordinates]
    total_contacts = 0
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            if abs(i - j) < min_sequence_separation:
                continue
            distance = math.dist(coordinates[i], coordinates[j])
            if distance <= distance_threshold_A:
                contact_matrix[i][j] = True
                contact_matrix[j][i] = True
                total_contacts += 1

    return {"contact_matrix": contact_matrix, "total_contacts": total_contacts}
