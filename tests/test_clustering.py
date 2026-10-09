"""Tests for clustering and dimensionality reduction (REQ-AIDS-016)."""

import math

import numpy as np
import pandas as pd
import pytest

from ai_data_scientist.clustering import cluster_or_reduce, fit_unsupervised_model


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


# @id TEST-AIDS-034
# @verifies REQ-AIDS-016
def test_TEST_AIDS_034_n_clusters_exceeding_rows_raises_clear_error():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})

    with pytest.raises(ValueError, match="n_clusters.*10.*rows.*3|rows.*3.*n_clusters.*10"):
        cluster_or_reduce(df, method="kmeans", params={"n_clusters": 10})


def _two_gaussian_clusters():
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=(0, 0), scale=0.3, size=(15, 2))
    cluster_b = rng.normal(loc=(20, 20), scale=0.3, size=(15, 2))
    return np.vstack([cluster_a, cluster_b]).tolist()


def _mean_pairwise_distance(points):
    total = 0.0
    count = 0
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            total += math.dist(points[i], points[j])
            count += 1
    return total / count if count else 0.0


# @id TEST-AIDS-481
# @verifies REQ-AIDS-111
def test_TEST_AIDS_481_tsne_embedding_separates_known_clusters():
    x = _two_gaussian_clusters()

    result = fit_unsupervised_model("tsne", x, perplexity=5)

    embedding = result["embedding"]
    assert len(embedding) == 30
    within_a = _mean_pairwise_distance(embedding[:15])
    within_b = _mean_pairwise_distance(embedding[15:])
    mean_within = (within_a + within_b) / 2
    between = [math.dist(p, q) for p in embedding[:15] for q in embedding[15:]]
    mean_between = sum(between) / len(between)

    assert mean_within < mean_between


# @id TEST-AIDS-482
# @verifies REQ-AIDS-111
def test_TEST_AIDS_482_unsupported_method_raises_value_error_naming_method():
    x = [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]

    with pytest.raises(ValueError, match="method"):
        fit_unsupervised_model("dbscan", x)


# @id TEST-AIDS-483
# @verifies REQ-AIDS-111
def test_TEST_AIDS_483_perplexity_at_least_sample_count_raises_value_error():
    x = [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]

    with pytest.raises(ValueError, match="perplexity.*must be less than the number of samples"):
        fit_unsupervised_model("tsne", x, perplexity=30)
