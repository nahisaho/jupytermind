"""Repetition-aware convergence classification for iterative deep-dive loops.

GitHub #77 / REQ-AIDS-098 / DES-AIDS-098 / ADR-0115.

``evaluate_convergence`` distinguishes a genuine metric plateau (evidence
drawn from distinct actions) from a loop that has simply run out of
distinct deep-dive actions and started mechanically repeating the same
deterministic computation -- a real bug found twice in a Kaggle-100
batch-analysis script built on this skill.

Change: CHANGE-032
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

__all__ = ["ConvergenceVerdict", "Round", "RoundLike", "evaluate_convergence"]


_Status = Literal[
    "converged",
    "repetition_detected",
    "exhausted",
    "continue",
    "converged_with_secondary_regression",
]


class _Missing:
    """Private sentinel type; a field could not be resolved from a record."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return "<MISSING>"


_MISSING = _Missing()


@dataclass(frozen=True)
class Round:
    """A single iteration round: its resulting metric and action identity."""

    metric: float
    action_signature: str
    secondary_metrics: Mapping[str, float] | None = None


@runtime_checkable
class RoundLike(Protocol):
    """Structural protocol satisfied by `Round` and any similar dataclass."""

    metric: float
    action_signature: str


@dataclass(frozen=True)
class ConvergenceVerdict:
    """The classification result returned by `evaluate_convergence`."""

    status: _Status
    repeated_signature: str | None
    repeated_rounds: tuple[int, int] | None
    secondary_regressions: tuple[str, ...] = ()


# @id CODE-AIDS-150
# @implements REQ-AIDS-098
# @design DES-AIDS-098
def _resolve_field(entry: Any, name: str) -> Any:
    """Resolve ``name`` from ``entry``, never letting an Exception escape.

    Attempts attribute access first, then (only on ``AttributeError``) a
    mapping-style lookup; the entire attempt is wrapped in one outermost
    ``except Exception`` so any failure from a malformed, adversarial, or
    otherwise non-conforming ``entry`` (a custom ``__getattr__``/property
    raising, or a custom ``Mapping`` whose ``__contains__``/``__getitem__``
    itself raises) is uniformly treated as "field absent" rather than ever
    propagating. Each access path is attempted at most once.
    """
    try:
        try:
            return getattr(entry, name)
        except AttributeError:
            if isinstance(entry, Mapping):
                return entry[name]
            return _MISSING
    except Exception:
        return _MISSING


def _relative_change(prev: float, curr: float) -> float:
    if prev != 0.0:
        return abs(curr - prev) / abs(prev)
    return 0.0 if curr == 0.0 else math.inf


# @id CODE-AIDS-156
# @implements REQ-AIDS-102
# @design DES-AIDS-102
def _resolve_secondary_value(entry: Any, name: str) -> Any:
    """Resolve secondary metric ``name`` for one round, never raising.

    First resolves the round's `secondary_metrics` mapping via the
    existing attribute-then-mapping `_resolve_field` helper, then, only
    if that result is a `Mapping`, performs a key-only lookup (never
    attribute access, so names such as ``"items"`` or ``"keys"`` resolve
    correctly) wrapped in its own exception containment, mirroring
    `_resolve_field`'s own outermost `except Exception` pattern so a
    custom `Mapping` whose `get`/`__getitem__` itself raises is treated
    as absent rather than propagating.
    """
    container = _resolve_field(entry, "secondary_metrics")
    if not isinstance(container, Mapping):
        return _MISSING
    try:
        return container.get(name, _MISSING)
    except Exception:  # noqa: BLE001 - a custom Mapping get() may raise; treat as absent
        return _MISSING


