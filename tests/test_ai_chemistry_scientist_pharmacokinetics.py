"""Tests for ai_chemistry_scientist.pharmacokinetics (DES-ACHEM-130)."""

from __future__ import annotations

import pytest

_TIMES = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
_CONCENTRATIONS = [
    45.241870901797974,
    40.936537653899094,
    33.51600230178197,
    22.466448205861077,
    10.094825899732768,
    4.535897664470624,
]
_DOSE = 500.0


# @id TEST-ACHEM-130
# @verifies REQ-ACHEM-130
def test_TEST_ACHEM_130_computes_known_exponential_decay_pk_parameters_exactly():
    from ai_chemistry_scientist.pharmacokinetics import run_pharmacokinetics

    result = run_pharmacokinetics(_TIMES, _CONCENTRATIONS, _DOSE)

    assert result["cmax"] == pytest.approx(45.241870901797974, abs=1e-6)
    assert result["tmax"] == pytest.approx(0.5, abs=1e-6)
    assert result["auc_last"] == pytest.approx(209.13731796400234, abs=1e-6)
    assert result["k_el"] == pytest.approx(0.2, abs=1e-6)
    assert result["half_life"] == pytest.approx(3.465735902799724, abs=1e-6)
    assert result["auc_inf"] == pytest.approx(231.81680628635544, abs=1e-6)
    assert result["clearance"] == pytest.approx(2.156875543278631, abs=1e-6)
    assert result["volume_of_distribution"] == pytest.approx(10.784377716393147, abs=1e-6)


# @id TEST-ACHEM-131
# @verifies REQ-ACHEM-130
def test_TEST_ACHEM_131_result_fields_are_plain_python_floats():
    from ai_chemistry_scientist.pharmacokinetics import run_pharmacokinetics

    result = run_pharmacokinetics(_TIMES, _CONCENTRATIONS, _DOSE)

    for key in result:
        assert isinstance(result[key], float)


# @id TEST-ACHEM-132
# @verifies REQ-ACHEM-003 REQ-ACHEM-130
def test_TEST_ACHEM_132_fewer_than_four_points_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "pharmacokinetic-analysis",
        {"times": [0.5, 1.0, 2.0], "concentrations": [45.0, 40.0, 33.0], "dose": 500.0},
    )

    assert result["ok"] is False
    assert result["parameter"] == "times"


# @id TEST-ACHEM-133
# @verifies REQ-ACHEM-003 REQ-ACHEM-130
def test_TEST_ACHEM_133_non_increasing_times_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "pharmacokinetic-analysis",
        {
            "times": [0.5, 2.0, 1.0, 4.0],
            "concentrations": [45.0, 40.0, 33.0, 22.0],
            "dose": 500.0,
        },
    )

    assert result["ok"] is False
    assert result["parameter"] == "times"


# @id TEST-ACHEM-134
# @verifies REQ-ACHEM-003 REQ-ACHEM-130
def test_TEST_ACHEM_134_non_positive_dose_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "pharmacokinetic-analysis",
        {"times": _TIMES, "concentrations": _CONCENTRATIONS, "dose": 0.0},
    )

    assert result["ok"] is False
    assert result["parameter"] == "dose"


# @id TEST-ACHEM-135
# @verifies REQ-ACHEM-003 REQ-ACHEM-130
def test_TEST_ACHEM_135_n_terminal_out_of_range_is_rejected():
    from ai_chemistry_scientist.validation import validate_parameters

    result = validate_parameters(
        "pharmacokinetic-analysis",
        {
            "times": _TIMES,
            "concentrations": _CONCENTRATIONS,
            "dose": _DOSE,
            "n_terminal": 1,
        },
    )

    assert result["ok"] is False
    assert result["parameter"] == "n_terminal"


# @id TEST-ACHEM-136
# @verifies REQ-ACHEM-130
def test_TEST_ACHEM_136_rising_terminal_concentrations_raises_value_error():
    from ai_chemistry_scientist.pharmacokinetics import run_pharmacokinetics

    with pytest.raises(
        ValueError,
        match="terminal concentrations must yield a positive elimination rate constant",
    ):
        run_pharmacokinetics(
            [0.5, 1.0, 2.0, 4.0],
            [10.0, 15.0, 20.0, 25.0],
            500.0,
        )
