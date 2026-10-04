# CHANGE-014: ai-data-scientist defect-fix batch (#57, #54, #53)

## Summary

Bundled defect-fix batch for three independent GitHub issues in the
`ai-data-scientist` feature:

- **#57**: `ingestion.ingest()` silently truncated local CSV/Excel sources
  to `row_limit` (default 100,000 rows), even though REQ-AIDS-032 scopes
  that safety control to remote (database/API) sources only. Fixed by
  gating truncation on `source_spec.kind in _REMOTE_KINDS`.
- **#54**: `insight_engine._find_evidence_cell` matched only on
  `execution_count`/`cited_value` and silently resolved to the first
  matching cell when duplicates existed (common after a kernel restart or
  appending to a notebook in a new session); `notebook_audit.audit_notebook`
  did not flag this ambiguity either. Fixed by adding
  `AmbiguousEvidenceError` (a subclass of the existing
  `EvidenceMissingError`), raised whenever more than one executed cell
  matches, and by having `audit_notebook` report both duplicate
  `execution_count` values (warning) and ambiguous evidence manifests
  (error).
- **#53**: `sensitivity.run_sensitivity` only used relative-deviation-
  from-baseline to set a boolean `stable` flag, misclassifying large
  same-signed metric drops as "stable" and small sign-consistent
  improvements as "unstable" when the baseline was tiny, and mishandling
  zero-baseline cases. REQ-AIDS-056's acceptance criteria already mandated
  a 4-way classification (`stable`/`attenuated`/`reversed`/`not_comparable`)
  that had never actually been implemented. Fixed by adding
  `absolute_tolerance`, per-specification failure capture, and a new
  `_classify_stability` helper implementing the full 4-way classification
  with `sign_consistent`/`magnitude_criterion` reporting.

During design review, a related pre-existing defect was discovered and
fixed as part of the same REQ-AIDS-056 classification-consistency
correction: `run_sensitivity` returned `stable=True` for the empty-grid
edge case despite `classification="not_comparable"`, contradicting the new
"`stable` is `True` exactly when `classification == "stable"`" invariant.
Also during design review, a genuinely separate, pre-existing gap was
discovered — `SensitivityPlan` has no `target_claim` field even though
REQ-AIDS-056's statement describes one — and was filed as GitHub #59
rather than silently fixed (out of this change's bundled-defect scope) or
silently left undocumented.

## Scope

- Existing feature: `ai-data-scientist` (governs `ingestion.ingest`,
  `insight_engine.record_insight`, `notebook_audit.audit_notebook`,
  `sensitivity.run_sensitivity`).
- Touches: `src/ai_data_scientist/ingestion.py`,
  `src/ai_data_scientist/insight_engine.py`,
  `src/ai_data_scientist/notebook_audit.py`,
  `src/ai_data_scientist/sensitivity.py`, their four test files, and the
  governing feature's `requirements.md`/`design.md`.
- #57 and #53 are pure defect corrections: implementation violated an
  existing requirement/design intent in each case, and no requirement
  text changed. #54 is a defect fix that also required broadening
  REQ-AIDS-010/REQ-AIDS-045's acceptance text (same IDs kept, since the
  underlying obligation is unchanged in kind): the prior text only
  required resolving a cited `execution_count`/`cited_value` to "an
  existing executed cell", which the implementation satisfied even when
  it silently picked the first of several matching cells; it did not yet
  say that resolution must be *unambiguous*. The acceptance text was
  extended to make that already-intended invariant explicit, and the
  implementation was fixed to enforce it (`AmbiguousEvidenceError`)
  rather than rewriting the requirement to excuse the prior silent
  first-match behavior.
