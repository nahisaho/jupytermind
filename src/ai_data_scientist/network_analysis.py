"""Graph connectivity and centrality analysis over an unweighted undirected graph."""

import numpy as np
from scipy.sparse.csgraph import connected_components, shortest_path


def _validate_adjacency_matrix(adjacency_matrix: list) -> None:
    if not isinstance(adjacency_matrix, list) or len(adjacency_matrix) < 2:
        raise ValueError("adjacency_matrix: must be a square matrix with at least 2 nodes")
    n = len(adjacency_matrix)
    if not all(isinstance(row, list) and len(row) == n for row in adjacency_matrix):
        raise ValueError("adjacency_matrix: must be square")
    for row in adjacency_matrix:
        for entry in row:
            if not (isinstance(entry, int) and not isinstance(entry, bool) and entry in (0, 1)):
                raise ValueError("adjacency_matrix: entries must each be exactly 0 or 1")
    for i in range(n):
        if adjacency_matrix[i][i] != 0:
            raise ValueError("adjacency_matrix: diagonal must be all zero (no self-loops)")
    for i in range(n):
        for j in range(n):
            if adjacency_matrix[i][j] != adjacency_matrix[j][i]:
                raise ValueError("adjacency_matrix: must be symmetric (undirected graph)")


# @id CODE-AIDS-169
# @implements REQ-AIDS-116
# @design DES-AIDS-114
def analyze_network(adjacency_matrix: list) -> dict:
    """Compute connectivity/centrality metrics for an unweighted undirected graph."""
    _validate_adjacency_matrix(adjacency_matrix)

    arr = np.array(adjacency_matrix)
    n = arr.shape[0]
    n_components, labels = connected_components(arr, directed=False)
    degree = arr.sum(axis=1)
    dist = shortest_path(arr, method="D", unweighted=True, directed=False)

    closeness_centrality = []
    for i in range(n):
        finite_distances = [d for j, d in enumerate(dist[i]) if j != i and np.isfinite(d)]
        if not finite_distances:
            closeness_centrality.append(None)
        else:
            closeness_centrality.append(len(finite_distances) / sum(finite_distances))

    return {
        "n_components": int(n_components),
        "component_labels": [int(label) for label in labels],
        "degree": [float(d) for d in degree],
        "closeness_centrality": closeness_centrality,
    }
