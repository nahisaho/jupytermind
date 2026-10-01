"""Tests for dependency pin bounds (REQ-AIDS-050)."""

from importlib.metadata import version

import pytest
from packaging.requirements import Requirement

from ai_data_scientist.dependency_pins import get_dependency_specifier


def _is_bounded_both_sides(specifier_text: str) -> bool:
    requirement = Requirement(specifier_text)
    has_lower = any(spec.operator in (">=", ">", "==", "~=") for spec in requirement.specifier)
    has_upper = any(spec.operator in ("<=", "<", "==", "~=") for spec in requirement.specifier)
    return has_lower and has_upper


# @id TEST-AIDS-072
# @verifies REQ-AIDS-050
@pytest.mark.parametrize(
    ("package_name", "distribution_name"),
    [
        ("mcp", "mcp"),
        ("jupyter-mcp-server", "jupyter_mcp_server"),
    ],
)
def test_TEST_AIDS_072_mcp_stack_pins_are_bounded_and_satisfied(package_name, distribution_name):
    spec_text = get_dependency_specifier(package_name)
    requirement = Requirement(spec_text)

    assert _is_bounded_both_sides(spec_text), (
        f"{package_name} dependency specifier {spec_text!r} must declare both a "
        "lower and an upper bound."
    )

    installed_version = version(distribution_name)
    assert requirement.specifier.contains(installed_version), (
        f"installed {package_name} {installed_version} does not satisfy the "
        f"declared pin {spec_text!r}"
    )


# @id TEST-AIDS-073
# @verifies REQ-AIDS-050
def test_TEST_AIDS_073_unknown_dependency_raises_key_error():
    with pytest.raises(KeyError):
        get_dependency_specifier("not-a-real-declared-dependency")
