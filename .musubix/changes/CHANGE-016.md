# CHANGE-016: Add seed-variability aggregation, adoption thresholds, and holdout selection-bias evaluation (#56)

## Summary

Extend `ai_data_scientist.experiment_evaluation` with three experiment-analysis
helpers for small ML deltas that are sensitive to seed choice and selection
bias. CHANGE-016 adds repeated multi-seed comparison summaries, a
seed-variability-based adoption classifier, and a three-way holdout evaluator
that quantifies selection optimism after choosing among candidate
configurations.

## Scope

- Existing feature: `ai-data-scientist-ml`.
- Touches: `.musubix/features/ai-data-scientist-ml/requirements.md`,
  `.musubix/features/ai-data-scientist-ml/design.md`,
  `src/ai_data_scientist/experiment_evaluation.py`, and
  `tests/test_experiment_evaluation.py`.
- Keeps existing `evaluate_experiment(...)` paired-test behavior unchanged.
- Out of scope: new plotting/reporting surfaces, nested resampling frameworks,
  or additional model-selection APIs beyond the requested helpers.

## Affected Requirements

Requirements: REQ-AIDS-090, REQ-AIDS-091, REQ-AIDS-092.

These are new normative requirements for repeated seed summaries, adoption
threshold classification, and selection-bias holdout evaluation.

## Design

Design: DES-AIDS-090 (seed-summary aggregator), DES-AIDS-091 (threshold
classifier), DES-AIDS-092 (three-way holdout evaluator). ADRs: none — the
change extends the existing experiment-evaluation module directly without a new
architectural boundary.

## Implementation Plan

- [x] Verify approved requirements/design hashes for CHANGE-016.
- [x] Audit existing TDD evidence for TEST-AIDS-220/221/222 and replace
  incomplete Green evidence with genuine stub-based Red/Green cycles.
- [x] Add extra REQ-AIDS-090 coverage for optional model-seed preservation
  (`TEST-AIDS-223`) with a genuine Red/Green cycle.
- [x] Implement and verify `summarize_seed_variability`,
  `judge_improvement`, and `evaluate_selection_bias_holdout`.
- [x] Fix follow-up release blockers: derive the holdout winner from
  selection-only metrics with deterministic tie-breaking, guarantee non-empty
  three-way partitions, reject non-finite seed metrics, and cover the new
  boundary/regression cases (`TEST-AIDS-224`..`TEST-AIDS-228`) with genuine
  Red/Green cycles.
- [x] Address final rubber-duck review findings: accept array-like
  `split_seeds`, reject non-finite `judge_improvement` inputs, and update this
  status text to reflect the actual remaining gate blockers
  (`TEST-AIDS-229`/`230`).
- [x] Record CHANGE-016 change-record phases and narrowly-scoped TDD-order
  waivers caused by retroactive bookkeeping.
- [x] Rebuild trace/graph/gate evidence and update this status with final
  readiness.

## Status

Follow-up validation is complete, but the change is still not release-ready.
The focused experiment-evaluation suite now passes (`29 passed`), including
the final rubber-duck regressions for array-like `split_seeds` and non-finite
`judge_improvement` inputs (`TEST-AIDS-229`/`230`) in addition to the earlier
selection-bias/partition/boundary coverage (`TEST-AIDS-224`..`228`). The full
configured pytest suite also passes (`466 passed`).

Genuine Red/Green TDD cycles now exist for TEST-AIDS-220..230. `trace build`
passes, `graph gate` passes, and refreshed CHANGE-016 waivers keep the
bounded TDD-order findings for REQ-AIDS-090/091/092
(`CHANGE_RED_UNPROVEN`, `CHANGE_GREEN_UNPROVEN`, `CHANGE_COMPLETENESS_TDD`)
at warning severity only. Remaining blockers are unchanged repo-wide baseline
checks (notably the pre-existing `ai-genomics-scientist` trace coverage
failures and other historical gate debt), CHANGE-016's non-waivable
`CHANGE_COMPLETENESS_ADR` errors for REQ-AIDS-090/091/092, and the expected
missing release approval. A final rubber-duck review over the current diff
found no remaining actionable issues.

`CHANGE_COMPLETENESS_ADR` resolved: `ADR-0054.md` (seed-variability range
statistic), `ADR-0055.md` (three-category adoption threshold classifier), and
`ADR-0056.md` (three-way holdout selection-bias evaluator design, documenting
the selection-only winner derivation and guaranteed-non-empty-partition fix)
now cover REQ-AIDS-090/091/092 respectively, and `DES-AIDS-090`/`091`/`092`'s
`ADRs:` fields reference them. Design approval was re-recorded against the
refreshed manifest (new design manifest:
`0a8e81fff1420ece68caa4909f8216a1206038c3d81fd8dbb75f72ed76bfdceb`, approver
nahisaho). `gate --changed --json` now reports zero CHANGE-016-owned error
diagnostics (only pre-existing warnings remain).

## Release Approval

`npx musubix3 approval record release` is blocked by pre-existing repo-wide
non-approval quality checks (`trace`, `workflow`, `tdd`, `change-history`,
`change-completeness`, `performance`, `model-correspondence`,
`constitution:RULE-001`) that fail for reasons outside CHANGE-016's scope
(ai-genomics trace/TDD coverage gaps pending PR #60's merge, unreconciled
workflow history, stale CHANGE-005/CHANGE-011 waivers, legacy performance
evidence) — consistent with every prior CHANGE in this repository (006
through 017). Human release approval is therefore recorded here directly:

- **Approver**: nahisaho
- **Release artifact manifest (artifactSha256)**:
  `f92ef2c9a737bce998e04b53b6241d73c759ef92521de214a5419e00cfae6432`
- **Approved**: 2026-10-04 (via `ask_user`, file list and hash shown in full)
- **Residual risks disclosed and accepted**: the repo-wide pre-existing
  quality-check failures listed above remain outstanding and are tracked
  independently of CHANGE-016; they are not introduced or worsened by this
  change.
