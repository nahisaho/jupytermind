"""Local helper for REQ-AISCI-024's configured test-suite gate."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

_SKIPPED_TEST_RE = re.compile(r"\b\d+\s+skipped\b", re.IGNORECASE)


class TestSuiteGateError(RuntimeError):
    """Configured test-suite run failed the ai_scientist TDD gate."""


def _is_pytest_invocation(command: Sequence[str]) -> bool:
    """True only for an actual pytest invocation: an executable literally
    named ``pytest``/``pytest-<suffix>``, or ``-m pytest``. A substring match
    against arbitrary command parts would also match an unrelated script or
    test-file path that merely contains "pytest" in its name. Closes a
    rubber-duck finding from the CHANGE-019 review; see TEST-AISCI-047."""
    parts = [str(part) for part in command]
    for index, part in enumerate(parts):
        basename = Path(part).name
        if basename == "pytest" or basename.startswith("pytest-"):
            return True
        if part == "-m" and index + 1 < len(parts) and parts[index + 1] == "pytest":
            return True
    return False


def _unapproved_skips(report_path: str, approved_skips: frozenset[str]) -> list[str]:
    """Return skipped test nodeids from the musubix-json pytest report that
    are not present in ``approved_skips``, structurally (not by text-parsing
    console output). Closes jupytermind#67 / CHANGE-019 (ADR-0091); see
    TEST-AISCI-044 and TEST-AISCI-045."""
    with open(report_path, encoding="utf-8") as handle:
        report = json.load(handle)
    skipped = [
        test["nodeid"] for test in report.get("tests", []) if test.get("outcome") == "skipped"
    ]
    return sorted(nodeid for nodeid in skipped if nodeid not in approved_skips)


# @id CODE-AISCI-024
# @implements REQ-AISCI-024
# @design DES-AISCI-019
def run_configured_test_suite(
    command: Sequence[str],
    *,
    approved_skips: frozenset[str] = frozenset(),
) -> subprocess.CompletedProcess[str]:
    """Execute the configured test suite command and return its completed
    process, failing on any non-zero exit or any unapproved skipped test.

    Skip detection is structural (via a ``pytest-json-report`` machine
    report) rather than console-text parsing whenever the command invokes
    pytest, so a differently worded summary line cannot hide a real skip and
    an explicitly approved skip does not fail the gate.
    """
    is_pytest = _is_pytest_invocation(command)
    report_path: str | None = None
    full_command = list(command)
    if is_pytest:
        fd, report_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        full_command = [*command, "--json-report", f"--json-report-file={report_path}"]

    try:
        result = subprocess.run(full_command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise TestSuiteGateError("Configured test suite failed.")

        if report_path is not None:
            unapproved = _unapproved_skips(report_path, approved_skips)
            if unapproved:
                raise TestSuiteGateError(
                    "Configured test suite reported unapproved skipped tests: "
                    + ", ".join(unapproved)
                )
        else:
            combined_output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            if _SKIPPED_TEST_RE.search(combined_output):
                raise TestSuiteGateError("Configured test suite reported skipped tests.")
        return result
    finally:
        if report_path is not None:
            Path(report_path).unlink(missing_ok=True)
