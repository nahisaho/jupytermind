"""Tests for ai_structural_biology_scientist.structural_similarity."""

from __future__ import annotations

import numpy as np
import pytest

import ai_structural_biology_scientist.structural_similarity  # noqa: F401


# @id TEST-ASTRUCT-041
# @verifies REQ-ASTRUCT-040
def test_TEST_ASTRUCT_041_computes_reference_kabsch_rotation_translation_and_rmsd():
    from ai_structural_biology_scientist.structural_similarity import run_structural_similarity

    exact_result = run_structural_similarity(
        structure_a=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        structure_b=[[5.0, 5.0, 5.0], [5.0, 6.0, 5.0], [4.0, 5.0, 5.0]],
    )

    assert exact_result["rmsd"] == pytest.approx(0.0, abs=1e-9)
    assert exact_result["translation"] == pytest.approx([5.0, 5.0, 5.0], abs=1e-9)
    assert exact_result["rotation_matrix"][0] == pytest.approx(
        [-2.2536733244499676e-16, -1.0000000000000002, 0.0], abs=1e-9
    )
    assert exact_result["rotation_matrix"][1] == pytest.approx(
        [1.0000000000000002, -1.2116883882008518e-16, 0.0], abs=1e-9
    )
    assert exact_result["rotation_matrix"][2] == pytest.approx([0.0, 0.0, 1.0], abs=1e-9)

    perturbed_result = run_structural_similarity(
        structure_a=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        structure_b=[[5.0, 5.0, 5.0], [5.0, 6.0, 5.0], [4.2, 5.0, 5.0]],
    )

    assert perturbed_result["rmsd"] == pytest.approx(0.08749441193078264, abs=1e-9)


# @id TEST-ASTRUCT-073
# @verifies REQ-ASTRUCT-040
def test_TEST_ASTRUCT_073_accepts_tuple_coordinate_sets_for_the_same_kabsch_superposition():
    from ai_structural_biology_scientist.structural_similarity import run_structural_similarity

    result = run_structural_similarity(
        structure_a=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        structure_b=((5.0, 5.0, 5.0), (5.0, 6.0, 5.0), (4.0, 5.0, 5.0)),
    )

    assert result["rmsd"] == pytest.approx(0.0, abs=1e-9)
    assert result["translation"] == pytest.approx([5.0, 5.0, 5.0], abs=1e-9)
    assert result["rotation_matrix"][0] == pytest.approx(
        [-2.2536733244499676e-16, -1.0000000000000002, 0.0], abs=1e-9
    )


# @id TEST-ASTRUCT-084
# @verifies REQ-ASTRUCT-040
def test_TEST_ASTRUCT_084_enforces_proper_rotation_for_mirrored_tetrahedron_inputs():
    from ai_structural_biology_scientist.structural_similarity import run_structural_similarity

    structure_a = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    structure_b = [
        [0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    result = run_structural_similarity(structure_a=structure_a, structure_b=structure_b)

    rotation = np.asarray(result["rotation_matrix"], dtype=float)
    translation = np.asarray(result["translation"], dtype=float)
    aligned_a = (rotation @ np.asarray(structure_a, dtype=float).T).T + translation
    manual_rmsd = np.sqrt(
        np.mean(np.sum((aligned_a - np.asarray(structure_b, dtype=float)) ** 2, axis=1))
    )

    assert np.linalg.det(rotation) == pytest.approx(1.0, abs=1e-9)
    assert result["rmsd"] == pytest.approx(0.5, abs=1e-9)
    assert result["rmsd"] == pytest.approx(float(manual_rmsd), abs=1e-12)
