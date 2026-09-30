"""Tests for anomaly detection (REQ-AIDS-017)."""

import pandas as pd

from ai_data_scientist.anomaly_detection import detect_anomalies


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
