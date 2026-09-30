"""Tests for clustering and dimensionality reduction (REQ-AIDS-016)."""

import pandas as pd

from ai_data_scientist.clustering import cluster_or_reduce


# @id TEST-AIDS-016
# @verifies REQ-AIDS-016
def test_TEST_AIDS_016():
    df = pd.DataFrame(
        {
            "x": [0.0, 0.1, 0.2, 10.0, 10.1, 10.2, 20.0, 20.1, 20.2],
            "y": [0.0, 0.1, -0.1, 10.0, 9.9, 10.1, 20.0, 20.2, 19.9],
        }
    )

    result = cluster_or_reduce(df, method="kmeans", params={"n_clusters": 3, "random_state": 0})

    assert result.method == "kmeans"
    value_counts = pd.Series(result.labels_or_components).value_counts()
    assert value_counts.sum() == len(df)
