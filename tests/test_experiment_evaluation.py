"""Tests for A/B testing and experiment evaluation (REQ-AIDS-022)."""

import pandas as pd
from scipy import stats as scipy_stats

from ai_data_scientist.experiment_evaluation import evaluate_experiment


# @id TEST-AIDS-022
# @verifies REQ-AIDS-022
def test_TEST_AIDS_022():
    control = pd.Series([10.1, 9.8, 10.3, 9.9, 10.0, 9.7, 10.2, 9.95, 10.05, 9.85])
    treatment = pd.Series([12.1, 11.8, 12.3, 11.9, 12.0, 11.7, 12.2, 11.95, 12.05, 11.85])

    result = evaluate_experiment(control, treatment, test="ttest")

    reference_stat, reference_p = scipy_stats.ttest_ind(control, treatment)

    assert abs(result.statistic - reference_stat) < 1e-6
    assert abs(result.p_value - reference_p) < 1e-6
    assert isinstance(result.interpretation, str) and len(result.interpretation) > 0

    ja_result = evaluate_experiment(control, treatment, test="ttest", language="ja")
    assert isinstance(ja_result.interpretation, str) and len(ja_result.interpretation) > 0
