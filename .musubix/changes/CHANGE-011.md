# CHANGE-011: explainability.explain_model signed contributions and permutation importance (#49)

> DRAFT — NOT YET APPROVED. This document is prepared for later human review in
> the orchestrating session. Do not treat it as approved release evidence.

## Summary

Extend `src/ai_data_scientist/explainability.py` so
`explainability.explain_model` can do more than a legacy magnitude-only global
ranking. The change keeps the existing 2-argument call behavior intact by
default, but adds:

- explicit `importance_kind` labeling for every returned ranking;
- opt-in signed local contributions with additive-consistency reporting; and
- opt-in permutation importance with configurable scoring.

The enhancement addresses issue #49's explainability gap: callers can keep the
legacy ranking where backward compatibility matters, but they also gain an
auditable route to directional/local explanations and a scale-robust global
importance method.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches:
  `.musubix/features/ai-data-scientist-ml/requirements.md`,
  `.musubix/features/ai-data-scientist-ml/design.md`,
  `src/ai_data_scientist/explainability.py`,
  `tests/test_explainability.py`.
- No change-record, approval-record, TDD-evidence, workflow-record, or gate
  ledger writes are included in this branch by design; those shared-evidence
  steps must be serialized later through `main`.
- SHAP support is planned as optional: if the environment already provides the
  `shap` package, the signed-contribution path may use it; otherwise the module
  falls back to native `pred_contrib`, linear additive decomposition, or an
  explicit instruction to use permutation importance/install SHAP.
- Signed local contributions are currently scoped to supported single-output
  regression and binary-classification models; multi-class provider outputs are
  intentionally left out of this draft's scope.

## Affected Requirements

Requirements: REQ-AIDS-082, REQ-AIDS-083, REQ-AIDS-084.

## Design

Design: DES-AIDS-070 (result contract + method selection), DES-AIDS-071
(signed-contribution provider normalization + additivity check),
DES-AIDS-072 (permutation-importance path). ADRs: none — each entry is a
localized extension of the existing explainability module with existing
library primitives.

## Implementation Plan

- [x] Draft requirements for default-compatibility labeling, signed
  contributions, and permutation importance.
- [x] Draft design for the result contract, provider-selection order, and
  permutation-importance execution path.
- [x] Validate requirements and manually rubber-duck review requirements/design,
  fixing validator/EARS issues found during review.
- [x] Add failing tests for the new opt-in explainability paths.
- [x] Implement `explain_model` method selection, result metadata, signed
  contributions, and permutation importance.
- [x] Run focused, module-level, and full-suite pytest coverage, confirming no
  regressions.
- [x] Cover SHAP-provider selection with mocked tests and ensure additivity is
  reported as unavailable when raw model outputs cannot be retrieved.
- [ ] Re-run `design validate` after fresh requirements approval is recorded by
  the orchestrating session; the current branch correctly leaves shared
  approval/evidence files untouched, so the validator is presently blocked by
  stale approval state rather than a known design-structure error.
- [ ] Hand off this draft for human approval and serialized musubix evidence
  recording in the orchestrating session.

## Status

Implementation and pytest verification are complete in this worktree. Remaining
musubix workflow steps intentionally deferred to the orchestrating session are:
(1) human review/approval for updated requirements and design, (2) the
approval-sensitive `design validate` rerun, and (3) serialized shared-evidence
ledger writes (`approval record`, `change-record`, `tdd`, `gate`,
`workflow-record`).
