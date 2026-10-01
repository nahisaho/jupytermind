# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/)
(pre-1.0, so minor versions may still include breaking changes).

## [Unreleased]
### Added
- Japanese (and other non-ASCII) chart title/axis-label support in
  `visualization.render_chart`, using a bundled font (`japanize-matplotlib` /
  IPAexGothic) so text renders correctly regardless of host fonts
  (REQ-AIDS-046 / DES-AIDS-034).

## [0.1.2] - 2026-10-01
### Fixed
- `project_manager.resolve_project` now resolves its default `projects_root`
  independently of the process's current working directory at call time,
  preventing nested `projects/<slug>/notebooks/projects/<slug>` paths when
  the kernel cwd drifts. Configurable via `AI_DATA_SCIENTIST_PROJECTS_ROOT`
  (closes #11, REQ-AIDS-044 / DES-AIDS-032).

### Added
- `notebook_audit.audit_notebook()`: a read-only audit of a project notebook
  reporting nbformat validity, unexecuted/error code cells, chart outputs,
  and missing/stale insight evidence manifests. Exposed via
  `ai-data-scientist validate-notebook <path>` (closes #12,
  REQ-AIDS-045 / DES-AIDS-033).

## [0.1.1] - 2026-10-01
### Fixed
- `mcp_gateway.execute_cell` no longer blocks the caller waiting for a slow
  worker thread to finish after a timeout; it now returns promptly and lets
  the worker shut down in the background (closes #9).

### Added
- `eda.explore()` now reports a categorical column distribution summary and
  an explicit missing-value summary (including all-missing columns), with a
  configurable `top_n` truncation (closes #10).

## [0.1.0] - 2026-09
Initial public release of the AI Data Scientist GitHub Copilot Agent Skill:
natural-language (Japanese/English) data analysis over a Jupyter MCP server,
with reasoning-based insights recorded as evidence-backed notebook cells,
per-project notebooks, and an npm-distributed bootstrap for the Python
environment.

### Fixed (post-MVP hardening, pre-0.1.1)
- `clustering.cluster_or_reduce`: unhandled `sklearn` `ValueError` when
  `n_clusters > n_samples` (closes #1).
- `timeseries.analyze_time_series`: unhandled `statsmodels` `ValueError` on
  short series for forecasting (closes #2).
- `report_export` PDF format requiring system `xelatex`/TeX is now documented
  with a clear, actionable error instead of an opaque failure (closes #3).
- `mcp_gateway.run_and_record` now always stamps a non-null
  `execution_count`, satisfying REQ-AIDS-009's acceptance criterion
  (closes #4).
- Added `visualization.record_chart()` as a convenience helper to persist
  chart/image outputs to the notebook, parallel to `run_and_record`
  (closes #5).
- `insight_engine.extract_cited_value()` added to derive `cited_value` from
  an executed cell's actual output, avoiding hand-transcription mistakes
  (closes #6).
- `visualization.record_chart()` no longer records a code cell as
  "executed" without a real kernel execution behind it (closes #7).
- `mcp_runtime`: added a bounded polling helper to wait for full termination
  after `stop()` (closes #8).

[Unreleased]: https://github.com/nahisaho/jupytermind/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/nahisaho/jupytermind/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nahisaho/jupytermind/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nahisaho/jupytermind/releases/tag/v0.1.0
