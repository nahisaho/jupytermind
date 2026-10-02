"""Phase-field microstructure evolution module (DES-AIMS-010 / REQ-AIMS-010)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import (
    check_finite_array,
    check_positive_output_interval,
    check_positive_step_count,
    register_validator,
    validate_parameters,
)

_MODULE_NAME = "phase-field"
_MODELS = ("allen-cahn", "cahn-hilliard")


def _laplacian(c: np.ndarray, dx: float) -> np.ndarray:
    """Periodic five-point discrete Laplacian L(c) (REQ-AIMS-010)."""
    return (
        np.roll(c, -1, axis=0)
        + np.roll(c, 1, axis=0)
        + np.roll(c, -1, axis=1)
        + np.roll(c, 1, axis=1)
        - 4 * c
    ) / (dx**2)


def _f_prime(c: np.ndarray) -> np.ndarray:
    """Derivative of f(c) = c^2 * (1-c)^2."""
    return 2 * c * (1 - c) ** 2 - 2 * (c**2) * (1 - c)


# @id CODE-AIMS-010
# @implements REQ-AIMS-010
# @design DES-AIMS-010
def compute_dt_bound(model: str, M: float, kappa: float, dx: float) -> float:
    """Return the model-specific explicit stability time-step bound."""
    lambda_max = 8.0 / (dx**2)
    if model == "allen-cahn":
        return 2.0 / (M * (2 + kappa * lambda_max))
    if model == "cahn-hilliard":
        return 2.0 / (M * lambda_max * (2 + kappa * lambda_max))
    raise ValueError(f"model must be one of {_MODELS}, got {model!r}")


def _phase_field_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='phase-field'."""
    model = params["model"]
    M = params["M"]
    kappa = params["kappa"]
    dx = params["dx"]
    dt = params["dt"]

    if model not in _MODELS:
        return {"ok": False, "parameter": "model", "constraint": f"model in {_MODELS}"}
    if M <= 0:
        return {"ok": False, "parameter": "M", "constraint": "M > 0"}
    if kappa < 0:
        return {"ok": False, "parameter": "kappa", "constraint": "kappa >= 0"}
    if dx <= 0:
        return {"ok": False, "parameter": "dx", "constraint": "dx > 0"}
    if dt <= 0:
        return {"ok": False, "parameter": "dt", "constraint": "dt > 0"}

    finite_check = check_finite_array("field0", params["field0"])
    if not finite_check["ok"]:
        return finite_check
    steps_check = check_positive_step_count(params["steps"])
    if not steps_check["ok"]:
        return steps_check
    interval_check = check_positive_output_interval(params["output_every"])
    if not interval_check["ok"]:
        return interval_check

    dt_bound = compute_dt_bound(model, M, kappa, dx)
    if dt > dt_bound:
        return {
            "parameter": "dt",
            "ok": False,
            "constraint": f"dt <= dt_bound ({dt_bound}) for model {model!r}",
        }
    return {"ok": True}


register_validator(_MODULE_NAME, _phase_field_validator)


def _validate(field0, model, dx, M, kappa, dt, steps, output_every) -> None:
    """Route through the shared DES-AIMS-002 registry (REQ-AIMS-003)."""
    result = validate_parameters(
        _MODULE_NAME,
        {
            "field0": field0,
            "model": model,
            "dx": dx,
            "M": M,
            "kappa": kappa,
            "dt": dt,
            "steps": steps,
            "output_every": output_every,
        },
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-911
# @implements REQ-AIMS-010 REQ-AIMS-003
# @design DES-AIMS-010
def run_phase_field(
    field0: np.ndarray,
    model: str,
    dx: float,
    M: float,
    kappa: float,
    dt: float,
    steps: int,
    output_every: int,
) -> dict:
    """Integrate the Allen-Cahn or Cahn-Hilliard PDE and report snapshots.

    Rejects any out-of-domain parameter (REQ-AIMS-003) before performing any
    integration step or mutating ``field0``.
    """
    _validate(field0, model, dx, M, kappa, dt, steps, output_every)

    c = field0.astype(np.float64).copy()
    snapshots = [c.copy()]
    times = [0.0]

    for step in range(1, steps + 1):
        mu = _f_prime(c) - kappa * _laplacian(c, dx)
        if model == "allen-cahn":
            c = c - dt * M * mu
        else:  # cahn-hilliard
            c = c + dt * M * _laplacian(mu, dx)
        if step % output_every == 0:
            snapshots.append(c.copy())
            times.append(step * dt)

    dt_bound = compute_dt_bound(model, M, kappa, dx)
    return {
        "snapshots": snapshots,
        "times": times,
        "dt_bound": dt_bound,
    }


# @id CODE-AIMS-912
# @implements REQ-AIMS-010 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-010
def run_phase_field_with_evidence(**kwargs) -> dict:
    """Run phase-field and wrap the result as a reproducible RunRecord."""
    result = run_phase_field(**kwargs)
    return record_run(
        module_name="phase-field",
        unit_system="dimensionless-order-parameter",
        params={k: v for k, v in kwargs.items() if k != "field0"},
        arrays={
            "snapshots": np.stack(result["snapshots"]),
            "times": np.array(result["times"], dtype=np.float64),
        },
        seed=None,
    )
