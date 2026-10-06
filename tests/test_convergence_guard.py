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
    # and round 2's duplicate-looking name is irrelevant to that pair.
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
