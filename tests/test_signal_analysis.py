"""Tests for the signal_analysis module (REQ-AIDS-094, REQ-AIDS-095, REQ-AIDS-096).

GitHub #74: baseline correction, spectral peak/FWHM detection, and a
glue-free sensitivity.SensitivityPlan helper for 2-column x/y spectra.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ai_data_scientist.sensitivity import SensitivityBudgetExceededError, run_sensitivity
from ai_data_scientist.signal_analysis import (
    baseline_correct,
    build_peak_sensitivity_plan,
    find_spectral_peaks,
)


def _gaussian(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    return amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)


_FWHM_FACTOR = 2.0 * math.sqrt(2.0 * math.log(2.0))


# ---------------------------------------------------------------------------
# REQ-AIDS-094: baseline_correct
# ---------------------------------------------------------------------------


# @id TEST-AIDS-294
# @verifies REQ-AIDS-094
def test_TEST_AIDS_294_linear_baseline_correction_removes_slope():
    x = np.linspace(-50, 50, 1001)
    gaussian = _gaussian(x, amplitude=10.0, center=0.0, sigma=3.0)
    y = gaussian + 0.01 * x + 5.0
    x_copy, y_copy = x.copy(), y.copy()

    corrected = np.asarray(baseline_correct(x, y, method="linear"))

    assert abs(corrected[0]) < 1e-9
    assert abs(corrected[-1]) < 1e-9
    assert np.max(np.abs(corrected - gaussian)) <= 0.1
    np.testing.assert_array_equal(x, x_copy)
    np.testing.assert_array_equal(y, y_copy)


# @id TEST-AIDS-295
# @verifies REQ-AIDS-094
def test_TEST_AIDS_295_asls_baseline_correction_preserves_peak_removes_curvature():
    x = np.linspace(0, 200, 1001)
    baseline = 0.0005 * (x - 100.0) ** 2 + 2.0
    peak = _gaussian(x, amplitude=20.0, center=100.0, sigma=5.0)
    y = baseline + peak
    x_copy, y_copy = x.copy(), y.copy()

    corrected = np.asarray(baseline_correct(x, y, method="asls"))

    far_from_peak = np.abs(x - 100.0) >= 40.0
    assert np.mean(np.abs(corrected[far_from_peak])) <= 1.0
    assert 19.0 <= np.max(corrected) <= 21.0
    np.testing.assert_array_equal(x, x_copy)
    np.testing.assert_array_equal(y, y_copy)


# @id TEST-AIDS-296
# @verifies REQ-AIDS-094
def test_TEST_AIDS_296_unsupported_method_raises_without_mutating_inputs():
    x = np.linspace(0, 10, 50)
    y = np.sin(x)
    x_copy, y_copy = x.copy(), y.copy()

    with pytest.raises(ValueError):
        baseline_correct(x, y, method="unsupported-value")

    np.testing.assert_array_equal(x, x_copy)
    np.testing.assert_array_equal(y, y_copy)


# @id TEST-AIDS-297
# @verifies REQ-AIDS-094
def test_TEST_AIDS_297_accepts_plain_lists_without_pandas():
    x = list(np.linspace(-10, 10, 101))
    y = [v * v for v in x]

    corrected = baseline_correct(x, y, method="linear")

    assert len(corrected) == len(y)
    # indexable / iterable like a 1-D array
    assert next(iter(corrected)) == corrected[0]


# ---------------------------------------------------------------------------
# REQ-AIDS-095: find_spectral_peaks
# ---------------------------------------------------------------------------


def _two_peak_spectrum():
    x = np.linspace(0, 100, 1001)
    peak1 = _gaussian(x, amplitude=5.0, center=30.0, sigma=2.0)
    peak2 = _gaussian(x, amplitude=8.0, center=70.0, sigma=3.0)
    return x, peak1, peak2


# @id TEST-AIDS-298
# @verifies REQ-AIDS-095
def test_TEST_AIDS_298_detects_two_clean_peaks_with_fwhm_prominence_height():
    x, peak1, peak2 = _two_peak_spectrum()
    y = peak1 + peak2

    peaks = find_spectral_peaks(x, y, prominence_frac=0.05)

    assert len(peaks) == 2
    fwhm1 = _FWHM_FACTOR * 2.0
    fwhm2 = _FWHM_FACTOR * 3.0

    first, second = peaks
    assert {"position", "fwhm", "prominence", "height"} == set(first.keys())

    assert abs(first["position"] - 30.0) <= 0.1
    assert abs(first["fwhm"] - fwhm1) <= 0.05 * fwhm1
    assert abs(first["height"] - 5.0) <= 0.01 * 5.0
    assert abs(first["prominence"] - first["height"]) <= 0.01 * first["height"]

    assert abs(second["position"] - 70.0) <= 0.1
    assert abs(second["fwhm"] - fwhm2) <= 0.05 * fwhm2
    assert abs(second["height"] - 8.0) <= 0.01 * 8.0
    assert abs(second["prominence"] - second["height"]) <= 0.01 * second["height"]


# @id TEST-AIDS-299
# @verifies REQ-AIDS-095
def test_TEST_AIDS_299_low_prominence_peak_is_filtered_out():
    x, _peak1, peak2 = _two_peak_spectrum()
    small_peak1 = _gaussian(x, amplitude=0.1, center=30.0, sigma=2.0)
    y = small_peak1 + peak2

    peaks = find_spectral_peaks(x, y, prominence_frac=0.05)

    assert len(peaks) == 1
    assert abs(peaks[0]["position"] - 70.0) <= 0.1


# @id TEST-AIDS-300
# @verifies REQ-AIDS-095
def test_TEST_AIDS_300_savgol_smoothing_recovers_peaks_from_noise():
    x, peak1, peak2 = _two_peak_spectrum()
    noise = np.random.default_rng(42).normal(scale=0.15, size=x.shape)
    y = peak1 + peak2 + noise

    peaks = find_spectral_peaks(x, y, prominence_frac=0.05, window=11)

    assert len(peaks) == 2
    assert abs(peaks[0]["position"] - 30.0) <= 0.5
    assert abs(peaks[1]["position"] - 70.0) <= 0.5


# @id TEST-AIDS-301
# @verifies REQ-AIDS-095
def test_TEST_AIDS_301_invalid_window_values_raise_value_error():
    x, peak1, peak2 = _two_peak_spectrum()
    noise = np.random.default_rng(42).normal(scale=0.15, size=x.shape)
    y = peak1 + peak2 + noise

    with pytest.raises(ValueError):
        find_spectral_peaks(x, y, prominence_frac=0.05, window=10)
    with pytest.raises(ValueError):
        find_spectral_peaks(x, y, prominence_frac=0.05, window=3)
    with pytest.raises(ValueError):
        find_spectral_peaks(x, y, prominence_frac=0.05, window=len(y) + 2)


# @id TEST-AIDS-302
# @verifies REQ-AIDS-095
def test_TEST_AIDS_302_flat_spectrum_returns_empty_list():
    x = np.linspace(0, 10, 101)
    y = np.full_like(x, 3.0)

    peaks = find_spectral_peaks(x, y)

    assert peaks == []


# @id TEST-AIDS-303
# @verifies REQ-AIDS-095
def test_TEST_AIDS_303_non_uniform_x_raises_value_error():
    x = np.concatenate([np.linspace(0, 10, 50), np.linspace(10.5, 20, 50)])
    y = np.sin(x)

    with pytest.raises(ValueError):
        find_spectral_peaks(x, y)


# ---------------------------------------------------------------------------
# REQ-AIDS-096: build_peak_sensitivity_plan
# ---------------------------------------------------------------------------


# @id TEST-AIDS-304
# @verifies REQ-AIDS-096
def test_TEST_AIDS_304_plan_shape_and_stable_classification():
    x, peak1, peak2 = _two_peak_spectrum()
    y = peak1 + peak2
    prominence_fracs = [0.05, 0.1, 0.2]
    windows = [None, 11]

    plan, analysis_fn = build_peak_sensitivity_plan(
        x, y, prominence_fracs, windows, target_claim="peak_count"
    )

    assert plan.target_claim == "peak_count"
    assert plan.parameter_grid == {"prominence_frac": prominence_fracs, "window": windows}
    assert plan.max_runs == 100

    report = run_sensitivity(plan, analysis_fn)

    assert report.target_claim == "peak_count"
    assert len(report.results) == 6
    assert report.classification == "stable"


# @id TEST-AIDS-305
# @verifies REQ-AIDS-096
def test_TEST_AIDS_305_analysis_fn_forwards_kwargs_to_find_spectral_peaks(monkeypatch):
    x, peak1, peak2 = _two_peak_spectrum()
    y = peak1 + peak2
    calls = []

    def _stub(x_arg, y_arg, prominence_frac=0.05, window=None):
        calls.append({"x": x_arg, "y": y_arg, "prominence_frac": prominence_frac, "window": window})
        return [{"position": 0.0, "fwhm": 0.0, "prominence": 0.0, "height": 0.0}] * 3

    monkeypatch.setattr("ai_data_scientist.signal_analysis.find_spectral_peaks", _stub)

    _plan, analysis_fn = build_peak_sensitivity_plan(x, y, [0.1], [11], target_claim="peak_count")

    result = analysis_fn(prominence_frac=0.1, window=11)

    assert result == 3.0
    assert len(calls) == 1
    np.testing.assert_array_equal(calls[0]["x"], x)
    np.testing.assert_array_equal(calls[0]["y"], y)
    assert calls[0]["prominence_frac"] == 0.1
    assert calls[0]["window"] == 11


# @id TEST-AIDS-306
# @verifies REQ-AIDS-096
def test_TEST_AIDS_306_over_budget_grid_raises_sensitivity_budget_error():
    x, peak1, peak2 = _two_peak_spectrum()
    y = peak1 + peak2

    plan, analysis_fn = build_peak_sensitivity_plan(
        x, y, [0.05, 0.1, 0.2], [None, 11], target_claim="peak_count", max_runs=5
    )

    with pytest.raises(SensitivityBudgetExceededError):
        run_sensitivity(plan, analysis_fn)
