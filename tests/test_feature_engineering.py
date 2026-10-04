"""Tests for feature engineering (REQ-AIDS-015, REQ-AIDS-073)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from ai_data_scientist.feature_engineering import (
    engineer_features,
    fit_features,
    transform_features,
)


# @id TEST-AIDS-015
# @verifies REQ-AIDS-015
def test_TEST_AIDS_015():
    df = pd.DataFrame({"category": ["a", "b", "a", "c"], "value": [1, 2, 3, 4]})

    result = engineer_features(df, operation="one_hot", columns=["category"])

    reference = pd.get_dummies(df, columns=["category"])
    for col in reference.columns:
        assert col in result.dataframe.columns
    pd.testing.assert_frame_equal(
        result.dataframe[reference.columns].astype(reference.dtypes),
        reference,
        check_like=True,
    )
    assert set(result.added_columns) == {c for c in reference.columns if c not in df.columns}
    assert all(result.definitions[c] for c in result.added_columns)


# @id TEST-AIDS-151
# @verifies REQ-AIDS-015
def test_TEST_AIDS_151_aggregate_mean():
    df = pd.DataFrame({"grp": ["a", "a", "b", "b"], "val": [1.0, 3.0, None, 10.0]})

    result = engineer_features(
        df, operation="aggregate", columns=["val"], group_col="grp", agg_func="mean"
    )

    reference = df.groupby("grp")["val"].transform("mean")
    added = result.added_columns
    assert len(added) == 1
    pd.testing.assert_series_equal(result.dataframe[added[0]], reference, check_names=False)
    assert result.definitions[added[0]]


# @id TEST-AIDS-152
# @verifies REQ-AIDS-015
def test_TEST_AIDS_152_aggregate_count_eq():
    df = pd.DataFrame({"grp": ["a", "a", "b", "b"], "val": ["x", "y", "x", "x"]})

    result = engineer_features(
        df,
        operation="aggregate",
        columns=["val"],
        group_col="grp",
        agg_func="count_eq",
        compare_value="x",
    )

    reference = df["val"].eq("x").groupby(df["grp"]).transform("sum")
    added = result.added_columns
    assert len(added) == 1
    pd.testing.assert_series_equal(result.dataframe[added[0]], reference, check_names=False)


# @id TEST-AIDS-153
# @verifies REQ-AIDS-015
def test_TEST_AIDS_153_interaction():
    df = pd.DataFrame({"a": ["x", "y", None], "b": ["1", "2", "3"]})

    result = engineer_features(df, operation="interaction", col_a="a", col_b="b")

    reference = df["a"].astype("string") + "__" + df["b"].astype("string")
    added = result.added_columns
    assert len(added) == 1
    pd.testing.assert_series_equal(
        result.dataframe[added[0]].astype("string"), reference, check_names=False
    )
    assert pd.isna(result.dataframe[added[0]].iloc[2])


# @id TEST-AIDS-154
# @verifies REQ-AIDS-015
def test_TEST_AIDS_154_missing_flag():
    df = pd.DataFrame({"val": [1.0, None, 3.0]})

    result = engineer_features(df, operation="missing_flag", columns=["val"])

    reference = df["val"].isna()
    added = result.added_columns
    assert len(added) == 1
    pd.testing.assert_series_equal(result.dataframe[added[0]], reference, check_names=False)


# @id TEST-AIDS-155
# @verifies REQ-AIDS-015
def test_TEST_AIDS_155_bin():
    df = pd.DataFrame({"val": [-5.0, 0.5, 5.0, 15.0]})

    result = engineer_features(df, operation="bin", columns=["val"], edges=[0.0, 1.0, 10.0])

    reference = pd.cut(df["val"], bins=[0.0, 1.0, 10.0], right=True, include_lowest=True)
    added = result.added_columns
    assert len(added) == 1
    pd.testing.assert_series_equal(result.dataframe[added[0]], reference, check_names=False)


# @id TEST-AIDS-156
# @verifies REQ-AIDS-015
def test_TEST_AIDS_156_unknown_params_raise():
    df = pd.DataFrame({"val": [1.0, 2.0]})

    with pytest.raises(ValueError):
        engineer_features(df, operation="aggregate", columns=["val"])


# @id TEST-AIDS-157
# @verifies REQ-AIDS-073
def test_TEST_AIDS_157_fit_features_matches_standard_scaler():
    train_df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})

    fitted = fit_features(train_df, "scale", ["a", "b"])

    reference = StandardScaler().fit(train_df[["a", "b"]])
    np.testing.assert_array_equal(fitted.scaler.mean_, reference.mean_)
    np.testing.assert_array_equal(fitted.scaler.scale_, reference.scale_)


# @id TEST-AIDS-158
# @verifies REQ-AIDS-073
def test_TEST_AIDS_158_transform_features_no_leakage():
    train_df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    validation_df = pd.DataFrame({"a": [100.0, 200.0, 300.0]})

    fitted = fit_features(train_df, "scale", ["a"])
    result = transform_features(fitted, validation_df)

    leaked_reference = StandardScaler().fit_transform(validation_df[["a"]])
    assert not np.allclose(result.dataframe[["a"]].to_numpy(), leaked_reference)

    correct_reference = fitted.scaler.transform(validation_df[["a"]])
    np.testing.assert_array_equal(result.dataframe[["a"]].to_numpy(), correct_reference)


# @id TEST-AIDS-159
# @verifies REQ-AIDS-073
def test_TEST_AIDS_159_transform_features_reproduces_legacy_scale():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [5.0, 5.0, 5.0]})

    fitted = fit_features(df, "scale", ["a", "b"])
    result = transform_features(fitted, df)

    legacy = engineer_features(df, operation="scale", columns=["a", "b"])
    pd.testing.assert_frame_equal(result.dataframe, legacy.dataframe)
    # zero-variance column "b" keeps StandardScaler's scale_=1 convention,
    # so it reduces to mean-centering without a division-by-zero error.
    assert fitted.scaler.scale_[1] == 1.0
    np.testing.assert_array_equal(result.dataframe["b"].to_numpy(), [0.0, 0.0, 0.0])
