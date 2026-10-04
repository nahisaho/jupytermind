"""Reusable sensitivity-analysis plans for conclusion-stability testing.

Implements DES-AIDS-044 (REQ-AIDS-056): runs an analysis function
across a grid of alternative specifications (model/parameter/subset
choices) and reports whether the conclusion direction/magnitude is
stable, bounded by an explicit evaluation budget.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class SensitivityBudgetExceededError(RuntimeError):
    """Raised when a specification grid would exceed the run budget."""


# @id CODE-AIDS-079
# @implements REQ-AIDS-056
# @design DES-AIDS-044
@dataclass(frozen=True)
class SensitivityPlan:
    """A grid of alternative specifications to re-run an analysis under."""

    parameter_grid: dict[str, list[Any]]
    max_runs: int = 100

    def specifications(self) -> tuple[dict[str, Any], ...]:
        """Enumerate the Cartesian product of ``parameter_grid`` values."""
        if not self.parameter_grid:
            return ({},)
        keys = list(self.parameter_grid.keys())
        combos = itertools.product(*(self.parameter_grid[k] for k in keys))
        specs = tuple(dict(zip(keys, combo, strict=True)) for combo in combos)
        if len(specs) > self.max_runs:
            raise SensitivityBudgetExceededError(
                f"Specification grid has {len(specs)} combinations, "
                f"exceeding max_runs={self.max_runs}."
            )
        return specs


@dataclass(frozen=True)
class SensitivityResult:
    """Outcome of one specification run plus the overall stability verdict."""

    specification: dict[str, Any]
    value: float
    # GitHub #53 / REQ-AIDS-056: an evaluator failure is recorded as a
    # failed specification instead of aborting the remaining plan.
    failed: bool = False
    error: str | None = None


@dataclass(frozen=True)
class SensitivityReport:
    """Aggregated result of running a plan: all outcomes and a stability verdict."""

    results: tuple[SensitivityResult, ...] = field(default_factory=tuple)
    baseline_value: float | None = None
    stable: bool = True
    max_relative_deviation: float = 0.0
    # GitHub #53: REQ-AIDS-056 requires classifying the conclusion as one of
    # "stable", "attenuated", "reversed", or "not_comparable" rather than a
    # bare relative-deviation threshold, which conflates a large same-signed
    # change with a sign reversal and mishandles a near-zero baseline.
    classification: str = "stable"
    max_absolute_deviation: float = 0.0
    sign_consistent: bool | None = None
    magnitude_criterion: str = "relative_tolerance"


def _sign(value: float) -> int:
    if value == 0:
        return 0
    return 1 if value > 0 else -1


# @id CODE-AIDS-127
# @implements REQ-AIDS-056
# @design DES-AIDS-044
def _classify_stability(
    successful: list[SensitivityResult],
    *,
    baseline_value: float,
    max_relative_deviation: float,
    max_absolute_deviation: float,
    stability_tolerance: float,
    absolute_tolerance: float | None,
) -> tuple[bool, str]:
    """Return ``(sign_consistent, classification)`` for a non-empty ``successful``.

    GitHub #53: classifies as ``"reversed"`` whenever successful values
    disagree in sign (instead of a bare relative-deviation threshold, which
    can mark a large same-signed drop "stable" and a small sign-consistent
    change "unstable"), as ``"not_comparable"`` when the baseline is ``0``
    and no ``absolute_tolerance`` was supplied (undefined relative
    deviation), otherwise as ``"stable"``/``"attenuated"`` by whichever of
    ``absolute_tolerance``/``stability_tolerance`` is configured.
    """
    signs = {_sign(r.value) for r in successful} - {0}
    sign_consistent = len(signs) <= 1

    if absolute_tolerance is not None:
        within_tolerance = max_absolute_deviation <= absolute_tolerance
    else:
        within_tolerance = max_relative_deviation <= stability_tolerance

    if not sign_consistent:
        return sign_consistent, "reversed"
    if baseline_value == 0 and absolute_tolerance is None:
        return sign_consistent, "not_comparable"
    if within_tolerance:
        return sign_consistent, "stable"
    return sign_consistent, "attenuated"


# @id CODE-AIDS-080
# @implements REQ-AIDS-056
# @design DES-AIDS-044
def run_sensitivity(
    plan: SensitivityPlan,
    analysis_fn: Callable[..., float],
    stability_tolerance: float = 0.2,
    absolute_tolerance: float | None = None,
) -> SensitivityReport:
    """Run ``analysis_fn`` across every specification in ``plan``.

    ``analysis_fn`` is called once per specification as
    ``analysis_fn(**specification)`` and must return a numeric
    conclusion-relevant value; an exception it raises, or a non-finite
    (``NaN``/``inf``) return value, is recorded on that specification's
    ``SensitivityResult.failed``/``error`` instead of aborting the
    remaining plan (REQ-AIDS-056). The first specification's value is
    treated as the baseline.

    The report's ``classification`` is one of:

    - ``"reversed"``: at least one successful result's value has the
      opposite sign from another (direction of the conclusion flips).
    - ``"not_comparable"``: the baseline value is ``0`` and no
      ``absolute_tolerance`` was given, so a relative deviation is
      undefined (GitHub #53); or every specification failed.
    - ``"stable"``: all successful values share a sign and the maximum
      deviation from the baseline is within tolerance. Deviation is
      measured by ``absolute_tolerance`` (against
      ``max_absolute_deviation``) when given, otherwise by
      ``stability_tolerance`` (against ``max_relative_deviation``); the
      criterion actually used is recorded in ``magnitude_criterion``.
    - ``"attenuated"``: all successful values share a sign but the
      deviation exceeds the configured tolerance.

    ``stable`` (bool) is kept for backward compatibility and is ``True``
    exactly when ``classification == "stable"``.
    """
    specifications = plan.specifications()
    results = []
    for spec in specifications:
        try:
            value = float(analysis_fn(**spec))
            if not math.isfinite(value):
                # GitHub #53 follow-up (rubber-duck review): a non-finite
                # value (NaN/inf) is not a meaningfully comparable
                # conclusion value; treat it as a failed specification
                # rather than letting it masquerade as "stable".
                raise ValueError(f"analysis_fn returned a non-finite value: {value!r}")
        except Exception as exc:  # noqa: BLE001 - recorded, not re-raised
            results.append(
                SensitivityResult(
                    specification=spec, value=float("nan"), failed=True, error=str(exc)
                )
            )
        else:
            results.append(SensitivityResult(specification=spec, value=value))
    results = tuple(results)

    if not results:
        return SensitivityReport(
            results=(), baseline_value=None, stable=False, classification="not_comparable"
        )

    successful = [r for r in results if not r.failed]
    if not successful:
        return SensitivityReport(
            results=results, baseline_value=None, stable=False, classification="not_comparable"
        )

    baseline_value = successful[0].value
    magnitude_criterion = (
        "absolute_tolerance" if absolute_tolerance is not None else "relative_tolerance"
    )

    max_relative_deviation = 0.0
    max_absolute_deviation = 0.0
    for result in successful[1:]:
        absolute_deviation = abs(result.value - baseline_value)
        if baseline_value == 0:
            relative_deviation = absolute_deviation
        else:
            relative_deviation = absolute_deviation / abs(baseline_value)
        max_relative_deviation = max(max_relative_deviation, relative_deviation)
        max_absolute_deviation = max(max_absolute_deviation, absolute_deviation)

    sign_consistent, classification = _classify_stability(
        successful,
        baseline_value=baseline_value,
        max_relative_deviation=max_relative_deviation,
        max_absolute_deviation=max_absolute_deviation,
        stability_tolerance=stability_tolerance,
        absolute_tolerance=absolute_tolerance,
    )

    return SensitivityReport(
        results=results,
        baseline_value=baseline_value,
        stable=classification == "stable",
        max_relative_deviation=max_relative_deviation,
        classification=classification,
        max_absolute_deviation=max_absolute_deviation,
        sign_consistent=sign_consistent,
        magnitude_criterion=magnitude_criterion,
    )
