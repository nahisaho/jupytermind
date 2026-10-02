"""Simplified binary CALPHAD phase diagram module (DES-AIMS-070 / REQ-AIMS-070)."""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import register_validator, validate_parameters

_MODULE_NAME = "calphad"
_R = 8.314
_ROOT_BRACKET_EPSILON = 1e-9


def _free_energy_of_mixing(x: np.ndarray, omega: float, temperature: float) -> np.ndarray:
    return _R * temperature * (x * np.log(x) + (1 - x) * np.log(1 - x)) + omega * x * (1 - x)


def _coexistence_residual(x: float, omega: float, temperature: float) -> float:
    return np.log(x / (1 - x)) + (omega / (_R * temperature)) * (1 - 2 * x)


def _calphad_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='calphad'."""
    omega = params["omega"]
    temperature = params["temperature"]
    composition_grid = params["composition_grid"]

    if not np.isfinite(omega) or omega <= 0:
        return {"ok": False, "parameter": "omega", "constraint": "omega > 0"}
    if not np.isfinite(temperature) or temperature <= 0:
        return {"ok": False, "parameter": "temperature", "constraint": "temperature > 0"}

    t_c = omega / (2 * _R)
    if temperature >= t_c:
        return {
            "ok": False,
            "parameter": "temperature",
            "constraint": "temperature < consolute_temperature (omega / (2 * R))",
        }

    composition_grid = np.asarray(composition_grid, dtype=np.float64)
    if not np.all(np.isfinite(composition_grid)):
        return {
            "ok": False,
            "parameter": "composition_grid",
            "constraint": "composition_grid entries must be finite",
        }
    if np.any(composition_grid <= 0) or np.any(composition_grid >= 1):
        return {
            "ok": False,
            "parameter": "composition_grid",
            "constraint": "composition_grid entries must lie in the open interval (0, 1)",
        }
    return {"ok": True}


register_validator(_MODULE_NAME, _calphad_validator)


def _validate(omega: float, temperature: float, composition_grid: np.ndarray) -> None:
    result = validate_parameters(
        _MODULE_NAME,
        {"omega": omega, "temperature": temperature, "composition_grid": composition_grid},
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-070
# @implements REQ-AIMS-070 REQ-AIMS-003
# @design DES-AIMS-070
def run_calphad(omega: float, temperature: float, composition_grid: np.ndarray) -> dict:
    """Compute the regular-solution G_mix curve and the two binodal compositions."""
    composition_grid = np.asarray(composition_grid, dtype=np.float64)
    _validate(omega, temperature, composition_grid)

    free_energy_curve = _free_energy_of_mixing(composition_grid, omega, temperature)

    x_alpha = brentq(
        _coexistence_residual,
        _ROOT_BRACKET_EPSILON,
        0.5 - _ROOT_BRACKET_EPSILON,
        args=(omega, temperature),
    )
    x_beta = brentq(
        _coexistence_residual,
        0.5 + _ROOT_BRACKET_EPSILON,
        1.0 - _ROOT_BRACKET_EPSILON,
        args=(omega, temperature),
    )

    return {
        "x_alpha": x_alpha,
        "x_beta": x_beta,
        "free_energy_curve": free_energy_curve,
    }


# @id CODE-AIMS-900
# @implements REQ-AIMS-070 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-070
def run_calphad_with_evidence(**kwargs) -> dict:
    """Run the CALPHAD module and wrap the result as a reproducible RunRecord."""
    result = run_calphad(**kwargs)
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="J-per-mol",
        params={k: v for k, v in kwargs.items() if k != "composition_grid"},
        arrays={
            "x_alpha": np.array([result["x_alpha"]], dtype=np.float64),
            "x_beta": np.array([result["x_beta"]], dtype=np.float64),
            "free_energy_curve": np.asarray(result["free_energy_curve"], dtype=np.float64),
        },
        seed=None,
    )
