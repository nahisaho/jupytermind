---
schemaVersion: 1
feature: ai-data-scientist
---
# Requirements / 要求 (MVP)

Feature: MVP scope of the GitHub Copilot Agent Skill "AI Data Scientist" that
lets a user perform natural language data analysis (Japanese or English)
through a Jupyter MCP server (Datalayer jupyter-mcp-server), recording every
analysis step and every reasoning-based insight as notebook cells inside a
per-project notebook. Advanced modeling and analytics capabilities are tracked
separately in the `ai-data-scientist-ml` feature so this MVP boundary stays
independently shippable and testable (see rubber-duck review: scope risk).

## REQ-AIDS-001: Bilingual instruction support / 日英両対応の指示理解
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user submits an analysis instruction in Japanese or English, the system shall respond in the same language as that instruction.
Acceptance: A test feeds 10 paired Japanese/English prompts and asserts the assistant response language matches the input language in all 10 cases.

## REQ-AIDS-002: Project-scoped notebook creation / プロジェクト単位のNotebook作成
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user starts analysis work for a project with no existing notebook, the system shall create a notebook file at projects/<project_name>/notebooks/<project_name>.ipynb before executing any analysis cell.
Acceptance: Starting analysis on a new project name creates exactly one ipynb file at the expected path, and starting analysis again on the same project reuses the existing file instead of creating a duplicate.
Formal: {"kind":"conditional","condition":"notebook_missing","consequence":"create_notebook"}

## REQ-AIDS-003: Jupyter MCP execution backend / Jupyter MCP実行バックエンド
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall execute all analysis code through the configured Jupyter MCP server tools against the project notebook kernel.
Acceptance: A test instruments MCP tool calls during an analysis session and asserts 100 percent of code execution requests are routed through the configured jupyter-mcp-server tools.

## REQ-AIDS-004: Data cleaning operations / データクリーニング操作
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a data cleaning operation, the system shall execute a notebook code cell performing that operation and report the row and column impact in the cell output.
Acceptance: Given a dataset with injected nulls and duplicates, a cleaning instruction removes or imputes them as requested and the resulting cell output states the number of rows and columns affected.

## REQ-AIDS-005: Exploratory data analysis / 探索的データ分析
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests exploratory analysis, the system shall execute a notebook code cell that computes summary statistics, data types, and missing value counts for the target dataset.
Acceptance: Running an EDA instruction against a sample CSV produces a cell whose output includes column dtypes, non-null counts, and mean and std for numeric columns, matching pandas describe and info reference values.

## REQ-AIDS-006: Statistical analysis / 統計分析
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a statistical test or correlation analysis, the system shall execute a notebook code cell reporting the statistic and an adjacent markdown cell with a natural language interpretation.
Acceptance: A correlation request on a known synthetic dataset yields a correlation coefficient matching the scipy or numpy reference value within 1e-6, paired with a markdown interpretation cell.

## REQ-AIDS-007: Visualization generation / 可視化生成
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests a chart or plot, the system shall execute a notebook code cell that renders the requested visualization into the cell output.
Acceptance: A visualization instruction results in a code cell whose output contains an image MIME bundle, PNG or SVG, in the saved ipynb JSON.

## REQ-AIDS-009: Insight generation with recorded rationale / 根拠を伴うInsight生成
Priority: must
Type: functional
Pattern: event-driven
Statement: When the system generates a reasoning based insight, the system shall insert a markdown cell containing that insight immediately after the executed code cell that constitutes its evidentiary basis.
Acceptance: For every insight markdown cell added in a session, a test parses the ipynb and asserts the directly preceding code cell has a non-null execution_count and its output is referenced by the insight text, for 100 percent of insight cells.
Formal: {"kind":"transition","from":"evidence_executed","event":"insight_requested","to":"insight_recorded"}

