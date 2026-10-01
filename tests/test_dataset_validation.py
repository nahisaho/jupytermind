"""Tests for independent-dataset overlap comparison (REQ-AIDS-057)."""

import pandas as pd

from ai_data_scientist.dataset_validation import compare_datasets


# @id TEST-AIDS-100
# @verifies REQ-AIDS-057
def test_TEST_AIDS_100_matched_keys_and_agreeing_values_reported():
    primary = pd.DataFrame({"id": [1, 2, 3], "fare": [10.0, 20.0, 30.0]})
    candidate = pd.DataFrame({"trip_id": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})
    report = compare_datasets(
        primary,
        candidate,
        key_mapping={"id": "trip_id"},
        value_mapping={"fare": "amount"},
        candidate_relationship="independent",
    )
    assert report.matched_keys == 3
    assert report.primary_only_keys == 0
    assert report.column_comparisons[0].agreement_rate == 1.0


# @id TEST-AIDS-101
# @verifies REQ-AIDS-057
def test_TEST_AIDS_101_unmatched_keys_counted_on_both_sides():
    primary = pd.DataFrame({"id": [1, 2, 3]})
    candidate = pd.DataFrame({"trip_id": [2, 3, 4]})
    report = compare_datasets(primary, candidate, key_mapping={"id": "trip_id"}, value_mapping={})
    assert report.matched_keys == 2
    assert report.primary_only_keys == 1
    assert report.candidate_only_keys == 1


# @id TEST-AIDS-102
# @verifies REQ-AIDS-057
def test_TEST_AIDS_102_disagreeing_values_lower_agreement_rate():
    primary = pd.DataFrame({"id": [1, 2], "fare": [10.0, 20.0]})
    candidate = pd.DataFrame({"trip_id": [1, 2], "amount": [10.0, 99.0]})
    report = compare_datasets(
        primary, candidate, key_mapping={"id": "trip_id"}, value_mapping={"fare": "amount"}
    )
    assert report.column_comparisons[0].mismatched_rows == 1
    assert report.column_comparisons[0].agreement_rate == 0.5


# @id TEST-AIDS-103
# @verifies REQ-AIDS-057
def test_TEST_AIDS_103_invalid_relationship_raises():
    primary = pd.DataFrame({"id": [1]})
    candidate = pd.DataFrame({"trip_id": [1]})
    try:
        compare_datasets(
            primary,
            candidate,
            key_mapping={"id": "trip_id"},
            value_mapping={},
            candidate_relationship="bogus",
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