def _is_present_numeric(value: Any) -> bool:
    return (
        value is not _MISSING
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


# @id CODE-AIDS-151
# @implements REQ-AIDS-098, REQ-AIDS-102
# @design DES-AIDS-098, DES-AIDS-102
def evaluate_convergence(
    history: Sequence[Any],
    rel_tol: float = 0.02,
    min_consecutive: int = 2,
    actions_exhausted: bool = False,
    secondary_metrics: Sequence[str] | None = None,
    secondary_rel_tol: float | None = None,
) -> ConvergenceVerdict:
    """Classify an iterative loop's convergence status from its `history`.

    See REQ-AIDS-098 / DES-AIDS-098 for the full normative contract.
    """
    valid_min_consecutive = (
        isinstance(min_consecutive, int)
        and not isinstance(min_consecutive, bool)
        and min_consecutive >= 1
    )
    if not valid_min_consecutive:
        raise ValueError(f"min_consecutive must be a positive int, got {min_consecutive!r}")

    valid_rel_tol = (
        isinstance(rel_tol, (int, float))
        and not isinstance(rel_tol, bool)
        and math.isfinite(rel_tol)
        and rel_tol >= 0.0
    )
    if not valid_rel_tol:
        raise ValueError(f"rel_tol must be a finite number >= 0.0, got {rel_tol!r}")

    if secondary_rel_tol is None:
        resolved_secondary_rel_tol = rel_tol
    else:
        valid_secondary_rel_tol = (
            isinstance(secondary_rel_tol, (int, float))
            and not isinstance(secondary_rel_tol, bool)
            and math.isfinite(secondary_rel_tol)
            and secondary_rel_tol >= 0.0
        )
        if not valid_secondary_rel_tol:
            raise ValueError(
                f"secondary_rel_tol must be a finite number >= 0.0, got {secondary_rel_tol!r}"
            )
        resolved_secondary_rel_tol = secondary_rel_tol

    metrics: list[float] = []
    signatures: list[str] = []
    for entry in history:
        metric = _resolve_field(entry, "metric")
        action_signature = _resolve_field(entry, "action_signature")

        valid_metric = (
            metric is not _MISSING
            and isinstance(metric, (int, float))
            and not isinstance(metric, bool)
            and math.isfinite(metric)
        )
        if not valid_metric:
            raise ValueError(f"history entry has an invalid metric: {metric!r}")

        valid_action_signature = (
            action_signature is not _MISSING
            and isinstance(action_signature, str)
            and len(action_signature) > 0
        )
        if not valid_action_signature:
            raise ValueError(f"history entry has an invalid action_signature: {action_signature!r}")

        metrics.append(float(metric))
        signatures.append(action_signature)

    n = len(metrics)

    # Step 2: relative-change sequence and transition qualification.
    # qualifies[i] (0-based, i in 0..n-2) tracks the transition from round
    # i+1 to round i+2 (1-based transition index i+1).
    qualifies: list[bool] = []
    for i in range(1, n):
        rel_change = _relative_change(metrics[i - 1], metrics[i])
        qualifies.append(rel_change < rel_tol)

    # Step 3: trailing qualifying run length (suffix of True values).
    run_length = 0
    for qualifies_value in reversed(qualifies):
        if qualifies_value:
            run_length += 1
        else:
            break
    length_qualified = run_length >= min_consecutive

    repeated_signature: str | None = None
    repeated_rounds: tuple[int, int] | None = None

    if length_qualified:
        # Step 4: contributing destination rounds (1-based).
        contributing_rounds = list(range(n - min_consecutive + 1, n + 1))

        # Step 5: duplicate scan, candidate rounds from greatest to smallest.
        for r in reversed(contributing_rounds):
            r_signature = signatures[r - 1]
            best_e: int | None = None
            for e in range(1, r):
                if signatures[e - 1] == r_signature:
                    if best_e is None or e > best_e:
                        best_e = e
            if best_e is not None:
                repeated_signature = r_signature
                repeated_rounds = (best_e, r)
                break

    # Step 6: status decision.
    if length_qualified and repeated_rounds is not None:
        status: _Status = "repetition_detected"
    elif length_qualified:
        status = "converged"
    elif actions_exhausted:
        status = "exhausted"
    else:
        status = "continue"

    if status != "repetition_detected":
        repeated_signature = None
        repeated_rounds = None

    # Step 7 (REQ-AIDS-102 / DES-AIDS-102): secondary-metric regression
    # check, scoped strictly to the base "converged" status.
    secondary_regressions: tuple[str, ...] = ()
    if status == "converged" and secondary_metrics:
        regressed_names: list[str] = []
        for name in secondary_metrics:
            present_values: list[float] = []
            final_value: float | None = None
            for round_index, entry in enumerate(history):
                raw_value = _resolve_secondary_value(entry, name)
                if _is_present_numeric(raw_value):
                    value = float(raw_value)
                    present_values.append(value)
                    if round_index == n - 1:
                        final_value = value
            if not present_values or final_value is None:
                continue
            peak_value = max(present_values)
            regression = _relative_change(peak_value, final_value)
            if regression > resolved_secondary_rel_tol:
                regressed_names.append(name)
        secondary_regressions = tuple(regressed_names)
        if secondary_regressions:
            status = "converged_with_secondary_regression"

    return ConvergenceVerdict(
        status=status,
        repeated_signature=repeated_signature,
        repeated_rounds=repeated_rounds,
        secondary_regressions=secondary_regressions,
    )
