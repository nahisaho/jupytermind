"""Single-point crystal plasticity slip activation module (DES-AIMS-050 / REQ-AIMS-050)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import (
    check_finite_array,
    register_validator,
    validate_parameters,
)

_MODULE_NAME = "crystal-plasticity"

# Table CP-12: fixed ordered (plane normal, slip direction) pairs, crystal frame.
_SLIP_SYSTEMS = [
    ((1, 1, 1), (0, 1, -1)),
    ((1, 1, 1), (1, 0, -1)),
    ((1, 1, 1), (1, -1, 0)),
    ((1, 1, -1), (0, 1, 1)),
    ((1, 1, -1), (1, 0, 1)),
    ((1, 1, -1), (1, -1, 0)),
    ((1, -1, 1), (0, 1, 1)),
    ((1, -1, 1), (1, 0, -1)),
    ((1, -1, 1), (1, 1, 0)),
    ((-1, 1, 1), (0, 1, -1)),
    ((-1, 1, 1), (1, 0, 1)),
    ((-1, 1, 1), (1, 1, 0)),
]

_ORTHOGONALITY_TOL = 1e-6
_DETERMINANT_TOL = 1e-6
_SYMMETRY_TOL = 1e-6
_MIN_STRESS_NORM = 1e-12


def _cp_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='crystal-plasticity'."""
    q = params["orientation_q"]
    stress = params["stress_tensor"]
    crss = params["crss"]
    gamma_dot_0 = params["gamma_dot_0"]
    n = params["n"]

    q_check = check_finite_array("orientation_q", q)
    if not q_check["ok"]:
        return q_check
    if q.shape != (3, 3):
        return {"ok": False, "parameter": "orientation_q", "constraint": "shape == (3, 3)"}
    if np.max(np.abs(q.T @ q - np.eye(3))) > _ORTHOGONALITY_TOL:
        return {
            "ok": False,
            "parameter": "orientation_q",
            "constraint": "Q must be orthogonal (Q^T Q == I within 1e-6)",
        }
    if abs(np.linalg.det(q) - 1.0) > _DETERMINANT_TOL:
        return {
            "ok": False,
            "parameter": "orientation_q",
            "constraint": "det(Q) == 1 within 1e-6",
        }

    stress_check = check_finite_array("stress_tensor", stress)
    if not stress_check["ok"]:
        return stress_check
    if stress.shape != (3, 3):
        return {"ok": False, "parameter": "stress_tensor", "constraint": "shape == (3, 3)"}
    if np.max(np.abs(stress - stress.T)) > _SYMMETRY_TOL:
        return {
            "ok": False,
            "parameter": "stress_tensor",
            "constraint": "stress_tensor must be symmetric within 1e-6",
        }
    if np.linalg.norm(stress) < _MIN_STRESS_NORM:
        return {
            "ok": False,
            "parameter": "stress_tensor",
            "constraint": "Frobenius norm must be >= 1e-12",
        }

    if crss <= 0 or not np.isfinite(crss):
        return {"ok": False, "parameter": "crss", "constraint": "crss > 0 and finite"}
    if gamma_dot_0 <= 0 or not np.isfinite(gamma_dot_0):
        return {
            "ok": False,
            "parameter": "gamma_dot_0",
            "constraint": "gamma_dot_0 > 0 and finite",
        }
    if n <= 0 or not np.isfinite(n):
        return {"ok": False, "parameter": "n", "constraint": "n > 0 and finite"}
    return {"ok": True}


register_validator(_MODULE_NAME, _cp_validator)


def _validate(orientation_q, stress_tensor, crss, gamma_dot_0, n) -> None:
    result = validate_parameters(
        _MODULE_NAME,
        {
            "orientation_q": orientation_q,
            "stress_tensor": stress_tensor,
            "crss": crss,
            "gamma_dot_0": gamma_dot_0,
            "n": n,
        },
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-050
# @implements REQ-AIMS-050 REQ-AIMS-003
# @design DES-AIMS-050
def run_crystal_plasticity(
    orientation_q: np.ndarray,
    stress_tensor: np.ndarray,
    crss: float,
    gamma_dot_0: float,
    n: float,
) -> dict:
    """Evaluate Schmid factors, resolved shear stresses, and slip activation.

    Rejects any out-of-domain parameter (REQ-AIMS-003) before any
    Schmid-factor computation (REQ-AIMS-050).
    """
    _validate(orientation_q, stress_tensor, crss, gamma_dot_0, n)

    stress_norm = np.linalg.norm(stress_tensor)
    stress_hat = stress_tensor / stress_norm

    schmid_factors = []
    resolved_shear_stresses = []
    active_systems = []
    shear_strain_rates = []

    for plane_normal, slip_direction in _SLIP_SYSTEMS:
        n_crystal = np.array(plane_normal, dtype=np.float64)
        d_crystal = np.array(slip_direction, dtype=np.float64)
        n_sample = orientation_q @ n_crystal
        d_sample = orientation_q @ d_crystal
        n_hat = n_sample / np.linalg.norm(n_sample)
        d_hat = d_sample / np.linalg.norm(d_sample)

        schmid_tensor = np.outer(n_hat, d_hat)
        schmid_factor = float(np.sum(schmid_tensor * stress_hat))
        tau = schmid_factor * stress_norm

        is_active = bool(abs(tau) >= crss)
        shear_rate = gamma_dot_0 * np.sign(tau) * abs(tau / crss) ** n if is_active else 0.0

        schmid_factors.append(schmid_factor)
        resolved_shear_stresses.append(tau)
        active_systems.append(is_active)
        shear_strain_rates.append(float(shear_rate))

    return {
        "schmid_factors": schmid_factors,
        "resolved_shear_stresses": resolved_shear_stresses,
        "active_systems": active_systems,
        "shear_strain_rates": shear_strain_rates,
    }


# @id CODE-AIMS-902
# @implements REQ-AIMS-050 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-050
def run_crystal_plasticity_with_evidence(**kwargs) -> dict:
    """Run crystal plasticity and wrap the result as a reproducible RunRecord."""
    result = run_crystal_plasticity(**kwargs)
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="stress-units-as-supplied",
        params={k: v for k, v in kwargs.items() if k not in ("orientation_q", "stress_tensor")},
        arrays={
            "schmid_factors": np.array(result["schmid_factors"], dtype=np.float64),
            "resolved_shear_stresses": np.array(
                result["resolved_shear_stresses"], dtype=np.float64
            ),
            "shear_strain_rates": np.array(result["shear_strain_rates"], dtype=np.float64),
        },
        seed=None,
    )
