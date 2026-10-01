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
Statement: If the system cannot locate an executed evidentiary cell for a candidate insight, then the system shall withhold that insight and notify the user that supporting evidence could not be established.
Acceptance: Simulating a failed or skipped execution before an insight request results in no insight markdown cell being written and a user visible notification message in the configured response language.

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
Statement: When a caller requests an audit of a project notebook, the system shall report, without modifying the notebook, its nbformat validity, any unexecuted or error-producing code cells, and, for every markdown cell carrying or expected to carry an evidence manifest, whether that manifest is present, well-formed, and resolves to an existing executed cell whose output actually contains the cited value.
Acceptance: Given a notebook with at least one unexecuted code cell, one error output, one chart output, one insight cell with a valid evidence manifest, and one insight-like cell with a missing or stale evidence manifest, auditing it reports each condition tied to its originating cell index, leaves the notebook file byte-for-byte unmodified, and yields a report whose overall pass/fail status is false whenever any error-level finding exists (so it is usable as a CI gate); auditing a fully well-formed notebook yields a passing status.

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
Acceptance: Building a manifest for a variable whose unit was only inferred from numeric scale (not read from an explicit source field) records that unit's status as "inferred", not "verified"; a variable with no available unit information at all records status "unknown"; a manifest-level check surfaces every field whose status is "unknown" as an actionable, listed item; a field explicitly supplied with status "verified" and its source text is preserved verbatim and distinguishable from an inferred field with the same value.

## REQ-AIDS-053: Visual-readability audit for chart outputs / チャート出力の可読性監査
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall provide an optional notebook-audit phase that inspects each chart-bearing code cell's recorded rendering metadata and outputs, reporting a finding when a chart has missing-glyph warnings, is empty/near-empty, or is missing a declared title, axis label, or legend where required by policy.
Acceptance: A chart cell whose recorded rendering metadata includes a missing-glyph warning is reported as not readable with a "missing_glyphs" finding identifying the cell; the same chart cell with no missing-glyph warning and complete title/axis/legend metadata is reported as readable; an all-uniform (near-empty) PNG output is detected and reported as a finding distinct from the missing-glyph case; running audit_notebook without requesting the visual-audit phase preserves its prior findings and ok value unchanged (backward compatible when the phase is not requested).

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
