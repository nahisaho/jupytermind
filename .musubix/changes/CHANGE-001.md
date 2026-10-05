# CHANGE-001: Add ai-scientist Agent Skill

## Summary

Introduce a new `ai-scientist` Agent Skill that orchestrates an 8-phase
research lifecycle (research-planning, literature-review,
experimental-design, data-analysis, manuscript-writing, peer-review,
reproducibility-check, presentation) within a single continuous session,
delegating to sibling skills (`ai-data-scientist`, `tech-writer`,
`japanese-prose`, `presentation-planner`) and to configurable MCP servers
(e.g. ToolUniverse) for literature/domain-tool search.

## Scope

- New feature slug: `ai-scientist`.
- New requirements: REQ-AISCI-001 through REQ-AISCI-024.
- No existing feature's requirements are modified.

## Affected Requirements

Requirements: REQ-AISCI-001, REQ-AISCI-002, REQ-AISCI-003, REQ-AISCI-004, REQ-AISCI-005, REQ-AISCI-006, REQ-AISCI-007, REQ-AISCI-008, REQ-AISCI-009, REQ-AISCI-010, REQ-AISCI-011, REQ-AISCI-012, REQ-AISCI-013, REQ-AISCI-014, REQ-AISCI-015, REQ-AISCI-016, REQ-AISCI-017, REQ-AISCI-018, REQ-AISCI-019, REQ-AISCI-020, REQ-AISCI-021, REQ-AISCI-022, REQ-AISCI-023, REQ-AISCI-024.

## Rationale

A single-skill-plus-modules architecture (reusing the `ai-data-scientist`
pattern) was chosen over a large set of fine-grained sub-skills, to reduce
context overhead and reuse the existing stable-workspace-root and
project-handle validation contracts already proven in `ai-data-scientist`.

## #62 Remediation