- Out of scope: the `target_claim` gap in `SensitivityPlan` (tracked as
  GitHub #59) and any pre-existing generic interface-description drift in
  DES-AIDS-005/DES-AIDS-010 unrelated to these three issues.

## Affected Requirements

Requirements: REQ-AIDS-010, REQ-AIDS-032, REQ-AIDS-045, REQ-AIDS-056.

## Design

Design: DES-AIDS-005 (remote-only row-limit truncation, fetch-then-truncate
wording corrected), DES-AIDS-010 (ambiguous-evidence withholding via
`AmbiguousEvidenceError`), DES-AIDS-033 (duplicate execution_count warning
and ambiguous-manifest error reporting), DES-AIDS-044 (full 4-way
stability classification, `absolute_tolerance`, `sign_consistent`,
`magnitude_criterion`, and the `target_claim` known-gap disclosure
referencing GitHub #59). ADRs: none — all four are direct corrections of
existing documented behavior, no new architectural alternative considered.

## Implementation Plan

- [x] Investigate all three issues: #57 and #53 are pure defect
  corrections against existing requirement/design intent with no
  requirement-text change; #54 required genuinely broadening
  REQ-AIDS-010/REQ-AIDS-045's acceptance text to make an already-intended
  unambiguous-resolution invariant explicit (see Scope) — not a rewrite
  that excuses the prior incorrect behavior.
- [x] Fix `ingestion.py` (#57): truncation gated on
  `source_spec.kind in _REMOTE_KINDS`; module docstring corrected to
  describe fetch-then-truncate, remote-only semantics.
- [x] Fix `sensitivity.py` (#53): `absolute_tolerance` parameter,
  per-specification failure capture (`failed`/`error`), new
  `_classify_stability` helper (CODE-AIDS-127) implementing
  stable/attenuated/reversed/not_comparable, `sign_consistent`/
  `magnitude_criterion` reporting, and the empty-grid `stable`/
  `classification` consistency fix.
- [x] Fix `insight_engine.py`/`notebook_audit.py` (#54): new
  `AmbiguousEvidenceError` (CODE-AIDS-125, subclass of
  `EvidenceMissingError`), refactored `_find_evidence_cell` via
  `_matching_evidence_cells`/`_cell_output_contains`, duplicate
  execution_count detection in `audit_notebook` (CODE-AIDS-126).
- [x] Amended REQ-AIDS-010/REQ-AIDS-045 acceptance text (same IDs,
  broadened obligations); ran `requirements validate` (PASS).
- [x] Rubber-duck review of the requirements amendment — no blocking
  issues (2 non-blocking suggestions addressed: strengthened
  TEST-AIDS-210's assertion to check message content, TEST-AIDS-211's to
  check exact execution_count/indices).
- [x] Human approval of requirements (approver: nahisaho, exact file list
  shown via `ask_user`, hash
  `e882b67c23301906918258152c61b3509b80652598b9e1c74b5028a6f2a23226`).
- [x] Updated DES-AIDS-005/010/033/044; ran `design validate` (PASS).
- [x] Rubber-duck review of the design amendment, iterated 3 times: round 1
  found 3 blocking issues (DES-AIDS-044 overclaiming REQ-AIDS-056 target
  claim conformance; `stable=True`/`classification="not_comparable"`
  contradiction on the empty-grid branch; DES-AIDS-005's stale
  "before load" wording for remote row-limit truncation). Fixed the
  `stable` code bug (and added TEST-AIDS-213 regression test), corrected
  the DES-AIDS-005 wording to match the real fetch-then-truncate flow, and
  filed GitHub #59 for the target_claim gap rather than silently
  overclaiming or expanding this change's scope to implement it. Round 2
  found 1 remaining blocking issue (trace metadata still implying full
  REQ-AIDS-056 conformance) — resolved by referencing GitHub #59 by name
  in the design's "Known gap" disclosure, fixing the stale
  `ingestion.py` module docstring, and adding TEST-AIDS-214 (all-failed
  branch regression). Round 3: PASS, zero remaining issues.
- [x] Human approval of design (approver: nahisaho, exact file list shown
  via `ask_user`, hash
  `3af5ca856c4e20db56d4f569756b7a4b5cd311f8cf85e6be4409b06f7ae35bd0`).
- [x] TDD Red/Green per requirement, using a temporary stub-based revert
  of just the implementation (git stash for `ingestion.py`/
  `sensitivity.py`; a scoped temporary stub disabling the new
  ambiguity-detection branches for `insight_engine.py`/
  `notebook_audit.py`, since a full revert broke test collection via
  `ImportError` on `AmbiguousEvidenceError`) to confirm genuine failures
  before restoring the fix and confirming genuine passes:
  - REQ-AIDS-032: TEST-AIDS-203, TEST-AIDS-204.
  - REQ-AIDS-056: TEST-AIDS-205–209, TEST-AIDS-213, TEST-AIDS-214,
    TEST-AIDS-291 (added during rubber-duck re-review: `run_sensitivity`
    accepted non-finite (`NaN`/`inf`) evaluator results as a comparable
    "stable" value; fixed by rejecting them as failed specifications).
  - REQ-AIDS-010: TEST-AIDS-210, TEST-AIDS-290 (the duplicate-ID
    Japanese-message variant discovered and renamed by `trace check`).
  - REQ-AIDS-045: TEST-AIDS-211, TEST-AIDS-212, TEST-AIDS-292 (added
    during rubber-duck re-review: a `supporting_evidence` entry's own
    ambiguous resolution was implemented but untested).
- [x] Full suite: `465 passed` (`pytest tests/ -q`).
- [x] `trace build` (851 nodes, 0 diagnostics), `trace check --strict`,
  `graph index`/`graph gate` (PASS, no cycles).
- [x] `change-record` phases: impact, requirements, design, red,
  implementation, green, quality.
- [x] Release approval: explicit human sign-off (approver: nahisaho) via
  `ask_user`, approving the exact changed-file list and the manifest hash
  `04883a31e300f96a36f4a258ffd684551b7d1df56b8bc03fe567dd6e4414f501`
  (repo-wide `approval prepare release` manifest) together with all
  residual risks disclosed above. `musubix3 approval record release`
  itself cannot complete: it requires passing non-approval repo-wide
  quality checks (trace, workflow, tdd, change-history,
  change-completeness, performance, model-correspondence,
  constitution:RULE-001, input-stability) that are pre-existing failures
  on `main` itself, unrelated to CHANGE-014 — consistent with
  CHANGE-006/CHANGE-008/CHANGE-009/CHANGE-010/CHANGE-011/CHANGE-012
  precedent.
- [x] Commit (Closes #57, Closes #54, Closes #53), push, clean up worktree.

## Status

Released. Human release approval recorded (approver: nahisaho, hash
`04883a31e300f96a36f4a258ffd684551b7d1df56b8bc03fe567dd6e4414f501`);
`musubix3 approval record release` blocked only by pre-existing,
non-CHANGE-014 repo-wide diagnostics (see above), consistent with prior
precedent. Waivers were recorded for
`CHANGE_RED_UNPROVEN`/`CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD`
(all four requirements) and `CHANGE_ORDER_MIGRATION_REQUIRED`
(REQ-AIDS-010), matching the established CHANGE-006 precedent for TDD
evidence recorded chronologically before `change-record` bookkeeping. A
rubber-duck re-review of this release evidence found and the fixes above
resolved: a mischaracterization of #54's requirement-text change (see
Scope), a premature completion checklist, the `run_sensitivity`
non-finite-value bug, and a test-coverage gap for ambiguous
`supporting_evidence` entries. Full suite: `465 passed`.
