"""Tests for ai_structural_biology_scientist.evidence."""

from __future__ import annotations

import json

import numpy as np


# @id TEST-ASTRUCT-004
# @verifies REQ-ASTRUCT-004
def test_TEST_ASTRUCT_004_record_run_has_exactly_three_top_level_keys():
    from ai_structural_biology_scientist.evidence import record_run

    record = record_run(
        module_name="secondary-structure-heuristic",
        params={"sequence": "MKVLAGPIW"},
        result={
            "secondary_structure": "HHEEHCCEE",
            "helix_fraction": 0.3333333333333333,
            "sheet_fraction": 0.4444444444444444,
            "coil_fraction": 0.2222222222222222,
        },
        numpy_version="2.5.3",
    )

    assert set(record.keys()) == {"metadata", "parameters", "result"}
    assert record["metadata"] == {
        "module": "secondary-structure-heuristic",
        "schema_version": 1,
        "numpy_version": "2.5.3",
    }
    assert record["parameters"] == {"sequence": "MKVLAGPIW"}
    assert record["result"] == {
        "secondary_structure": "HHEEHCCEE",
        "helix_fraction": 0.3333333333333333,
        "sheet_fraction": 0.4444444444444444,
        "coil_fraction": 0.2222222222222222,
    }


# @id TEST-ASTRUCT-060
# @verifies REQ-ASTRUCT-004
def test_TEST_ASTRUCT_060_record_run_deep_copies_nested_parameters():
    from ai_structural_biology_scientist.evidence import record_run

    params = {
        "partner_a": {"hydrophobic_count": 6, "charged_count": 2},
        "partner_b": {"hydrophobic_count": 4, "charged_count": 3},
    }

    record = record_run(
        module_name="protein-protein-docking-score",
        params=params,
        result={"score": 0.66875},
        numpy_version="2.5.3",
    )

    params["partner_a"]["hydrophobic_count"] = 999
    params["partner_b"]["charged_count"] = 999

    assert record["parameters"] == {
        "partner_a": {"hydrophobic_count": 6, "charged_count": 2},
        "partner_b": {"hydrophobic_count": 4, "charged_count": 3},
    }


# @id TEST-ASTRUCT-077
# @verifies REQ-ASTRUCT-004
def test_TEST_ASTRUCT_077_record_run_normalizes_numpy_scalars_to_json_safe_values():
    from ai_structural_biology_scientist.evidence import record_run

    record = record_run(
        module_name="protein-protein-docking-score",
        params={
            "partner_a": {"hydrophobic_count": np.int64(6), "charged_count": np.int64(2)},
            "partner_b": {"hydrophobic_count": np.int64(4), "charged_count": np.int64(3)},
        },
        result={"score": np.float64(0.66875)},
        numpy_version="2.5.3",
    )

    assert json.loads(json.dumps(record)) == {
        "metadata": {
            "module": "protein-protein-docking-score",
            "schema_version": 1,
            "numpy_version": "2.5.3",
        },
        "parameters": {
            "partner_a": {"hydrophobic_count": 6, "charged_count": 2},
            "partner_b": {"hydrophobic_count": 4, "charged_count": 3},
        },
        "result": {"score": 0.66875},
    }