Repo-wide pre-existing change-history/change-completeness gate debt (issue
#62) had its waivable diagnostics remediated for CHANGE-001 as follows.
Unlike CHANGE-003/CHANGE-005, this change had no non-waivable
`CHANGE_PHASE_ORDER` diagnostic; all identified diagnostics were waivable
and waived, and the 24 `CHANGE_COMPLETENESS_ADR` diagnostics were resolved
substantively by authoring the missing ADRs (not waived).

### ADRs authored (19 total: ADR-0073 through ADR-0091)

Each of the 19 `DES-AISCI-001` through `DES-AISCI-019` design sections
previously had `ADRs: none`. One ADR was authored per design section,
documenting the architectural decision, genuine rejected alternatives, and
the specific test file(s) proving the decision, and `design.md` was updated
to link each section to its new ADR. This substantively resolved all 24
`CHANGE_COMPLETENESS_ADR` diagnostics (one per REQ-AISCI requirement; some
design sections cover more than one requirement).

A Copilot `rubber-duck` review of all 19 ADRs against `design.md` and the
actual `src/ai_scientist/*.py` implementation found 5 ADRs overclaiming
design-constraint compliance that the real implementation does not fully
satisfy, and 2 ADRs with lesser wording inaccuracies. All 7 were corrected
to accurately describe current behavior (adding honest "Known limitation"
paragraphs where real gaps exist), and the 5 genuine implementation gaps
were filed as separate GitHub issues rather than fixed here (out of scope
for an ADR-authoring debt-remediation change):

- **jupytermind#64** — `phase_state.py` lacks cross-process concurrency
  guard around its read-modify-write cycle (ADR-0075).
- **jupytermind#65** — `manifest.py` verifies sibling-skill dependencies
  against a repository-local scan, not the host Copilot CLI's live
  installed-skill registry as the design requires (ADR-0087).
- **jupytermind#66** — `mcp_managed.py` has a port-allocation TOCTOU window
  and no registry-level synchronization, so concurrent calls can start
  duplicate processes for the same server name; loopback-only binding is
  also not validated (ADR-0084).
- **jupytermind#67** — `tdd_gate.py` skip detection relies on a narrow
  regex matched against free text, not a structural, runner-agnostic
  parse, and has no approved-skip mechanism (ADR-0091).
- **jupytermind#68** — `latex_renderer.py` strips per-line and
  assembled-body whitespace, which can alter indentation/trailing-space
  formatting and discard boundary blank lines (ADR-0090).

A second rubber-duck pass after the corrections found the follow-up issue
numbers had been cross-wired for 4 of the ADRs (an artifact of filing the 5
issues via parallel shell commands, which reordered their returned numbers
relative to the order requested) plus 3 further smaller wording
inaccuracies (ADR-0074's claimed upstream error type, ADR-0090's
blank-line-preservation overstatement, ADR-0091's Consequences/Known-
limitation contradiction about skip approval). All were corrected and a
final rubber-duck pass confirmed all 7 ADRs, plus the other 12 (ADR-0073,
ADR-0076 through ADR-0081, ADR-0083, ADR-0085, ADR-0086, ADR-0088,
ADR-0089) which were clean from the first review, are now accurate.

### Waivers recorded (74 total, all approver `nahisaho`)

All 74 waiver records cite, as their recorded reason text, the same
underlying evidence-repair limitation already documented for prior changes
in this remediation effort: musubix3 cannot repair stale or re-validated
TDD evidence short of a disproportionate project-wide `tdd.json` reset
(issue #39, previously declined by the user). The `ai-scientist` feature's
implementation was genuinely Red-then-Green TDD-developed; the full 580/580
suite passes as of this remediation, with no identified functional defect
in the TDD evidence itself — the diagnostics reflect evidence staleness
from the same repo-wide `@id`/evidence-format history as other changes in
this remediation, not unproven requirements.

- `CHANGE_RED_UNPROVEN` x24 — one per REQ-AISCI-001 through REQ-AISCI-024.
- `CHANGE_GREEN_UNPROVEN` x24 — same 24 requirements.
- `CHANGE_COMPLETENESS_TDD` x24 — same 24 requirements.
- `CHANGE_TEST_CHANGED_AFTER_RED` x2 — detail-scoped: one batch covering
  REQ-AISCI-004/005/006/007, one batch covering the remaining 20
  requirements.

### musubix3 tooling feedback filed

Beyond the two tool defects already filed in prior changes of this
remediation (nahisaho/musubix3#55, nahisaho/musubix3#56), this change's
work prompted a consolidated enhancement request,
**nahisaho/musubix3#57**, proposing: (1) a lightweight identifier-rename
migration mode for TDD evidence that doesn't require a full Red/Green redo,
(2) an audited "supersede" re-record mechanism for singular phases like
`quality`, and (3) adding `CHANGE_PHASE_ORDER` to the waivable code set as a
documented fallback when (2) isn't retroactively applicable.

### Verification

- `trace build`: 1094 nodes, 1590 edges, 0 diagnostics.
- `gate --json`: 0 error-severity diagnostics attributable to CHANGE-001
  (the overall gate status remains `fail` only due to pre-existing,
  out-of-#62-scope debt for other changes and repo-wide checks, unaffected
  by this change).
- `pytest`: 580/580 passed.

### Debt Remediation Approval

- Approver: `nahisaho`
- Decision: approve (merge to main)
- artifactSha256: `bac2fa9bea2120ae11d7bee72ea9392984abc34a1db27c288a658db98483d951`
- Approved files (36): `.musubix/changes/CHANGE-001.md`;
  `.musubix/decisions/ADR-0073.md` through `ADR-0091.md` (19 new files);
  `.musubix/evidence/change-waivers.json`, `formal.json`,
  `model-correspondence.json`, `native/test/aggregate.json`, `order.json`,
  `performance.json`, `quality.json`;
  `.musubix/features/ai-chemistry-scientist/trace.json`,
  `ai-data-scientist-ml/trace.json`, `ai-data-scientist/trace.json`,
  `ai-genomics-scientist/trace.json`, `ai-materials-scientist/trace.json`,
  `ai-structural-biology-scientist/trace.json`, `example/trace.json`;
  `.musubix/features/ai-scientist/design.md`;
  `.musubix/features/ai-scientist/trace.json`.
