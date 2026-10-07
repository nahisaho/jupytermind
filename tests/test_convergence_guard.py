"""Tests for the convergence_guard module (REQ-AIDS-098).

GitHub #77: a reusable, repetition-aware convergence classifier for
iterative deep-dive loops, preventing both weak single-point convergence
and repetition-masked false convergence (the two bugs found in the
Kaggle-100 batch-analysis `run_all.py` script).

Change: CHANGE-032
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pytest

from ai_data_scientist.convergence_guard import (
    ConvergenceVerdict,
    Round,
    evaluate_convergence,
)


def _rounds(metrics: list[float], signatures: list[str]) -> list[Round]:
    assert len(metrics) == len(signatures)
    return [Round(metric=m, action_signature=s) for m, s in zip(metrics, signatures)]


# ---------------------------------------------------------------------------
# REQ-AIDS-098: evaluate_convergence
# ---------------------------------------------------------------------------


# @id TEST-AIDS-317
# @verifies REQ-AIDS-098
def test_TEST_AIDS_317_two_distinct_small_transitions_converge():
    history = _rounds(
        [0.70, 0.76, 0.761, 0.762],
        ["baseline", "gradient_boosting", "feature_select", "n_estimators_tune"],
    )

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict == ConvergenceVerdict(
        status="converged", repeated_signature=None, repeated_rounds=None
    )


# @id TEST-AIDS-318
# @verifies REQ-AIDS-098
def test_TEST_AIDS_318_adjacent_repeated_action_is_repetition_detected():
    history = _rounds(
        [0.70, 0.76, 0.761, 0.762],
        ["baseline", "gradient_boosting", "n_estimators_tune", "n_estimators_tune"],
    )

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict.status == "repetition_detected"
    assert verdict.repeated_signature == "n_estimators_tune"
    assert verdict.repeated_rounds == (3, 4)


# @id TEST-AIDS-319
# @verifies REQ-AIDS-098
def test_TEST_AIDS_319_non_adjacent_repeated_action_is_repetition_detected():
    history = _rounds(
        [0.70, 0.76, 0.761, 0.762],
        ["baseline", "feature_select", "n_estimators_tune", "feature_select"],
    )

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict.status == "repetition_detected"
    assert verdict.repeated_signature == "feature_select"
    assert verdict.repeated_rounds == (2, 4)


# @id TEST-AIDS-320
# @verifies REQ-AIDS-098
def test_TEST_AIDS_320_multi_duplicate_tie_break_prefers_latest_contributing_round():
    history = _rounds([0.70, 0.76, 0.761, 0.7615, 0.762], ["baseline", "A", "B", "A", "B"])

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict.status == "repetition_detected"
    assert verdict.repeated_signature == "B"
    assert verdict.repeated_rounds == (3, 5)


# @id TEST-AIDS-321
# @verifies REQ-AIDS-098
def test_TEST_AIDS_321_earlier_non_contributing_duplicate_does_not_block_convergence():
    # Round 2 ("baseline") repeats round-0-like naming only incidentally; what
    # matters is that only the last 2 destination rounds (4, 5) are checked,
    # and round 2 duplicate-looking name is irrelevant to that pair.
    history = _rounds(
        [0.60, 0.70, 0.76, 0.761, 0.762],
        [
            "start",
            "gradient_boosting",
            "gradient_boosting_retry",
            "feature_select",
            "n_estimators_tune",
        ],
    )

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict == ConvergenceVerdict(
        status="converged", repeated_signature=None, repeated_rounds=None
    )


# @id TEST-AIDS-322
# @verifies REQ-AIDS-098
def test_TEST_AIDS_322_short_history_without_qualifying_run_is_exhausted_or_continue():
    history = _rounds([0.60, 0.70, 0.76], ["baseline", "gradient_boosting", "feature_select"])

    exhausted_verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=True
    )
    continue_verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert exhausted_verdict.status == "exhausted"
    assert continue_verdict.status == "continue"


# @id TEST-AIDS-323
# @verifies REQ-AIDS-098
def test_TEST_AIDS_323_history_shorter_than_min_consecutive_plus_one():
    history = _rounds([0.60, 0.70], ["baseline", "gradient_boosting"])

    assert (
        evaluate_convergence(
            history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
        ).status
        == "continue"
    )
    assert (
        evaluate_convergence(
            history, rel_tol=0.02, min_consecutive=2, actions_exhausted=True
        ).status
        == "exhausted"
    )


# @id TEST-AIDS-324
# @verifies REQ-AIDS-098
def test_TEST_AIDS_324_zero_rel_tol_never_qualifies_even_with_identical_metrics():
    history = _rounds([0.70, 0.70, 0.70], ["baseline", "n_estimators_tune", "n_estimators_tune"])

    verdict = evaluate_convergence(history, rel_tol=0.0, min_consecutive=2, actions_exhausted=True)

    assert verdict.status == "exhausted"


# @id TEST-AIDS-325
# @verifies REQ-AIDS-098
def test_TEST_AIDS_325_invalid_min_consecutive_raises_value_error():
    history = _rounds([0.70, 0.71, 0.711], ["a", "b", "c"])
    for bad in (0, -1, 1.5, True, "2", None):
        with pytest.raises(ValueError):
            evaluate_convergence(
                history, rel_tol=0.02, min_consecutive=bad, actions_exhausted=False
            )


# @id TEST-AIDS-326
# @verifies REQ-AIDS-098
def test_TEST_AIDS_326_invalid_rel_tol_raises_value_error():
    history = _rounds([0.70, 0.71, 0.711], ["a", "b", "c"])
    for bad in (-0.01, math.inf, math.nan, "0.02", True, None):
        with pytest.raises(ValueError):
            evaluate_convergence(history, rel_tol=bad, min_consecutive=2, actions_exhausted=False)


# @id TEST-AIDS-327
# @verifies REQ-AIDS-098
def test_TEST_AIDS_327_malformed_history_entries_raise_value_error_not_other_exceptions():
    class RaisingMapping(Mapping):
        def __getitem__(self, key):
            raise RuntimeError("boom")

        def __iter__(self):
            return iter(())

        def __len__(self):
            return 0

        def __contains__(self, key):
            raise RuntimeError("boom-contains")

    bad_histories = [
        [{"metric": 0.5}],  # missing action_signature
        [{"action_signature": "x"}],  # missing metric
        [{"metric": float("nan"), "action_signature": "x"}],
        [{"metric": 0.5, "action_signature": ""}],
        [{"metric": "0.5", "action_signature": "x"}],
        [RaisingMapping()],
    ]
    for history in bad_histories:
        with pytest.raises(ValueError):
            evaluate_convergence(history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False)


# @id TEST-AIDS-328
# @verifies REQ-AIDS-098
def test_TEST_AIDS_328_accepts_plain_dict_records_as_well_as_round_dataclass():
    history = [
        {"metric": 0.70, "action_signature": "baseline"},
        {"metric": 0.76, "action_signature": "gradient_boosting"},
        {"metric": 0.761, "action_signature": "feature_select"},
        {"metric": 0.762, "action_signature": "n_estimators_tune"},
    ]

    verdict = evaluate_convergence(
        history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False
    )

    assert verdict.status == "converged"


# @id TEST-AIDS-329
# @verifies REQ-AIDS-098
def test_TEST_AIDS_329_does_not_mutate_history_argument():
    history = _rounds(
        [0.70, 0.76, 0.761, 0.762],
        ["baseline", "gradient_boosting", "feature_select", "n_estimators_tune"],
    )
    snapshot = list(history)

    evaluate_convergence(history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False)

    assert history == snapshot


# @id TEST-AIDS-330
# @verifies REQ-AIDS-098
def test_TEST_AIDS_330_stateful_accessor_is_read_at_most_once_per_field():
    class Counting:
        def __init__(self, metric: float, action_signature: str) -> None:
            self._metric = metric
            self._action_signature = action_signature
            self.metric_reads = 0
            self.signature_reads = 0

        @property
        def metric(self) -> float:
            self.metric_reads += 1
            return self._metric

        @property
        def action_signature(self) -> str:
            self.signature_reads += 1
            return self._action_signature

    history = [
        Counting(0.70, "baseline"),
        Counting(0.76, "gradient_boosting"),
        Counting(0.761, "feature_select"),
        Counting(0.762, "n_estimators_tune"),
    ]

    evaluate_convergence(history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False)

    for entry in history:
        assert entry.metric_reads == 1
        assert entry.signature_reads == 1


# ---------------------------------------------------------------------------
# REQ-AIDS-102: secondary-metric regression detection
# ---------------------------------------------------------------------------


def _rounds_with_secondary(
    metrics: list[float],
    signatures: list[str],
    secondary: list[dict[str, float] | None],
) -> list[Round]:
    assert len(metrics) == len(signatures) == len(secondary)
    return [
        Round(metric=m, action_signature=s, secondary_metrics=sec)
        for m, s, sec in zip(metrics, signatures, secondary)
    ]


# @id TEST-AIDS-361
# @verifies REQ-AIDS-102
def test_TEST_AIDS_361_issue_80_recall_regression_upgrades_status():
    # GitHub #80 reproduction: accuracy converges over the last two rounds,
    # but recall peaked at round 2 (0.7844) and regressed to 0.6232 by the
    # final round 5 -- a ~20.5% relative drop, exceeding rel_tol=0.02.
    history = _rounds_with_secondary(
        metrics=[0.8328, 0.8190, 0.8420, 0.8367, 0.8380],
        signatures=[
            "baseline_random_forest",
            "class_weight_balanced",
            "model_gradient_boosting",
            "cv_5fold",
            "feature_importance_trim",
        ],
        secondary=[
            {"recall": 0.6578},
            {"recall": 0.7844},
            {"recall": 0.6304},
            {"recall": 0.6173},
            {"recall": 0.6232},
        ],
    )

    verdict = evaluate_convergence(
        history,
        rel_tol=0.02,
        min_consecutive=2,
        secondary_metrics=["recall"],
    )

    assert verdict.status == "converged_with_secondary_regression"
    assert verdict.secondary_regressions == ("recall",)


# @id TEST-AIDS-362
# @verifies REQ-AIDS-102
def test_TEST_AIDS_362_omitting_secondary_metrics_is_unchanged():
    # Same history as TEST-AIDS-361, but secondary_metrics is not passed:
    # behavior must be identical to REQ-AIDS-098 alone.
    history = _rounds_with_secondary(
        metrics=[0.8328, 0.8190, 0.8420, 0.8367, 0.8380],
        signatures=[
            "baseline_random_forest",
            "class_weight_balanced",
            "model_gradient_boosting",
            "cv_5fold",
            "feature_importance_trim",
        ],
        secondary=[
            {"recall": 0.6578},
            {"recall": 0.7844},
            {"recall": 0.6304},
            {"recall": 0.6173},
            {"recall": 0.6232},
        ],
    )

    verdict = evaluate_convergence(history, rel_tol=0.02, min_consecutive=2)

    assert verdict.status == "converged"
    assert verdict.secondary_regressions == ()


# @id TEST-AIDS-363
# @verifies REQ-AIDS-102
def test_TEST_AIDS_363_no_regression_stays_converged():
    history = _rounds_with_secondary(
        metrics=[0.70, 0.76, 0.761, 0.762],
        signatures=["baseline", "gradient_boosting", "feature_select", "n_estimators_tune"],
        secondary=[
            {"recall": 0.60},
            {"recall": 0.65},
            {"recall": 0.66},
            {"recall": 0.67},
        ],
    )

    verdict = evaluate_convergence(
        history,
        rel_tol=0.02,
        min_consecutive=2,
        secondary_metrics=["recall"],
    )

    assert verdict.status == "converged"
    assert verdict.secondary_regressions == ()


# @id TEST-AIDS-364
# @verifies REQ-AIDS-102
def test_TEST_AIDS_364_secondary_regression_never_upgrades_non_converged_status():
    # repetition_detected: round 4 repeats round 3 signature verbatim.
    history_repetition = _rounds_with_secondary(
        metrics=[0.70, 0.76, 0.761, 0.762],
        signatures=["baseline", "gradient_boosting", "n_estimators_tune", "n_estimators_tune"],
        secondary=[
            {"recall": 0.80},
            {"recall": 0.75},
            {"recall": 0.70},
            {"recall": 0.40},
        ],
    )
    verdict_repetition = evaluate_convergence(
        history_repetition,
        rel_tol=0.02,
        min_consecutive=2,
        secondary_metrics=["recall"],
    )
    assert verdict_repetition.status == "repetition_detected"
    assert verdict_repetition.secondary_regressions == ()

    # exhausted: no length-qualifying trailing run, actions_exhausted=True.
    history_exhausted = _rounds_with_secondary(
        metrics=[0.70, 0.90, 0.50],
        signatures=["a", "b", "c"],
        secondary=[{"recall": 0.80}, {"recall": 0.75}, {"recall": 0.10}],
    )
    verdict_exhausted = evaluate_convergence(
        history_exhausted,
        rel_tol=0.02,
        min_consecutive=2,
        actions_exhausted=True,
        secondary_metrics=["recall"],
    )
    assert verdict_exhausted.status == "exhausted"
    assert verdict_exhausted.secondary_regressions == ()

    # continue: same as above but actions_exhausted=False.
    verdict_continue = evaluate_convergence(
        history_exhausted,
        rel_tol=0.02,
        min_consecutive=2,
        actions_exhausted=False,
        secondary_metrics=["recall"],
    )
    assert verdict_continue.status == "continue"
    assert verdict_continue.secondary_regressions == ()


# @id TEST-AIDS-365
# @verifies REQ-AIDS-102
def test_TEST_AIDS_365_key_only_lookup_and_nonfinite_values_excluded():
    # Round 1 uses a metric name that collides with a dict method ("items");
    # a key-only lookup must still resolve it correctly (not dict.items).
    # Round 2 "items" value is NaN and must be excluded from peak/final
    # consideration rather than corrupting the max()/comparison.
    # Round 3 (the final round) has a present, non-regressed "items" value.
    history = _rounds_with_secondary(
        metrics=[0.750, 0.76, 0.761],
        signatures=["baseline", "gradient_boosting", "feature_select"],
        secondary=[
            {"items": 0.50},
            {"items": math.nan},
            {"items": 0.52},
        ],
    )

    verdict = evaluate_convergence(
        history,
        rel_tol=0.02,
        min_consecutive=2,
        secondary_metrics=["items"],
    )

    # peak across present values (round1=0.50, round3=0.52; round2 NaN is
    # excluded) is 0.52, equal to the final round own value -> no regression.
    assert verdict.status == "converged"
    assert verdict.secondary_regressions == ()

    # A custom Mapping whose __getitem__ raises must be treated as absent,
    # never propagating, for the round where it appears.
    class RaisingMapping(Mapping):
        def __getitem__(self, key):
            raise RuntimeError("boom")

        def __iter__(self):
            return iter(())

        def __len__(self):
            return 0

    history_raising = [
        Round(metric=0.750, action_signature="baseline", secondary_metrics={"recall": 0.9}),
        Round(metric=0.76, action_signature="gradient_boosting", secondary_metrics={"recall": 0.5}),
        Round(metric=0.761, action_signature="feature_select", secondary_metrics=RaisingMapping()),
    ]

    verdict_raising = evaluate_convergence(
        history_raising,
        rel_tol=0.02,
        min_consecutive=2,
        secondary_metrics=["recall"],
    )

    # The final round recall value is unresolvable (raises) -> treated as
    # absent at the final round -> "recall" contributes no regression.
    assert verdict_raising.status == "converged"
    assert verdict_raising.secondary_regressions == ()
