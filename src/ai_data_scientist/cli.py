"""Command-line entrypoint for the ai-data-scientist skill.

This is a thin diagnostic/bootstrap CLI invoked via the npm wrapper
(`bin/ai-data-scientist.js`); it is not itself part of the SDD requirement
set. Copilot invokes the skill's Python modules directly per
`.github/skills/ai-data-scientist/SKILL.md`, not through this CLI.
"""

from __future__ import annotations

import argparse
import importlib

_MODULES = [
    "ai_data_scientist.language_router",
    "ai_data_scientist.project_manager",
    "ai_data_scientist.mcp_gateway",
    "ai_data_scientist.ingestion",
    "ai_data_scientist.cleaning",
    "ai_data_scientist.eda",
    "ai_data_scientist.stats_analysis",
    "ai_data_scientist.visualization",
    "ai_data_scientist.insight_engine",
    "ai_data_scientist.gate_config",
    "ai_data_scientist.skill_packaging",
]


def doctor() -> int:
    """Import every skill module to confirm the environment is ready."""
    failures = []
    for module_name in _MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report every import failure
            failures.append(f"{module_name}: {exc}")

    if failures:
        print("NG: 以下のモジュールを読み込めませんでした / failed to import:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"OK: {len(_MODULES)} モジュールを正常に読み込みました / modules import cleanly.")
    return 0


def validate_notebook(path: str) -> int:
    """Audit a notebook (read-only) and print findings; exit 1 if any error finding."""
    from ai_data_scientist.notebook_audit import audit_notebook

    report = audit_notebook(path)
    print(f"Notebook: {report.path}")
    print(f"nbformat_valid={report.nbformat_valid} ok={report.ok}")
    print(
        f"code_cells={report.code_cell_count} executed={report.executed_code_cell_count} "
        f"insight_cells={report.insight_cell_count}"
    )
    if not report.findings:
        print("OK: 問題は見つかりませんでした / no issues found.")
        return 0

    print("findings:")
    for finding in report.findings:
        location = f"cell[{finding.cell_index}]" if finding.cell_index is not None else "-"
        print(f"  - [{finding.severity}] {location}: {finding.message}")
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-data-scientist")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Verify the Python environment can import every module.")
    validate_parser = subparsers.add_parser(
        "validate-notebook", help="Audit a notebook's execution/evidence completeness (read-only)."
    )
    validate_parser.add_argument("path", help="Path to the .ipynb file to audit.")
    args = parser.parse_args(argv)

    if args.command in (None, "doctor"):
        return doctor()
    if args.command == "validate-notebook":
        return validate_notebook(args.path)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
