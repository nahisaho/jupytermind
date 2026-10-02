"""Minimal readiness reporting component for the starter example feature."""


# @id CODE-EXAMPLE-001
# @implements REQ-EXAMPLE-001
# @design DES-EXAMPLE-001
def report_readiness(checks: dict[str, bool]) -> dict:
    """Report fail when any required check is false, otherwise pass."""
    missing = sorted([name for name, passed in checks.items() if not passed])
    return {"status": "pass" if not missing else "fail", "missing": missing}
