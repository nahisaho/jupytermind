"""Simplified finite-element field solver module (DES-AIMS-060 / REQ-AIMS-060)."""

from __future__ import annotations

import numpy as np

from ai_materials_scientist.evidence import record_run
from ai_materials_scientist.validation import register_validator, validate_parameters

_MODULE_NAME = "finite-element"
_ALLOWED_MESH_TYPES = ("line", "quad2d")
_ALLOWED_ELEMENT_ORDER = "linear"
_RECIPROCAL_CONDITION_TOL = 1e-10
_GAUSS_POINT = 1.0 / np.sqrt(3.0)
_GAUSS_POINTS = [
    (-_GAUSS_POINT, -_GAUSS_POINT),
    (_GAUSS_POINT, -_GAUSS_POINT),
    (_GAUSS_POINT, _GAUSS_POINT),
    (-_GAUSS_POINT, _GAUSS_POINT),
]


def _quad_shape_derivs(xi: float, eta: float) -> tuple[np.ndarray, np.ndarray]:
    dN_dxi = 0.25 * np.array([-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)])
    dN_deta = 0.25 * np.array([-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)])
    return dN_dxi, dN_deta


def _plane_strain_constitutive(E: float, nu: float) -> np.ndarray:
    factor = E / ((1 + nu) * (1 - 2 * nu))
    return factor * np.array(
        [
            [1 - nu, nu, 0],
            [nu, 1 - nu, 0],
            [0, 0, (1 - 2 * nu) / 2],
        ]
    )


def _assemble_line_heat(mesh: dict, conductivity: float) -> tuple[np.ndarray, np.ndarray]:
    node_coords = np.asarray(mesh["node_coords"], dtype=np.float64)
    n = len(node_coords)
    K = np.zeros((n, n))
    f = np.zeros(n)
    for i, j in mesh["elements"]:
        length = abs(node_coords[j] - node_coords[i])
        k_local = (conductivity / length) * np.array([[1, -1], [-1, 1]])
        for a, node_a in enumerate((i, j)):
            for b, node_b in enumerate((i, j)):
                K[node_a, node_b] += k_local[a, b]
    return K, f


def _assemble_quad_heat(mesh: dict, conductivity: float) -> tuple[np.ndarray, np.ndarray]:
    node_coords = np.asarray(mesh["node_coords"], dtype=np.float64)
    n = len(node_coords)
    K = np.zeros((n, n))
    f = np.zeros(n)
    for element in mesh["elements"]:
        coords = node_coords[list(element)]
        k_local = np.zeros((4, 4))
        for xi, eta in _GAUSS_POINTS:
            dN_dxi, dN_deta = _quad_shape_derivs(xi, eta)
            jacobian = np.array([dN_dxi, dN_deta]) @ coords
            det_j = np.linalg.det(jacobian)
            jacobian_inv = np.linalg.inv(jacobian)
            grads = jacobian_inv @ np.array([dN_dxi, dN_deta])
            k_local += conductivity * (grads.T @ grads) * det_j
        for a, node_a in enumerate(element):
            for b, node_b in enumerate(element):
                K[node_a, node_b] += k_local[a, b]
    return K, f


def _assemble_quad_elasticity(
    mesh: dict, youngs_modulus: float, poisson_ratio: float
) -> tuple[np.ndarray, np.ndarray]:
    node_coords = np.asarray(mesh["node_coords"], dtype=np.float64)
    n_nodes = len(node_coords)
    n_dofs = n_nodes * 2
    K = np.zeros((n_dofs, n_dofs))
    f = np.zeros(n_dofs)
    D = _plane_strain_constitutive(youngs_modulus, poisson_ratio)
    for element in mesh["elements"]:
        coords = node_coords[list(element)]
        k_local = np.zeros((8, 8))
        for xi, eta in _GAUSS_POINTS:
            dN_dxi, dN_deta = _quad_shape_derivs(xi, eta)
            jacobian = np.array([dN_dxi, dN_deta]) @ coords
            det_j = np.linalg.det(jacobian)
            jacobian_inv = np.linalg.inv(jacobian)
            grads = jacobian_inv @ np.array([dN_dxi, dN_deta])
            dN_dx, dN_dy = grads[0], grads[1]
            B = np.zeros((3, 8))
            for a in range(4):
                B[0, 2 * a] = dN_dx[a]
                B[1, 2 * a + 1] = dN_dy[a]
                B[2, 2 * a] = dN_dy[a]
                B[2, 2 * a + 1] = dN_dx[a]
            k_local += B.T @ D @ B * det_j
        dofs = [2 * node + c for node in element for c in (0, 1)]
        for a, dof_a in enumerate(dofs):
            for b, dof_b in enumerate(dofs):
                K[dof_a, dof_b] += k_local[a, b]
    return K, f


def _ndof_per_node(physics: str) -> int:
    return 2 if physics == "plane_strain_elasticity" else 1


