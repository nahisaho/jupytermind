"""Tests for reusable sensitivity-analysis plans (REQ-AIDS-056)."""

import pytest

from ai_data_scientist.sensitivity import (
    SensitivityBudgetExceededError,
    SensitivityPlan,
    run_sensitivity,
)


# @id TEST-AIDS-096
# @verifies REQ-AIDS-056
def test_TEST_AIDS_096_specifications_enumerates_full_grid():
    plan = SensitivityPlan(parameter_grid={"model": ["ols", "ridge"], "subset": ["all", "recent"]})
    specs = plan.specifications()
    assert len(specs) == 4
    assert {"model": "ols", "subset": "all"} in specs


# @id TEST-AIDS-097
# @verifies REQ-AIDS-056
def test_TEST_AIDS_097_grid_exceeding_budget_raises():
    plan = SensitivityPlan(parameter_grid={"x": list(range(10)), "y": list(range(10))}, max_runs=5)
    with pytest.raises(SensitivityBudgetExceededError):
        plan.specifications()


# @id TEST-AIDS-098
# @verifies REQ-AIDS-056
def test_TEST_AIDS_098_stable_conclusion_across_specifications():
    plan = SensitivityPlan(parameter_grid={"model": ["ols", "ridge", "lasso"]})

    def analysis_fn(model):
        return {"ols": 1.00, "ridge": 1.02, "lasso": 0.98}[model]

    report = run_sensitivity(plan, analysis_fn, stability_tolerance=0.1)
    assert report.stable is True
    assert len(report.results) == 3


# @id TEST-AIDS-099
# @verifies REQ-AIDS-056
def test_TEST_AIDS_099_unstable_conclusion_flagged_with_deviation():
    plan = SensitivityPlan(parameter_grid={"model": ["ols", "outlier_sensitive"]})

    def analysis_fn(model):
        return {"ols": 1.0, "outlier_sensitive": 5.0}[model]

    report = run_sensitivity(plan, analysis_fn, stability_tolerance=0.2)
    assert report.stable is False
    assert report.max_relative_deviation == pytest.approx(4.0)


# @id TEST-AIDS-205
# @verifies REQ-AIDS-056
def test_TEST_AIDS_205_sign_reversal_is_classified_reversed_not_stable():
    """GitHub #53: a large same-signed AUC drop whose relative deviation
    stays within the default tolerance must not be classified "reversed",
    and a sign flip must be classified "reversed" regardless of how small
    the relative deviation looks."""
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    def analysis_fn(seed):
        return [0.0001, -0.00001][seed]

    report = run_sensitivity(plan, analysis_fn)
    assert report.classification == "reversed"
    assert report.sign_consistent is False
    assert report.stable is False


# @id TEST-AIDS-206
# @verifies REQ-AIDS-056
def test_TEST_AIDS_206_same_signed_small_improvement_is_attenuated_not_reversed():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    def analysis_fn(seed):
        return [2e-05, 5e-05][seed]

    report = run_sensitivity(plan, analysis_fn, stability_tolerance=0.2)
    assert report.classification == "attenuated"
    assert report.sign_consistent is True


# @id TEST-AIDS-207
# @verifies REQ-AIDS-056
def test_TEST_AIDS_207_zero_baseline_is_not_comparable_without_absolute_tolerance():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    def analysis_fn(seed):
        return [0.0, 0.15][seed]

    report = run_sensitivity(plan, analysis_fn)
    assert report.classification == "not_comparable"


# @id TEST-AIDS-208
# @verifies REQ-AIDS-056
def test_TEST_AIDS_208_absolute_tolerance_flags_large_same_signed_drop():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    def analysis_fn(seed):
        return [0.959027, 0.80][seed]

    lenient = run_sensitivity(plan, analysis_fn)
    assert lenient.classification == "stable"

    strict = run_sensitivity(plan, analysis_fn, absolute_tolerance=0.05)
    assert strict.classification == "attenuated"
    assert strict.magnitude_criterion == "absolute_tolerance"
    assert strict.max_absolute_deviation == pytest.approx(0.159027)


# @id TEST-AIDS-209
# @verifies REQ-AIDS-056
def test_TEST_AIDS_209_evaluator_failure_is_recorded_not_aborting():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1, 2]})

    def analysis_fn(seed):
        if seed == 1:
            raise ValueError("boom")
        return [1.0, None, 1.02][seed]

    report = run_sensitivity(plan, analysis_fn)
    assert len(report.results) == 3
    assert report.results[1].failed is True
    assert "boom" in report.results[1].error
    assert report.results[0].failed is False
    assert report.results[2].failed is False
    assert report.classification == "stable"


# @id TEST-AIDS-213
# @verifies REQ-AIDS-056
def test_TEST_AIDS_213_empty_specification_grid_is_not_comparable_and_not_stable():
    plan = SensitivityPlan(parameter_grid={"seed": []})

    report = run_sensitivity(plan, lambda seed: seed)

    assert report.results == ()
    assert report.classification == "not_comparable"
    assert report.stable is False


# @id TEST-AIDS-214
# @verifies REQ-AIDS-056
def test_TEST_AIDS_214_all_specifications_failing_is_not_comparable_and_not_stable():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    def analysis_fn(seed):
        raise ValueError("boom")

    report = run_sensitivity(plan, analysis_fn)

    assert len(report.results) == 2
    assert all(r.failed for r in report.results)
    assert report.classification == "not_comparable"
    assert report.stable is False


# @id TEST-AIDS-291
# @verifies REQ-AIDS-056
def test_TEST_AIDS_291_non_finite_values_are_recorded_as_failed_not_stable():
    plan = SensitivityPlan(parameter_grid={"seed": [0, 1]})

    nan_report = run_sensitivity(plan, lambda seed: float("nan"))
    assert all(r.failed for r in nan_report.results)
    assert nan_report.classification == "not_comparable"
    assert nan_report.stable is False

    inf_report = run_sensitivity(plan, lambda seed: float("inf"))
    assert all(r.failed for r in inf_report.results)
    assert inf_report.classification == "not_comparable"
    assert inf_report.stable is False
