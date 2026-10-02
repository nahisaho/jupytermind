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
