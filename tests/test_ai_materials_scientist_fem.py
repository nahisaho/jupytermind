"""Tests for the FEM module (DES-AIMS-060 / REQ-AIMS-060)."""

from __future__ import annotations

import numpy as np
import pytest


def _reference_1d_heat_fixture() -> dict:
    n_nodes = 11
    length = 1.0
    node_coords = np.linspace(0.0, length, n_nodes)
    elements = [(i, i + 1) for i in range(n_nodes - 1)]
    mesh = {
        "mesh_type": "line",
        "element_order": "linear",
        "node_coords": node_coords,
        "elements": elements,
    }
    material_properties = {"conductivity": 5.0}
    boundary_conditions = {
        "prescribed": {0: 273.15, n_nodes - 1: 373.15},
        "loads": {},
    }
    return {
        "mesh": mesh,
        "material_properties": material_properties,
        "boundary_conditions": boundary_conditions,
        "physics": "heat_conduction",
    }


def _two_element_quad_mesh() -> dict:
    node_coords = np.array(
        [
            [0.0, 0.0],
            [0.5, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 1.0],
            [1.0, 1.0],
        ]
    )
    elements = [(0, 1, 4, 3), (1, 2, 5, 4)]
    return {
        "mesh_type": "quad2d",
        "element_order": "linear",
        "node_coords": node_coords,
        "elements": elements,
    }


def _simple_quad_mesh() -> dict:
    node_coords = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    elements = [(0, 1, 2, 3)]
    return {
        "mesh_type": "quad2d",
        "element_order": "linear",
        "node_coords": node_coords,
        "elements": elements,
    }


# @id TEST-AIMS-060
# @verifies REQ-AIMS-060
def test_TEST_AIMS_060_1d_heat_conduction_matches_analytical_solution():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    result = run_fem(**params)

    node_coords = params["mesh"]["node_coords"]
    expected = 273.15 + 100 * node_coords
    np.testing.assert_allclose(result["nodal_values"], expected, atol=1e-6)


# @id TEST-AIMS-952
# @verifies REQ-AIMS-060
def test_TEST_AIMS_952_dispatches_through_manifest():
    from ai_materials_scientist.dispatch import load_manifest

    manifest = load_manifest()
    assert manifest["finite-element"]["modulePath"] == "ai_materials_scientist.fem"
    assert manifest["finite-element"]["functionName"] == "run_fem"


# @id TEST-AIMS-953
# @verifies REQ-AIMS-060
def test_TEST_AIMS_953_quad2d_heat_conduction_linear_gradient():
    from ai_materials_scientist.fem import run_fem

    mesh = _two_element_quad_mesh()
    params = {
        "mesh": mesh,
        "material_properties": {"conductivity": 2.0},
        "boundary_conditions": {"prescribed": {0: 0.0, 3: 0.0, 2: 10.0, 5: 10.0}, "loads": {}},
        "physics": "heat_conduction",
    }
    result = run_fem(**params)

    # Nodes 0,3 at x=0 held at 0; nodes 2,5 at x=1 held at 10; midline nodes
    # 1,4 at x=0.5 should land at the linear interpolation value 5.0.
    np.testing.assert_allclose(result["nodal_values"], [0.0, 5.0, 10.0, 0.0, 5.0, 10.0], atol=1e-9)


# @id TEST-AIMS-954
# @verifies REQ-AIMS-060
def test_TEST_AIMS_954_plane_strain_elasticity_stiffness_is_symmetric_and_psd():
    from ai_materials_scientist.fem import assemble_and_check

    mesh = _simple_quad_mesh()
    boundary_conditions = {"prescribed": {0: 0.0, 1: 0.0, 3: 0.0}, "loads": {}}
    material_properties = {"youngs_modulus": 200e9, "poisson_ratio": 0.3}

    result = assemble_and_check(
        mesh, material_properties, boundary_conditions, "plane_strain_elasticity"
    )

    assert result["ok"] is True
    k = result["constrained_stiffness"]
    assert np.allclose(k, k.T)
    eigenvalues = np.linalg.eigvalsh(k)
    assert np.all(eigenvalues > -1e-6)


# @id TEST-AIMS-955
# @verifies REQ-AIMS-060
def test_TEST_AIMS_955_rejects_unstructured_mesh():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["mesh"]["mesh_type"] = "unstructured"

    with pytest.raises(ValueError, match="mesh"):
        run_fem(**params)


# @id TEST-AIMS-956
# @verifies REQ-AIMS-060
def test_TEST_AIMS_956_rejects_higher_order_element():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["mesh"]["element_order"] = "quadratic"

    with pytest.raises(ValueError, match="element"):
        run_fem(**params)


# @id TEST-AIMS-957
# @verifies REQ-AIMS-060
def test_TEST_AIMS_957_rejects_nonlinear_material_law():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["material_properties"]["nonlinear"] = True

    with pytest.raises(ValueError, match="material"):
        run_fem(**params)


# @id TEST-AIMS-958
# @verifies REQ-AIMS-060
def test_TEST_AIMS_958_rejects_plane_strain_elasticity_on_1d_mesh():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["physics"] = "plane_strain_elasticity"
    params["material_properties"] = {"youngs_modulus": 200e9, "poisson_ratio": 0.3}

    with pytest.raises(ValueError, match="physics"):
        run_fem(**params)


# @id TEST-AIMS-959
# @verifies REQ-AIMS-060
def test_TEST_AIMS_959_rejects_unknown_physics_label():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["physics"] = "acoustics"

    with pytest.raises(ValueError, match="physics"):
        run_fem(**params)


# @id TEST-AIMS-960
# @verifies REQ-AIMS-003
def test_TEST_AIMS_960_rejects_empty_free_dofs():
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    n_nodes = len(params["mesh"]["node_coords"])
    params["boundary_conditions"]["prescribed"] = {i: 300.0 for i in range(n_nodes)}

    with pytest.raises(ValueError, match="free_dofs"):
        run_fem(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"conductivity": 0.0}, "conductivity"),
        ({"conductivity": -1.0}, "conductivity"),
    ],
)
# @id TEST-AIMS-961
# @verifies REQ-AIMS-003
def test_TEST_AIMS_961_rejects_invalid_conductivity(overrides, bad_parameter):
    from ai_materials_scientist.fem import run_fem

    params = _reference_1d_heat_fixture()
    params["material_properties"].update(overrides)

    with pytest.raises(ValueError, match=bad_parameter):
        run_fem(**params)


@pytest.mark.parametrize(
    ("overrides", "bad_parameter"),
    [
        ({"youngs_modulus": 0.0}, "youngs_modulus"),
        ({"youngs_modulus": -1.0}, "youngs_modulus"),
        ({"poisson_ratio": 0.5}, "poisson_ratio"),
        ({"poisson_ratio": -1.0}, "poisson_ratio"),
        ({"poisson_ratio": 0.6}, "poisson_ratio"),
    ],
)
# @id TEST-AIMS-962
# @verifies REQ-AIMS-003
def test_TEST_AIMS_962_rejects_invalid_elasticity_properties(overrides, bad_parameter):
    from ai_materials_scientist.fem import run_fem

    mesh = _simple_quad_mesh()
    params = {
        "mesh": mesh,
        "material_properties": {"youngs_modulus": 200e9, "poisson_ratio": 0.3, **overrides},
        "boundary_conditions": {"prescribed": {0: 0.0, 1: 0.0}, "loads": {}},
        "physics": "plane_strain_elasticity",
    }

    with pytest.raises(ValueError, match=bad_parameter):
        run_fem(**params)
