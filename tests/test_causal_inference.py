import pytest


# @id TEST-AIDS-419
# @verifies REQ-AIDS-113
def test_TEST_AIDS_419_propensity_scores_and_greedy_matches():
    from ai_data_scientist.causal_inference import propensity_score_match

    covariate = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    treatment = [0, 0, 0, 1, 1, 1, 0, 1, 0, 1]
    result = propensity_score_match(covariate, treatment)

    expected_scores = [
        0.21060384076906152,
        0.2635361539217682,
        0.32430667837956945,
        0.39163855644031065,
        0.4633632944072891,
        0.5366367055927108,
        0.6083614435596894,
        0.6756933216204305,
        0.7364638460782318,
        0.7893961592309384,
    ]
    assert result["propensity_scores"] == pytest.approx(expected_scores, abs=1e-6)

    expected_matches = [
        {"treated_index": 3, "control_index": 2, "score_distance": 0.0673318780607412},
        {"treated_index": 4, "control_index": 6, "score_distance": 0.14499814915240028},
        {"treated_index": 5, "control_index": 8, "score_distance": 0.19982714048552097},
        {"treated_index": 7, "control_index": 1, "score_distance": 0.4121571676986623},
        {"treated_index": 9, "control_index": 0, "score_distance": 0.5787923184618768},
    ]
    assert len(result["matches"]) == len(expected_matches)
    for actual_match, expected_match in zip(result["matches"], expected_matches):
        assert actual_match["treated_index"] == expected_match["treated_index"]
        assert actual_match["control_index"] == expected_match["control_index"]
        assert actual_match["score_distance"] == pytest.approx(
            expected_match["score_distance"], abs=1e-6
        )

    assert result["note"] == (
        "Matched pairs alone do not identify or estimate a causal effect; "
        "validity additionally requires exchangeability, positivity, correct "
        "model specification, and no unmeasured confounding."
    )


# @id TEST-AIDS-420
# @verifies REQ-AIDS-113
def test_TEST_AIDS_420_all_zero_treatment_is_rejected():
    from ai_data_scientist.causal_inference import propensity_score_match

    with pytest.raises(ValueError, match="at least 1 treated"):
        propensity_score_match([1, 2, 3, 4], [0, 0, 0, 0])


# @id TEST-AIDS-421
# @verifies REQ-AIDS-113
def test_TEST_AIDS_421_mismatched_lengths_is_rejected():
    from ai_data_scientist.causal_inference import propensity_score_match

    with pytest.raises(ValueError, match="must be the same length"):
        propensity_score_match([1, 2, 3], [0, 1])


# @id TEST-AIDS-422
# @verifies REQ-AIDS-113
def test_TEST_AIDS_422_perfect_separation_is_rejected():
    from ai_data_scientist.causal_inference import propensity_score_match

    with pytest.raises(ValueError, match="did not converge"):
        propensity_score_match([1, 2, 3, 4, 5, 6], [0, 0, 0, 1, 1, 1])


# @id TEST-AIDS-423
# @verifies REQ-AIDS-113
def test_TEST_AIDS_423_non_finite_covariate_is_rejected():
    from ai_data_scientist.causal_inference import propensity_score_match

    with pytest.raises(ValueError, match="covariate"):
        propensity_score_match([1, 2, float("nan"), 4], [0, 1, 0, 1])