## REQ-AIDS-010: No insight without notebook evidence / 根拠なきInsightの禁止
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If the system cannot locate exactly one executed evidentiary cell for a candidate insight, then the system shall withhold that insight and notify the user that supporting evidence could not be established or could not be uniquely identified.
Acceptance: Simulating a failed or skipped execution before an insight request results in no insight markdown cell being written and a user visible notification message in the configured response language. If more than one executed code cell shares the same execution_count and output containing the cited value (GitHub #54), the insight is likewise withheld with a distinct ambiguous-evidence notification instead of silently resolving to the first matching cell.

## REQ-AIDS-011: Analysis history persistence / 分析履歴の永続化
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall persist every executed analysis cell and its output in the project notebook file so the full analysis history is reconstructable by reopening the notebook.
Acceptance: After a multi-step analysis session, reopening the ipynb file with nbformat validate passes and the cell count matches the session execution log, with every executed cell showing its original output.

## REQ-AIDS-012: Skill packaging as SKILL.md / SKILL.md形式でのスキル提供
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall be packaged as a GitHub Copilot Agent Skill at .github/skills/ai-data-scientist/SKILL.md following the structural conventions used by this repository's existing sdd-* skills.
Acceptance: Manual review confirms the skill directory contains a SKILL.md that is discoverable and loadable the same way the sdd-requirements skill was loaded in this session.

## REQ-AIDS-013: Test-driven development coverage / TDDによるテスト網羅
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall require its pytest suite to pass before any implementation change is considered complete.
Acceptance: CI or local run of pytest reports zero failing tests immediately before a change is marked complete.
Performance: {"counter":"tests.pass_rate","max":100,"testId":"TEST-AIDS-PYTEST-001","unit":"operations"}

## REQ-AIDS-014: Diverse data source ingestion / 多様なデータソース取り込み
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests to load data from a CSV or Excel file or a database or API or image or text source, the system shall execute a notebook code cell that ingests the data into an in-memory dataframe available for subsequent analysis.
Acceptance: Ingestion instructions for a CSV, an Excel file, and a REST API endpoint each produce a code cell whose output confirms the loaded row count and column count.

## REQ-AIDS-027: Structured insight evidence manifest / 構造化Insightエビデンスマニフェスト
Priority: must
Type: functional
Pattern: event-driven
Statement: When the system inserts an insight markdown cell, the system shall include within that cell a structured evidence manifest identifying the source cell execution count, a cited output value, and the claim type.
Acceptance: A test parses each insight markdown cell in the notebook and confirms it contains a machine-readable evidence manifest whose cited execution count matches an actual executed cell and whose cited value appears verbatim in that cell's output, for 100 percent of insight cells.

## REQ-AIDS-028: Project identifier validation / プロジェクト識別子検証
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If a requested project name contains path traversal segments or characters outside the allowed identifier pattern, then the system shall reject the request and notify the user of the allowed naming rules.
Acceptance: Requests using project names such as a parent-directory reference or embedded path separators are rejected before any file system write, verified by asserting no file is created outside the projects directory tree.

## REQ-AIDS-029: Concurrent notebook access safety / Notebook同時アクセス安全性
Priority: must
Type: functional
Pattern: event-driven
Statement: When two analysis sessions target the same project notebook concurrently, the system shall serialize their writes so no cell or output from either session is lost or corrupted.
Acceptance: A test runs two concurrent write sessions against one project notebook and asserts the resulting ipynb passes nbformat validate and contains every cell submitted by both sessions.

## REQ-AIDS-030: Jupyter MCP unavailability handling / Jupyter MCP接続断時の処理
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If the configured Jupyter MCP server or kernel is unreachable when an analysis instruction is submitted, then the system shall report the failure to the user in the configured response language without writing a partial or corrupted cell to the notebook.
Acceptance: Simulating an unreachable MCP server during an analysis request results in a user-visible failure notification and no new cell appended to the notebook, verified by comparing cell count before and after the attempt.

## REQ-AIDS-031: Execution timeout handling / 実行タイムアウト処理
Priority: must
Type: functional
Pattern: event-driven
Statement: When a notebook cell execution exceeds the configured timeout, the system shall cancel that execution, mark the cell as failed, and notify the user without treating the cell as evidentiary basis for any insight.
Acceptance: A test forces a cell to exceed a configured timeout and asserts the cell is marked failed, no insight is generated from it, and a timeout notification is shown to the user.
Formal: {"kind":"temporal","trigger":"cell_execution_started","response":"timeout_cancelled","withinMs":30000}

## REQ-AIDS-032: Data source ingestion safety limits / データ取込の安全制限
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests ingestion from a database or API source, the system shall apply the configured authentication, network allowlist, and row-count limit before loading the data into a dataframe.
Acceptance: An ingestion request to a non-allowlisted host is rejected before any network call is attempted, and an ingestion request exceeding the configured row limit truncates the loaded data and reports the truncation to the user.

## REQ-AIDS-034: On-demand Jupyter MCP runtime startup / オンデマンドJupyter MCP起動
Priority: must
Type: functional
Pattern: event-driven
Statement: When the first analysis code execution is requested and no healthy Jupyter MCP runtime is already running, the system shall install (if needed) and start JupyterLab and the Jupyter MCP server inside the project's managed Python environment, binding to localhost only with automatically selected free ports and randomly generated authentication tokens (JupyterLab and the jupyter-mcp-server each require their own independent token), and reuse that running runtime for all subsequent execution requests in the same machine.
Acceptance: A test simulates a first execution request with no prior runtime present and asserts JupyterLab and the jupyter-mcp-server process are started, bound to 127.0.0.1 on dynamically chosen free ports, each configured with its own non-guessable generated token, and that a second execution request reuses the same runtime without starting a duplicate process.

## REQ-AIDS-035: Background daemon persistence across invocations / CLI呼び出しを跨いだ常駐継続
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall record the running Jupyter MCP runtime's process identifiers, port, and token in a project-independent state file so that a separate, later CLI invocation can detect and reuse the same still-running runtime without starting a duplicate one.
Acceptance: A test starts the runtime from one process invocation, then simulates a second independent invocation and asserts it detects the existing healthy runtime via the state file and performs no additional process start.

## REQ-AIDS-036: Jupyter MCP startup failure handling / Jupyter MCP起動失敗時の処理
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If JupyterLab or the Jupyter MCP server does not become healthy within the configured startup timeout, then the system shall raise the existing MCPUnavailableError, leave no partially started runtime registered as healthy, and report the failure to the user without retrying automatically.
Acceptance: A test forces the health check to never succeed and asserts MCPUnavailableError is raised within the configured timeout, the state file does not mark the runtime healthy, and no notebook cell is written.
Formal: {"kind":"temporal","trigger":"runtime_startup_requested","response":"mcp_unavailable_raised","withinMs":30000}

## REQ-AIDS-037: Explicit Jupyter MCP runtime status and stop control / 明示的な状態確認・停止操作
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user runs the status or stop command for the Jupyter MCP runtime, the system shall report whether a runtime is currently running and, for stop, terminate the recorded processes and clear the state file.
Acceptance: Running the status command against a running runtime reports it as healthy with its port; running the stop command terminates the recorded processes and a subsequent status command reports no runtime running.

## REQ-AIDS-038: Concrete Jupyter MCP client implementation / 具象Jupyter MCPクライアント実装
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a concrete implementation of the MCPClient contract that communicates with the started jupyter-mcp-server using its configured port and token, so that run_and_record can execute real code in a live Jupyter kernel without any caller-supplied client.
Acceptance: A test starts the on-demand runtime, executes a simple arithmetic expression through the concrete client without supplying any custom client implementation, and asserts the returned output matches the expected evaluated result.

## REQ-AIDS-039: Cited-value extraction helper for insight evidence / Insight根拠値抽出補助
Priority: should
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a helper that extracts a candidate cited value from a run_and_record (or execute_cell) result's output using a caller-supplied regular expression, so that callers constructing record_insight calls obtain the exact verbatim substring instead of manually transcribing or rounding it.
Acceptance: Given a result dict whose output contains a line matching a supplied pattern, the helper returns the exact matched substring; given no match, it raises a clear error rather than returning a guessed or empty value.

## REQ-AIDS-040: Documented chart-code kernel-consistency contract / チャートコードのカーネル整合性契約の明文化
Priority: should
Type: non-functional
Pattern: ubiquitous
Statement: The system shall document, in both the visualization module and the skill instructions, that the code string passed to record_chart is not executed against the live Jupyter kernel and therefore must reference only variables already established by prior run_and_record calls, so top-to-bottom notebook re-execution remains consistent.
Acceptance: The visualization module's record_chart docstring and the SKILL.md workflow step both state the kernel-consistency obligation explicitly.

## REQ-AIDS-041: Blocking wait option for Jupyter MCP runtime stop / Jupyter MCPランタイム停止の待機オプション
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests the Jupyter MCP runtime to stop with a wait option enabled, the system shall poll the recorded process IDs until they exit or a bounded timeout elapses, so callers can reliably confirm shutdown instead of guessing a fixed sleep duration.
Acceptance: Calling stop with wait=True on a running runtime returns only after the recorded processes have exited (or the timeout elapses, in which case it reports the remaining processes); calling stop without the option preserves today's fire-and-forget behavior.

## REQ-AIDS-042: Non-blocking hard timeout for MCP cell execution / MCPセル実行の非ブロッキングなハードタイムアウト
Priority: must
Type: functional
Pattern: event-driven
Statement: When execute_cell's configured timeout elapses before the underlying MCP client call returns, the system shall raise MCPExecutionTimeoutError to the caller immediately without waiting for the still-running worker thread to finish.
Acceptance: Given an MCP client call that takes materially longer than timeout_ms, execute_cell/run_and_record raise MCPExecutionTimeoutError within a bounded margin of timeout_ms (not after the client call actually completes), and no notebook cell is appended even if the worker later finishes successfully (its result is discarded, not retried or surfaced).

## REQ-AIDS-043: Categorical distribution and missing-value summary in EDA / EDAにおけるカテゴリ分布と欠損サマリー
Priority: should
Type: functional
Pattern: event-driven
Statement: When a user requests exploratory analysis, the system shall also report, for every column, its missing count and missing ratio, and, for every categorical column, its unique-value count and the counts and ratios of its most frequent values up to a bounded limit, while preserving the existing describe/dtypes/non_null_counts fields unchanged.
Acceptance: Running EDA against a dataset with categorical columns (e.g. a species/gender/category column) produces a report exposing, per categorical column, unique_count and a bounded list of top values with counts and ratios (with a truncated flag when more unique values exist than the limit), and a per-column missing_count/missing_ratio for every column; an empty DataFrame, an all-missing column, and a DataFrame with no categorical columns all return a well-formed report without raising, and the pre-existing describe/dtypes/non_null_counts values are unchanged from before this requirement.

## REQ-AIDS-044: Stable default project workspace root / プロジェクトワークスペースルートの安定化
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall resolve resolve_project's default projects_root to a location that is independent of the process's current working directory at call time, so that calling resolve_project with no explicit projects_root from the workspace root or from a project's own notebook subdirectory resolves to the same project root and notebook path.
Acceptance: Given the process working directory changes to a project's notebooks subdirectory after the module has been loaded, calling resolve_project(name) with no explicit projects_root still returns the same root/notebook_path as calling it from the original workspace root, and never creates a nested projects/<slug>/notebooks/projects/<slug> path; calling resolve_project with an explicit projects_root argument continues to honor that argument exactly as before.

## REQ-AIDS-045: Read-only notebook evidence/execution audit / 読み取り専用のノートブック実行・根拠監査
Priority: should
Type: functional
Pattern: event-driven
Statement: When a caller requests an audit of a project notebook, the system shall report, without modifying the notebook, its nbformat validity, any unexecuted or error-producing code cells, any execution_count value shared by more than one code cell, and, for every markdown cell carrying or expected to carry an evidence manifest, whether that manifest is present, well-formed, and resolves to exactly one existing executed cell whose output actually contains the cited value.
Acceptance: Given a notebook with at least one unexecuted code cell, one error output, one chart output, one insight cell with a valid evidence manifest, and one insight-like cell with a missing or stale evidence manifest, auditing it reports each condition tied to its originating cell index, leaves the notebook file byte-for-byte unmodified, and yields a report whose overall pass/fail status is false whenever any error-level finding exists (so it is usable as a CI gate); auditing a fully well-formed notebook yields a passing status. Given a notebook where two code cells share the same execution_count, auditing it reports a warning-level finding naming that execution_count and the sharing cell indices (GitHub #54); given an evidence manifest whose execution_count/cited_value pair matches more than one executed cell's output, auditing it reports an error-level finding that the evidentiary cell is ambiguous rather than silently validating against whichever cell is encountered first.

## REQ-AIDS-046: Legible Japanese chart text via bundled font / バンドル済みフォントによる日本語グラフ文言の可読表示
Priority: must
Type: functional
Pattern: event-driven
Statement: When render_chart is asked to render a chart title or axis label containing non-ASCII characters, the system shall configure matplotlib to use a bundled Japanese-capable font for that rendering.
Acceptance: Given a DataFrame and a title/xlabel/ylabel containing Japanese text, calling render_chart(df, ..., title=..., xlabel=..., ylabel=...) returns valid PNG bytes and matplotlib's active font family becomes the bundled Japanese-capable font (verified via matplotlib.rcParams after the call); calling render_chart with only ASCII text still returns valid PNG bytes without requiring the bundled font; because the font ships as a package dependency, this behavior is identical regardless of what fonts are installed on the host operating system.

## REQ-AIDS-047: Stable relative-path resolution for notebook audit / ノートブック監査における相対パスの安定解決
Priority: must
Type: functional
Pattern: event-driven
Statement: When audit_notebook is given a notebook path that does not resolve under the process's current working directory, the system shall resolve it against resolve_project's stable workspace root instead, reporting a distinct unresolved-path finding rather than a generic parse-failure finding when neither location contains the file.
Acceptance: Given a notebook created under the stable workspace root and a caller whose working directory has since moved into that notebook's own directory, calling audit_notebook with the original workspace-root-relative path succeeds identically to calling it from the workspace root; given a path that resolves under neither the current working directory nor the stable workspace root, the report's findings include an unresolved-path finding whose message is textually distinguishable from a parse-failure finding.

## REQ-AIDS-048: Self-referencing audit cell exclusion / 自己参照する監査セルの除外
Priority: should
Type: functional
Pattern: event-driven
Statement: When the last cell of an audited notebook is an unexecuted code cell whose source invokes audit_notebook, the system shall exclude that cell from the unexecuted-cell and error findings that determine the report's overall pass/fail status.
Acceptance: Given a notebook whose cells are all executed except a final code cell that is still running and whose source contains a call to audit_notebook, auditing that notebook reports ok=True provided no other failing condition exists; given a final unexecuted code cell whose source does not reference audit_notebook, it is still reported as an unexecuted-cell error exactly as before.

## REQ-AIDS-049: Stable project data directory / プロジェクトデータディレクトリの安定化
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall expose a stable workspace-root-anchored data directory path on every resolved ProjectHandle, together with a helper that creates it, so dataset files written during a session land under the same stable project root as the notebook.
Acceptance: Given a ProjectHandle returned by resolve_project, its data_dir attribute equals root/"data" regardless of the process's current working directory at the time of the call; calling the ensure_data_dir helper with that handle creates the directory (and any missing parents) if absent and returns its path; SKILL.md's ingestion step references handle.data_dir instead of a hand-rolled relative path.

## REQ-AIDS-050: Bounded Jupyter MCP dependency pins / Jupyter MCP依存バージョンの範囲固定
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall declare both a lower and an upper bound for its mcp and jupyter-mcp-server dependencies in pyproject.toml, so installing the package cannot silently resolve to an untested release pair whose negotiated MCP protocol version is incompatible.
Acceptance: pyproject.toml's mcp and jupyter-mcp-server dependency specifiers each include an explicit upper bound (not an open-ended "greater than or equal" range); a test parses both declared specifiers and confirms each is bounded on both sides and that the currently installed mcp/jupyter-mcp-server versions satisfy their respective declared ranges; raising either bound to admit a newer release requires a deliberate pyproject.toml edit, documented in CHANGELOG.md.

## REQ-AIDS-051: Cooperative run cancellation and quiescence barrier / 協調的キャンセルと静止確認
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a lifecycle API that lets a caller register a run, request cooperative cancellation of that run, query its current status (state, active cell executions, pending notebook writes, locks held), and wait for quiescence (all tracked activity settled) within a caller-supplied timeout.
Acceptance: A registered run that has an active tracked cell execution and a pending tracked notebook write reports active_cell_executions>=1 and pending_notebook_writes>=1 from get_run_status; after that execution and write complete, wait_for_quiescence returns a status with active_cell_executions==0, pending_notebook_writes==0 and locks_held==0 within the supplied timeout; calling request_cancel twice on the same run, or once on an already-completed run, does not raise and returns a status consistent with the run's actual completion state; a second run can register and complete after an earlier run on the same notebook path reaches quiescence, without a lock-acquisition error.

## REQ-AIDS-052: Data-definition and provenance manifest with confidence status / データ定義・来歴マニフェストと信頼度ステータス
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a DataDefinitionManifest builder that records, for a dataset's source, scope and variables, each semantic field together with an immutable status of verified, inferred, reported, or unknown, never silently upgrading an inferred or unknown field's recorded status to verified.
Acceptance: Building a manifest for a variable whose unit was only inferred from numeric scale (not read from an explicit source field) records that unit's status as "inferred", not "verified"; a variable with no available unit information at all records status "unknown"; a manifest-level check surfaces every field whose status is "unknown" as an actionable, listed item; a field explicitly supplied with status "verified" and its source text is preserved verbatim and distinguishable from an inferred field with the same value; a separate manifest-level check surfaces every field whose status is "inferred" as its own actionable, listed item, without that field also appearing in, or being conflated with, the "unknown" list.

## REQ-AIDS-053: Visual-readability audit for chart outputs / チャート出力の可読性監査
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide an optional notebook-audit phase that inspects each chart-bearing code cell's recorded rendering metadata and outputs, reporting a finding when a chart has missing-glyph warnings, is empty/near-empty, or is missing a declared title, axis label, or legend where required by policy.
Acceptance: A chart cell whose recorded rendering metadata includes a missing-glyph warning is reported as not readable with a "missing_glyphs" finding identifying the cell; the same chart cell with no missing-glyph warning and complete title/axis/legend metadata is reported as readable; an all-uniform (near-empty) PNG output is detected and reported as a finding distinct from the missing-glyph case; running audit_notebook without requesting the visual-audit phase preserves its prior findings and ok value unchanged (backward compatible when the phase is not requested); an image output whose own output-level `metadata["chart"]` (REQ-AIDS-071/072) and whose enclosing code cell's `metadata["chart"]` are both absent, empty, or non-mapping is reported with a distinct "unaudited" finding identifying that image, so "not audited" is never silently indistinguishable from "audited and passing"; this "unaudited" finding does not by itself fail the mandatory (non-visual-audit) findings this requirement already governs.

## REQ-AIDS-054: Analysis-assumption and applicability manifest / 分析前提・適用範囲マニフェスト
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a structured analysis-assumption manifest recording the analysis scope, a list of assumptions each with an explicit status of verified, tested, assumed, or rejected, and a causal_scope classification, surfacing as an unresolved risk any conclusion-critical assumption whose status is assumed or rejected.
Acceptance: A manifest declaring causal_scope "descriptive" alongside only descriptive claims produces no causal-identification finding; a manifest declaring causal_scope "causal" without any "tested" or "verified" identification assumption produces a finding naming the gap; an assumption recorded with status "assumed" and marked conclusion-critical appears in the manifest's unresolved_risks list; a sampled-model entry missing a recorded sample size or seed produces a finding.

## REQ-AIDS-055: Semantic anomaly detection and independent overlap validation / 意味的異常検知と独立データ重複検証
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide detect_anomalies, evaluating a dataframe against a declared per-column schema of semantic constraints (cross-column comparisons and declared missing-value sentinels) to report violating rows without modifying the source dataframe, and validate_anomalies, comparing two dataframes on a declared key to report matching coverage and per-column value differences beyond a declared tolerance.
Acceptance: A schema declaring column A must be less-than-or-equal-to column B flags every row where A>B and no others; a declared missing-value sentinel is reported as a distinct finding category from an out-of-range numeric value, and the source dataframe's values are unchanged after detection; comparing two dataframes on a shared date key with one anomalous, non-overlapping-value date isolates that date as the sole disagreement when every other overlapping date matches within the declared tolerance; neither function deletes or mutates input rows.

## REQ-AIDS-056: Reusable sensitivity-analysis plan with conclusion-stability reporting / 再利用可能な感度分析プランと結論安定性レポート
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a bounded SensitivityPlan (a target claim, a dictionary of named dimensions each with an explicit list of alternative values, and a configured maximum specification count) and a run_sensitivity function that evaluates every combination through a caller-supplied evaluator up to that bound, classifying the resulting conclusion across specifications as stable, attenuated, reversed, or not comparable.
Acceptance: A plan whose dimensions would exceed the configured maximum specification count raises a clear error before any evaluation runs; a two-alternative dimension whose evaluator returns opposite-signed metric values for a specified target claim is classified "reversed"; a dimension whose evaluator returns consistently same-signed, similarly-scaled values across every alternative is classified "stable"; each result records which dimension/alternative combination produced it and any evaluator failure is recorded as a failed specification rather than aborting the remaining plan.

## REQ-AIDS-057: Authorized independent-dataset overlap comparison / 認可済み独立データセット重複比較
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide compare_datasets, aligning a primary and a candidate dataframe on a declared key mapping and value mapping to report key coverage, rank correlation, value-difference statistics, the unmatched keys on each side, and for every candidate dataset its recorded relationship to the primary source (independent, same-upstream, or unknown) without ever inferring independence solely from a different owner/slug.
Acceptance: Two dataframes sharing 189 of a larger combined key set report exactly 189 matched keys and list the remaining keys on each side as unmatched; comparing two dataframes copied from the same declared upstream source records relationship "same-upstream", not "independent", even when their owner/slug differ; omitting explicit upstream-source information for a candidate records relationship "unknown" rather than defaulting to "independent"; rank correlation and absolute-value difference statistics are reported as distinct, separately labeled results.

## REQ-AIDS-058: Non-clipped chart text in saved rendering / グラフ描画文字のはみ出し防止
Priority: should
Type: functional
Pattern: event-driven
Statement: When a chart's title or x-axis label or y-axis label or tick label extends near the figure boundary, the system shall apply layout adjustment so that the saved PNG's rendered text stays within the saved image's pixel bounds.
Acceptance: Rendering a chart with long category tick labels and a wrapped multi-line axis label produces a saved PNG whose title, axis-label, and tick-label `Text` artists each report, via the renderer's `get_window_extent` after layout adjustment, a bounding box within the figure canvas's pixel dimensions at the same DPI/bbox convention used for the save; a chart whose labels already fit without adjustment keeps the same plotted data, labels, and `image/png` output contract as before.

## REQ-AIDS-059: Documented Jupyter MCP concurrent-write risk / Jupyter MCP同時書込みリスクの文書化
Priority: should
Type: non-functional
Pattern: ubiquitous
Statement: The system shall document, in both SKILL.md and the project-manager module, that writing directly to a notebook file via enqueue_write while the same file is open and later saved by a Jupyter MCP session can overwrite or lose that direct write.
Acceptance: SKILL.md's workflow guidance and the project_manager module's enqueue_write docstring both state the concurrent-external-save risk explicitly, together with the recommended mitigation of routing writes through the active MCP session (or pausing MCP-side saves) instead of writing directly to an MCP-opened notebook; enqueue_write's runtime behavior remains unchanged, and no code behavior change is required or implied by this requirement.

## REQ-AIDS-060: Chart authoring metadata persisted for visual audit / チャート生成メタデータの監査向け永続化
Priority: must
Type: functional
Pattern: event-driven
Statement: When render_chart renders a chart, the system shall return a rendering result object that carries the chart's title, axis labels, legend presence, and any font-glyph-rendering warnings observed during rendering, alongside the PNG image bytes.
Acceptance: Given a call to render_chart, its return value is an object usable anywhere raw PNG bytes are accepted (including base64 encoding and record_chart) and additionally exposes a "title", "xlabel", "ylabel", "legend", and "missing_glyphs" attribute reflecting what was actually rendered, with "missing_glyphs" listing the codepoints of any matplotlib "missing from font" warning raised during rendering (empty when none occurred); given a title/xlabel/ylabel combination that triggers a captured missing-glyph warning, "missing_glyphs" is non-empty and contains the warned codepoint(s).

## REQ-AIDS-061: Chart metadata captured by record_chart for visual audit / record_chartによるチャートメタデータの監査向け取り込み
Priority: must
Type: functional
Pattern: event-driven
Statement: When record_chart is called with a render_chart rendering result object, the system shall persist that object's title, axis labels, legend presence, and missing_glyphs attributes into the resulting cell's metadata["chart"] mapping.
Acceptance: Given record_chart called with the object returned by render_chart unchanged, the resulting cell's metadata["chart"] is a non-empty mapping containing "title", "xlabel", "ylabel", "legend", and "missing_glyphs" keys matching that object's attributes, and auditing that notebook with audit_notebook(..., visual_audit=True) reports no "unaudited" finding for that cell; given that object's missing_glyphs is non-empty, audit_notebook(..., visual_audit=True) reports the existing "missing_glyphs" finding for that cell carrying those codepoints; given record_chart called with plain bytes that are not a render_chart rendering result object (e.g. raw PNG bytes read from a file), the resulting cell has no metadata["chart"] entry, preserving the existing "unaudited" finding and the existing missing-glyph/near-empty/missing-label detection behavior unchanged.

## REQ-AIDS-062: Defined dataset-comparison agreement for zero overlapping rows / 重複行0件時の一致率の明確化
Priority: must
Type: functional
Pattern: event-driven
Statement: When compare_datasets computes a column's agreement_rate and that column has zero eligible joined rows (rows present on the same non-null key in both the primary and candidate dataframe), the system shall report that column's agreement_rate as undefined (None) rather than as a numeric value, distinguishing "nothing was compared" from "everything agreed".
Acceptance: Given a primary and candidate dataframe sharing no non-null key values, compare_datasets's returned report has matched_keys == 0 and every column_comparisons entry has agreement_rate is None and ColumnComparison.agreement_rate is typed as float | None; given a primary and candidate dataframe sharing exactly two non-null key values where a compared column agrees on one joined row and disagrees on the other, that column's agreement_rate equals 0.5 with matched_rows == 1 and total == 2 (its previous, unchanged numeric agreement_rate behavior of matched_rows / total); rows whose key is null on either side are excluded from both matched_keys and the per-column joined-row count on either side of this comparison.

## REQ-AIDS-063: Significance-aware correlation interpretation / 有意性を踏まえた相関解釈
Priority: must
Type: functional
Pattern: event-driven
Statement: When correlation generates its natural-language interpretation, the system shall state that no statistically clear correlation is observed whenever the p-value is greater than or equal to a significance_threshold parameter defaulting to 0.05, regardless of the coefficient's magnitude.
Acceptance: Given a correlation coefficient near zero with p-value 0.85 and the default significance_threshold, calling correlation(..., language="ja") returns an interpretation stating no statistically clear correlation is observed (not "weak ... correlation is seen"), and the English equivalent for language="en" states no statistically clear correlation rather than claiming any strength/direction; given a correlation coefficient of 0.9 (strong magnitude) with p-value 0.2 and the default significance_threshold, the interpretation still states no statistically clear correlation is observed, proving the rule applies regardless of magnitude; given a p-value exactly equal to significance_threshold, the interpretation states no statistically clear correlation is observed; given a correlation coefficient with p-value strictly below significance_threshold, the existing magnitude/direction-based wording is unchanged from current behavior; calling correlation(..., significance_threshold=0.10) applies that overridden threshold instead of the 0.05 default.

## REQ-AIDS-064: Bundled Japanese font applied to all rendered chart text / バンドル済み日本語フォントの全描画文言への適用
Priority: must
Type: functional
Pattern: event-driven
Statement: When render_chart renders a chart whose title or axis labels or tick labels or legend contain a Japanese character, the system shall configure matplotlib's font.family rcParam to the bundled Japanese-capable font for the entire rendering.
Acceptance: Given a DataFrame whose categorical values and/or legend entries contain Japanese text but whose title/xlabel/ylabel are ASCII-only, calling render_chart emits no matplotlib "missing from font" glyph warnings, the returned rendering result's missing_glyphs attribute is empty, and matplotlib.rcParams["font.family"] is set to the bundled Japanese-capable font family at the point tick labels and legend text are drawn; a title/xlabel/ylabel-only-Japanese case and a tick-label/legend-only-Japanese case are each tested separately; REQ-AIDS-046's existing acceptance (title/xlabel/ylabel non-ASCII triggers the bundled font; all-ASCII input, including tick labels and legend, does not require it) continues to hold unchanged.

## REQ-AIDS-065: Bounded display of a near-zero p-value / p値がゼロ丸めとなる場合の上限表記
Priority: should
Type: functional
Pattern: event-driven
Statement: When correlation's p-value is less than 1e-4, the system shall format the displayed p-value in its interpretation text as "p < 1e-4" instead of its formatted numeric value.
Acceptance: Given a p-value of 0 or any value strictly less than 1e-4 (e.g. 1e-10), the generated interpretation text contains "p < 1e-4" (not a numeric p-value) in both language="ja" and language="en" outputs; given a p-value of exactly 1e-4 or any value greater than or equal to 1e-4 (e.g. 0.05), the interpretation text displays its existing formatted numeric p-value unchanged.

## REQ-AIDS-066: Insight body text cross-checked against its cited value / Insight本文と引用値の整合確認
Priority: must
Type: functional
Pattern: event-driven
Statement: When audit_notebook validates an insight markdown cell's evidence manifest whose cited_value resolves to a real executed cell output, the system shall warn when neither that cited_value verbatim, nor any decimal number appearing in the cell's markdown body text (outside the evidence fence) that is numerically equal to cited_value when both are rounded to the appearing number's own decimal precision, is present in that body text.
Acceptance: Given an insight cell whose body states a numeric conclusion (e.g. "macro-F1 は 0.123 と低く") while its evidence manifest cites a different, verified value ("0.954", actually present in the referenced cell's output, and 0.123 does not round-equal 0.954 at any shared precision), audit_notebook's report contains a warning-severity finding identifying that cell and naming the cited value absent from the body text, and report.ok is unaffected by this warning alone (existing error-level evidence-resolution findings are unchanged); given an insight cell whose body text contains its manifest's cited_value verbatim (e.g. body mentions "0.954"), no such warning is produced; given a cited_value of "0.954" and a body text containing "0.95" (equal to 0.954 when both are rounded to 2 decimal places), no such warning is produced, since a legitimate rounded restatement is not a contradiction; given a non-numeric cited_value (e.g. "OK"), only the verbatim-substring check applies.

## REQ-AIDS-067: Explicit non-computable correlation interpretation for NaN statistics / NaN統計量に対する算出不能の明示
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If correlation's underlying coefficient or p-value is NaN (e.g. because an input column contains missing values), then the system shall state in its interpretation text that the correlation could not be computed rather than describing a magnitude, direction, or significance.
Acceptance: Given two numeric columns where at least one contains a missing value such that the underlying statistic returns NaN for the coefficient and/or p-value, calling correlation(..., language="ja") returns an interpretation stating the correlation could not be computed (not a "弱い"/"強い" magnitude or direction claim), and the language="en" equivalent states the correlation could not be computed; the returned coefficient and p-value fields remain NaN unchanged (only the interpretation text differs); given a coefficient and p-value that are both finite numbers, the existing REQ-AIDS-063 significance-gated interpretation behavior is unchanged.

## REQ-AIDS-068: Delimiter-aware CSV ingestion with mismatch warning / 区切り文字を考慮したCSV取込と不一致警告
Priority: must
Type: functional
Pattern: event-driven
Statement: When ingest loads a CSV source, the system shall determine the dataframe's column layout by sniffing the field delimiter actually used in the file from among comma, tab, and semicolon, instead of unconditionally assuming a comma, reporting a likely-delimiter-mismatch warning whenever sniffing is ambiguous and the comma-parsed fallback result still collapses to exactly one column whose header contains a tab or semicolon character.
Acceptance: Given a file with a ".csv" extension whose rows are tab-separated (e.g. "a\tb\tc\n1\t2\t3\n"), calling ingest(SourceSpec("csv", path)) returns a result whose dataframe has three columns named "a", "b", "c" (not one concatenated column) and an empty warnings collection; given a file with a ".csv" extension whose rows are semicolon-separated (e.g. "a;b;c\n1;2;3\n"), ingest similarly returns three correctly split columns with an empty warnings collection; given a genuinely comma-delimited CSV, sniffing resolves to comma and existing ingestion behavior (columns, row_count, column_count) is unchanged; given a CSV source where delimiter sniffing cannot confidently resolve a delimiter and the comma-parsed fallback result has exactly one column whose header contains a tab or semicolon character, the returned result's dataframe is the unchanged comma-parsed fallback but its warnings collection contains a message flagging a likely delimiter mismatch.

## REQ-AIDS-069: Exhaustive evidence-manifest validation within a single insight cell / 単一Insightセル内の全エビデンス網羅検証
Priority: must
Type: functional
Pattern: event-driven
Statement: When audit_notebook validates an insight markdown cell's evidence, the system shall check every ```evidence fenced block in that cell and every well-formed supporting_evidence entry (a mapping with an integer execution_count and a non-empty string cited_value) inside each block's manifest against real executed cell output, not only the first evidence block found in the cell, reporting an error-severity finding for any supporting_evidence entry that is malformed (not a mapping, or missing/wrong-typed execution_count or cited_value) or that does not resolve to real executed cell output.
Acceptance: Given an insight cell with two ```evidence fenced blocks where the second cites a value absent from any executed cell's output, audit_notebook's report has ok == False with an error-severity finding identifying that cell and the unresolved second block; given an insight cell whose sole evidence manifest's supporting_evidence field lists an entry with an execution_count that does not exist in the notebook, audit_notebook's report has ok == False with an error-severity finding identifying that cell and the unresolved supporting_evidence entry; given a supporting_evidence entry whose execution_count exists but whose cited_value is absent from that cell's output, audit_notebook's report has ok == False with an error-severity finding identifying that cell and that entry; given a supporting_evidence entry that is not a mapping, or is missing execution_count or cited_value, audit_notebook's report has ok == False with an error-severity finding identifying that cell and the malformed entry; given an insight cell with one evidence block and no supporting_evidence field (the existing common case), validation behavior is unchanged.

## REQ-AIDS-070: Heading-prefixed result paragraphs recognized as insight candidates / 見出し付き結論段落のInsight候補認定
Priority: must
Type: functional
Pattern: event-driven
Statement: When audit_notebook scans a markdown cell whose source begins with a heading line, the system shall apply the same insight-candidate detection used for non-heading-prefixed markdown cells to that cell's body text with the leading heading line(s) stripped, instead of unconditionally excluding every heading-prefixed cell.
Acceptance: Given a markdown cell consisting of a heading line followed by a paragraph stating a numeric conclusion (e.g. "## 結果\n平均購入額は9.9万円で、喫煙者は非喫煙者の3倍です。") with no evidence manifest, audit_notebook's report has ok == False with an error-severity finding for that cell reporting a missing evidence manifest, because that non-empty body text would already be treated as an insight candidate were it not heading-prefixed; given a markdown cell consisting solely of a heading line with no further body text (e.g. "## 結果\n" or "## 結果"), that cell's stripped body is empty, so it is not treated as an insight candidate and produces no missing-evidence finding, preserving existing section-heading behavior; the existing REQ-AIDS-048/#30 behavior (a heading-prefixed cell that does carry an evidence fence is validated) is unchanged.

## REQ-AIDS-071: Output-level chart metadata persisted by build_image_output / build_image_outputによる出力側チャートメタデータ永続化
Priority: must
Type: functional
Pattern: event-driven
Statement: When build_image_output wraps a render_chart rendering result into a notebook output, the system shall persist that result's chart authoring metadata into the output's own metadata["chart"] mapping, not only the enclosing cell's metadata.
Acceptance: Given build_image_output called with a render_chart rendering result object, the returned output's metadata["chart"] is a non-empty mapping containing the same title/xlabel/ylabel/legend/missing_glyphs keys as REQ-AIDS-061; given build_image_output called with plain bytes that are not a rendering result object, the returned output's metadata is unchanged (empty), preserving the existing "unaudited" finding for such outputs.

## REQ-AIDS-072: Per-image chart-metadata matching during visual audit / 視覚監査における画像単位でのチャートメタデータ照合
Priority: must
Type: functional
Pattern: event-driven
Statement: When audit_visual_outputs inspects a chart cell's image outputs, the system shall read each image output's own metadata["chart"] mapping to audit that image (identifying it in findings by its (cell_index, output_index) pair), falling back to the enclosing cell's metadata["chart"] only when the cell contains exactly one image output and that output's own metadata has no "chart" key.
Acceptance: Given a notebook containing only an output produced by the fixed build_image_output (REQ-AIDS-071), with no cell-level metadata["chart"], audit_notebook(..., visual_audit=True) reports no "unaudited" finding for that cell; given a single cell containing two image outputs where each has its own distinct, valid metadata["chart"] (one complete, one with a missing title), audit_visual_outputs reports findings keyed to each image's own (cell_index, output_index), flagging only the one missing a title, rather than conflating or applying one image's metadata to the other; given an image output whose own metadata["chart"] is present but empty or not a mapping, that specific output is reported "unaudited" and does not fall back to the cell-level mapping even when the cell-level mapping is valid; existing single-image, cell-level-only metadata["chart"] behavior (REQ-AIDS-061) continues to work unchanged when no output-level metadata is present.


## REQ-AIDS-085: Additional render_chart kinds for grouped distributions and matrix views / 群比較・行列表現向けrender_chart種類の拡張
Priority: must
Type: functional
Pattern: event-driven
Statement: When render_chart is called with kind "box" or "barh" or "heatmap", the system shall render that chart as PNG output instead of rejecting the kind as unsupported.
Acceptance: Given a dataframe with categorical group labels and numeric values, calling render_chart(df, kind="box", x="group", y="value") returns valid PNG bytes whose rendered-chart metadata reports the x-axis label as "group" and the y-axis label as "value"; given a dataframe with long category labels and numeric values, calling render_chart(df, kind="barh", x="label", y="value") returns valid PNG bytes without raising and preserves the ordinary RenderedChart bytes contract; given a dataframe with numeric columns x, y, z, calling render_chart(df, kind="heatmap") returns valid PNG bytes visualizing the correlation matrix of all numeric columns, and calling render_chart(df, kind="heatmap", x="x", y="y") returns valid PNG bytes visualizing the 2x2 correlation matrix of those selected numeric columns; given a square numeric dataframe whose index and columns already name the same variables (for example a precomputed correlation matrix), calling render_chart(df_corr, kind="heatmap") visualizes those matrix values directly without recomputing a second correlation matrix; existing render_chart calls for scatter/line/bar/hist with no new parameters continue to work unchanged.

## REQ-AIDS-086: Legend control for grouped chart rendering / グループ化チャート描画における凡例制御
Priority: must
Type: functional
Pattern: event-driven
Statement: When render_chart is called with a hue column for a scatter or line or bar or barh or hist chart, the system shall render one plotted series per distinct hue value and attach a legend whose title is legend_title when provided, otherwise the hue column name.
Acceptance: Given a dataframe with x, y, and group columns, calling render_chart(df, kind="scatter", x="x", y="y", hue="group", legend_title="Cluster") returns a RenderedChart whose legend attribute is True and whose legend_title attribute is "Cluster"; given the same call without legend_title, the returned legend_title is "group"; given an existing multi-series line chart request that already renders a legend without hue, passing only legend_title updates that legend's title while preserving the plotted data and existing PNG-bytes compatibility.

## REQ-AIDS-087: Error-range arguments for render_chart / render_chartにおける誤差範囲引数
Priority: should
Type: functional
Pattern: event-driven
Statement: When render_chart is called for a scatter or line or bar or barh chart with xerr and/or yerr naming one dataframe column for symmetric errors or two dataframe columns for lower/upper asymmetric errors, the system shall render those error ranges aligned to the plotted points or bars.
Acceptance: Given a dataframe with x, y, and err columns, calling render_chart(df, kind="bar", x="x", y="y", yerr="err") returns valid PNG bytes and draws one vertical error range per rendered bar; given a dataframe with x, y, low, and high columns, calling render_chart(df, kind="barh", x="x", y="y", xerr=("low", "high")) returns valid PNG bytes and draws one horizontal asymmetric error range per rendered bar; omitting xerr/yerr preserves the current rendering behavior unchanged.

## REQ-AIDS-088: Chart metadata helper for externally drawn matplotlib figures / 外部描画matplotlib Figure向けチャートメタデータ補助
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide a chart_metadata_from_figure(fig) helper that builds ChartMetadata from an existing matplotlib Figure so externally drawn charts can be wrapped as auditable RenderedChart outputs without hand-assembling metadata mappings.
Acceptance: Given a matplotlib Figure whose first plotting axes has a title, x-axis label, y-axis label, and legend, calling chart_metadata_from_figure(fig) returns a ChartMetadata object whose title/xlabel/ylabel/legend fields match the rendered figure and whose legend_title field matches the rendered legend title; wrapping saved PNG bytes as RenderedChart(png_bytes, chart_metadata_from_figure(fig)) and passing that object to record_chart persists the same chart metadata into the notebook cell metadata["chart"] mapping, with missing_glyphs defaulting to an empty tuple when no warning list is supplied.

## REQ-AIDS-093: Cross-process stable project root for multi-kernel sessions / 複数カーネルセッションにまたがる安定プロジェクトルート
Priority: must
Type: functional
Pattern: event-driven
Statement: When a newly started process's current working directory is already located inside an existing projects/<slug> tree for the specific project name being resolved at the time it first imports this module, the system shall discover that tree's existing projects_root by walking the current working directory and its ancestors and selecting the nearest directory whose basename is exactly "projects" and which already contains a subdirectory named exactly <slug> (including the current working directory itself as a candidate), instead of relying solely on that process's own import-time working directory, so that process still resolves the same project root and notebook path as the process that originally created that project, and resolve_project/ensure_notebook never recreate a nested projects/<slug>/notebooks/projects/<slug> path (GitHub #72, regression of #15/REQ-AIDS-044).
Acceptance: Given an existing projects/<slug> tree already created by one process (including its notebook, via ensure_notebook), starting a brand-new process whose current working directory is set to projects/<slug>/notebooks before it ever imports ai_data_scientist.project_manager (simulating a separately started kernel whose own import-time cwd has already drifted, so REQ-AIDS-044's single-process import-time-cwd anchor cannot by itself help it), with AI_DATA_SCIENTIST_PROJECTS_ROOT unset, and calling ensure_notebook(resolve_project(name)) from that new process: the returned/created notebook path equals the original process's projects/<slug>/notebooks/<slug>.ipynb, and no projects/<slug>/notebooks/projects directory is created. Given the same drifted-cwd new process but with AI_DATA_SCIENTIST_PROJECTS_ROOT set to a distinct, separately existing projects_root, resolve_project(name) resolves under that explicit environment-variable root instead of the discovered ancestor. Given a brand-new process whose current working directory, at first import, has no ancestor directory that is both named exactly "projects" and already contains a subdirectory named <name> (the first-ever call for this project name in a new workspace, with the environment variable unset), the system falls back to REQ-AIDS-044's existing import-time-cwd default (<import-time cwd>/projects) unchanged — including when the current working directory happens to sit beneath an unrelated directory literally named "projects" that does not yet contain this project's slug (for example a personal development workspace conventionally named ~/projects, which must not be mistaken for a module-managed root). Given a pre-existing, unrelated nested directory that is also named exactly "projects" but does not contain the requested project's slug as a direct child (for example another project's own generated-output subdirectory that happens to be named "projects"), the ancestor walk skips that directory and continues outward past it rather than selecting it as the root. Given a process whose current working directory is itself a directory literally named "projects" that already contains a subdirectory named <name>, that same directory is selected as the discovered root without further walking upward.

## REQ-AIDS-094: Baseline correction for spectral data / スペクトルデータのベースライン補正
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide ai_data_scientist.signal_analysis.baseline_correct(x, y, method="linear"|"asls") returning a corrected y array equal to the input y minus an estimated baseline, where for method="linear" the baseline is the straight line through the points (x[0], y[0]) and (x[-1], y[-1]), and for method="asls" the baseline is computed by Asymmetric Least Squares smoothing with fixed internal parameters lam=1e5 (smoothness), p=0.001 (asymmetry), and n_iter=10 (iteration count), and the function raises ValueError for any method value other than exactly "linear" or "asls", without modifying the input x/y arrays (GitHub #74).
Acceptance: Given x = numpy.linspace(-50, 50, 1001) and y = 10.0 * exp(-0.5 * (x/3.0)**2) + 0.01 * x + 5.0 (a Gaussian of amplitude 10.0, center 0, sigma 3.0, plus a linear baseline whose slope/intercept make y[0] and y[-1] the only baseline anchor points needed), calling baseline_correct(x, y, method="linear") returns corrected_y such that corrected_y[0] and corrected_y[-1] are both within absolute tolerance 1e-9 of 0.0, and max(abs(corrected_y - 10.0 * exp(-0.5 * (x/3.0)**2))) <= 0.1 (1% of the amplitude 10.0), and the x/y arrays passed in remain value-equal to pre-call copies afterward. Given x = numpy.linspace(0, 200, 1001), baseline = 0.0005 * (x - 100.0)**2 + 2.0, peak = 20.0 * exp(-0.5 * ((x-100.0)/5.0)**2), and y = baseline + peak, calling baseline_correct(x, y, method="asls") with the fixed lam/p/n_iter above returns corrected_y such that the mean absolute value of corrected_y over the baseline-only region where abs(x-100.0) >= 40.0 is <= 1.0 (5% of the peak amplitude 20.0), max(corrected_y) is within 5% of 20.0 (i.e. in [19.0, 21.0]), and the x/y arrays passed in remain value-equal to pre-call copies afterward. Given method="unsupported-value", calling baseline_correct(x, y, method="unsupported-value") raises ValueError, and the x/y arrays passed in are unchanged after the call (compared by value to pre-call copies). Given 1-D Python list or numpy-array x/y of equal length (no pandas DataFrame required), the function returns an object whose values are indexable/iterable like a 1-D array of the same length as y.

## REQ-AIDS-095: Spectral peak detection with FWHM / FWHMを伴うスペクトルピーク検出
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide ai_data_scientist.signal_analysis.find_spectral_peaks(x, y, prominence_frac=0.05, window=None) for a strictly increasing, uniformly spaced 1-D x and same-length y, which — after optionally replacing y with its Savitzky-Golay smoothed version (polyorder fixed at 3) when window is not None, and raising ValueError when window is not None and is not an odd integer that is >= 5 and <= len(y) — locates local maxima of the (possibly smoothed) y whose prominence (via scipy.signal.find_peaks) is at least prominence_frac times (max(y) - min(y)) of that same (possibly smoothed) y, and returns a list of dicts ordered by ascending x-position, one per detected peak, each containing exactly the keys "position" (x-coordinate of the maximum), "fwhm" (the full width at half maximum, from scipy.signal.peak_widths at rel_height=0.5, converted from sample units to x-units by multiplying by the uniform sample spacing dx = x[1] - x[0]), "prominence" (the peak's prominence in y-units), and "height" (the peak's y-value), all computed from the same (possibly smoothed) y used for detection (GitHub #74).
Acceptance: Given x = numpy.linspace(0, 100, 1001) (dx=0.1), peak1 = 5.0 * exp(-0.5 * ((x-30.0)/2.0)**2) (analytic FWHM = 2*sqrt(2*ln(2))*2.0 ≈ 4.7108), peak2 = 8.0 * exp(-0.5 * ((x-70.0)/3.0)**2) (analytic FWHM ≈ 7.0662), and y = peak1 + peak2 with no noise, calling find_spectral_peaks(x, y, prominence_frac=0.05) returns a list of exactly 2 dicts ordered by ascending "position", the first with "position" within 0.1 of 30.0, "fwhm" within 5% of 4.7108, "height" within 1% of 5.0, and "prominence" within 1% of "height" (flat zero baseline), and the second with "position" within 0.1 of 70.0, "fwhm" within 5% of 7.0662, "height" within 1% of 8.0, and "prominence" within 1% of "height". Given the same x with peak1 amplitude reduced to 0.1 (y = 0.1 * exp(-0.5 * ((x-30.0)/2.0)**2) + peak2), calling find_spectral_peaks(x, y, prominence_frac=0.05) returns a list containing exactly 1 dict, for the position-70.0 peak only. Given x as above and y equal to peak1 (amplitude 5.0) + peak2 (amplitude 8.0) plus a fixed deterministic noise vector numpy.random.default_rng(42).normal(scale=0.15, size=x.shape), calling find_spectral_peaks(x, y, prominence_frac=0.05, window=11) returns a list of exactly 2 dicts whose "position" values are each within 0.5 of 30.0 and 70.0 respectively. Given window=10 (an even integer), window=3 (odd but below the minimum of 5), and window=len(y)+2 (odd but exceeding len(y)) on that same noisy input, each of calling find_spectral_peaks(x, y, prominence_frac=0.05, window=10), window=3, and window=len(y)+2 raises ValueError. Given a flat y (constant value, zero variance) over any x, find_spectral_peaks returns an empty list rather than raising.

## REQ-AIDS-096: Sensitivity-plan helper for spectral peak parameters / スペクトルピークパラメータの感度プラン補助
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide ai_data_scientist.signal_analysis.build_peak_sensitivity_plan(x, y, prominence_fracs, windows, target_claim, max_runs=100) returning a (plan, analysis_fn) pair where plan equals sensitivity.SensitivityPlan(target_claim=target_claim, parameter_grid={"prominence_frac": prominence_fracs, "window": windows}, max_runs=max_runs), and analysis_fn is a callable that, when invoked as analysis_fn(prominence_frac=p, window=w) for any p in prominence_fracs and w in windows, calls find_spectral_peaks with the captured x and y and with prominence_frac and window forwarded as keyword arguments equal to p and w respectively, and returns float(len(result)) where result is that call's returned list, so (plan, analysis_fn) can be passed unchanged to sensitivity.run_sensitivity(plan, analysis_fn) with no caller-written glue code (GitHub #74).
Acceptance: Given x, y constructed as the two-peak noiseless spectrum of REQ-AIDS-095's first scenario, prominence_fracs=[0.05, 0.1, 0.2], windows=[None, 11], and target_claim="peak_count", calling plan, analysis_fn = build_peak_sensitivity_plan(x, y, prominence_fracs, windows, target_claim) returns a plan with plan.target_claim == "peak_count", plan.parameter_grid == {"prominence_frac": [0.05, 0.1, 0.2], "window": [None, 11]}, and plan.max_runs == 100; calling sensitivity.run_sensitivity(plan, analysis_fn) completes without raising and returns a SensitivityReport whose target_claim equals "peak_count", whose results length equals 6 (3 prominence_fracs * 2 windows), and whose classification equals "stable" (every combination detects the same 2 peaks). Given a monkeypatched ai_data_scientist.signal_analysis.find_spectral_peaks replaced by a stub that records its call keyword arguments and returns a fixed 3-element list, calling the returned analysis_fn(prominence_frac=0.1, window=11) returns exactly 3.0, and the stub's recorded call received x and y equal (by identity or value) to the originals passed to build_peak_sensitivity_plan, and prominence_frac=0.1 and window=11 as keyword arguments. Given prominence_fracs=[0.05, 0.1, 0.2], windows=[None, 11], and target_claim="peak_count" as above but calling plan, analysis_fn = build_peak_sensitivity_plan(x, y, prominence_fracs, windows, target_claim, max_runs=5) (a combination count of 6 exceeding max_runs=5), calling sensitivity.run_sensitivity(plan, analysis_fn) raises sensitivity.SensitivityBudgetExceededError (raised by plan.specifications() per existing SensitivityPlan behavior).

## REQ-AIDS-097: npm bootstrap setup deploys skills and their Python modules into the consuming project / npmブートストラップsetupが利用者プロジェクトへスキルとPythonモジュールを配置
Priority: must
Type: functional
Pattern: event-driven
Statement: When a consumer who installed the `jupytermind` npm package runs its CLI `setup` subcommand (invokable as `npx jupytermind setup` or its backward-compatible alias `npx ai-data-scientist setup` both running the same script), the system shall perform these additional steps beyond its existing `PACKAGE_ROOT/.venv`/dependency bootstrap (`PACKAGE_ROOT` being the installed npm package directory for a dependency install, or the repository root for a local checkout, as already resolved by the existing script): first, for an explicit fixed allowlist of exactly the 9 names `ai-data-scientist`, `ai-chemistry-scientist`, `ai-genomics-scientist`, `ai-materials-scientist`, `ai-structural-biology-scientist`, `ai-scientist`, `tech-writer`, `japanese-prose`, `presentation-planner` (never a `sdd-*`-prefix exclusion rule, and never any directory outside this allowlist even if present under the installed package's `.github/skills/`), preflight-validate every one of the 9 prospective destination paths `<current-working-directory>/.github/skills/<name>/` by, for each of `.github` then `.github/skills` in order, first resolving that level's nearest already-existing ancestor's real path and verifying containment (the ancestor's real path equals, or is a path-component-aware descendant of, `<current-working-directory>`'s own real path, never a mere string/sibling-prefix match such as `<cwd>-other`) before creating that level if it is missing, then resolving the newly-created or already-existing level's own real path and verifying that same containment condition before proceeding to the next level; only after both `.github` and `.github/skills` pass this containment check (verified relative to `<current-working-directory>`'s own real path) does the system fix `.github/skills`'s own just-validated real path as the canonical skills-root, then resolve each of the 9 destination skill paths' parent real path and verify it is equal to, or a path-component-aware descendant of, that canonical skills-root specifically (not merely somewhere under `<current-working-directory>`), refusing the entire `setup` invocation (nonzero exit, no success message, and no skill directory removed or copied for any of the 9 names) before any copy begins if any single one of the 9 resolves outside `<current-working-directory>/.github/skills/` (symlink escape), or if any single one is itself a symlink; only once all 9 pass this preflight does the system proceed, for each of the 9 in turn, to remove that destination skill directory entirely if it already exists and then recursively copy the installed package's `.github/skills/<name>/` full file tree into it, so every relative file path and byte content under the destination exactly matches the source tree afterward (no stale leftover files from a prior destination copy survive), logging one informational line per skill naming its destination path; and ensure `ai_data_scientist`, `ai_chemistry_scientist`, `ai_genomics_scientist`, `ai_materials_scientist`, `ai_structural_biology_scientist`, and `ai_scientist` (the application modules the 9 copied skills' documented Python entry points depend on, a subset of the packages `pyproject.toml`'s `[tool.setuptools.packages.find] where = ["src"]` discovers) are importable from that same `PACKAGE_ROOT/.venv`.
Acceptance: Given a clean consumer project directory with `jupytermind` installed under its `node_modules` and no `.github/skills/` directory yet, running `npx jupytermind setup` creates every missing `.github`/`.github/skills` ancestor directory and then, for every one of the 9 allowlisted skill names, a `<cwd>/.github/skills/<name>/` directory whose relative file set and byte contents exactly match `node_modules/jupytermind/.github/skills/<name>/` (including non-`SKILL.md` assets such as `japanese-prose/scripts/`, `japanese-prose/references/`, `presentation-planner/assets/`, and `presentation-planner/references/`), and creates no `<cwd>/.github/skills/sdd-*` directory even though the consumer's own repository (this one) separately contains `sdd-*` skill directories elsewhere that are never read by this copy step. Given a test double of the package's skill-source directory that additionally contains a `sdd-test/` directory alongside the 9 allowlisted ones, running the copy step against that source copies only the 9 allowlisted destinations and never creates `<destination>/.github/skills/sdd-test`, proving the implementation selects by explicit allowlist rather than by excluding an `sdd-*` name pattern. Given a consumer project whose `<cwd>/.github/skills/ai-data-scientist/` already contains a locally-modified `SKILL.md` plus an extra stale file `local-notes.txt` that does not exist in the packaged source, after `npx jupytermind setup` completes that directory's file set exactly equals the packaged source's file set (byte-identical `SKILL.md`, `local-notes.txt` no longer present), and a log line mentioning `ai-data-scientist` and the destination path was emitted. Given `<cwd>/.github/skills/ai-data-scientist/` already contains a sentinel file `sentinel.txt` with known content, and separately `<cwd>/.github/skills/ai-genomics-scientist` is a symlink pointing outside `<cwd>/.github/skills/` (allowlist order places `ai-data-scientist` before `ai-genomics-scientist`), running `npx jupytermind setup` exits nonzero, prints no overall success message, leaves that symlink and its target unmodified, and leaves `<cwd>/.github/skills/ai-data-scientist/sentinel.txt` byte-identical to its pre-run content (proving the preflight check rejects before any of the 9 directories, including ones earlier in allowlist order, are removed or copied). Given a consumer project where `<cwd>/.github` already exists as a symlink whose target resolves outside `<cwd>`'s real path, and `<cwd>/.github/skills` does not yet exist, running `npx jupytermind setup` exits nonzero, prints no overall success message, creates no `skills` directory or any of the 9 skill directories at the external symlink target or anywhere else, and leaves the existing `.github` symlink itself unmodified (proving the ancestor containment check runs on each already-existing level before any new component is created beneath it, not merely after). Given `<cwd>/.github` is a symlink whose target is `<cwd>/alternate-output` (within `<cwd>`'s own real path) and `<cwd>/alternate-output/skills` does not yet exist, running `npx jupytermind setup` exits 0, creates all 9 allowlisted skill directories under the resolved canonical skills-root `<cwd>/alternate-output/skills`, and those same 9 skill directories are also reachable at `<cwd>/.github/skills/<name>/` (via the existing symlink) with file trees byte-identical to the packaged source (proving in-cwd `.github` redirection is permitted while the canonical skills-root rule still binds all 9 destinations together). Given `npx ai-data-scientist setup` is invoked instead of `npx jupytermind setup` in the same clean consumer project, it performs the identical copy behavior (alias, not a distinct implementation). After either command completes successfully, running `<PACKAGE_ROOT>/.venv`'s platform-appropriate Python interpreter (`bin/python` on POSIX, `Scripts\\python.exe` on Windows, matching the existing script's own `IS_WINDOWS` branch) with `-c "import ai_data_scientist, ai_chemistry_scientist, ai_genomics_scientist, ai_materials_scientist, ai_structural_biology_scientist, ai_scientist"` exits 0 (all 6 application modules importable) without needing any manual `pip install` step beyond what `setup` already performed.

## REQ-AIDS-098: Convergence guard rejects repeated-action evidence as false convergence / 収束判定における同一処理反復の誤収束防止
Priority: must
Type: functional
Pattern: event-driven
Statement: When a caller invokes `ai_data_scientist.convergence_guard.evaluate_convergence` to check whether an iteration `history` has converged, the system shall classify its status as `"converged"` when the trailing run of consecutive rounds ending at the final round each having a relative metric change below `rel_tol` versus its immediate predecessor has length at least `min_consecutive` (a positive integer, default 2) and none of that run's last `min_consecutive` destination rounds shares its `action_signature` with any strictly earlier round in `history` (each round being a 1-based-position record of a finite numeric `metric` and a non-empty string `action_signature` that fully identifies the action type its effective parameters and its input-data identity such that two rounds sharing an `action_signature` are guaranteed to be a verbatim repeat of the same action on the same data) as `"repetition_detected"` when that same length-qualifying trailing run exists but at least one of its last `min_consecutive` destination rounds does share its `action_signature` with a strictly earlier round as `"exhausted"` when no length-qualifying trailing run exists and the caller passes `actions_exhausted=True` and as `"continue"` in every other case.
Acceptance: Relative metric change between a predecessor value `m_prev` and its successor `m_curr` is defined as `abs(m_curr - m_prev) / abs(m_prev)` when `m_prev != 0`, else `0.0` if `m_curr == 0.0` and `math.inf` otherwise; a transition qualifies only when this value is strictly less than `rel_tol` (`<`, not `<=`). Every successful call returns a verdict containing exactly `status`, `repeated_signature`, and `repeated_rounds`; `repeated_signature` and `repeated_rounds` are `None` for `status` in `{"converged", "exhausted", "continue"}` and are non-`None` only for `status="repetition_detected"`. Given `history` = rounds with signatures `["baseline", "gradient_boosting", "feature_select", "n_estimators_tune"]` and metrics `[0.70, 0.76, 0.761, 0.762]` (both of the last two transitions qualifying under `rel_tol=0.02`), calling `evaluate_convergence(history, rel_tol=0.02, min_consecutive=2, actions_exhausted=False)` returns `status="converged"`, `repeated_signature=None`, `repeated_rounds=None`, because the last 2 destination rounds (3 and 4, 1-based) have signatures `"feature_select"` and `"n_estimators_tune"`, neither matching any strictly earlier round. Given the same metrics but signatures `["baseline", "gradient_boosting", "n_estimators_tune", "n_estimators_tune"]` (round 4 verbatim-repeating round 3's action), calling `evaluate_convergence` with the same arguments returns `status="repetition_detected"`, `repeated_signature="n_estimators_tune"`, `repeated_rounds=(3, 4)` (1-based: the earlier matching round, then the later contributing round). Given signatures `["baseline", "feature_select", "n_estimators_tune", "feature_select"]` with the same metrics (round 4 repeats round 2's signature, a non-adjacent earlier round, not round 3's), `evaluate_convergence` still returns `status="repetition_detected"` with `repeated_signature="feature_select"` and `repeated_rounds=(2, 4)`, proving the duplicate search scans every strictly earlier round, not only the immediately preceding one. When more than one contributing destination round has a duplicate, or one contributing round matches more than one earlier round, `evaluate_convergence` resolves the ambiguity deterministically by selecting, among all duplicate matches found in the contributing rounds, the one whose later (contributing) round has the greatest 1-based position, and, if that later round itself matches more than one earlier round, by selecting the matching earlier round with the greatest 1-based position among those matches: given signatures `["baseline", "A", "B", "A", "B"]` with `min_consecutive=2` and both of the last two transitions qualifying, contributing rounds are 4 and 5, both of which repeat (round 4 repeats round 2's `"A"`, round 5 repeats round 3's `"B"`), so `evaluate_convergence` returns `repeated_signature="B"` and `repeated_rounds=(3, 5)` (round 5 is the later contributing round, so it is selected over round 4). Given a trailing run exactly 3 rounds long (all 3 of the last 3 transitions qualify) with `min_consecutive=2`, where an earlier, non-contributing destination round in that run repeats a signature from before the run began, but neither of the final `min_consecutive=2` destination rounds shares its signature with any strictly earlier round, `evaluate_convergence` still returns `status="converged"`, because only the last `min_consecutive` destination rounds are checked for duplicates, never a non-contributing round further back in the same qualifying run. Given a history of exactly 3 rounds with all-distinct signatures where the last two relative changes do not both qualify, calling `evaluate_convergence(history, rel_tol=0.02, min_consecutive=2, actions_exhausted=True)` returns `status="exhausted"` (not `"converged"` and not `"repetition_detected"`), and calling it with `actions_exhausted=False` instead returns `status="continue"`. Given a history shorter than `min_consecutive + 1` rounds, `evaluate_convergence` returns `status="continue"` when `actions_exhausted=False` and `status="exhausted"` when `actions_exhausted=True`, in both cases without raising. Given two consecutive equal metrics (`relative change == 0.0`) and `rel_tol=0.0`, that transition does not qualify (strict `<` against a zero tolerance can never be satisfied), so `evaluate_convergence` cannot return `"converged"`/`"repetition_detected"` from it alone. Given a `min_consecutive` that is not a positive `int` (including zero, a negative integer, a non-integer number such as `1.5`, a `bool`, a string, or `None`), a `rel_tol` that is not a finite number greater than or equal to `0.0`, or a history entry missing a finite numeric `metric` or a non-empty string `action_signature`, `evaluate_convergence` raises `ValueError` without mutating `history` and without classifying a status. The function is pure (no file or notebook I/O), does not call `ml_modeling.train_model`, and does not mutate its `history` argument.

## REQ-AIDS-099: CSV ingestion falls back to permissive decoding on non-UTF-8 input / CSV取り込みは非UTF-8入力に対しフォールバックデコードを行う
Priority: must
Type: functional
Pattern: event-driven
Statement: When `ai_data_scientist.ingestion.ingest` is invoked with a `SourceSpec` of `kind="csv"`, the system shall load the file by attempting `encoding="utf-8"` first, falling back to `encoding="cp1252"` (the deliberately preferred legacy single-byte fallback for Windows-exported CSVs; automatic charset detection is out of scope) only if the `utf-8` attempt raises `UnicodeDecodeError`, and falling back further to `encoding="latin-1"` only if the `cp1252` attempt also raises `UnicodeDecodeError` (byte-decoding under `latin-1` never raises `UnicodeDecodeError` for any byte sequence, so this final decode attempt always succeeds at the decoding step, though `pd.read_csv` may still raise a non-`UnicodeDecodeError` exception such as `pandas.errors.ParserError` from malformed CSV structure regardless of encoding), using whichever of these three encodings first successfully decodes the file to populate the returned `IngestionResult.dataframe`.
Acceptance: When the `utf-8` attempt succeeds (the common case, including a CSV containing non-ASCII UTF-8 text), `IngestionResult.warnings` contains no encoding-fallback warning and behavior is unchanged from before this requirement (GitHub #76 introduces no regression for already-working UTF-8 files). When the `utf-8` attempt raises `UnicodeDecodeError` and the `cp1252` retry succeeds — for example a file containing the cp1252-specific byte `0x80` (Euro sign), which is invalid UTF-8 but decodes cleanly under `cp1252` — `IngestionResult.warnings` contains exactly one additional warning string matching the template `f"CSV at {location!r} is not valid UTF-8; decoded using the 'cp1252' fallback encoding instead."`, where `{location!r}` is `source_spec.location`, and the resulting dataframe's cells contain the cp1252-decoded characters (e.g. `"€"` for byte `0x80`). When both `utf-8` and `cp1252` raise `UnicodeDecodeError` and the `latin-1` retry is used — for example a file containing byte `0x81`, which is undefined in cp1252 and therefore raises `UnicodeDecodeError` under it, but is a valid Latin-1 code point — `IngestionResult.warnings` contains exactly one additional warning string matching the template `f"CSV at {location!r} is not valid UTF-8 or cp1252; decoded using the 'latin-1' last-resort fallback encoding instead."`, and the resulting dataframe's cells contain the latin-1-decoded characters. Exactly one encoding-fallback warning is ever added per `ingest` call (never both the cp1252 and latin-1 templates together), and when a pre-existing delimiter-sniff-failure warning is also produced by the same call, it is appended first, before the encoding-fallback warning, into `IngestionResult.warnings` (both can be present simultaneously in `IngestionResult.warnings` for the same call, in that fixed order). The delimiter actually used (sniffed or comma-default) is unaffected by which encoding succeeded — the encoding retries re-use the same `delimiter`/`sniffed` values already computed by `_sniff_csv_delimiter` for that call, they are not re-sniffed per encoding attempt. No other `source_spec.kind` (`"excel"`, `"api"`, `"database"`) is affected by this requirement; `UnicodeDecodeError` handling added by this requirement applies only to `kind="csv"`. A non-existent file path, or a `UnicodeDecodeError`-unrelated exception raised by `pd.read_csv` at any encoding tier (e.g. `pandas.errors.ParserError` from a malformed CSV structure), propagates to the caller unchanged — this requirement only intercepts `UnicodeDecodeError`, it does not add a general exception-suppression behavior to `ingest`, and it makes no guarantee about CSV content encoded in a multi-byte scheme (e.g. UTF-16/UTF-32) that happens not to raise `UnicodeDecodeError` under an earlier tier while still being mis-decoded — such content is explicitly out of scope for this requirement.
