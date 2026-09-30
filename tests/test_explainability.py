"""Tests for model explainability (REQ-AIDS-021)."""

import numpy as np
import pandas as pd

from ai_data_scientist.explainability import explain_model
from ai_data_scientist.ml_modeling import train_model


# @id TEST-AIDS-021
# @verifies REQ-AIDS-021
def test_TEST_AIDS_021():
    rng = np.random.default_rng(0)
    n = 80
    important = np.arange(n) % 2
    noise = rng.integers(0, 5, size=n)
    df = pd.DataFrame({"important": important, "noise": noise, "label": important})

    result = train_model(df, target="label", model_type="classification", test_size=0.2)

    explanation = explain_model(result.model, feature_names=["important", "noise"])

    reference_importances = dict(zip(["important", "noise"], result.model.feature_importances_))
    reference_top = max(reference_importances, key=reference_importances.get)

    assert explanation.ranking[0] == reference_top
    assert set(explanation.feature_importances) == {"important", "noise"}
