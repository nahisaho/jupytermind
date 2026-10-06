# CHANGE-027: Clarify `EDAReport.missing_summary` is a return-value field, not a standalone function

## Summary

Fixes GitHub Issue #73. `SKILL.md` documents `ai_data_scientist.eda.explore(df)`
and, in the same sentence, mentions `missing_summary` and `categorical_summary`
without making explicit that these are **fields of the `EDAReport` object
returned by `explore()`**, not separately importable functions such as
`ai_data_scientist.eda.missing_summary`. A user following the documentation
attempted to use `eda.missing_summary` as a standalone symbol, which does not
exist and fails (the exact failure mode depends on the access form — e.g.
`AttributeError` on direct attribute access, or `ImportError` for
`from ai_data_scientist.eda import missing_summary`); the session
self-recovered by falling back to `eda.explore`, but the
documentation/implementation mismatch is a recurring risk for future readers.

## Classification

Documentation-only change. No requirement statement or implementation
behavior changes — `REQ-AIDS-005` and `REQ-AIDS-043` already correctly specify
that `explore()` returns these fields. Only the SKILL.md prose is revised for
clarity. TDD is not applicable (no code/behavior change); this is recorded per
the `sdd-change` skill's documentation-only exception.

## Scope

- `.github/skills/ai-data-scientist/SKILL.md`: reword step 6 to state
  explicitly that `missing_summary` and `categorical_summary` are accessed as
  `EDAReport.missing_summary` / `EDAReport.categorical_summary` attributes on
  the object returned by `explore(df)`, not standalone importable symbols.

## Requirements

No requirement IDs are added, changed, or reinterpreted by this change.

## Out of scope

- Any change to `src/ai_data_scientist/eda.py` behavior (already correct).
