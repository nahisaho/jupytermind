"""Local helper for REQ-AISCI-024's configured test-suite gate."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence

_SKIPPED_TEST_RE = re.compile(r"\b\d+\s+skipped\b", re.IGNORECASE)


class TestSuiteGateError(RuntimeError):
    """Configured test-suite run failed the ai_scientist TDD gate."""


# @id CODE-AISCI-024
# @implements REQ-AISCI-024
# @design DES-AISCI-019
def run_configured_test_suite(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Execute the configured test suite command and return its completed process."""
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise TestSuiteGateError("Configured test suite failed.")
    combined_output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if _SKIPPED_TEST_RE.search(combined_output):
        raise TestSuiteGateError("Configured test suite reported skipped tests.")
    return result
