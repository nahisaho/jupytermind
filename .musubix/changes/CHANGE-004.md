# CHANGE-004: Fix four ai-data-scientist defects (#35, #36, #37, #38)

## Summary

Fix four reported `ai-data-scientist` skill defects, each with a dedicated
EARS requirement and design entry, implemented via TDD. Issue-to-requirement
mapping: #35 → REQ-AIDS-060/061, #36 → REQ-AIDS-062, #37 → REQ-AIDS-063/065,
#38 → REQ-AIDS-064.

- **#35 (chart audit metadata)**: `render_chart` currently returns a bare
  `bytes` object, so the title/axis-label/legend/missing-glyph metadata used
  to author a chart is lost before `record_chart` persists cell metadata for
  visual audit. Fix: `render_chart` returns a `RenderedChart(bytes)` subclass
  carrying a `ChartMetadata` payload (with forwarding read-only properties),
  and `record_chart` detects this subclass and persists `.chart_metadata`
  into `cell["metadata"]["chart"]`.
- **#36 (dataset-comparison agreement rate)**: `compare_datasets` currently
  returns a misleading `agreement_rate` of `1.0` when zero rows overlap
  between primary and candidate datasets on the join key, and separately
  mishandles null-key rows (two `None` keys incorrectly count as a matched
  key pair due to Python tuple-set equality). Fix: `ColumnComparison.
  agreement_rate` becomes `float | None` (`None` when a column has zero
  eligible joined rows), and null-key rows are excluded from both
  `matched_keys`/`primary_only_keys`/`candidate_only_keys` computation and
  the per-column comparison merge.
- **#37 (significance-aware correlation interpretation)**: `correlation`'s
  interpretation text currently ignores statistical significance and
  displays raw p-values with excessive/misleading precision for very small
  values. Fix: add a `significance_threshold` parameter (default `0.05`) so
  `_interpret` produces a non-significant-aware template, and add a shared
  `p_display(p_value)` helper producing a "p < 1e-4"-style bounded display
  for very small p-values, used consistently in both branches.
- **#38 (Japanese font coverage)**: `render_chart`'s bundled-Japanese-font
  trigger currently inspects only the caller-supplied `title`/`xlabel`/
  `ylabel` strings for non-ASCII characters, missing Japanese text that
  appears only in plotted data values, tick labels, legend entries, or
  pandas-auto-generated axis labels (column names/index name). Fix: widen
  the trigger by OR-ing the existing `_contains_non_ascii(title/xlabel/
  ylabel)` check (preserved, unmodified, per REQ-AIDS-046) with a new
  `_contains_japanese` check over the selected `x`/`y` column values, index
  values, legend-source column names, and pandas-auto-generated axis-label
  sources (selected `x`/`y` column names, `df.index.name` when `x` is
  unset).

## Scope

- Existing feature: `ai-data-scientist`.
- Touches: `src/ai_data_scientist/visualization.py`,
  `src/ai_data_scientist/dataset_validation.py`,
  `src/ai_data_scientist/stats_analysis.py`, and their corresponding test
  files under `tests/`.
- No new skill boundary; no ADRs (all six design entries are narrow
  bugfixes with "ADRs: none", consistent with the DES-AIDS-042 precedent).
- Issue #39 (an external `musubix3` tooling limitation discovered during
  CHANGE-003) is explicitly out of scope for this change; it is a
  documentation-tracked, deferred, external-tool issue, not an
  `ai-data-scientist` code defect.

## Affected Requirements

Requirements: REQ-AIDS-060, REQ-AIDS-061, REQ-AIDS-062, REQ-AIDS-063, REQ-AIDS-064, REQ-AIDS-065.

## Design

Design: DES-AIDS-048 (RenderedChart/ChartMetadata subclass for render_chart),
DES-AIDS-049 (record_chart persists chart metadata via isinstance detection),
DES-AIDS-050 (dataset-comparison agreement rate as float | None, with
null-key exclusion fix), DES-AIDS-051 (significance-aware correlation
interpretation), DES-AIDS-052 (bundled Japanese font applied for the full
rendering lifetime, widened OR-combined trigger), DES-AIDS-053 (shared
p_display bounded p-value formatting). ADRs: none for all six (narrow
bugfix/data-structure entries; see each entry's "ADRs: none" justification).

Both requirements.md and design.md passed `musubix3` structural validation
and multiple rounds of native `rubber-duck` review (one round for
requirements; eight rounds for design, fixing real provenance/type/
precision/null-handling/Unicode-coverage/merge-column defects each round)
before explicit human approval of each phase.

## Implementation Plan

- [x] Requirements (REQ-AIDS-060–065): drafted, validated, rubber-duck
  reviewed, approved.
- [x] Design (DES-AIDS-048–053): drafted, validated, rubber-duck reviewed
  (8 rounds), approved.
- [x] TDD Red/Green per requirement, in order #35/#36→#37→#38.
- [x] `trace build`/`trace check --strict`, `graph index`/`graph gate`.
- [x] Quality gate (`gate --changed --json`, `status --json`): all
  `requiredChecks` (requirements, design, constitution, trace, graph,
  commands) pass. A `musubix3` trace-scanner defect (an unescaped
  apostrophe inside a `#` comment/docstring masks all subsequent `@id`
  annotations as a fake string literal until the next quote character)
  required fixing test-file wording after some Red/Green phases had
  already been captured in the append-only hash-chained evidence ledger,
  which cannot be re-recorded for an already-recorded requirement batch.
  The `tdd`/`change-history`/`change-completeness` checks (none of them in
  `requiredChecks`) therefore continue to emit non-required diagnostics
  for all six requirements — 6 `CHANGE_RED_UNPROVEN`, 6
  `CHANGE_GREEN_UNPROVEN`, 3 `CHANGE_ORDER_MIGRATION_REQUIRED`, and 2
  `CHANGE_TEST_CHANGED_AFTER_RED` — because the recorded Red/Green
  fingerprints no longer hash-match the corrected current test sources.
  17 `change waiver record` entries (approver: nahisaho; see
  `.musubix/evidence/change-waivers.json`) authorize accepting that
  mismatch, each documenting the apostrophe-fix cause and re-verified by a
  full `pytest` pass and `trace check --strict` PASS against the current
  source; the waivers do not restore hash-verifiability of the original
  ledger entries. `CHANGE_COMPLETENESS_ADR` remains a separate, expected
  non-blocking finding consistent with each design entry's own "ADRs:
  none" exemption.
- [x] Final rubber-duck review of release/quality evidence + this document.
- [ ] Release approval.
