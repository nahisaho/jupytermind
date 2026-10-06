"""Spectral signal analysis: baseline correction and peak/FWHM detection.

Implements DES-AIDS-094 (REQ-AIDS-094, REQ-AIDS-095, REQ-AIDS-096): a
first-class module for spectral/scientific-signal analysis (GitHub #74)
operating on a generic 2-column ``x, y`` spectrum — baseline correction
(linear two-point fit or Asymmetric Least Squares), a
``scipy.signal.find_peaks``/``peak_widths`` wrapper returning
``{position, fwhm, prominence, height}`` dicts, and a thin helper that
builds a ``sensitivity.SensitivityPlan`` over
``(prominence_frac, window)`` so a peak-count stability check requires
no caller-written glue code around ``sensitivity.run_sensitivity``.
"""

from __future__ import annotations

import numbers
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import scipy.sparse
import scipy.sparse.linalg
from scipy.signal import find_peaks, peak_widths, savgol_filter

from ai_data_scientist.sensitivity import SensitivityPlan

_SUPPORTED_BASELINE_METHODS = ("linear", "asls")

# Fixed internal AsLS (Eilers & Boelens, 2005) parameters (DES-AIDS-094 /
# ADR-0112): not part of the public signature, so behavior is fully
# deterministic for a given x/y/method.
_ASLS_LAM = 1e5
_ASLS_P = 0.001
_ASLS_N_ITER = 10


# @id CODE-AIDS-146
# @implements REQ-AIDS-094 REQ-AIDS-095
# @design DES-AIDS-094
def _coerce_xy(
    x: Sequence[float], y: Sequence[float], *, min_len: int = 2
) -> tuple[np.ndarray, np.ndarray]:
    x_arr = np.array(x, dtype=float, copy=True)
    y_arr = np.array(y, dtype=float, copy=True)
    if x_arr.ndim != 1 or y_arr.ndim != 1:
        raise ValueError("x and y must be 1-D sequences.")
    if x_arr.shape[0] != y_arr.shape[0]:
        raise ValueError("x and y must have equal length.")
    if x_arr.shape[0] < min_len:
        raise ValueError(f"x/y must have at least {min_len} elements.")
    if not (np.all(np.isfinite(x_arr)) and np.all(np.isfinite(y_arr))):
        raise ValueError("x and y must contain only finite values.")
    return x_arr, y_arr


# @id CODE-AIDS-141
# @implements REQ-AIDS-094
# @design DES-AIDS-094
def _linear_baseline(x_arr: np.ndarray, y_arr: np.ndarray) -> np.ndarray:
    if x_arr[0] == x_arr[-1]:
        raise ValueError("x[0] and x[-1] must differ for a linear baseline fit.")
    slope = (y_arr[-1] - y_arr[0]) / (x_arr[-1] - x_arr[0])
    return y_arr[0] + slope * (x_arr - x_arr[0])


# @id CODE-AIDS-142
# @implements REQ-AIDS-094
# @design DES-AIDS-094
def _asls_baseline(y_arr: np.ndarray) -> np.ndarray:
    n = y_arr.shape[0]
    if n < 3:
        raise ValueError("AsLS baseline correction requires at least 3 elements.")
    diff_matrix = scipy.sparse.diags([1.0, -2.0, 1.0], offsets=[0, 1, 2], shape=(n - 2, n))
    penalty = _ASLS_LAM * (diff_matrix.T @ diff_matrix)
    weights = np.ones(n, dtype=float)
    baseline = y_arr
    for iteration in range(_ASLS_N_ITER):
        weight_matrix = scipy.sparse.diags(weights, 0, shape=(n, n))
        baseline = scipy.sparse.linalg.spsolve((weight_matrix + penalty).tocsc(), weights * y_arr)
        if iteration < _ASLS_N_ITER - 1:
            weights = np.where(y_arr > baseline, _ASLS_P, 1.0 - _ASLS_P)
    return baseline


