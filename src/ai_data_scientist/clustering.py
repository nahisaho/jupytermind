"""Clustering and dimensionality reduction.

Implements DES-AIDS-014 (REQ-AIDS-016): fits the requested unsupervised
model (clustering or dimensionality reduction) and reports cluster
assignments or reduced component values.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

_SUPPORTED_METHODS = ("kmeans", "pca")
_UNSUPERVISED_MODEL_METHODS = ("tsne",)


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
        if params["n_clusters"] > len(df):
            raise ValueError(
                f"n_clusters ({params['n_clusters']}) must not exceed the "
                f"number of rows ({len(df)})"
            )
        model = KMeans(**params)
        labels_or_components = model.fit_predict(df).tolist()
    else:  # pca
        params.setdefault("n_components", min(2, df.shape[1]))
        model = PCA(**params)
        labels_or_components = model.fit_transform(df).tolist()

    return UnsupervisedResult(
        labels_or_components=labels_or_components, method=method, params=params
    )


# @id CODE-AIDS-171
# @implements REQ-AIDS-111
# @design DES-AIDS-115
def fit_unsupervised_model(
    method: str,
    x: list[list[float]],
    n_components: int = 2,
    random_state: int = 42,
    perplexity: float = 30.0,
) -> dict[str, list[list[float]]]:
    """Fit a non-linear unsupervised embedding model (``t-SNE``) on ``x``.

    Independent of, and never reads or writes, ``cluster_or_reduce``'s own
    ``_SUPPORTED_METHODS`` value domain.
    """
    if method not in _UNSUPERVISED_MODEL_METHODS:
        raise ValueError(f"Unsupported method: {method!r}")
    if perplexity >= len(x):
        raise ValueError(
            f"perplexity ({perplexity}) must be less than the number of samples ({len(x)})"
        )

    model = TSNE(
        n_components=n_components,
        random_state=random_state,
        perplexity=perplexity,
        init="pca",
    )
    embedding = model.fit_transform(np.asarray(x, dtype=float)).tolist()

    return {"embedding": embedding}
