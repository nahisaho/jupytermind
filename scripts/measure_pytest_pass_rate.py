"""Deterministic pytest pass-rate provenance for REQ-AIDS-013 / TEST-AIDS-PYTEST-001.

Runs the repository's full authoritative pytest suite (the same suite backing
the configured `test` command), computes the percentage of executed tests
that passed, and emits a single musubix-json structured test report whose
sole entry is the synthetic performance test ``TEST-AIDS-PYTEST-001`` with an
``operations.tests.pass_rate`` integer counter (0-100). This counter is
derived from the real pytest run, never a hand-authored/synthetic value, per
DES-RELGATE-004's constraint.

Usage: measure_pytest_pass_rate.py <output-report-path>
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


# @id CODE-RELGATE-004
# @implements REQ-RELGATE-004
# @design DES-RELGATE-004
def build_structured_report(summary: dict, returncode: int) -> dict:
    """Derive the musubix-json structured report from a pytest ``summary`` dict.

    ``summary`` is the ``summary`` object of a pytest-json-report output
    (keys such as ``collected``/``passed``). Returns the single-test
    musubix-json payload for ``TEST-AIDS-PYTEST-001`` with its
    ``tests.pass_rate`` integer counter (0-100), derived only from the real
    collected/passed counts, never a hand-authored value.
    """
    total = int(summary.get("collected", 0))
    passed = int(summary.get("passed", 0))
    if passed > total:
        raise ValueError(f"passed count ({passed}) cannot exceed collected count ({total}).")
    pass_rate = round((passed / total) * 100) if total else 0
    all_passed = returncode == 0 and total > 0 and passed == total
    return {
        "schemaVersion": 1,
        "tests": [
            {
                "id": "TEST-AIDS-PYTEST-001",
                "status": "passed" if all_passed else "failed",
                "operations": {"tests.pass_rate": pass_rate},
            }
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: measure_pytest_pass_rate.py <output-report-path>", file=sys.stderr)
        return 2

    output_path = Path(sys.argv[1])
    repo_root = Path(__file__).resolve().parent.parent
    python = repo_root / ".venv" / "bin" / "python"

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_report_path = Path(tmpdir) / "pytest-raw-report.json"
        result = subprocess.run(
            [
                str(python),
                "-m",
                "pytest",
                "-q",
                "--json-report",
                f"--json-report-file={raw_report_path}",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if not raw_report_path.exists():
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("pytest did not produce a JSON report.", file=sys.stderr)
            return 1

        raw_report = json.loads(raw_report_path.read_text(encoding="utf-8"))

    structured_report = build_structured_report(raw_report.get("summary", {}), result.returncode)
    counter = structured_report["tests"][0]["operations"]["tests.pass_rate"]
    status = structured_report["tests"][0]["status"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(structured_report, indent=2) + "\n", encoding="utf-8")

    print(f"Measured pytest pass rate: {counter}% (status={status}); wrote {output_path}")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
