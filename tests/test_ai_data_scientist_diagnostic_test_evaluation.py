"""Tests for ai_data_scientist.diagnostic_test_evaluation (DES-AIDS-105)."""

from __future__ import annotations

import math

import pytest

from ai_data_scientist.diagnostic_test_evaluation import evaluate_diagnostic_test


# @id TEST-AIDS-379
# @verifies REQ-AIDS-105
def test_TEST_AIDS_379_computes_fixture_diagnostic_metrics_exactly():
    result = evaluate_diagnostic_test(
        true_positive=80, false_negative=20, false_positive=10, true_negative=90
    )

    expected = {
        "sensitivity": 0.8,
        "specificity": 0.9,
        "ppv": 0.8888888888888888,
        "npv": 0.8181818181818182,
        "positive_likelihood_ratio": 8.000000000000002,
        "negative_likelihood_ratio": 0.22222222222222215,
        "youden_j": 0.7000000000000002,
    }
    assert result.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert math.isclose(result[key], expected_value, abs_tol=1e-9)


# @id TEST-AIDS-380
# @verifies REQ-AIDS-105
def test_TEST_AIDS_380_tp_fn_both_zero_is_rejected():
    with pytest.raises(ValueError, match="true_positive, false_negative"):
        evaluate_diagnostic_test(
            true_positive=0, false_negative=0, false_positive=10, true_negative=90
        )


# @id TEST-AIDS-381
# @verifies REQ-AIDS-105
def test_TEST_AIDS_381_tp_fp_both_zero_is_rejected():
    with pytest.raises(ValueError, match="true_positive, false_positive"):
        evaluate_diagnostic_test(
            true_positive=0, false_negative=1, false_positive=0, true_negative=1
        )


# @id TEST-AIDS-382
# @verifies REQ-AIDS-105
def test_TEST_AIDS_382_tn_fn_both_zero_is_rejected():
    with pytest.raises(ValueError, match="true_negative, false_negative"):
        evaluate_diagnostic_test(
            true_positive=1, false_negative=0, false_positive=1, true_negative=0
        )


# @id TEST-AIDS-383
# @verifies REQ-AIDS-105
def test_TEST_AIDS_383_negative_count_is_rejected():
    with pytest.raises(ValueError, match="true_positive"):
        evaluate_diagnostic_test(
            true_positive=-1, false_negative=20, false_positive=10, true_negative=90
        )


# @id TEST-AIDS-384
# @verifies REQ-AIDS-105
def test_TEST_AIDS_384_perfect_specificity_yields_infinite_positive_lr():
    result = evaluate_diagnostic_test(
        true_positive=10, false_negative=0, false_positive=0, true_negative=10
    )

    assert result["positive_likelihood_ratio"] == math.inf


# @id TEST-AIDS-385
# @verifies REQ-AIDS-105
def test_TEST_AIDS_385_fp_tn_both_zero_is_rejected():
    with pytest.raises(ValueError, match="false_positive, true_negative"):
        evaluate_diagnostic_test(
            true_positive=80, false_negative=20, false_positive=0, true_negative=0
        )
