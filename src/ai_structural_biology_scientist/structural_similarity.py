"""Structural similarity module (DES-ASTRUCT-040 / REQ-ASTRUCT-040)."""

from __future__ import annotations

import numpy as np

from ai_structural_biology_scientist.validation import fail, register_validator, validate_coordinate

_MODULE_NAME = "structural-similarity-rmsd"


def _structural_similarity_validator(params: dict) -> dict:
    """DES-ASTRUCT-002 registered atomic validator for this module."""
    for name in ("structure_a", "structure_b"):
        if name not in params:
            return fail(name, "is required")

    structure_a = params["structure_a"]
    structure_b = params["structure_b"]
    if not isinstance(structure_a, (list, tuple)):
        return fail("structure_a", "must be a list/tuple of coordinates")
    if not isinstance(structure_b, (list, tuple)):
        return fail("structure_b", "must be a list/tuple of coordinates")
    if len(structure_a) != len(structure_b):
        return fail("structure_b", "must have the same length as structure_a")
    if len(structure_a) < 3:
        return fail("structure_a", "must contain at least 3 coordinates")

    for name, structure in (("structure_a", structure_a), ("structure_b", structure_b)):
        for index, coordinate in enumerate(structure):
            coordinate_validation = validate_coordinate(coordinate, parameter=f"{name}[{index}]")
            if not coordinate_validation["ok"]:
                return coordinate_validation

    return {"ok": True}


register_validator(_MODULE_NAME, _structural_similarity_validator)


# @id CODE-ASTRUCT-040
# @implements REQ-ASTRUCT-040
# @design DES-ASTRUCT-040
def run_structural_similarity(structure_a: list, structure_b: list) -> dict:
    """Compute Kabsch RMSD after optimal rigid-body superposition."""
    validation = _structural_similarity_validator(
        {"structure_a": structure_a, "structure_b": structure_b}
    )
    if not validation["ok"]:
        raise ValueError("parameters must already be validated by the handler wrapper")

    a = np.asarray(structure_a, dtype=float)
    b = np.asarray(structure_b, dtype=float)
    centroid_a = a.mean(axis=0)
    centroid_b = b.mean(axis=0)
    centered_a = a - centroid_a
    centered_b = b - centroid_b

    cross_covariance = centered_a.T @ centered_b
    u, _, vt = np.linalg.svd(cross_covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T

    translation = centroid_b - rotation @ centroid_a
    aligned_a = (rotation @ a.T).T + translation
    rmsd = np.sqrt(np.mean(np.sum((aligned_a - b) ** 2, axis=1)))

    return {
        "rmsd": float(rmsd),
        "rotation_matrix": rotation.tolist(),
        "translation": translation.tolist(),
    }
