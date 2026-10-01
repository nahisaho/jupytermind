"""Analysis-assumption and applicability manifest.

Implements DES-AIDS-042 (REQ-AIDS-054): records conclusion-critical
analytical choices (preprocessing, sampling, causal scope) with an
explicit status, so a written caveat is never mistaken for a verified
check, and surfaces unresolved risk before a conclusion is finalized.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_VALID_ASSUMPTION_STATUSES = frozenset({"verified", "tested", "assumed", "rejected"})
_VALID_CAUSAL_SCOPES = frozenset({"descriptive", "associational", "causal"})
_TESTED_OR_VERIFIED = frozenset({"tested", "verified"})


# @id CODE-AIDS-074
# @implements REQ-AIDS-054
# @design DES-AIDS-042
@dataclass(frozen=True)
class Assumption:
    """A single analytical assumption and its verification status."""

    id: str
    statement: str
    status: str
    evidence_cell: int | None = None
    impact_if_false: str | None = None
    conclusion_critical: bool = False

    def __post_init__(self) -> None:
        if self.status not in _VALID_ASSUMPTION_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_VALID_ASSUMPTION_STATUSES)}, got {self.status!r}."
            )


@dataclass(frozen=True)
class AssumptionFinding:
    """A single applicability-check observation."""

    code: str
    severity: str  # "error" | "warning"
    message: str
    assumption_id: str | None = None


@dataclass(frozen=True)
class AnalysisAssumptionManifest:
    """Scope, assumptions, and causal classification for one analysis."""

    analysis_scope: dict
    assumptions: tuple[Assumption, ...] = field(default_factory=tuple)
    causal_scope: str = "descriptive"
    sampling: dict | None = None

    def __post_init__(self) -> None:
        if self.causal_scope not in _VALID_CAUSAL_SCOPES:
            raise ValueError(
                f"causal_scope must be one of {sorted(_VALID_CAUSAL_SCOPES)}, "
                f"got {self.causal_scope!r}."
            )

    def unresolved_risks(self) -> tuple[Assumption, ...]:
        """Conclusion-critical assumptions whose status is assumed or rejected."""
        return tuple(
            assumption
            for assumption in self.assumptions
            if assumption.conclusion_critical and assumption.status in ("assumed", "rejected")
        )


# @id CODE-AIDS-075
# @implements REQ-AIDS-054
# @design DES-AIDS-042
def check_manifest(manifest: AnalysisAssumptionManifest) -> tuple[AssumptionFinding, ...]:
    """Validate ``manifest``, returning one finding per detected gap."""
    findings: list[AssumptionFinding] = []

    if manifest.causal_scope == "causal":
        has_identification = any(
            assumption.status in _TESTED_OR_VERIFIED for assumption in manifest.assumptions
        )
        if not has_identification:
            findings.append(
                AssumptionFinding(
                    code="missing_causal_identification",
                    severity="error",
                    message=(
                        "causal_scope is 'causal' but no assumption has status "
                        "'tested' or 'verified' to support identification."
                    ),
                )
            )

    for assumption in manifest.unresolved_risks():
        findings.append(
            AssumptionFinding(
                code="unresolved_conclusion_critical_assumption",
                severity="warning",
                message=(
                    f"Conclusion-critical assumption {assumption.id!r} has status "
                    f"{assumption.status!r}, not verified/tested."
                ),
                assumption_id=assumption.id,
            )
        )

    if manifest.sampling is not None:
        missing = {"n", "seed"} - manifest.sampling.keys()
        if missing:
            findings.append(
                AssumptionFinding(
                    code="incomplete_sampling_record",
                    severity="error",
                    message=f"sampling is missing required keys: {sorted(missing)}.",
                )
            )

    return tuple(findings)
