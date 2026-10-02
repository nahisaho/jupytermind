# CHANGE-002: Fix ai-data-scientist defects and gaps found by v0.2.0 benchmark

## Summary

Address 8 GitHub issues (#27-#34) discovered during the ai-data-scientist
v0.2.0 benchmark (50 experiments). Four are defect corrections against
existing, already-approved requirement text (no specification change
required). Four expose genuine gaps or new capability requests and require
requirements/design updates with explicit human approval before
implementation; one of those four (#34) is documentation-only (root cause
unconfirmed, no code fix mandated).

## Scope

- Existing feature: `ai-data-scientist`.
- No new skill or module boundary introduced.
- Touches: `project_manager.py`, `notebook_audit.py`, `insight_engine.py`,
  `visualization.py`, `data_definition.py`, `SKILL.md`.

## Affected Requirements

Requirements: REQ-AIDS-029, REQ-AIDS-053, REQ-AIDS-009, REQ-AIDS-010, REQ-AIDS-045, REQ-AIDS-058, REQ-AIDS-046, REQ-AIDS-052, REQ-AIDS-059.

## Per-Issue Classification

### Defect corrections — requirement text unchanged, straight to TDD

- **#27** `enqueue_write` non-atomic write can truncate/lose notebook
  content when serialization fails mid-write.
  Violates REQ-AIDS-029 ("...the system shall serialize their writes so no
  cell or output from either session is lost or corrupted."). Fix:
  serialize to string first, write to temp file in same directory, fsync,
  then `os.replace()`; never touch the original file on serialization
  failure.

- **#29** `insight_engine._find_evidence_cell` only scans
  `execute_result`/`display_data` output `data` fields, ignoring `stream`
  (print) output text, so insights backed only by printed evidence are
  wrongly withheld.
  Violates REQ-AIDS-009/REQ-AIDS-010 (an executed cell whose stream output
  genuinely contains the cited value IS an "executed evidentiary cell";
  failing to search it is a search-method defect, not a specification
  gap). Fix: also scan `output.text` for `stream` outputs.

- **#30** `notebook_audit._looks_like_insight_candidate` excludes any
  markdown cell starting with `#` even if it contains a fenced
  ` ```evidence ` block, letting malformed evidence in heading-prefixed
  cells bypass validation.
  Violates REQ-AIDS-045 ("for every markdown cell carrying or expected to
  carry an evidence manifest..."); a cell containing an evidence block is
  "carrying" one regardless of a leading heading. Fix: also treat a cell
  as a candidate when it contains a ` ```evidence ` fence.

- **#32** `visualization.render_chart`'s Japanese-font configuration is
  not reasserted per call, so a caller resetting matplotlib's global
  `rcParams` (e.g. `plt.rcdefaults()`) between calls causes subsequent
  Japanese text to render as "tofu" boxes.
  Violates REQ-AIDS-046 ("...the system shall configure matplotlib to use
  a bundled Japanese-capable font **for that rendering**" — implies
  per-call, not one-time, configuration). Fix: apply the font
  configuration unconditionally at the start of every `render_chart` call.

### Requirement/design updates required — approval gate before implementation

- **#28** `audit_visual_outputs` silently returns no findings for a
  chart-output cell whose code cell carries no `metadata["chart"]` at all,
  making "not audited" indistinguishable from "audited and passing".
  REQ-AIDS-053's existing acceptance criteria only exercise the
  metadata-present case; add a new acceptance clause defining a distinct
  "unaudited" finding for chart-bearing cells with no `metadata["chart"]`.

- **#31** `render_chart` does not call `tight_layout`/
  `bbox_inches="tight"`, so long tick/axis labels can be clipped outside
  the saved image bounds.
  No existing requirement constrains chart layout/legibility beyond
  "renders... into the cell output" (REQ-AIDS-007). Add new
  REQ-AIDS-058 requiring non-clipped axis/tick/title text in the saved
  image.

- **#33** `DataDefinitionManifest.unresolved_fields()` only surfaces
  `status == "unknown"` fields; there is no way to also list
  `status == "inferred"` (unconfirmed-but-assumed) fields.
  Treated by the issue itself as an enhancement. Add an acceptance clause
  to REQ-AIDS-052 for a manifest-level check that separately surfaces
  "inferred" fields without conflating them with "unknown" ones.

- **#34** Writing directly to a notebook via `enqueue_write` while the
  same file is open in Jupyter MCP can be overwritten/lost when the
  MCP-side Jupyter server later saves. Root cause unconfirmed
  ("帰属未確定" per the issue). Add new REQ-AIDS-059: a documentation-only
  requirement that SKILL.md and the project_manager module document the
  concurrent-external-editor risk and recommended mitigation. No code
  fix; no TDD cycle (documentation-only change).

## Rationale

All 8 issues affect the same existing feature and were discovered by one
benchmark run; a single CHANGE groups them while still allowing
independent TDD batches per issue/requirement for `red`/`implementation`/
`green`.
