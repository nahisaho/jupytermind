"""Tests for ai_structural_biology_scientist.hydrophobicity."""

from __future__ import annotations

import numpy as np
import pytest

import ai_structural_biology_scientist.hydrophobicity  # noqa: F401


# @id TEST-ASTRUCT-020
# @verifies REQ-ASTRUCT-020
def test_TEST_ASTRUCT_020_computes_reference_kd_window_averages_and_burial_labels():
    from ai_structural_biology_scientist.hydrophobicity import run_hydrophobicity

    result = run_hydrophobicity("LLLKKKLLL", window_size=3, burial_threshold=1.5)

    assert result["residues"] == [
        {"position": 0, "residue": "L", "kd_value": 3.8, "window_average": 3.8, "label": "buried"},
        {
            "position": 1,
            "residue": "L",
            "kd_value": 3.8,
            "window_average": pytest.approx(3.7999999999999994, abs=1e-9),
            "label": "buried",
        },
        {
            "position": 2,
            "residue": "L",
            "kd_value": 3.8,
            "window_average": pytest.approx(1.2333333333333332, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 3,
            "residue": "K",
            "kd_value": -3.9,
            "window_average": pytest.approx(-1.3333333333333333, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 4,
            "residue": "K",
            "kd_value": -3.9,
            "window_average": -3.9,
            "label": "exposed",
        },
        {
            "position": 5,
            "residue": "K",
            "kd_value": -3.9,
            "window_average": pytest.approx(-1.3333333333333333, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 6,
            "residue": "L",
            "kd_value": 3.8,
            "window_average": pytest.approx(1.2333333333333332, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 7,
            "residue": "L",
            "kd_value": 3.8,
            "window_average": pytest.approx(3.8, abs=1e-9),
            "label": "buried",
        },
        {"position": 8, "residue": "L", "kd_value": 3.8, "window_average": 3.8, "label": "buried"},
    ]


# @id TEST-ASTRUCT-071
# @verifies REQ-ASTRUCT-020
def test_TEST_ASTRUCT_071_accepts_numpy_integer_window_sizes_as_positive_odd_integers():
    from ai_structural_biology_scientist.hydrophobicity import run_hydrophobicity

    result = run_hydrophobicity("LLL", window_size=np.int64(3), burial_threshold=3.8)

    assert result["residues"] == [
        {"position": 0, "residue": "L", "kd_value": 3.8, "window_average": 3.8, "label": "exposed"},
        {
            "position": 1,
            "residue": "L",
            "kd_value": 3.8,
            "window_average": pytest.approx(3.7999999999999994, abs=1e-9),
            "label": "exposed",
        },
        {"position": 2, "residue": "L", "kd_value": 3.8, "window_average": 3.8, "label": "exposed"},
    ]


# @id TEST-ASTRUCT-083
# @verifies REQ-ASTRUCT-020
def test_TEST_ASTRUCT_083_uses_only_in_bounds_residues_when_window_exceeds_sequence_length():
    from ai_structural_biology_scientist.hydrophobicity import run_hydrophobicity

    result = run_hydrophobicity("AKV", window_size=9, burial_threshold=10.0)

    assert result["residues"] == [
        {
            "position": 0,
            "residue": "A",
            "kd_value": 1.8,
            "window_average": pytest.approx(0.7000000000000002, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 1,
            "residue": "K",
            "kd_value": -3.9,
            "window_average": pytest.approx(0.7000000000000002, abs=1e-9),
            "label": "exposed",
        },
        {
            "position": 2,
            "residue": "V",
            "kd_value": 4.2,
            "window_average": pytest.approx(0.7000000000000002, abs=1e-9),
            "label": "exposed",
        },
    ]
