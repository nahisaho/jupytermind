import pytest


# @id TEST-AIDS-444
# @verifies REQ-AIDS-116
def test_TEST_AIDS_444_triangle_and_path_happy_path():
    from ai_data_scientist.network_analysis import analyze_network

    adjacency_matrix = [
        [0, 1, 1, 0, 0, 0],
        [1, 0, 1, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 1, 0],
    ]
    result = analyze_network(adjacency_matrix)

    assert result["n_components"] == 2
    assert result["component_labels"] == [0, 0, 0, 1, 1, 1]
    assert result["degree"] == [2.0, 2.0, 2.0, 1.0, 2.0, 1.0]
    assert result["closeness_centrality"][0] == pytest.approx(1.0)
    assert result["closeness_centrality"][1] == pytest.approx(1.0)
    assert result["closeness_centrality"][2] == pytest.approx(1.0)


# @id TEST-AIDS-445
# @verifies REQ-AIDS-116
def test_TEST_AIDS_445_non_square_matrix_is_rejected():
    from ai_data_scientist.network_analysis import analyze_network

    with pytest.raises(ValueError, match="must be square"):
        analyze_network([[0, 1], [1, 0], [0, 0]])


# @id TEST-AIDS-446
# @verifies REQ-AIDS-116
def test_TEST_AIDS_446_non_symmetric_matrix_is_rejected():
    from ai_data_scientist.network_analysis import analyze_network

    with pytest.raises(ValueError, match="must be symmetric"):
        analyze_network([[0, 1, 0], [0, 0, 1], [0, 1, 0]])


# @id TEST-AIDS-447
# @verifies REQ-AIDS-116
def test_TEST_AIDS_447_non_zero_diagonal_is_rejected():
    from ai_data_scientist.network_analysis import analyze_network

    with pytest.raises(ValueError, match="diagonal must be all zero"):
        analyze_network([[1, 1, 0], [1, 0, 1], [0, 1, 0]])


# @id TEST-AIDS-448
# @verifies REQ-AIDS-116
def test_TEST_AIDS_448_invalid_entry_is_rejected():
    from ai_data_scientist.network_analysis import analyze_network

    with pytest.raises(ValueError, match="must each be exactly 0 or 1"):
        analyze_network([[0, 2, 0], [2, 0, 1], [0, 1, 0]])
