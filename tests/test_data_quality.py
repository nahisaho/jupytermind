"""Tests for semantic data-quality checks (REQ-AIDS-055)."""

import pandas as pd

from ai_data_scientist.data_quality import detect_anomalies, validate_anomalies


# @id TEST-AIDS-091
# @verifies REQ-AIDS-055
def test_TEST_AIDS_091_out_of_range_values_detected():
    df = pd.DataFrame({"age": [25, 30, -5, 150, 40]})
    records = detect_anomalies(df, schema={"age": {"min": 0, "max": 120}})
    assert len(records) == 1
    assert records[0].rule == "range"
    assert records[0].row_count == 2


# @id TEST-AIDS-092
# @verifies REQ-AIDS-055
def test_TEST_AIDS_092_disallowed_category_and_null_detected_separately():
    df = pd.DataFrame({"status": ["active", "inactive", "bogus", None]})
    records = detect_anomalies(
        df, schema={"status": {"allowed": ["active", "inactive"], "not_null": True}}
    )
    rules = {r.rule for r in records}
    assert rules == {"allowed_values", "not_null"}


# @id TEST-AIDS-093
# @verifies REQ-AIDS-055
def test_TEST_AIDS_093_clean_column_produces_no_records():
    df = pd.DataFrame({"age": [25, 30, 40]})
    records = detect_anomalies(df, schema={"age": {"min": 0, "max": 120}})
    assert records == ()


# @id TEST-AIDS-094
# @verifies REQ-AIDS-055
def test_TEST_AIDS_094_overlap_validation_flags_diverging_reference():
    primary = pd.DataFrame({"fare": [10.0, 12.0, 11.0]})
    reference = pd.DataFrame({"fare": [20.0, 22.0, 21.0]})
    mismatches = validate_anomalies(primary, reference, columns=["fare"], tolerance=0.1)
    assert len(mismatches) == 1
    assert mismatches[0].column == "fare"


# @id TEST-AIDS-095
# @verifies REQ-AIDS-055
def test_TEST_AIDS_095_overlap_validation_passes_within_tolerance():
    primary = pd.DataFrame({"fare": [10.0, 12.0, 11.0]})
    reference = pd.DataFrame({"fare": [10.2, 11.8, 11.1]})
    mismatches = validate_anomalies(primary, reference, columns=["fare"], tolerance=0.1)
    assert mismatches == ()
