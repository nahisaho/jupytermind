"""Reusable sensitivity-analysis plans for conclusion-stability testing.

Implements DES-AIDS-044 (REQ-AIDS-056): runs an analysis function
across a grid of alternative specifications (model/parameter/subset
choices) and reports whether the conclusion direction/magnitude is
stable, bounded by an explicit evaluation budget.
"""

from __future__ import annotations

import itertools
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


@dataclass(frozen=True)
class SensitivityReport:
    """Aggregated result of running a plan: all outcomes and a stability verdict."""

    results: tuple[SensitivityResult, ...] = field(default_factory=tuple)
    baseline_value: float | None = None
    stable: bool = True
    max_relative_deviation: float = 0.0


# @id CODE-AIDS-080
# @implements REQ-AIDS-056
# @design DES-AIDS-044
def run_sensitivity(
    plan: SensitivityPlan,
    analysis_fn: Callable[..., float],
    stability_tolerance: float = 0.2,
) -> SensitivityReport:
    """Run ``analysis_fn`` across every specification in ``plan``.

    ``analysis_fn`` is called once per specification as
    ``analysis_fn(**specification)`` and must return a numeric
    conclusion-relevant value. The first specification's value is
    treated as the baseline; the report is "stable" only if every
    other outcome's relative deviation from the baseline is within
    ``stability_tolerance``.
    """
    specifications = plan.specifications()
    results = tuple(
        SensitivityResult(specification=spec, value=float(analysis_fn(**spec)))
        for spec in specifications
    )
    if not results:
        return SensitivityReport(results=(), baseline_value=None, stable=True)

    baseline_value = results[0].value
    max_relative_deviation = 0.0
    for result in results[1:]:
        if baseline_value == 0:
            deviation = abs(result.value - baseline_value)
        else:
            deviation = abs(result.value - baseline_value) / abs(baseline_value)
        max_relative_deviation = max(max_relative_deviation, deviation)

    stable = max_relative_deviation <= stability_tolerance
    return SensitivityReport(
        results=results,
        baseline_value=baseline_value,
        stable=stable,
        max_relative_deviation=max_relative_deviation,
    )
