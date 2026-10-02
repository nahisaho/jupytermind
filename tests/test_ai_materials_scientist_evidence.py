"""Tests for ai_materials_scientist run evidence recording (REQ-AIMS-004/005)."""

from __future__ import annotations

import numpy as np


# @id TEST-AIMS-004
# @verifies REQ-AIMS-004
def test_TEST_AIMS_004_record_run_has_exactly_three_top_level_keys():
    from ai_materials_scientist.evidence import record_run

    record = record_run(
        module_name="phase-field",
        unit_system="dimensionless-order-parameter",
        params={"dx": 1.0, "M": 1.0},
        arrays={"snapshots": np.zeros((2, 2), dtype="float64")},
        seed=None,
    )

    assert set(record.keys()) == {"metadata", "parameters", "arrays"}
    assert record["metadata"]["module"] == "phase-field"
    assert record["metadata"]["unit_system"] == "dimensionless-order-parameter"
    assert record["metadata"]["seed"] is None
    assert "schema_version" in record["metadata"]
    assert record["parameters"] == {"dx": 1.0, "M": 1.0}


# @id TEST-AIMS-949
# @verifies REQ-AIMS-004
def test_TEST_AIMS_949_stochastic_module_records_explicit_seed():
    from ai_materials_scientist.evidence import record_run

    record = record_run(
        module_name="classical-monte-carlo",
        unit_system="J=kB=1",
        params={"L": 20},
        arrays={"magnetization": np.array([0.5], dtype="float64")},
        seed=12345,
    )

    assert record["metadata"]["seed"] == 12345


# @id TEST-AIMS-005
# @verifies REQ-AIMS-005
def test_TEST_AIMS_005_json_round_trip_preserves_arrays_array_equal():
    from ai_materials_scientist.evidence import from_json, record_run, to_json

    original = record_run(
        module_name="finite-element",
        unit_system="SI",
        params={"n_nodes": 5},
        arrays={"nodal_values": np.array([273.15, 283.15, 293.15], dtype="float64")},
        seed=None,
    )

    round_tripped = from_json(to_json(original))

    assert np.array_equal(
        round_tripped["arrays"]["nodal_values"], original["arrays"]["nodal_values"]
    )
    assert round_tripped["metadata"] == original["metadata"]
    assert round_tripped["parameters"] == original["parameters"]


# @id TEST-AIMS-950
# @verifies REQ-AIMS-004
def test_TEST_AIMS_950_non_float64_array_is_rejected_unless_declared_integer():
    import pytest

    from ai_materials_scientist.evidence import record_run

    with pytest.raises(ValueError, match="float64"):
        record_run(
            module_name="kinetic-monte-carlo",
            unit_system="J=kB=1",
            params={},
            arrays={"occupancy": np.array([1, 0, 1], dtype="int64")},
            seed=7,
        )

    # Explicitly declared integer array is accepted.
    record = record_run(
        module_name="kinetic-monte-carlo",
        unit_system="J=kB=1",
        params={},
        arrays={"occupancy": np.array([1, 0, 1], dtype="int64")},
        seed=7,
        allow_integer_arrays=frozenset({"occupancy"}),
    )
    assert record["arrays"]["occupancy"].dtype == np.int64


# @id TEST-AIMS-951
# @verifies REQ-AIMS-004
def test_TEST_AIMS_951_to_json_arrays_are_json_safe_dtype_shape_data():
    import json

    from ai_materials_scientist.evidence import record_run, to_json

    record = record_run(
        module_name="calphad",
        unit_system="SI",
        params={"omega": 10000.0},
        arrays={"x_curve": np.array([0.1, 0.2], dtype="float64")},
        seed=None,
    )

    safe = to_json(record)
    # Must be plain-JSON-serializable (no numpy objects).
    json.dumps(safe)
    assert set(safe["arrays"]["x_curve"].keys()) == {"dtype", "shape", "data"}
    assert safe["arrays"]["x_curve"]["shape"] == [2]
