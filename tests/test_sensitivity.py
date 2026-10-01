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