def _fem_validator(params: dict) -> dict:
    """DES-AIMS-002 registered validator for module_name='finite-element'."""
    mesh = params["mesh"]
    material_properties = params["material_properties"]
    physics = params["physics"]

    if physics not in ("heat_conduction", "plane_strain_elasticity"):
        return {
            "ok": False,
            "parameter": "physics",
            "constraint": "physics in ('heat_conduction', 'plane_strain_elasticity')",
        }
    if mesh["mesh_type"] not in _ALLOWED_MESH_TYPES:
        return {
            "ok": False,
            "parameter": "mesh",
            "constraint": f"mesh_type in {_ALLOWED_MESH_TYPES} (unstructured mesh rejected)",
        }
    if mesh["element_order"] != _ALLOWED_ELEMENT_ORDER:
        return {
            "ok": False,
            "parameter": "element_order",
            "constraint": "element_order == 'linear' (higher-order element rejected)",
        }
    if material_properties.get("nonlinear", False):
        return {
            "ok": False,
            "parameter": "material_properties",
            "constraint": "material law must be linear",
        }
    if physics == "plane_strain_elasticity" and mesh["mesh_type"] == "line":
        return {
            "ok": False,
            "parameter": "physics",
            "constraint": "plane_strain_elasticity is not supported on a 1D line mesh",
        }

    if physics == "heat_conduction":
        conductivity = material_properties["conductivity"]
        if conductivity <= 0:
            return {
                "ok": False,
                "parameter": "conductivity",
                "constraint": "conductivity > 0",
            }
    elif physics == "plane_strain_elasticity":
        youngs_modulus = material_properties["youngs_modulus"]
        poisson_ratio = material_properties["poisson_ratio"]
        if youngs_modulus <= 0:
            return {
                "ok": False,
                "parameter": "youngs_modulus",
                "constraint": "youngs_modulus > 0",
            }
        if not (-1 < poisson_ratio < 0.5):
            return {
                "ok": False,
                "parameter": "poisson_ratio",
                "constraint": "-1 < poisson_ratio < 0.5",
            }
    return {"ok": True}


register_validator(_MODULE_NAME, _fem_validator)


def _validate(mesh, material_properties, boundary_conditions, physics) -> None:
    result = validate_parameters(
        _MODULE_NAME,
        {
            "mesh": mesh,
            "material_properties": material_properties,
            "boundary_conditions": boundary_conditions,
            "physics": physics,
        },
    )
    if not result["ok"]:
        raise ValueError(f"{result['parameter']}: {result['constraint']}")


# @id CODE-AIMS-060
# @implements REQ-AIMS-060 REQ-AIMS-003
# @design DES-AIMS-060
def assemble_and_check(
    mesh: dict, material_properties: dict, boundary_conditions: dict, physics: str
) -> dict:
    """Assemble K, partition DOFs, and verify constrained_stiffness is well-posed.

    Rejects an empty free-DOF set or a singular/underconstrained
    constrained_stiffness (REQ-AIMS-003) before any solve is attempted.
    """
    _validate(mesh, material_properties, boundary_conditions, physics)

    if physics == "heat_conduction":
        if mesh["mesh_type"] == "line":
            K, f = _assemble_line_heat(mesh, material_properties["conductivity"])
        else:
            K, f = _assemble_quad_heat(mesh, material_properties["conductivity"])
    else:  # plane_strain_elasticity
        K, f = _assemble_quad_elasticity(
            mesh, material_properties["youngs_modulus"], material_properties["poisson_ratio"]
        )

    n_dofs = K.shape[0]
    prescribed = boundary_conditions.get("prescribed", {})
    loads = boundary_conditions.get("loads", {})
    for dof, value in loads.items():
        f[dof] += value

    prescribed_dofs = sorted(prescribed.keys())
    free_dofs = [d for d in range(n_dofs) if d not in prescribed]

    if len(free_dofs) == 0:
        return {"ok": False, "violated_condition": "free_dofs set is empty"}

    u_prescribed = np.array([prescribed[d] for d in prescribed_dofs])
    f_adjusted = f[free_dofs] - K[np.ix_(free_dofs, prescribed_dofs)] @ u_prescribed
    constrained_stiffness = K[np.ix_(free_dofs, free_dofs)]

    reciprocal_cond = 1.0 / np.linalg.cond(constrained_stiffness, 2)
    if reciprocal_cond < _RECIPROCAL_CONDITION_TOL:
        return {
            "ok": False,
            "violated_condition": "constrained_stiffness is singular/underconstrained",
        }

    return {
        "ok": True,
        "constrained_stiffness": constrained_stiffness,
        "free_dofs": free_dofs,
        "prescribed_dofs": prescribed_dofs,
        "u_prescribed": u_prescribed,
        "rhs_adjusted": f_adjusted,
        "n_dofs": n_dofs,
    }


# @id CODE-AIMS-905
# @implements REQ-AIMS-060
# @design DES-AIMS-060
def run_fem(mesh: dict, material_properties: dict, boundary_conditions: dict, physics: str) -> dict:
    """Assemble and solve the FEM system for the nodal field (REQ-AIMS-060)."""
    assembly = assemble_and_check(mesh, material_properties, boundary_conditions, physics)
    if not assembly["ok"]:
        raise ValueError(f"free_dofs: {assembly['violated_condition']}")

    u = np.zeros(assembly["n_dofs"])
    u[assembly["prescribed_dofs"]] = assembly["u_prescribed"]
    u[assembly["free_dofs"]] = np.linalg.solve(
        assembly["constrained_stiffness"], assembly["rhs_adjusted"]
    )

    return {"nodal_values": u, "mesh": mesh}


# @id CODE-AIMS-906
# @implements REQ-AIMS-060 REQ-AIMS-004 REQ-AIMS-005
# @design DES-AIMS-060
def run_fem_with_evidence(**kwargs) -> dict:
    """Run FEM and wrap the result as a reproducible RunRecord (temperatures in Kelvin)."""
    result = run_fem(**kwargs)
    return record_run(
        module_name=_MODULE_NAME,
        unit_system="si-kelvin-meter" if kwargs["physics"] == "heat_conduction" else "si",
        params={k: v for k, v in kwargs.items() if k != "mesh"},
        arrays={"nodal_values": np.asarray(result["nodal_values"], dtype=np.float64)},
        seed=None,
    )
