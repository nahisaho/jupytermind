"""Tests for ai_materials_scientist module routing by request content."""

from __future__ import annotations

import pytest


# @id TEST-AIMS-002
# @verifies REQ-AIMS-002
@pytest.mark.parametrize(
    ("request_text", "expected_module"),
    [
        ("I want to run a phase-field simulation", "phase-field"),
        ("フェーズフィールド法でシミュレーションしたい", "phase-field"),
        ("Please run a molecular dynamics simulation", "molecular-dynamics"),
        ("分子動力学のシミュレーションを実行してください", "molecular-dynamics"),
        ("Run a classical monte carlo simulation", "classical-monte-carlo"),
        ("古典モンテカルロで計算して", "classical-monte-carlo"),
        ("Run a kinetic monte carlo simulation", "kinetic-monte-carlo"),
        ("速度論的モンテカルロで計算して", "kinetic-monte-carlo"),
        ("Compute crystal plasticity slip activation", "crystal-plasticity"),
        ("結晶塑性のすべり活性化を計算して", "crystal-plasticity"),
        ("Solve this with the finite element method", "finite-element"),
        ("有限要素法で解いて", "finite-element"),
        ("Compute a CALPHAD phase diagram", "calphad"),
        ("CALPHADで状態図を計算して", "calphad"),
    ],
)
def test_TEST_AIMS_002_dispatches_to_exactly_one_matched_module(request_text, expected_module):
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch(request_text)

    assert result["outcome"] == "dispatch"
    assert result["module"] == expected_module
    assert "handler_result" in result


# @id TEST-AIMS-947
# @verifies REQ-AIMS-002
def test_TEST_AIMS_947_two_matched_modules_yields_clarification_with_no_dispatch():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("Should I use phase-field or molecular dynamics here?")

    assert result["outcome"] == "clarification"
    assert set(result["candidates"]) == {"phase-field", "molecular-dynamics"}


# @id TEST-AIMS-948
# @verifies REQ-AIMS-002
def test_TEST_AIMS_948_no_matched_module_yields_rejection_with_no_dispatch():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("What is the weather today?")

    assert result["outcome"] == "rejected"


# @id TEST-AIMS-990
# @verifies REQ-AIMS-002
def test_TEST_AIMS_990_rejects_non_string_request_text():
    from ai_materials_scientist.dispatch import dispatch

    with pytest.raises(ValueError, match="request_text"):
        dispatch(None)


# @id TEST-AIMS-991
# @verifies REQ-AIMS-002
def test_TEST_AIMS_991_rejects_unsupported_explicit_language_override():
    from ai_materials_scientist.dispatch import dispatch

    with pytest.raises(ValueError, match="language"):
        dispatch("Run a phase-field simulation", language="fr")
