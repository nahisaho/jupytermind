"""Reusable sensitivity-analysis plans for conclusion-stability testing.

Implements DES-AIDS-044 (REQ-AIDS-056): runs an analysis function
across a grid of alternative specifications (model/parameter/subset
choices) for a named target claim and reports whether the conclusion
direction/magnitude is stable, bounded by an explicit evaluation budget.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class SensitivityBudgetExceededError(RuntimeError):
    """Raised when a specification grid would exceed the run budget."""


_UNSET = object()


def _validate_target_claim(target_claim: str) -> None:
    if not isinstance(target_claim, str):
        raise TypeError("target_claim must be a string.")
    if not target_claim.strip():
        raise ValueError("target_claim must be a non-empty string.")


# @id CODE-AIDS-079
# @implements REQ-AIDS-056
# @design DES-AIDS-044
@dataclass(frozen=True, init=False)
class SensitivityPlan:
    """A grid of alternative specifications to re-run an analysis under."""

    target_claim: str
    parameter_grid: dict[str, list[Any]]
    max_runs: int = 100

    def __init__(
        self,
        *args: Any,
        target_claim: Any = _UNSET,
        parameter_grid: Any = _UNSET,
        max_runs: Any = _UNSET,
    ) -> None:
        if args and isinstance(args[0], str):
            if len(args) > 3:
                raise TypeError("SensitivityPlan accepts at most 3 positional arguments.")
            if target_claim is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for target_claim.")
            if len(args) > 1 and parameter_grid is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for parameter_grid.")
            if len(args) > 2 and max_runs is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for max_runs.")
            target_claim = args[0]
            if len(args) > 1:
                parameter_grid = args[1]
            if len(args) > 2:
                max_runs = args[2]
        elif args:
            if len(args) > 3:
                raise TypeError("SensitivityPlan accepts at most 3 positional arguments.")
            if parameter_grid is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for parameter_grid.")
            if len(args) > 1 and max_runs is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for max_runs.")
            if len(args) > 2 and target_claim is not _UNSET:
                raise TypeError("SensitivityPlan got multiple values for target_claim.")
            parameter_grid = args[0]
            if len(args) > 1:
                max_runs = args[1]
            if len(args) > 2:
                target_claim = args[2]
        if target_claim is _UNSET:
            raise TypeError("SensitivityPlan requires target_claim.")
        if parameter_grid is _UNSET:
            raise TypeError("SensitivityPlan requires parameter_grid.")
        if max_runs is _UNSET:
            max_runs = 100
        object.__setattr__(self, "target_claim", target_claim)
        object.__setattr__(self, "parameter_grid", parameter_grid)
        object.__setattr__(self, "max_runs", max_runs)
        _validate_target_claim(self.target_claim)

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


@dataclass(frozen=True, init=False)
class SensitivityResult:
    """Outcome of one specification run plus the overall stability verdict."""

    target_claim: str
    specification: dict[str, Any]
    value: float
    # GitHub #53 / REQ-AIDS-056: an evaluator failure is recorded as a
    # failed specification instead of aborting the remaining plan.
    failed: bool = False
    error: str | None = None

    def __init__(
        self,
        *args: Any,
        target_claim: Any = _UNSET,
        specification: Any = _UNSET,
        value: Any = _UNSET,
        failed: Any = _UNSET,
        error: Any = _UNSET,
    ) -> None:
        if args and isinstance(args[0], str):
            if len(args) > 5:
                raise TypeError("SensitivityResult accepts at most 5 positional arguments.")
            if target_claim is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for target_claim.")
            if len(args) > 1 and specification is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for specification.")
            if len(args) > 2 and value is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for value.")
            if len(args) > 3 and failed is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for failed.")
            if len(args) > 4 and error is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for error.")
            target_claim = args[0]
            if len(args) > 1:
                specification = args[1]
            if len(args) > 2:
                value = args[2]
            if len(args) > 3:
                failed = args[3]
            if len(args) > 4:
                error = args[4]
        elif args:
            if len(args) > 5:
                raise TypeError("SensitivityResult accepts at most 5 positional arguments.")
            if specification is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for specification.")
            if len(args) > 1 and value is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for value.")
            if len(args) > 2 and failed is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for failed.")
            if len(args) > 3 and error is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for error.")
            if len(args) > 4 and target_claim is not _UNSET:
                raise TypeError("SensitivityResult got multiple values for target_claim.")
            specification = args[0]
            if len(args) > 1:
                value = args[1]
            if len(args) > 2:
                failed = args[2]
            if len(args) > 3:
                error = args[3]
            if len(args) > 4:
                target_claim = args[4]
        if target_claim is _UNSET:
            raise TypeError("SensitivityResult requires target_claim.")
        if specification is _UNSET:
            raise TypeError("SensitivityResult requires specification.")
        if value is _UNSET:
            raise TypeError("SensitivityResult requires value.")
        if failed is _UNSET:
            failed = False
        if error is _UNSET:
            error = None
        object.__setattr__(self, "target_claim", target_claim)
        object.__setattr__(self, "specification", specification)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "failed", failed)
        object.__setattr__(self, "error", error)
        _validate_target_claim(self.target_claim)


@dataclass(frozen=True, init=False)
class SensitivityReport:
    """Aggregated result of running a plan: all outcomes and a stability verdict."""

    target_claim: str
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

    def __init__(
        self,
        *args: Any,
        target_claim: Any = _UNSET,
        results: Any = _UNSET,
        baseline_value: Any = _UNSET,
        stable: Any = _UNSET,
        max_relative_deviation: Any = _UNSET,
        classification: Any = _UNSET,
        max_absolute_deviation: Any = _UNSET,
        sign_consistent: Any = _UNSET,
        magnitude_criterion: Any = _UNSET,
    ) -> None:
        fields = (
            "results",
            "baseline_value",
            "stable",
            "max_relative_deviation",
            "classification",
            "max_absolute_deviation",
            "sign_consistent",
            "magnitude_criterion",
        )
        values = {
            "results": results,
            "baseline_value": baseline_value,
            "stable": stable,
            "max_relative_deviation": max_relative_deviation,
            "classification": classification,
            "max_absolute_deviation": max_absolute_deviation,
            "sign_consistent": sign_consistent,
            "magnitude_criterion": magnitude_criterion,
        }
        if args and isinstance(args[0], str):
            if len(args) > 9:
                raise TypeError("SensitivityReport accepts at most 9 positional arguments.")
            if target_claim is not _UNSET:
                raise TypeError("SensitivityReport got multiple values for target_claim.")
            for name, value in zip(fields, args[1:], strict=False):
                if values[name] is not _UNSET:
                    raise TypeError(f"SensitivityReport got multiple values for {name}.")
            target_claim = args[0]
            for name, value in zip(fields, args[1:], strict=False):
                values[name] = value
        elif args:
            if len(args) > 9:
                raise TypeError("SensitivityReport accepts at most 9 positional arguments.")
            for name, value in zip(fields, args[: len(fields)], strict=False):
                if values[name] is not _UNSET:
                    raise TypeError(f"SensitivityReport got multiple values for {name}.")
            for name, value in zip(fields, args[: len(fields)], strict=False):
                values[name] = value
            if len(args) > len(fields):
                if target_claim is not _UNSET:
                    raise TypeError("SensitivityReport got multiple values for target_claim.")
                target_claim = args[len(fields)]
        if target_claim is _UNSET:
            raise TypeError("SensitivityReport requires target_claim.")
        defaults = {
            "results": (),
            "baseline_value": None,
            "stable": True,
            "max_relative_deviation": 0.0,
            "classification": "stable",
            "max_absolute_deviation": 0.0,
            "sign_consistent": None,
            "magnitude_criterion": "relative_tolerance",
        }
        object.__setattr__(self, "target_claim", target_claim)
        for name, value in values.items():
            if value is _UNSET:
                value = defaults[name]
            object.__setattr__(self, name, value)
        _validate_target_claim(self.target_claim)


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
                    target_claim=plan.target_claim,
                    specification=spec,
                    value=float("nan"),
                    failed=True,
                    error=str(exc),
                )
            )
        else:
            results.append(
                SensitivityResult(target_claim=plan.target_claim, specification=spec, value=value)
            )
    results = tuple(results)

    if not results:
        return SensitivityReport(
            target_claim=plan.target_claim,
            results=(),
            baseline_value=None,
            stable=False,
            classification="not_comparable",
        )

    successful = [r for r in results if not r.failed]
    if not successful:
        return SensitivityReport(
            target_claim=plan.target_claim,
            results=results,
            baseline_value=None,
            stable=False,
            classification="not_comparable",
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
        target_claim=plan.target_claim,
        results=results,
        baseline_value=baseline_value,
        stable=classification == "stable",
        max_relative_deviation=max_relative_deviation,
        classification=classification,
        max_absolute_deviation=max_absolute_deviation,
        sign_consistent=sign_consistent,
        magnitude_criterion=magnitude_criterion,
    )
