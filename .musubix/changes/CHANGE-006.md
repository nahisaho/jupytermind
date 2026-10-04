# CHANGE-006: Fix six ai-data-scientist accuracy/correctness defects (#40, #42, #43, #44, #45, #47)

## Summary

Fix six reported `ai-data-scientist` skill accuracy/correctness defects,
discovered via the v0.2.3 benchmark, each with dedicated EARS requirement(s)
and design entries, implemented via TDD. Issue-to-requirement mapping:
#45 → REQ-AIDS-066, #47 → REQ-AIDS-067, #42 → REQ-AIDS-068, #44 → REQ-AIDS-069,
#43 → REQ-AIDS-070, #40 → REQ-AIDS-071 + REQ-AIDS-072 (also updates
REQ-AIDS-053's acceptance text to accommodate output-level metadata as an
additional valid audit-evidence source).

- **#45 (insight text vs. cited-value contradiction)**: `audit_notebook`
  only confirms a cited value appears in its referenced cell's output; it
  never checks whether the insight's own body text actually states that
  value (or contradicts it with a different number). Fix: a new
  warning-severity check scans the markdown body (minus evidence fences)
  for the cited value verbatim or a numerically-equal rounded restatement.
- **#47 (NaN correlation gives a confident, spurious interpretation)**:
  when `scipy_stats.pearsonr` returns NaN (e.g. a column has missing
  values), `_interpret`'s significance/magnitude branches are all `False`
  for NaN comparisons, so it falls through to a wrongly-worded "weak ...
  correlation" claim. Fix: an explicit NaN guard states the correlation
  could not be computed instead.
- **#42 (tab-separated .csv silently read as one column)**: `ingest`
  assumes a comma delimiter for every `.csv` source. Fix: sniff the
  delimiter among comma/tab/semicolon via `csv.Sniffer`; add a `warnings`
  field to `IngestionResult` and emit a mismatch warning when sniffing
  falls back to comma and still yields one suspicious column.
- **#44 (only the first evidence block/no supporting_evidence validation)**:
  `_extract_evidence_manifest` only inspects the first fenced block in a
  cell. Fix: validate every fenced block (reporting malformed blocks as
  errors) and every well-formed `supporting_evidence` entry.
- **#43 (heading-prefixed result paragraphs bypass evidence requirements)**:
  a heading-prefixed cell without an evidence fence is unconditionally
  excluded from insight-candidacy, even when it states a clear numeric
  conclusion. Fix: strip the leading heading and apply the same
  non-heading insight-candidate heuristic to what remains.
