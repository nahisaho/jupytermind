"""Tests for the ai_scientist TDD verification gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# @id TEST-AISCI-035
# @verifies REQ-AISCI-024
def test_TEST_AISCI_035_rejects_failing_or_skipped_test_suites(tmp_path):
    from ai_scientist.tdd_gate import run_configured_test_suite

    with pytest.raises(RuntimeError, match="test suite"):
        run_configured_test_suite([sys.executable, "-c", "import sys; sys.exit(1)"])

    skipped_test = tmp_path / "test_skipped_suite.py"
    skipped_test.write_text(
        "\n".join(
            [
                "import pytest",
                "",
                "@pytest.mark.skip(reason='covered elsewhere')",
                "def test_skip_me():",
                "    pass",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="skip"):
        run_configured_test_suite([sys.executable, "-m", "pytest", "-q", str(skipped_test)])


def _write_mixed_skip_suite(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "import pytest",
                "",
                "@pytest.mark.skip(reason='approved: covered by TEST-AISCI-000')",
                "def test_approved_skip():",
                "    pass",
                "",
                "@pytest.mark.skip(reason='unapproved')",
                "def test_unapproved_skip():",
                "    pass",
                "",
                "def test_passes():",
                "    assert True",
            ]
        ),
        encoding="utf-8",
    )


# @id TEST-AISCI-044
# @verifies REQ-AISCI-024
def test_TEST_AISCI_044_allows_an_explicitly_approved_skip_but_rejects_the_rest(tmp_path):
    """DES-AISCI-019: zero *unapproved* skipped tests -- an approved skip must
    not fail the gate, but any other skip in the same run still must.

    Regression test for jupytermind#67; closed by CHANGE-019 (ADR-0091).
    Exercises the approved_skips allowlist parameter end to end."""
    from ai_scientist.tdd_gate import run_configured_test_suite

    mixed_suite = tmp_path / "test_mixed_skip_suite.py"
    _write_mixed_skip_suite(mixed_suite)
    approved_nodeid = f"{mixed_suite.name}::test_approved_skip"

    with pytest.raises(RuntimeError, match="unapproved") as excinfo:
        run_configured_test_suite(
            [sys.executable, "-m", "pytest", "-q", str(mixed_suite)],
            approved_skips=frozenset({approved_nodeid}),
        )

    assert "test_unapproved_skip" in str(excinfo.value)
    assert "test_approved_skip" not in str(excinfo.value)


# @id TEST-AISCI-045
# @verifies REQ-AISCI-024
def test_TEST_AISCI_045_detects_a_skip_structurally_even_with_an_unusual_summary_wording(
    tmp_path,
):
    """Skip detection must come from the pytest-json-report machine report,
    not from matching a particular console summary phrase, so a verbose or
    reworded `-r` summary line cannot hide a real skip.

    Regression test for jupytermind#67; closed by CHANGE-019 (ADR-0091).
    Verifies structural detection is independent of `-r`/`-v` verbosity."""
    from ai_scientist.tdd_gate import run_configured_test_suite

    skipped_test = tmp_path / "test_verbose_skipped_suite.py"
    skipped_test.write_text(
        "\n".join(
            [
                "import pytest",
                "",
                "@pytest.mark.skip(reason='covered elsewhere')",
                "def test_skip_me():",
                "    pass",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="unapproved skipped"):
        run_configured_test_suite([sys.executable, "-m", "pytest", "-rA", "-v", str(skipped_test)])


# @id TEST-AISCI-047
# @verifies REQ-AISCI-024
def test_TEST_AISCI_047_pytest_detection_requires_an_actual_pytest_invocation():
    """DES-AISCI-019: the gate must inject pytest-only `--json-report` flags
    only for an actual pytest invocation (executable `pytest`/`pytest-<x>`,
    or `-m pytest`), not for any command that merely contains the substring
    "pytest" somewhere in an argument such as a script or test-file path.

    Regression test for a rubber-duck finding during CHANGE-019 review:
    the original detection was `"pytest" in str(part)`, which would also
    match an unrelated non-pytest command such as a script literally named
    `run_pytest_wrapper.sh`. Covers true and false cases for _is_pytest_invocation."""
    from ai_scientist.tdd_gate import _is_pytest_invocation

    assert _is_pytest_invocation([sys.executable, "-m", "pytest", "-q"]) is True
    assert _is_pytest_invocation(["pytest", "-q"]) is True
    assert _is_pytest_invocation(["/usr/bin/pytest-3", "-q"]) is True
    assert _is_pytest_invocation(["./run_pytest_wrapper.sh"]) is False
    assert _is_pytest_invocation([sys.executable, "tests/test_pytest_helper.py"]) is False
    assert _is_pytest_invocation(["-m", "pytest_randomly"]) is False
