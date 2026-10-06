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
3. **Execute analysis code via Jupyter MCP** — `run_and_record` is a
   **host-side** API: it takes an in-process `MCPClient` object (anything
   exposing `.execute(code) -> dict`) and is meant for a Python process that
   holds its own direct connection to the Jupyter MCP server/kernel. If
   your own process has such a client, call
   `ai_data_scientist.mcp_gateway.run_and_record(client, handle, code,
   timeout_ms=30000)`; it routes execution only through that client,
   enforces the timeout, and appends the executed cell only on success —
   never a partial/corrupted cell (REQ-AIDS-003/030/031).

   If instead you are a Copilot CLI (or similar) agent that executes code
   by calling Jupyter MCP tools directly (e.g. `insert_execute_code_cell`)
   — with no in-process `MCPClient` instance of your own to pass in — do
   **not** try to construct/pass a client whose transport would submit work
   synchronously back into the same kernel that is executing it (risks
   deadlock/reentrancy). `run_and_record` itself cannot run in that case, so
   you are responsible for reproducing its guarantees yourself: no
   partial/corrupted cell on failure or timeout, and the user is notified on
   failure (REQ-AIDS-003/030/031) — lifecycle calls alone do **not** provide
   this; they only track run/cancellation state. At minimum: call
   `register_run(run_id, handle.notebook_path)`, then
   `mark_execution_start(run_id)` before invoking the MCP tool. On success,
   call `mark_execution_end(run_id)` and then `mark_completed(run_id)`. On a
   failure that truly corresponds to the kernel execution having stopped, call
   `mark_execution_end(run_id)` and `mark_failed(run_id)` **and** ensure the
   MCP tool did not leave a partial/corrupted cell (e.g. delete it if it did)
   and surface the failure to the user — do not rely on
   `insert_execute_code_cell` alone to guarantee this (see step 11 for the
   full lifecycle-call set, including `mark_write_start`/`mark_write_end`
   if the same tool call also writes the notebook). If a direct-MCP-tool
   timeout only means the host stopped waiting for output and the kernel may
   still be running, do **not** immediately clear lifecycle execution state as
   though the cell had finished; first confirm real completion by the methods
   in step 11, then close the lifecycle record consistently with the actual
   outcome. Note the fallback explicitly in the notebook or hand-off notes
   (e.g. "executed via MCP tool, not run_and_record") so later audits are not
   misled into assuming a host-side client was used.

   **Known ordering constraint (jupyter-mcp-server cache coherency,
   Issue #75)**: `insert_execute_code_cell` keeps its own in-memory cached
   notebook model, while `insight_engine.record_insight`/
   `visualization.record_chart` (step 9/8) write directly to the notebook
   file on disk, bypassing that cache. If a direct-write call is
   immediately followed by another `insert_execute_code_cell` call in the
   same session, jupyter-mcp-server's cache can be stale relative to the
   file it just missed, so the next `insert_execute_code_cell` call may
   report success without actually appending a cell (silently dropped), and
   a caller that retries by polling cell count can end up inserting a
   genuine duplicate once the cache catches up. Until this cache-coherency
   issue is fixed upstream, there is **no supported safe way to interleave
   them**: in a given MCP/Jupyter session, complete every
   `insert_execute_code_cell` call you need before making any
   `record_insight`/`record_chart` direct write, and once a direct write has
   occurred, do not issue another `insert_execute_code_cell` call in that
   same session. Retrying an `insert_execute_code_cell` call after a direct
   write (e.g. by polling cell count) does not reliably avoid the duplicate
   described above and must not be used as a workaround. If an insight
   needs to be recorded between two dependent live-execution steps,
   restructure the work into a new session/kernel handle for the
   remaining `insert_execute_code_cell` calls instead.
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
   non-null counts, and summary statistics (REQ-AIDS-005). The returned
   `EDAReport` object exposes two further attributes — `EDAReport.missing_summary`
   (per-column count/ratio) and, for categorical columns,
   `EDAReport.categorical_summary` (unique_count and top `top_n` values with
   counts/ratios, `truncated` flag) (REQ-AIDS-043) — read them off the
   object returned by `explore()`; there is no separate
   `eda.missing_summary(...)` function to import.
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
   established by a prior successful MCP-routed execution (via
   `run_and_record`, or the direct-MCP-tool fallback from step 3) in that
   code string, so the notebook stays consistent if a human re-runs it
   top-to-bottom later.
   Pass Japanese (or other non-ASCII) text in `title`/`xlabel`/`ylabel`
   freely: `render_chart` automatically switches to a bundled
   Japanese-capable font the first time such text appears in a process, so
   it renders as legible glyphs instead of mojibake/placeholder boxes,
   regardless of what fonts are installed on the host (REQ-AIDS-046).
   **Concurrent-write risk**: calling `enqueue_write` directly against a
   notebook file that a human has simultaneously open in a Jupyter MCP
   session can be silently overwritten when that MCP session later saves
   its own in-memory copy (REQ-AIDS-059). Prefer routing writes through the
   active MCP session instead, or ask the human to pause MCP-side saves
   while this skill writes to the notebook file directly.
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
    checks. For a stricter pre-handoff pass, call
    `ai_data_scientist.notebook_audit.audit_notebook(path, visual_audit=True)`
    (REQ-AIDS-053) to additionally flag charts with missing glyph metadata,
    missing title/axis-label/legend metadata, or a near-empty-looking image
    (a byte-density heuristic, not an exact pixel scan — see
    `audit_visual_outputs`), surfaced in `report.visual_findings`.
11. **Manage long-running or cancellable work** — for any analysis that may
    run long enough that a user wants to cancel it, or that writes to the
    notebook from a background task, call
    `ai_data_scientist.lifecycle.register_run(run_id, handle.notebook_path)`
    first (both arguments are required), call
    `mark_execution_start`/`mark_execution_end` (and
    `mark_write_start`/`mark_write_end`) around the corresponding work, check
    `is_cancel_requested(run_id)` between steps, and call
    `mark_completed`/`mark_failed` at the end. A caller elsewhere can call
    `request_cancel(run_id)` (cooperative only — it cannot interrupt a cell
    already executing in the kernel) and `wait_for_quiescence(run_id)` to
    wait until that run becomes quiescent **or** the supplied timeout elapses;
    inspect the returned status before assuming execution/write activity has
    fully settled (REQ-AIDS-051). For Copilot CLI / direct-Jupyter-MCP operation,
    `insert_execute_code_cell`-style tools may stop waiting for output after
    roughly 120 seconds even while the kernel keeps running the cell; treat
    that as **execution still unconfirmed**, not as proof that the run is
    finished. Therefore:
    - Split any work likely to exceed that wait window into restartable units
      such as fold-by-fold training, stage-by-stage preprocessing, or
      checkpointed batch chunks, with each unit persisting its own durable
      output before the next unit begins.
    - After any host/tool timeout, **do not execute another cell yet**. First
      confirm completion with an actual idle/quiescent signal: the active MCP
      session reports the kernel as idle if that capability is truly available
      in your environment, and/or your own orchestration still shows full
      lifecycle quiescence. `lifecycle.get_run_status` /
      `wait_for_quiescence` are useful only when your orchestration keeps the
      lifecycle counters aligned with the kernel's real completion state; in
      the simple direct-tool fallback where a timeout path immediately runs
      `mark_execution_end`/`mark_failed`, those lifecycle calls alone are **not**
      sufficient proof that the kernel is idle. When you do rely on lifecycle
      state, require full quiescence (`active_cell_executions == 0`,
      `pending_notebook_writes == 0`, and `locks_held == 0`), not just the
      first two counters. A durable result/checkpoint file is valuable for
      resume/restart, but by itself does **not** prove that the timed-out cell
      has finished; if no real idle/quiescent signal is available yet,
      completion remains unconfirmed and you still must not submit another
      cell on that kernel. In that situation, treat the current kernel/session
      as unsafe to reuse for follow-up cells and resume only from the latest
      durable checkpoint/cache/result shard in a fresh kernel/session (or
      another execution context whose clean idle state you can actually
      verify).
    - If the run was cancelled or interrupted, resume from the latest durable
      cache/checkpoint/result shard (for example a completed fold's model or
      metrics file) instead of restarting the whole job in one giant cell.
      Prefer idempotent chunks that can be skipped safely when their output
      already exists.
12. **Record what each field actually means** — before relying on a
    column's unit or definition in an insight, build a
    `ai_data_scientist.data_definition.DataDefinitionManifest` via
    `build_manifest(...)`, recording each semantic field's value plus a
    status of `verified` (confirmed against a data dictionary/source),
    `inferred` (inferred from values/name), `reported` (as stated by the
    user), or `unknown`. Call `manifest.unresolved_fields()` and surface any
    `unknown`/`inferred` fields as caveats rather than presenting them as
    verified facts (REQ-AIDS-052).
13. **Record assumptions and causal scope** — for any conclusion that
    depends on a non-obvious analytical choice (sampling, preprocessing,
    causal interpretation), build an
    `ai_data_scientist.analysis_assumptions.AnalysisAssumptionManifest`
    (one `Assumption` per choice, with a `status` of `verified`/`tested`/
    `assumed`/`rejected`, and `causal_scope` of `descriptive`/
    `associational`/`causal`). Call `check_manifest(manifest)` and report
    every returned finding to the user — in particular, never present a
    `causal` conclusion without a `tested`/`verified` identification
    assumption, and flag any conclusion-critical assumption left `assumed`
    or `rejected` (REQ-AIDS-054).
14. **Check for semantic data-quality issues** — beyond the statistical
    z-score check in `anomaly_detection.detect_anomalies`, use
    `ai_data_scientist.data_quality.detect_anomalies(df, schema={...})` to
    check declarative per-column constraints (`min`/`max`, `allowed`
    categories, `not_null`, `unique`). When an independent reference
    dataset is available, call
    `validate_anomalies(primary, reference, columns, tolerance=...)` to
    confirm a detected anomaly isn't an artifact of the primary dataset
    alone (REQ-AIDS-055).
15. **Test conclusion stability** — before stating a conclusion as robust,
    define an `ai_data_scientist.sensitivity.SensitivityPlan(target_claim=
    "...", parameter_grid={...}, max_runs=...)` covering the alternative
    specifications that matter (model choice, subset, parameters), and
    call `run_sensitivity(plan, analysis_fn, stability_tolerance=...)`.
    Report the target claim together with `report.stable` and
    `report.max_relative_deviation` to the user;
    `SensitivityBudgetExceededError` means the grid must be narrowed rather
    than silently truncated (REQ-AIDS-056).
16. **Compare against an independent dataset** — when the user supplies or
    names a second, already-loaded dataset to validate findings against,
    call `ai_data_scientist.dataset_validation.compare_datasets(primary,
    candidate, key_mapping, value_mapping, candidate_relationship=...)` to
    report key overlap and per-column agreement. Automated dataset
    *discovery* (e.g. searching an external catalog such as Kaggle) is out
    of scope for this module — the caller must load the candidate dataset
    first (REQ-AIDS-057).
17. **Analyze spectral/signal peaks** — when the user has 1-D
    spectrum-like data (x/y pairs such as wavelength/intensity or
    time/amplitude), first remove the background with
    `ai_data_scientist.signal_analysis.baseline_correct(x, y,
    method="linear"|"asls")` (`"linear"` anchors the two endpoints;
    `"asls"` runs a fixed-parameter Asymmetric Least Squares fit for
    curved backgrounds), then call
    `ai_data_scientist.signal_analysis.find_spectral_peaks(x, y,
    prominence_frac=..., window=...)` to get a list of
    `{"position", "fwhm", "prominence", "height"}` dicts, one per
    detected peak, ordered by ascending `position` (set `window`, an odd
    integer >= 5, to apply Savitzky-Golay smoothing before peak-finding
    on noisy data) (REQ-AIDS-094, REQ-AIDS-095). To check whether a peak
    count/position conclusion is robust to the detection parameters,
    build a plan with
    `ai_data_scientist.signal_analysis.build_peak_sensitivity_plan(x, y,
    prominence_fracs=[...], windows=[...], target_claim="...")`, which
    returns a ready-to-use `(SensitivityPlan, analysis_fn)` pair — pass
    both straight into `sensitivity.run_sensitivity` exactly as in step 15
    with no extra glue code required (REQ-AIDS-096).

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
- `src/ai_data_scientist/notebook_audit.py` — DES-AIDS-033, DES-AIDS-041
- `src/ai_data_scientist/gate_config.py` — DES-AIDS-011
- `src/ai_data_scientist/dependency_pins.py` — DES-AIDS-038
- `src/ai_data_scientist/lifecycle.py` — DES-AIDS-039
- `src/ai_data_scientist/data_definition.py` — DES-AIDS-040
- `src/ai_data_scientist/analysis_assumptions.py` — DES-AIDS-042
- `src/ai_data_scientist/data_quality.py` — DES-AIDS-043
- `src/ai_data_scientist/sensitivity.py` — DES-AIDS-044
- `src/ai_data_scientist/dataset_validation.py` — DES-AIDS-045
- `src/ai_data_scientist/signal_analysis.py` — DES-AIDS-094
