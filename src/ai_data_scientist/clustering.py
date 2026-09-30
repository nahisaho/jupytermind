"""Clustering and dimensionality reduction.

Implements DES-AIDS-014 (REQ-AIDS-016): fits the requested unsupervised
model (clustering or dimensionality reduction) and reports cluster
assignments or reduced component values.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

_SUPPORTED_METHODS = ("kmeans", "pca")


@dataclass(frozen=True)
class UnsupervisedResult:
    labels_or_components: object
    method: str
    params: dict


# @id CODE-AIDS-016
# @implements REQ-AIDS-016
# @design DES-AIDS-014
def cluster_or_reduce(
    df: pd.DataFrame, method: str = "kmeans", params: dict | None = None
) -> UnsupervisedResult:
    """Fit ``method`` (e.g. kmeans, pca) on ``df`` and report the result."""
    if method not in _SUPPORTED_METHODS:
        raise ValueError(f"Unsupported unsupervised method: {method!r}")
    params = dict(params or {})

    if method == "kmeans":
        params.setdefault("n_clusters", 2)
        params.setdefault("n_init", 10)
        model = KMeans(**params)
        labels_or_components = model.fit_predict(df).tolist()
    else:  # pca
        params.setdefault("n_components", min(2, df.shape[1]))
        model = PCA(**params)
        labels_or_components = model.fit_transform(df).tolist()

    return UnsupervisedResult(
        labels_or_components=labels_or_components, method=method, params=params
    )
