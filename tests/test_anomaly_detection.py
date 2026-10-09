"""Tests for anomaly detection (REQ-AIDS-017)."""

import numpy as np
import pandas as pd
import pytest

from ai_data_scientist.anomaly_detection import detect_anomalies, detect_multivariate_anomalies


# @id TEST-AIDS-017
# @verifies REQ-AIDS-017
def test_TEST_AIDS_017():
    normal = [0.1, -0.2, 0.3, -0.1, 0.2, -0.3, 0.0, 0.15, -0.05, 0.05] * 3
    injected_indices = {5, 17}
    values = list(normal)
    for idx in injected_indices:
        values[idx] = 100.0

    df = pd.DataFrame({"value": values})

    result = detect_anomalies(df, column="value", method="zscore", params={"threshold": 3.0})

    assert injected_indices <= set(result.flagged_indices)
    assert result.method == "zscore"


def _fixture_with_far_outliers():
    rng = np.random.default_rng(42)
    normal_points = rng.normal(loc=[0, 0], scale=0.5, size=(18, 2))
    outliers = [[10, 10], [-10, -10]]
    return np.vstack([normal_points, outliers]).tolist()


def _assert_label_shape_and_boolean_equivalence(result, n_expected):
    labels = result["labels"]
    is_outlier = result["is_outlier"]
    assert len(labels) == n_expected
    assert len(is_outlier) == n_expected
    assert set(labels) <= {1, -1}
    assert all(is_outlier[i] == (labels[i] == -1) for i in range(n_expected))


# @id TEST-AIDS-484
# @verifies REQ-AIDS-112
def test_TEST_AIDS_484_isolation_forest_flags_known_far_outliers():
    x = _fixture_with_far_outliers()

    result = detect_multivariate_anomalies("isolation_forest", x)

    _assert_label_shape_and_boolean_equivalence(result, 20)
    assert result["labels"][18] == -1
    assert result["labels"][19] == -1
    assert result["is_outlier"][18] is True
    assert result["is_outlier"][19] is True


# @id TEST-AIDS-485
# @verifies REQ-AIDS-112
def test_TEST_AIDS_485_lof_flags_known_far_outliers():
    x = _fixture_with_far_outliers()

    result = detect_multivariate_anomalies("lof", x, n_neighbors=5)

    _assert_label_shape_and_boolean_equivalence(result, 20)
    assert result["labels"][18] == -1
    assert result["labels"][19] == -1
    assert result["is_outlier"][18] is True
    assert result["is_outlier"][19] is True


# @id TEST-AIDS-486
# @verifies REQ-AIDS-112
def test_TEST_AIDS_486_unsupported_method_raises_value_error_naming_method():
    x = [[0.0, 0.0], [1.0, 1.0]]

    with pytest.raises(ValueError, match="method"):
        detect_multivariate_anomalies("dbscan", x)


# @id TEST-AIDS-487
# @verifies REQ-AIDS-112
def test_TEST_AIDS_487_lof_n_neighbors_zero_raises_value_error_naming_n_neighbors():
    x = [[0.0, 0.0], [1.0, 1.0]]

    with pytest.raises(ValueError, match="n_neighbors.*must be >= 1"):
        detect_multivariate_anomalies("lof", x, n_neighbors=0)
