# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/)
(pre-1.0, so minor versions may still include breaking changes).

## [Unreleased]

## [0.2.2] - 2026-10-02
### Added
- Published npm package now also bundles the `ai-scientist`, `tech-writer`,
  `japanese-prose`, and `presentation-planner` Copilot Agent Skills
  (previously only `ai-data-scientist` was listed in `package.json`'s
  `files`, so `npm install`/`npx` consumers never received these skills).

## [0.2.1] - 2026-10-02
### Fixed
- `project_manager.enqueue_write` writes atomically, so a serialization
  failure can no longer leave an existing notebook truncated to 0 bytes
  (closes #27; REQ-AIDS-029).
- `insight_engine.record_insight` / `audit_notebook` can match cited values
  from a cell's `stream` stdout output, not only structured result output
  (closes #29; REQ-AIDS-009/010).
- `notebook_audit.audit_notebook` validates the evidence block of
  Markdown cells that begin with a heading, instead of skipping them
  (closes #30; REQ-AIDS-045).
- `notebook_audit.audit_visual_outputs` reports chart cells with no
  `metadata["chart"]` as a distinct "unaudited" finding instead of
  silently passing them (closes #28; REQ-AIDS-053).
- `visualization.render_chart` no longer clips long category tick labels
  or axis labels outside the saved PNG, via unconditional
  `tight_layout()`/`bbox_inches="tight"` (closes #31; REQ-AIDS-058;
  ADR-0013).
- `visualization.render_chart` reasserts the bundled Japanese
  (`japanize-matplotlib`) font on every call needing non-ASCII text,
  fixing Japanese text rendering as "tofu" boxes after a caller resets
  `matplotlib.rcParams` (closes #32; REQ-AIDS-046; ADR-0010).
### Added
- `data_definition.DataDefinitionManifest.inferred_fields()`: a derived,
  read-only query listing every field whose status is "inferred",
  mirroring `unresolved_fields()` (closes #33; REQ-AIDS-052; ADR-0011).
- Documented the Jupyter MCP concurrent-write risk in SKILL.md and
  `project_manager.enqueue_write`'s docstring: a direct `enqueue_write`
  call against a notebook simultaneously open in a Jupyter MCP session can
  be overwritten on that session's next save (closes #34; REQ-AIDS-059;
  ADR-0014; documentation only, no runtime behavior change).
- ADR-0009 through ADR-0014 formalizing the above as explicit, reviewed
  architecture decisions.

## [0.2.0] - 2026-10-02
### Added
- Cooperative run-lifecycle API (`ai_data_scientist.lifecycle`): register a
  run, mark execution/write phases, request cooperative cancellation, query
  run status, and block until a run is quiescent (closes #20;
  REQ-AIDS-051 / DES-AIDS-039).
- Structured data-definition manifest (`ai_data_scientist.data_definition`):
  records each semantic field's value with an explicit
  verified/inferred/reported/unknown status, and surfaces unresolved fields
  so an inferred unit/definition is never silently treated as confirmed
  (closes #21; REQ-AIDS-052 / DES-AIDS-040).
- Visual-readability audit extension to `notebook_audit.audit_notebook`
  (opt-in `visual_audit=True`): flags charts with missing glyph metadata,
  missing title/axis-label/legend metadata, or a near-empty-looking image,
  via a byte-density heuristic that intentionally avoids adding a new
  imaging dependency (closes #22; REQ-AIDS-053 / DES-AIDS-041).
- Analysis-assumptions and applicability manifest
  (`ai_data_scientist.analysis_assumptions`): records conclusion-critical
  assumptions with a verified/tested/assumed/rejected status and a
  descriptive/associational/causal scope, and flags causal conclusions
  lacking a tested/verified identification assumption, plus any unresolved
  conclusion-critical risk (closes #23; REQ-AIDS-054 / DES-AIDS-042).
- Semantic data-quality checks (`ai_data_scientist.data_quality`):
  schema-driven `detect_anomalies` (range/allowed-values/not-null/unique
  constraints) distinct from the existing statistical z-score detector, plus
  `validate_anomalies` to cross-check against an independent reference
  dataset (closes #24; REQ-AIDS-055 / DES-AIDS-043).
- Reusable sensitivity-analysis plans (`ai_data_scientist.sensitivity`):
  `SensitivityPlan`/`run_sensitivity` re-run an analysis function across a
  bounded grid of alternative specifications and report whether the
  conclusion is stable within a tolerance (closes #25;
  REQ-AIDS-056 / DES-AIDS-044).
- Independent-dataset overlap comparison
  (`ai_data_scientist.dataset_validation.compare_datasets`): key-overlap and
  per-column agreement checks against an already-loaded candidate dataset.
  Automated dataset *discovery* (e.g. searching an external catalog) was
  explicitly scoped out per design review and is not implemented (closes
  #26, narrowed scope; REQ-AIDS-057 / DES-AIDS-045).

## [0.1.5] - 2026-10-01
### Changed
- Narrowed the `mcp` and `jupyter-mcp-server` dependency specifiers from
  open-ended ranges (`mcp>=2,<3`, `jupyter-mcp-server>=2.2`) to the exact
  minor-version range verified to interoperate in this repository's test
  suite (`>=2.2,<2.3` for both), preventing a silent upgrade to an untested
  client/server combination whose negotiated MCP protocol version may not
  be compatible (addresses the in-repo dependency-pinning portion of #17;
  REQ-AIDS-050 / DES-AIDS-038). The remaining part of #17 — a benchmark
  harness (`.benchmark-runner.py`) misreporting success on semantic
  failure — lives outside this repository and is not addressed here.
- Added `packaging` as an explicit runtime dependency (previously only an
  indirect/tooling dependency) so the new dependency-pin check can parse
  version specifiers without relying on an undeclared transitive package.

### Added
- `ai_data_scientist.dependency_pins.get_dependency_specifier` reads the
  raw version specifier declared for a package in `pyproject.toml`'s
  `[project].dependencies` array, used to assert the MCP stack pins stay
  bounded on both sides and that the installed versions satisfy them
  (CODE-AIDS-059).

## [0.1.4] - 2026-10-01
### Fixed
- `notebook_audit.audit_notebook` now resolves a relative notebook path
  against the same stable workspace root `resolve_project` uses when it does
  not resolve under the current working directory, and reports a distinct
  unresolved-path finding instead of conflating it with a parse failure
  (closes #13, REQ-AIDS-047 / DES-AIDS-035).
- `notebook_audit.audit_notebook` no longer reports a false failure for the
  one documented self-audit pattern: a notebook's own trailing, still-running
  cell that invokes `audit_notebook` is excluded from the unexecuted-cell
  findings that determine `report.ok` (closes #14, REQ-AIDS-048 / DES-AIDS-036).

### Added
- `ProjectHandle` now exposes a stable, workspace-root-anchored `data_dir`
  field (`root / "data"`) and a matching `project_manager.ensure_data_dir`
  helper, so dataset files land under the same stable project root as the
  notebook instead of being derived from a possibly-drifted kernel cwd
  (closes #15, REQ-AIDS-049 / DES-AIDS-037).

## [0.1.3] - 2026-10-01
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

[Unreleased]: https://github.com/nahisaho/jupytermind/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/nahisaho/jupytermind/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/nahisaho/jupytermind/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nahisaho/jupytermind/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nahisaho/jupytermind/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nahisaho/jupytermind/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nahisaho/jupytermind/releases/tag/v0.1.0