# @id CODE-AIDS-143
# @implements REQ-AIDS-094
# @design DES-AIDS-094
def baseline_correct(x: Sequence[float], y: Sequence[float], method: str = "linear") -> np.ndarray:
    """Return ``y`` with an estimated baseline subtracted (GitHub #74).

    ``method="linear"`` fits a straight line through the first and last
    points; ``method="asls"`` uses Asymmetric Least Squares smoothing
    with fixed internal parameters (``lam=1e5``, ``p=0.001``,
    ``n_iter=10``). Neither ``x`` nor ``y`` is mutated.
    """
    if method not in _SUPPORTED_BASELINE_METHODS:
        raise ValueError(f"Unsupported baseline_correct method: {method!r}")
    min_len = 3 if method == "asls" else 2
    x_arr, y_arr = _coerce_xy(x, y, min_len=min_len)
    if method == "linear":
        baseline = _linear_baseline(x_arr, y_arr)
    else:
        baseline = _asls_baseline(y_arr)
    return y_arr - baseline


# @id CODE-AIDS-147
# @implements REQ-AIDS-095
# @design DES-AIDS-094
def _validate_window(window: Any, n: int) -> int:
    if not isinstance(window, numbers.Integral) or isinstance(window, bool):
        raise ValueError(  # noqa: TRY004 - ValueError required by REQ-AIDS-095
            "window must be an odd integer (bool is not accepted)."
        )
    window = int(window)
    if window % 2 == 0 or window < 5 or window > n:
        raise ValueError(f"window must be an odd integer in [5, {n}]; got {window}.")
    return window


# @id CODE-AIDS-144
# @implements REQ-AIDS-095
# @design DES-AIDS-094
def find_spectral_peaks(
    x: Sequence[float],
    y: Sequence[float],
    prominence_frac: float = 0.05,
    window: int | None = None,
) -> list[dict[str, float]]:
    """Return ``{position, fwhm, prominence, height}`` dicts for each peak.

    ``x`` must be strictly increasing and uniformly spaced. When
    ``window`` is given, ``y`` is Savitzky-Golay smoothed (``polyorder``
    fixed at 3) before detection, and every returned value is computed
    from that smoothed ``y`` (GitHub #74).
    """
    x_arr, y_arr = _coerce_xy(x, y, min_len=2)
    diffs = np.diff(x_arr)
    if not np.all(diffs > 0):
        raise ValueError("x must be strictly increasing.")
    dx = x_arr[1] - x_arr[0]
    if not np.allclose(diffs, dx, rtol=1e-6, atol=0.0):
        raise ValueError("x must be uniformly spaced.")

    n = x_arr.shape[0]
    if window is not None:
        window = _validate_window(window, n)
        y_arr = savgol_filter(y_arr, window_length=window, polyorder=3)

    y_range = y_arr.max() - y_arr.min()
    indices, properties = find_peaks(y_arr, prominence=prominence_frac * y_range)
    if indices.size == 0:
        return []

    widths_samples, *_rest = peak_widths(y_arr, indices, rel_height=0.5)

    peaks = []
    for position_index, width_samples, prominence in zip(
        indices, widths_samples, properties["prominences"], strict=True
    ):
        peaks.append(
            {
                "position": float(x_arr[position_index]),
                "fwhm": float(width_samples * dx),
                "prominence": float(prominence),
                "height": float(y_arr[position_index]),
            }
        )
    return peaks


# @id CODE-AIDS-145
# @implements REQ-AIDS-096
# @design DES-AIDS-094
def build_peak_sensitivity_plan(
    x: Sequence[float],
    y: Sequence[float],
    prominence_fracs: list[float],
    windows: list[int | None],
    target_claim: str,
    max_runs: int = 100,
) -> tuple[SensitivityPlan, Callable[..., float]]:
    """Return a ``(SensitivityPlan, analysis_fn)`` pair for peak-count stability.

    ``analysis_fn`` calls :func:`find_spectral_peaks` with the captured
    ``x``/``y`` and the specification's ``prominence_frac``/``window``,
    returning the peak count as a ``float`` — so the pair can be passed
    unchanged to ``sensitivity.run_sensitivity`` with no caller-written
    glue code (GitHub #74).
    """
    plan = SensitivityPlan(
        target_claim=target_claim,
        parameter_grid={"prominence_frac": prominence_fracs, "window": windows},
        max_runs=max_runs,
    )

    def analysis_fn(*, prominence_frac: float, window: int | None) -> float:
        peaks = find_spectral_peaks(x, y, prominence_frac=prominence_frac, window=window)
        return float(len(peaks))

    return plan, analysis_fn
