"""Tests for ai_data_scientist.clinical_risk_scoring (DES-AIDS-104)."""

from __future__ import annotations

import pytest

from ai_data_scientist.clinical_risk_scoring import cha2ds2_vasc_score


# @id TEST-AIDS-372
# @verifies REQ-AIDS-104
def test_TEST_AIDS_372_computes_high_risk_fixture():
    result = cha2ds2_vasc_score(
        congestive_heart_failure=True,
        hypertension=True,
        age=78,
        diabetes=False,
        stroke_tia_thromboembolism_history=True,
        vascular_disease=False,
        sex="female",
    )

    assert result == {"score": 7, "risk_category": "high"}


# @id TEST-AIDS-373
# @verifies REQ-AIDS-104
def test_TEST_AIDS_373_computes_low_risk_fixture():
    result = cha2ds2_vasc_score(
        congestive_heart_failure=False,
        hypertension=False,
        age=50,
        diabetes=False,
        stroke_tia_thromboembolism_history=False,
        vascular_disease=False,
        sex="male",
    )

    assert result == {"score": 0, "risk_category": "low"}


# @id TEST-AIDS-374
# @verifies REQ-AIDS-104
def test_TEST_AIDS_374_computes_moderate_risk_fixture():
    result = cha2ds2_vasc_score(
        congestive_heart_failure=False,
        hypertension=False,
        age=70,
        diabetes=False,
        stroke_tia_thromboembolism_history=False,
        vascular_disease=False,
        sex="male",
    )

    assert result == {"score": 1, "risk_category": "moderate"}


# @id TEST-AIDS-375
# @verifies REQ-AIDS-104
def test_TEST_AIDS_375_negative_age_is_rejected():
    with pytest.raises(ValueError, match="must be >= 0"):
        cha2ds2_vasc_score(False, False, -1, False, False, False, "male")


# @id TEST-AIDS-376
# @verifies REQ-AIDS-104
@pytest.mark.parametrize("age", [65.5, True])
def test_TEST_AIDS_376_non_int_age_is_rejected(age):
    with pytest.raises(ValueError, match="must be a non-negative int, not bool or float"):
        cha2ds2_vasc_score(False, False, age, False, False, False, "male")


# @id TEST-AIDS-377
# @verifies REQ-AIDS-104
def test_TEST_AIDS_377_invalid_sex_is_rejected():
    with pytest.raises(ValueError, match="must be 'male' or 'female'"):
        cha2ds2_vasc_score(False, False, 50, False, False, False, "unknown")


# @id TEST-AIDS-378
# @verifies REQ-AIDS-104
def test_TEST_AIDS_378_non_boolean_flag_is_rejected():
    with pytest.raises(ValueError, match="must be exactly True or False"):
        cha2ds2_vasc_score(1, False, 50, False, False, False, "male")
