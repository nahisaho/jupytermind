---
name: ai-data-scientist
description: "Use when a user asks, in Japanese or English, to load, clean, explore, analyze, visualize, or draw insights from a dataset via Jupyter. データ分析・可視化・統計・Insight抽出をJupyter上で自然言語で行う際に使用。"
---
# AI Data Scientist / AIデータサイエンティスト

Respond in the user's input language (日本語 / English) for every user-facing
message, per REQ-AIDS-001. Route execution exclusively through the Jupyter
MCP (Datalayer `jupyter-mcp-server`) tools configured for this project;
never execute analysis code outside that path (REQ-AIDS-003). The `mcp` and
`jupyter-mcp-server` packages are pinned to a narrow, verified-interoperable
minor-version range (`>=2.2,<2.3` for both) rather than an open-ended range,
so client/server MCP protocol negotiation cannot silently drift to an
untested combination (REQ-AIDS-050 / DES-AIDS-038); see
`ai_data_scientist.dependency_pins.get_dependency_specifier` for the
programmatic check.

## Scope / 対象範囲 (MVP)
Data ingestion (CSV/Excel/DB/API), cleaning, exploratory data analysis,
statistical analysis, visualization, and reasoning-based insight generation
whose evidence is always recorded inside the project notebook. See
`.musubix/features/ai-data-scientist/requirements.md` for the full,
authoritative requirement set (REQ-AIDS-001–014, 027–032). ML-extension
capabilities (clustering, AutoML, GiNZA-based Japanese NLP, etc.) live in
the separate `ai-data-scientist-ml` feature and are out of scope here.

## Workflow / 手順
1. **Resolve project & notebook** — call
   `ai_data_scientist.project_manager.resolve_project(name)` to validate the
   project identifier (ADR-0005 slug policy), then
   `ensure_notebook(handle)` to create or reuse
   `projects/<name>/notebooks/<name>.ipynb` (REQ-AIDS-002/028). The default
   `projects/` root is stable across kernel working-directory changes
   (REQ-AIDS-044): set `AI_DATA_SCIENTIST_PROJECTS_ROOT` to an absolute path
   to pin the workspace root explicitly, especially if the kernel may `cd`
   into a dataset or notebook directory during the session.
2. **Detect instruction language** — call
   `ai_data_scientist.language_router.detect_language(instruction_text)` and
   use its result for every reply and inserted markdown cell in this turn
   (REQ-AIDS-001).
3. **Execute analysis code via Jupyter MCP** — call
   `ai_data_scientist.mcp_gateway.run_and_record(client, handle, code,
   timeout_ms=30000)`. It routes execution only through the configured MCP
   client, enforces the timeout, and appends the executed cell only on
   success — never a partial/corrupted cell (REQ-AIDS-003/030/031).
4. **Ingest data** with `ai_data_scientist.ingestion.ingest(source_spec,
   fetcher=..., allowlist=..., row_limit=...)` for CSV, Excel, database, or
   API sources; non-allowlisted hosts and over-limit responses are rejected
   or truncated before load (REQ-AIDS-014/032). Write any downloaded/staged
   dataset file under `ai_data_scientist.project_manager.ensure_data_dir(handle)`
   (i.e. `handle.data_dir`), not a hand-rolled `projects/<name>/data` relative
   path — `data_dir` is anchored to the same stable workspace root as
   `notebook_path`, so it stays correct even if the kernel's working
   directory has drifted into the notebook's own directory (REQ-AIDS-049).
5. **Clean data** with `ai_data_scientist.cleaning.clean_dataset(df,
   operation=...)` (`drop_duplicates` | `drop_na` | `fillna`); report the
   returned row/column impact to the user (REQ-AIDS-004).
6. **Explore data** with `ai_data_scientist.eda.explore(df)` for dtypes,
   non-null counts, and summary statistics (REQ-AIDS-005), plus per-column
   `missing_summary` (count/ratio) and, for categorical columns,
   `categorical_summary` (unique_count and top `top_n` values with
   counts/ratios, `truncated` flag) (REQ-AIDS-043).
7. **Run statistics** with
   `ai_data_scientist.stats_analysis.correlation(df, col_a, col_b,
   language=...)`; write the resulting statistic in a code cell and its
   `interpretation` in an adjacent markdown cell (REQ-AIDS-006).
