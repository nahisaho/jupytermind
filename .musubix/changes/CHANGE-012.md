# CHANGE-012: render_chart に box・barh・heatmap と凡例・誤差範囲指定を追加する (#46)

## Summary

**DRAFT — NOT YET APPROVED.**

Extend `ai_data_scientist.visualization.render_chart` so benchmark cases no
longer need hand-written Matplotlib for grouped-distribution, horizontal-bar,
correlation-matrix, or confidence-interval chart outputs. This draft change
adds `box`, `barh`, and `heatmap` kinds, optional legend grouping/title
controls (`hue`, `legend_title`), optional error-range arguments (`xerr`,
`yerr`), and a `chart_metadata_from_figure(fig)` helper for wrapping
externally drawn figures as auditable `RenderedChart` outputs. Grouped
`bar`/`barh` rendering now explicitly preserves missing `hue` values as a
visible `"NaN"` legend series, and rejects duplicate `(x, hue)` rows with a
clear `ValueError` instead of silently keeping only the first row.

## Scope

- Existing feature: `ai-data-scientist` (governs `visualization.render_chart`
  and chart-audit metadata).
- Touches planned: `src/ai_data_scientist/visualization.py` and
  `tests/test_visualization.py`, plus the governing feature's
  `requirements.md` and `design.md`.
- Out of scope for this draft: panel/facet splitting API (mentioned in the
  issue background but not in the requested expected-result bullets).
- No ADR planned unless design validation uncovers an architectural trade-off
  that the current repo policy requires to be documented separately.

## Affected Requirements

Requirements: REQ-AIDS-085, REQ-AIDS-086, REQ-AIDS-087, REQ-AIDS-088.

## Design

Design: DES-AIDS-073 (new chart-kind dispatch for `box`/`barh`/`heatmap`),
DES-AIDS-074 (hue-driven grouping and legend-title capture), DES-AIDS-075
(error-range normalization and plotting), DES-AIDS-076 (Figure-to-ChartMetadata
helper). ADRs: none currently planned.

## Implementation Plan

- [x] Draft requirements/design updates for the governing
  `ai-data-scientist` feature.
- [x] Run `requirements validate`; `design validate` is currently blocked by
  musubix3's stale-approval precondition, so no approval-writing command was
  run in this parallel worktree.
- [x] Implement targeted tests first for each new requirement.
- [x] Extend `render_chart`/`ChartMetadata` and add
  `chart_metadata_from_figure`.
- [x] Run focused pytest for visualization, then the full visualization module
  regression suite.
- [ ] Leave evidence-ledger commands, approvals, and commit/push for the
  orchestrating session after review.
