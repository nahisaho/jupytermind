"""Tests for ai_structural_biology_scientist.contact_map."""

from __future__ import annotations

import numpy as np

import ai_structural_biology_scientist.contact_map  # noqa: F401


# @id TEST-ASTRUCT-050
# @verifies REQ-ASTRUCT-050
def test_TEST_ASTRUCT_050_computes_reference_contact_matrix_and_upper_triangle_contact_count():
    from ai_structural_biology_scientist.contact_map import run_contact_map

    result = run_contact_map(
        coordinates=[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 0.0, 7.5],
            [2.0, 0.0, 7.0],
        ],
        distance_threshold_A=8.0,
        min_sequence_separation=3,
    )

    assert result["contact_matrix"] == [
        [False, False, False, True, True],
        [False, False, False, False, True],
        [False, False, False, False, False],
        [True, False, False, False, False],
        [True, True, False, False, False],
    ]
    assert result["total_contacts"] == 3


# @id TEST-ASTRUCT-076
# @verifies REQ-ASTRUCT-050
def test_TEST_ASTRUCT_076_contact_map_accepts_numpy_integer_min_sequence_separation():
    from ai_structural_biology_scientist.contact_map import run_contact_map

    result = run_contact_map(
        coordinates=[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 0.0, 7.5],
            [2.0, 0.0, 7.0],
        ],
        distance_threshold_A=8.0,
        min_sequence_separation=np.int64(3),
    )

    assert result["total_contacts"] == 3
