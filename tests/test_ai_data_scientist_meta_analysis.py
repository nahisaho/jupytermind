"""Tests for ai_data_scientist.meta_analysis (DES-AIDS-103)."""

from __future__ import annotations

import math

import pytest

from ai_data_scientist.meta_analysis import pool_effect_sizes


def _assert_close(actual: dict, expected: dict, tol: float = 1e-9) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert math.isclose(actual[key], expected_value, abs_tol=tol), (key, actual[key])


# @id TEST-AIDS-366
# @verifies REQ-AIDS-103
def test_TEST_AIDS_366_pools_fixture_effect_sizes_exactly():
    result = pool_effect_sizes([0.5, 0.7, 0.6, 1.5], [0.1, 0.2, 0.15, 0.3])

    _assert_close(
        result,
        {
            "pooled_fe": 0.6138461538461538,
            "se_fe": 0.07442084075352508,
            "q_statistic": 10.215384615384615,
            "i_squared": 70.63253012048193,
            "tau_squared": 0.06554347826086955,
            "pooled_re": 0.7335801573413859,
            "se_re": 0.15713624940689194,
        },
    )


# @id TEST-AIDS-367
# @verifies REQ-AIDS-103
def test_TEST_AIDS_367_fewer_than_two_studies_is_rejected():
    with pytest.raises(ValueError, match="must contain at least 2 studies"):
        pool_effect_sizes([0.5], [0.1])


# @id TEST-AIDS-368
# @verifies REQ-AIDS-103
def test_TEST_AIDS_368_mismatched_lengths_is_rejected():
    with pytest.raises(ValueError):
        pool_effect_sizes([0.5, 0.6, 0.7], [0.1, 0.2])


# @id TEST-AIDS-369
# @verifies REQ-AIDS-103
def test_TEST_AIDS_369_non_positive_standard_error_is_rejected():
    with pytest.raises(ValueError, match="standard_errors"):
        pool_effect_sizes([0.5, 0.6], [0.1, 0.0])


# @id TEST-AIDS-370
# @verifies REQ-AIDS-103
def test_TEST_AIDS_370_non_finite_effect_is_rejected():
    with pytest.raises(ValueError, match="must be a list of finite numbers"):
        pool_effect_sizes([0.5, float("nan")], [0.1, 0.2])

    with pytest.raises(ValueError, match="must be a list of finite numbers"):
        pool_effect_sizes([0.5, float("inf")], [0.1, 0.2])


# @id TEST-AIDS-371
# @verifies REQ-AIDS-103
def test_TEST_AIDS_371_int_standard_error_is_rejected():
    with pytest.raises(ValueError, match="standard_errors"):
        pool_effect_sizes([0.5, 0.6], [1, 0.2])


# @id TEST-AIDS-392
# @verifies REQ-AIDS-103
def test_TEST_AIDS_392_underflowing_standard_error_is_rejected():
    with pytest.raises(ValueError, match="underflows to zero"):
        pool_effect_sizes([0.5, 0.6], [1e-308, 0.2])