- **#40 (officially-rendered charts via build_image_output/MCP display
  flagged "unaudited")**: `build_image_output` never attaches chart
  metadata to the output it builds, and `audit_visual_outputs` only reads
  cell-level metadata, which also cannot disambiguate multiple images in
  one cell. Fix: `build_image_output` persists `RenderedChart` metadata
  into the output's own `metadata["chart"]`; `audit_visual_outputs` reads
  each image output's own metadata first, matching multiple images
  independently, falling back to cell-level metadata only for a single
  unlabeled image (REQ-AIDS-053's acceptance text updated to match).

## Scope

- Existing feature: `ai-data-scientist`.
- Touches: `src/ai_data_scientist/notebook_audit.py`,
  `src/ai_data_scientist/stats_analysis.py`,
  `src/ai_data_scientist/ingestion.py`,
  `src/ai_data_scientist/visualization.py`, and their corresponding test
  files under `tests/`.
- No new skill boundary; no ADRs (all seven new design entries are narrow
  bugfixes/extensions with "ADRs: none", consistent with the DES-AIDS-042/
  048-053 precedent).
- The remaining 7 open issues (#41, #46, #48, #49, #50, #51, #52) are
  explicitly out of scope for this change; they are tracked separately per
  the user-approved priority ordering (2 documentation-caused bugs, then 5
  feature enhancements).

## Affected Requirements

Requirements: REQ-AIDS-053, REQ-AIDS-066, REQ-AIDS-067, REQ-AIDS-068, REQ-AIDS-069, REQ-AIDS-070, REQ-AIDS-071, REQ-AIDS-072.

(REQ-AIDS-053's Statement is unchanged; only its Acceptance text was
extended to reconcile with REQ-AIDS-072's output-level-metadata fallback
rule — see rubber-duck review finding during requirements review.)

## Design

Design: DES-AIDS-054 (insight body/cited-value cross-check), DES-AIDS-055
(NaN-safe correlation interpretation), DES-AIDS-056 (delimiter-sniffing CSV
ingestion with mismatch warning), DES-AIDS-057 (exhaustive evidence-manifest
validation, multi-block + supporting_evidence), DES-AIDS-058
(heading-prefixed insight-candidate detection), DES-AIDS-059 (output-level
chart metadata persisted by build_image_output), DES-AIDS-060 (per-image
chart-metadata matching during visual audit). ADRs: none for all seven
(narrow bugfix/extension entries; see each entry's "ADRs: none"
justification).

Both requirements.md and design.md passed `musubix3` structural validation
and two rounds of native `rubber-duck` review each (requirements: fixed 3
EARS multi-obligation statements, 1 cross-requirement conflict with
REQ-AIDS-053, and under-specified acceptance criteria for #45/#42/#44/#43/
#40; design: fixed a silently-skipped-malformed-evidence-block gap, an
over-broad CSV mismatch-warning condition, a missing `import math`, a false
claim of reusing an existing sampling mechanism, and a body-check/
supporting_evidence scope disagreement) before explicit human approval of
each phase.

## Implementation Plan

- [x] Requirements (REQ-AIDS-066–072, REQ-AIDS-053 acceptance update):
  drafted, validated, rubber-duck reviewed (2 rounds), approved.
- [x] Design (DES-AIDS-054–060): drafted, validated, rubber-duck reviewed
  (2 rounds), approved.
- [x] TDD Red/Green per requirement, in order #45→#47→#42→#44→#43→#40, plus
  a dedicated red/implementation/green cycle for REQ-AIDS-053's amended
  acceptance text (dual-tagged onto `TEST-AIDS-146`). 399/399 tests
  passing, zero regressions. REQ-AIDS-066's change-record red/implementation/
  green phases were recorded out of chronological order against its TDD
  evidence (original tdd green order 588 predates change-record
  implementation order 590). A fully-corrected tdd red (order 627) and tdd
  green (order 632) independently re-prove the fix in proper Red→Green
  sequence, and the full 399-test pytest suite passes, but the immutable
  change-record phase orders (589/590/591) are locked before this later,
  properly-ordered cycle, so they fall outside the bounded-cycle order
  window the gate checks against. The resulting `CHANGE_RED_UNPROVEN`/
  `CHANGE_GREEN_UNPROVEN`/`CHANGE_COMPLETENESS_TDD` diagnostics are
  downgraded to warnings via audited `change waiver record` entries
  (approver: nahisaho).
- [x] `trace build`/`trace check --strict` (clean, `valid: true`),
  `graph index`/`graph gate` (clean, `valid: true`, no cycles).
- [x] Quality gate (`gate --changed --json`, `status --json`): overall
  `status.gate.ready` is **false**, blocked solely by `CHANGE_COMPLETENESS_ADR`
  (7 occurrences, one each for REQ-AIDS-066–072; the amended REQ-AIDS-053
  does not itself produce this diagnostic). This check is new in the
  current musubix3 version and requires a `decides`-edge ADR node for every
  design component; it is **not waivable** via `change waiver record`. All
  seven DES-AIDS-054–060 entries explicitly declare `ADRs: none` with a
  narrow-bugfix justification (no real architectural trade-off exists to
  document — authoring one would violate the design skill's "do not invent
  existing decisions" rule). This is an existing, repo-wide musubix3
  policy/tooling incompatibility — it also fires identically for CHANGE-001
  (24 occurrences) and CHANGE-004 (6 occurrences), both previously-approved,
  already-released changes — but CHANGE-006 currently carries seven
  resulting non-waivable diagnostics of its own from this same pre-existing
  gap. Tracked as a known residual-risk blocker to resolve separately (e.g.
  a future musubix3 config/precedent update), not forced here.
- [x] Final rubber-duck review of release/quality evidence + this document.
- [ ] Release approval (pending explicit human decision given the known
  `CHANGE_COMPLETENESS_ADR` gate blocker above).