8. **Visualize** with `ai_data_scientist.visualization.render_chart(df,
   kind=..., x=..., y=..., title=..., xlabel=..., ylabel=...)` and
   `build_image_output(png_bytes)`, then append via
   `project_manager.enqueue_write` so the image MIME bundle is persisted
   in the notebook JSON (REQ-AIDS-007). `render_chart`/`record_chart` render
   locally and never execute the stored code string against the live
   Jupyter kernel (REQ-AIDS-040): only reference variables already
   established by a prior `run_and_record` call in that code string, so the
   notebook stays consistent if a human re-runs it top-to-bottom later.
   Pass Japanese (or other non-ASCII) text in `title`/`xlabel`/`ylabel`
   freely: `render_chart` automatically switches to a bundled
   Japanese-capable font the first time such text appears in a process, so
   it renders as legible glyphs instead of mojibake/placeholder boxes,
   regardless of what fonts are installed on the host (REQ-AIDS-046).
9. **Record insights with evidence** — only after executing the
   evidentiary cell, derive `cited_value` from the executed cell's actual
   output with `ai_data_scientist.insight_engine.extract_cited_value(result,
   pattern)` (REQ-AIDS-039) rather than hand-transcribing or rounding a
   number, then call
   `ai_data_scientist.insight_engine.record_insight(handle, insight_text,
   evidence_execution_count, cited_value, claim_type, language=...)`. It
   verifies the cited value actually appears in that cell's output, embeds
   a structured `evidence` manifest (execution count, cited value, claim
   type — ADR-0003) in the markdown cell, and raises
   `EvidenceMissingError` (which you must report to the user, not silently
   swallow) instead of writing an insight with no notebook-backed rationale
   (REQ-AIDS-009/010/027).
10. **Audit before handing off** — before telling the user the notebook is
    complete, run `ai_data_scientist.notebook_audit.audit_notebook(path)`
    (REQ-AIDS-045). It is read-only (never rewrites the notebook) and
    reports unexecuted/error code cells and any insight-like markdown cell
    whose evidence manifest is missing or no longer resolves to a real
    executed output. `path` may be the same workspace-root-relative path
    used elsewhere (e.g. `handle.notebook_path`); it resolves against the
    stable workspace root even if the kernel's cwd has drifted into the
    notebook's own directory, and reports a distinct, clearly-worded
    finding instead of a parse-failure finding when the path genuinely
    cannot be found (REQ-AIDS-047). Because the audit is typically run from
    inside the notebook's own still-running final cell, that one trailing,
    not-yet-executed cell is excluded from the unexecuted-cell findings
    when its source invokes `audit_notebook` — only a different unexecuted
    or error-producing cell will fail the audit (REQ-AIDS-048). If
    `report.ok` is `False`, fix the underlying cells or insights before
    finishing, rather than reporting success with unresolved findings. The
    same check is available from the shell as
    `ai-data-scientist validate-notebook <path>` for CI or manual spot
    checks.

## Constraints / 制約
- Every notebook write goes through
  `project_manager.enqueue_write`/`ensure_notebook`, which serialize
  concurrent writers and guarantee `nbformat`-valid output (REQ-AIDS-011/029).
- Never accept a project name outside the ADR-0005 slug pattern
  (`^[a-z0-9]+(-[a-z0-9]+)*$`); ask the user to choose a valid slug instead
  of silently transforming their input.
- Never fabricate an insight without a located, executed evidence cell.
- All modules are covered by TDD (pytest) per REQ-AIDS-013; run
  `.venv/bin/pytest` before considering any change to this skill complete.

## Source layout / 実装
- `src/ai_data_scientist/language_router.py` — DES-AIDS-002
- `src/ai_data_scientist/project_manager.py` — DES-AIDS-003
- `src/ai_data_scientist/mcp_gateway.py` — DES-AIDS-004
- `src/ai_data_scientist/ingestion.py` — DES-AIDS-005
- `src/ai_data_scientist/cleaning.py` — DES-AIDS-006
- `src/ai_data_scientist/eda.py` — DES-AIDS-007
- `src/ai_data_scientist/stats_analysis.py` — DES-AIDS-008
- `src/ai_data_scientist/visualization.py` — DES-AIDS-009
- `src/ai_data_scientist/insight_engine.py` — DES-AIDS-010
- `src/ai_data_scientist/notebook_audit.py` — DES-AIDS-033
- `src/ai_data_scientist/gate_config.py` — DES-AIDS-011
