"""Tests for scripts/measure_pytest_pass_rate.py."""

from __future__ import annotations

import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from measure_pytest_pass_rate import build_structured_report  # noqa: E402


# @id TEST-RELGATE-101
# @verifies REQ-RELGATE-004
def test_TEST_RELGATE_101_reports_full_pass_rate_as_passed():
    """A fully-passing pytest summary yields a 100% counter and a
    ``passed`` status for TEST-AIDS-PYTEST-001."""
    report = build_structured_report({"collected": 602, "passed": 602}, returncode=0)

    assert report["schemaVersion"] == 1
    test = report["tests"][0]
    assert test["id"] == "TEST-AIDS-PYTEST-001"
    assert test["status"] == "passed"
    assert test["operations"]["tests.pass_rate"] == 100


# @id TEST-RELGATE-102
# @verifies REQ-RELGATE-004
def test_TEST_RELGATE_102_reports_partial_pass_rate_as_failed():
    """A partial pass rate must be reported as a nonnegative integer
    counter below 100 with a ``failed`` status, never fabricated."""
    report = build_structured_report({"collected": 4, "passed": 3}, returncode=1)

    test = report["tests"][0]
    assert test["status"] == "failed"
    assert test["operations"]["tests.pass_rate"] == 75


# @id TEST-RELGATE-103
# @verifies REQ-RELGATE-004
def test_TEST_RELGATE_103_handles_zero_collected_tests():
    """An empty collection must not divide by zero and must report 0%."""
    report = build_structured_report({"collected": 0, "passed": 0}, returncode=0)

    test = report["tests"][0]
    assert test["status"] == "failed"
    assert test["operations"]["tests.pass_rate"] == 0
