---
schemaVersion: 1
feature: ai-data-scientist
---
# Design / 設計 (MVP)

## DES-AIDS-001: Skill entry orchestrator / スキルエントリ・オーケストレータ
Responsibilities: Expose the GitHub Copilot Agent Skill entry point, parse the
user's natural language instruction, dispatch it to the Language Router and
the appropriate analysis module, and assemble the user-facing response.
Interfaces: SKILL.md instructions consumed by the Copilot agent runtime;
internal dispatch(instruction, projectContext) -> ModuleResult.
Constraints: Must not execute any analysis code itself; all execution is
delegated to DES-AIDS-004. Must follow the same structural conventions as the
repository's existing sdd-* skills.
Requirements: REQ-AIDS-012
ADRs: none — packaging conventions are fixed by existing repository structure, not a new trade-off.
Depends-On: DES-AIDS-002, DES-AIDS-003, DES-AIDS-004, DES-AIDS-005, DES-AIDS-006, DES-AIDS-007, DES-AIDS-008, DES-AIDS-009, DES-AIDS-010

## DES-AIDS-002: Bilingual language router / 日英言語ルーター
Responsibilities: Detect whether the current instruction is Japanese or
English and set the response language for the current turn accordingly.
Interfaces: detectLanguage(instructionText) -> "ja" | "en"; used by every
module that renders markdown cells or user-facing messages.
Constraints: Detection must be deterministic for a given instruction text and
must not require a network call.
Requirements: REQ-AIDS-001
ADRs: none — language detection is an implementation detail with no rejected architectural alternative recorded yet.
Depends-On: none

## DES-AIDS-003: Project and notebook manager / プロジェクト・Notebook管理
Responsibilities: Validate project identifiers, create or reuse the
per-project notebook file, and serialize all notebook writes through a
single-writer queue so concurrent sessions cannot corrupt the file.
Interfaces: resolveProject(name) -> ProjectHandle; ensureNotebook(handle) ->
NotebookPath; enqueueWrite(handle, cellMutation) -> WriteResult.
Constraints: Must reject any project name not matching the ADR-0005 slug
pattern before touching the filesystem. Must guarantee nbformat-valid output
after every flush (REQ-AIDS-011).
Requirements: REQ-AIDS-002, REQ-AIDS-011, REQ-AIDS-028, REQ-AIDS-029
ADRs: ADR-0004, ADR-0005
Depends-On: none

## DES-AIDS-004: Jupyter MCP execution gateway / Jupyter MCP実行ゲートウェイ
Responsibilities: Route every analysis code execution request to the
configured Datalayer jupyter-mcp-server tools against the project notebook
kernel, enforce execution timeouts, and translate MCP/kernel unavailability
into user-facing failures without leaving partial cells behind.
Interfaces: executeCell(handle, code, timeoutMs) -> ExecutionResult; on
failure raises a classified error consumed by DES-AIDS-002 for localized
messaging.
Constraints: Must not call any code-execution path other than the configured
jupyter-mcp-server tools. Must cancel and mark-failed any execution exceeding
the configured timeout (default 30000 ms) rather than let it run unbounded.
Requirements: REQ-AIDS-003, REQ-AIDS-030, REQ-AIDS-031
ADRs: ADR-0002
Depends-On: DES-AIDS-003

## DES-AIDS-005: Data ingestion module / データ取込モジュール
Responsibilities: Load data from CSV, Excel, database, API, image, or text
sources into an in-memory dataframe, applying authentication, network
allowlist, and row-count limits for remote sources before load.
Interfaces: ingest(sourceSpec) -> DataframeHandle, executed via
DES-AIDS-004.executeCell.
Constraints: Must reject non-allowlisted hosts before any network call; must
truncate and report when a configured row limit is exceeded.
Requirements: REQ-AIDS-014, REQ-AIDS-032
ADRs: none — ingestion safety limits follow directly from REQ-AIDS-032 with no competing architectural option considered.
Depends-On: DES-AIDS-004

## DES-AIDS-006: Data cleaning module / データクリーニングモジュール
Responsibilities: Execute requested cleaning operations (missing value
handling, type correction, deduplication, outlier flagging) and report the
row/column impact in the cell output.
Interfaces: clean(dataframeHandle, operationSpec) -> CleaningReport, executed
via DES-AIDS-004.executeCell.
Constraints: Must report a structured before/after row and column count for
every operation.
Requirements: REQ-AIDS-004
ADRs: none — a single direct implementation satisfies REQ-AIDS-004 with no recorded alternative.
Depends-On: DES-AIDS-004, DES-AIDS-005

## DES-AIDS-007: Exploratory data analysis module / 探索的データ分析モジュール
Responsibilities: Compute summary statistics, dtypes, and missing value
counts for a target dataset and render them as cell output.
Interfaces: runEda(dataframeHandle) -> EdaReport, executed via
DES-AIDS-004.executeCell.
Constraints: Reported statistics must match pandas describe/info reference
values for the same input.
Requirements: REQ-AIDS-005
ADRs: none — EDA output directly follows pandas semantics with no alternative design considered.
Depends-On: DES-AIDS-004

## DES-AIDS-008: Statistical analysis module / 統計分析モジュール
Responsibilities: Run requested statistical tests or correlation analyses and
pair the numeric result with a markdown interpretation cell.
Interfaces: runStatisticalTest(dataframeHandle, testSpec) -> StatResult,
executed via DES-AIDS-004.executeCell.
Constraints: Numeric results must match scipy/numpy reference values within
1e-6.
Requirements: REQ-AIDS-006
ADRs: none — statistic computation follows scipy/numpy reference semantics with no alternative design considered.
Depends-On: DES-AIDS-004

## DES-AIDS-009: Visualization module / 可視化モジュール
Responsibilities: Render requested charts/plots and embed the resulting image
in the notebook cell output.
Interfaces: renderChart(dataframeHandle, chartSpec) -> ChartOutput, executed
via DES-AIDS-004.executeCell.
Constraints: Output must be an image MIME bundle (PNG or SVG) persisted in the
saved ipynb JSON.
Requirements: REQ-AIDS-007
ADRs: none — chart rendering directly satisfies REQ-AIDS-007 with no recorded alternative.
Depends-On: DES-AIDS-004

## DES-AIDS-010: Insight and evidence engine / Insight・エビデンスエンジン
Responsibilities: Generate reasoning-based insights, attach a structured
evidence manifest citing the source cell's execution_count and cited output
value, validate the manifest against the actual notebook JSON, and withhold
the insight with a user notification when no valid evidentiary cell exists.
Interfaces: proposeInsight(handle, candidateText, evidenceRefs) ->
InsightWriteResult | WithheldNotification.
Constraints: Must never write an insight markdown cell whose evidence
manifest fails validation. Must use DES-AIDS-003.enqueueWrite for all cell
writes so concurrency guarantees hold.
Requirements: REQ-AIDS-009, REQ-AIDS-010, REQ-AIDS-027
ADRs: ADR-0003
Depends-On: DES-AIDS-003, DES-AIDS-004

## DES-AIDS-011: TDD verification gate / TDD検証ゲート
Responsibilities: Require the pytest suite covering all components above to
pass with zero failures before any implementation change is considered
complete.
Interfaces: runPytestSuite() -> TestRunResult consumed by CI/local workflow
gating.
Constraints: Zero failing and zero unapproved skipped tests; this gate does
not itself certify correctness beyond what the executed tests check.
Requirements: REQ-AIDS-013
ADRs: none — this is a process gate, not an architectural component with alternatives.
Depends-On: none
