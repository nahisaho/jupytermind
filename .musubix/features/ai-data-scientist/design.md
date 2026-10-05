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
sources into an in-memory dataframe, applying authentication and network
allowlist checks before any network call for remote (database/API)
sources, then applying row-count limits to the resulting dataframe for
those remote sources only.
Interfaces: ingest(sourceSpec) -> DataframeHandle, executed via
DES-AIDS-004.executeCell.
Constraints: Must reject non-allowlisted hosts before any network call;
after a remote ("api"/"database") fetch completes, must truncate the
resulting dataframe to the configured row limit and report the truncation
when the fetched row count exceeds it (this bounds downstream processing,
not the remote transfer/fetch itself). A local ("csv"/"excel") source must
never be truncated by the row limit (GitHub #57): it is a remote-source
safety control (REQ-AIDS-032), not a general ingestion cap.
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

## DES-AIDS-031: Categorical/missing summary extension of EDAReport / EDAReportのカテゴリ・欠損サマリー拡張
Responsibilities: Extend EDAReport with two additional fields computed from
the same input DataFrame as the existing describe/dtypes/non_null_counts,
without altering those three fields: a per-column missing_summary
(missing_count, missing_ratio) covering every column, and a
categorical_summary covering columns with dtype kind object/category/bool
only, each entry carrying unique_count (nunique, dropna) and a top_values
list (value, count, ratio) sorted by descending count and bounded to a
fixed limit (default 10), with a truncated flag set when unique_count
exceeds that limit.
Interfaces: explore(df, top_n: int = 10) -> EDAReport (new optional
parameter, existing single-argument call sites unchanged); EDAReport gains
missing_summary: dict and categorical_summary: dict fields in addition to
the existing describe/dtypes/non_null_counts.
Constraints: Must not change the existing describe/dtypes/non_null_counts
values or their keys; must return a well-formed (non-raising) report for an
empty DataFrame, an all-missing column, and a DataFrame with no categorical
columns (categorical_summary == {} in the last case); top_values list length
must never exceed top_n.
Requirements: REQ-AIDS-043
ADRs: none — an additive, backward-compatible extension of the existing EDA report.
Depends-On: DES-AIDS-007

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
the insight with a user notification when no valid evidentiary cell exists
or when more than one executed code cell shares the same
execution_count/cited_value pair (`AmbiguousEvidenceError`, a subclass of
`EvidenceMissingError`; GitHub #54 — duplicate execution_count values are
common after a kernel restart or appending to a notebook in a new
session, and silently resolving to the first match risks attributing an
insight to the wrong evidence).
Interfaces: proposeInsight(handle, candidateText, evidenceRefs) ->
InsightWriteResult | WithheldNotification.
Constraints: Must never write an insight markdown cell whose evidence
manifest fails validation or resolves ambiguously. Must use
DES-AIDS-003.enqueueWrite for all cell writes so concurrency guarantees
hold.
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

## DES-AIDS-025: Jupyter MCP runtime manager / Jupyter MCPランタイム管理
Responsibilities: On the first execution request with no healthy runtime
registered, install (if missing) and launch JupyterLab and the
jupyter-mcp-server inside the project's managed `.venv`, bound to
127.0.0.1 on automatically chosen free ports with randomly generated
tokens; poll for health within the configured startup timeout; persist the
process identifiers, ports, and tokens to a machine-local state file so a
separate later CLI invocation can detect and reuse the same runtime instead
of starting a duplicate one; and expose explicit status/stop operations.
Interfaces: ensureRuntime(timeoutMs) -> RuntimeInfo{jupyterPid, jupyterPort,
jupyterToken, mcpServerPid, mcpPort, mcpToken}; status() -> RuntimeInfo |
None; stop() -> None.
Constraints: Must bind only to 127.0.0.1, never a public interface. Must not
mark the state file healthy until the health check passes. On startup
failure or timeout it must raise MCPUnavailableError, deregister any
partially started state, and must not retry automatically. `stop()` must
terminate every recorded process id and remove the state file.
Implementation note (confirmed by live verification against jupyter-mcp-server
2.2.3): JupyterLab and jupyter-mcp-server are two independent processes with
two independent (port, token) pairs — the streamable-http MCP transport
refuses to start without its own `--mcp-token`, distinct from the Jupyter
server's own token, so RuntimeInfo tracks both pairs rather than a single
shared port/token.
Requirements: REQ-AIDS-034, REQ-AIDS-035, REQ-AIDS-036, REQ-AIDS-037
ADRs: ADR-0008
Depends-On: DES-AIDS-003

## DES-AIDS-026: Concrete Jupyter MCP client / 具象Jupyter MCPクライアント
Responsibilities: Implement the MCPClient contract declared by
DES-AIDS-004 by communicating with the runtime started by DES-AIDS-025
(using its recorded MCP port and MCP token) so run_and_record can execute
real code against a live Jupyter kernel without any caller-supplied client.
Interfaces: execute(code) -> dict, satisfying mcp_gateway.MCPClient; obtains
connection details via DES-AIDS-025.ensureRuntime before first use. The real
transport speaks the MCP streamable-http protocol (JSON-RPC
initialize -> tools/call("execute_code", {code})) over
`http://127.0.0.1:<mcpPort>/mcp` authenticated with `Authorization: Bearer
<mcpToken>`.
Constraints: Must only be used as the default client when no other MCPClient
is explicitly supplied; must surface the same MCPUnavailableError /
MCPExecutionTimeoutError classification already defined by DES-AIDS-004
rather than leaking transport-specific exceptions.
Requirements: REQ-AIDS-038
ADRs: none — this component is a direct, non-competing fulfillment of
REQ-AIDS-038 within the boundary already decided by ADR-0002 and ADR-0008.
Depends-On: DES-AIDS-004, DES-AIDS-025

## DES-AIDS-027: Cited-value extraction helper / 根拠値抽出補助
Responsibilities: Provide a small, dependency-free helper that takes a
run_and_record/execute_cell result dict and a caller-supplied regular
expression, searches the result's `output` string, and returns the exact
matched substring (or raises a clear error on no match) so callers building
`record_insight(..., cited_value=...)` calls never hand-transcribe or round
a value themselves.
Interfaces: extract_cited_value(result: dict, pattern: str) -> str, raising
CitedValueNotFoundError (ValueError subclass) when the pattern does not
match `result["output"]`.
Constraints: Must not mutate the input result; must not silently truncate or
reformat the matched substring (returns exactly what the regex matched,
using group(1) when the pattern defines a capture group, else group(0)).
Requirements: REQ-AIDS-039
ADRs: none — a pure helper function fulfilling REQ-AIDS-039 directly.
Depends-On: DES-AIDS-004, DES-AIDS-010

## DES-AIDS-028: Chart-code kernel-consistency documentation / チャートコードのカーネル整合性文書化
Responsibilities: Make the existing (intentional) gap between
`record_chart`'s stored code string and actual kernel execution an explicit,
documented contract rather than an implicit assumption, in both the
`visualization` module docstring and the SKILL.md workflow step that
describes visualization.
Interfaces: No new interface; `record_chart`'s docstring and SKILL.md step 8
gain an explicit sentence stating the code string is never executed against
the live kernel and must only reference variables already established by
prior `run_and_record` calls.
Constraints: Documentation-only; must not change `record_chart`'s behavior
or signature.
Requirements: REQ-AIDS-040
ADRs: none — documents an existing accepted design decision (REQ-AIDS-007 /
DES-AIDS-009's local-rendering boundary) rather than introducing a new one.
Depends-On: DES-AIDS-009

## DES-AIDS-029: Blocking stop with bounded polling / 有限待機付き停止
Responsibilities: Extend the existing fire-and-forget `stop(launcher)` with
an optional bounded wait that polls the recorded jupyter_pid/mcp_server_pid
for exit after sending SIGTERM, so callers can reliably confirm shutdown
instead of guessing a fixed sleep duration.
Interfaces: stop(launcher, wait: bool = False, timeout_s: float = 5.0,
poll_interval_s: float = 0.2) -> StopResult (StopResult records which PIDs,
if any, were still alive when the timeout elapsed). Default behavior
(wait=False) is unchanged for existing callers.
Constraints: Must not busy-loop past timeout_s; must use a process-liveness
check portable to the already-supported platforms (os.kill(pid, 0) probing,
consistent with the existing SIGTERM mechanism).
Requirements: REQ-AIDS-041
ADRs: none — a bounded-polling extension of the existing stop() mechanism.
Depends-On: DES-AIDS-025

## DES-AIDS-030: Non-blocking timeout detection via concurrent.futures.wait / concurrent.futures.waitによる非ブロッキングなタイムアウト検出
Responsibilities: Replace execute_cell's `with ThreadPoolExecutor(...)` block
(whose `__exit__` performs an implicit `shutdown(wait=True)` on any exit path,
including the TimeoutError branch) with an executor created and shut down
explicitly via `shutdown(wait=False)`, and detect timeout by calling
`concurrent.futures.wait({future}, timeout=timeout_s)` instead of
`future.result(timeout=timeout_s)`, so the timeout branch returns to the
caller as soon as the deadline elapses regardless of worker-thread state.
Interfaces: execute_cell(client, code, timeout_ms) -> dict (signature
unchanged). Internally: a module-level helper constructs the executor,
submits client.execute, and on timeout raises MCPExecutionTimeoutError
without retaining a reference the caller could use to later consume the
stale result; run_and_record's write-on-success-only control flow already
ensures a cell is appended only from the dict returned by execute_cell, so
a late-finishing worker's result is never read.
Constraints: Must preserve existing ConnectionError -> MCPUnavailableError
classification; must not introduce a busy-wait loop (rely on
concurrent.futures.wait's native blocking-with-timeout); must not change
execute_cell's public signature or return type on the success path.
Requirements: REQ-AIDS-042
ADRs: none — a non-blocking refinement of the existing timeout mechanism.
Depends-On: DES-AIDS-004

## DES-AIDS-032: Import-time-anchored default projects root / インポート時アンカー付きデフォルトprojects_root
Responsibilities: Replace resolve_project's default `projects_root="projects"`
(resolved relative to the process's current working directory at call time)
with a default that is independent of later `os.chdir` calls: an explicit
`AI_DATA_SCIENTIST_PROJECTS_ROOT` environment variable takes precedence when
set; otherwise the module captures the process working directory once, at
import time (before any skill code can chdir into a notebook/dataset
directory), and anchors `<that directory>/projects` as the default root for
the lifetime of the process.
Interfaces: resolve_project(name, projects_root: Path | str | None = None)
-> ProjectHandle (projects_root now defaults to None, meaning "use the
stable default root"; passing an explicit projects_root is unchanged from
today). A module-level `_default_projects_root() -> Path` helper performs
the environment-variable-then-import-time-cwd resolution.
Constraints: Must not change behavior for any caller that already passes an
explicit projects_root; must not perform the cwd capture lazily per-call
(that would reintroduce the bug), only once at import time; must document
the AI_DATA_SCIENTIST_PROJECTS_ROOT override in the skill instructions.
Requirements: REQ-AIDS-044
ADRs: none — a stability fix anchoring an existing default, no new architectural alternative.
Depends-On: DES-AIDS-003

## DES-AIDS-033: Read-only notebook audit module / 読み取り専用ノートブック監査モジュール
Responsibilities: Load a notebook via nbformat (without writing it back),
and report: nbformat validity; per code cell, whether execution_count is set
and whether any output has output_type "error"; per code cell, whether an
"image/png" output is present (chart detection); every execution_count value
shared by more than one code cell, reported as a warning-level finding
naming the execution_count and the sharing cell indices (GitHub #54 — a
reused execution_count after a kernel restart or appending to a notebook
in a new session does not by itself invalidate any specific insight, so it
is a warning rather than an error); and, per markdown cell whose source is
non-empty and does not start with a heading ("#"), whether it carries a
`\`\`\`evidence\n{...}\n\`\`\`` fenced JSON manifest with
execution_count/cited_value/claim_type keys that resolves (via the same
matching rule insight_engine.record_insight uses) to exactly one existing
code cell output containing cited_value — flagging missing, stale, or
ambiguous (matching more than one code cell) manifests as error-level
findings tied to their cell index.
Interfaces: audit_notebook(path: Path | str) -> NotebookAuditReport, where
NotebookAuditReport exposes nbformat_valid, unexecuted_cell_indices,
error_cell_indices, chart_cell_indices, findings (tuple of
severity/message/cell_index), and an `ok` property that is False whenever
any error-level finding exists (including nbformat invalidity).
Constraints: Must never call nbformat.write or otherwise mutate the file on
disk; must not raise for a structurally valid-but-incomplete notebook (e.g.
zero cells, zero insights) — only for an unreadable/invalid notebook file,
which is instead reported as a single error-level finding; must reuse the
same evidence cross-check semantics as DES-AIDS-010 (including its
`AmbiguousEvidenceError` ambiguity signal) rather than re-implementing a
divergent matching rule.
Requirements: REQ-AIDS-045
ADRs: ADR-0009
Depends-On: DES-AIDS-003, DES-AIDS-010

## DES-AIDS-034: Bundled Japanese font for chart text / バンドル済み日本語フォントによるグラフ文言対応
Responsibilities: Extend render_chart with optional title/xlabel/ylabel
parameters. When any of title/xlabel/ylabel contains a non-ASCII character,
import the `japanize-matplotlib` package (its import side effect registers
the bundled IPAexGothic TrueType font with matplotlib's font manager and
sets it as the active `font.family` via `matplotlib.rc`), and reassert the
registered font as the active `font.family` at the top of every such
`render_chart` call, not only on first trigger. This removes the prior
sticky, process-global assumption: a caller resetting matplotlib's global
`rcParams` (e.g. `plt.rcdefaults()`) between calls previously silently
undid the font registration, causing Japanese text to render as "tofu"
boxes on later calls (GitHub issue #32) — the module-level flag now only
gates the one-time `import japanize_matplotlib` (an expensive, idempotent
side effect), while the inexpensive `font.family` assertion itself runs
unconditionally whenever non-ASCII text is requested, so each rendering's
font state is self-contained and does not depend on any prior call's
surviving global state. Charts with only ASCII title/xlabel/ylabel (or
none at all) never trigger either step, so default matplotlib font
behavior for existing callers is unchanged.
Interfaces: render_chart(df, kind="scatter", x=None, y=None, title=None,
xlabel=None, ylabel=None) -> bytes (new optional keyword-only-by-convention
parameters; existing positional/keyword call sites are unaffected since the
new parameters default to None and are appended after the existing ones).
Constraints: Must not require any font to be pre-installed on the host
(the font ships inside the `japanize-matplotlib` PyPI package, itself
bundling IPA's freely redistributable IPAexGothic font); must not import
`japanize-matplotlib` eagerly at module load (keeps import cost and any
transitional deprecation warnings it emits out of the common ASCII-only
path); must reassert `font.family` on every call that needs it regardless
of any intervening global `rcParams` reset by the caller.
Requirements: REQ-AIDS-046
ADRs: ADR-0010
Depends-On: DES-AIDS-009

## DES-AIDS-035: Stable-root path resolution for notebook audit / ノートブック監査向けの安定ルートパス解決
Responsibilities: Before attempting to parse a notebook, resolve a possibly
relative input path by first checking it against the process's current
working directory and, only if that does not exist, re-checking it against
`project_manager`'s stable import-time workspace root (the same root
`resolve_project` anchors to under REQ-AIDS-044). Expose this as a reusable
`project_manager.resolve_stable_path(path)` helper that raises a dedicated
`StablePathResolutionError` when neither location contains the file, which
`audit_notebook` catches to emit a distinct unresolved-path finding instead
of folding it into the generic nbformat parse-failure branch.
Interfaces: project_manager.resolve_stable_path(path: Path | str) -> Path
(raises StablePathResolutionError); notebook_audit.audit_notebook unchanged
signature, now resolving its `path` argument through this helper before
calling nbformat.read.
Constraints: Must not change behavior for already-absolute or
already-cwd-resolvable paths (zero regression for the existing common case);
must not swallow genuine nbformat parse/validate errors into the
unresolved-path finding category, and vice versa.
Requirements: REQ-AIDS-047
ADRs: none — a narrow two-location fallback mirrors the existing
`_default_projects_root` resolution rule rather than introducing a new
path-search policy.
Depends-On: DES-AIDS-003, DES-AIDS-033

## DES-AIDS-036: Self-referencing audit cell exclusion / 自己参照する監査セルの除外
Responsibilities: When classifying code cells, detect the specific case of
the notebook's last cell being unexecuted (`execution_count is None`) with
source text that contains a call to `audit_notebook`, and exclude that one
cell from the unexecuted-cell and error findings that feed `report.ok`,
instead reporting it as a non-error informational finding. Every other
unexecuted or error-producing cell (including a non-trailing one, or a
trailing one that does not reference `audit_notebook`) is still reported
exactly as before.
Interfaces: notebook_audit.audit_notebook(path) -> NotebookAuditReport
(signature unchanged); internal classification only.
Constraints: Must not change `ok` for any notebook whose trailing unexecuted
cell does not reference `audit_notebook`; must not suppress a genuine error
output on that same cell (an error output on the self-audit cell is still a
real failure and remains an error-level finding).
Requirements: REQ-AIDS-048
ADRs: none — a narrow source-text heuristic scoped to the one documented
self-audit pattern, not a general unexecuted-cell exemption mechanism.
Depends-On: DES-AIDS-033

## DES-AIDS-037: Stable project data directory / プロジェクトデータディレクトリの安定化
Responsibilities: Extend `ProjectHandle` with a `data_dir` field computed as
`root / "data"` at resolution time (anchored to the same stable `root` that
REQ-AIDS-044 already stabilizes), and add an `ensure_data_dir(handle)`
helper, mirroring `ensure_notebook`, that creates the directory (and any
missing parents) if absent and returns its path. Update SKILL.md's ingestion
step to reference `handle.data_dir` / `ensure_data_dir(handle)` instead of a
hand-rolled `projects/<slug>/data` relative path.
Interfaces: ProjectHandle gains `data_dir: Path`;
project_manager.ensure_data_dir(handle: ProjectHandle) -> Path.
Constraints: Must not change the existing `name`/`root`/`notebook_path`
semantics or require callers who only used those fields to change anything.
Requirements: REQ-AIDS-049
ADRs: none — extends the existing `ProjectHandle`/`ensure_notebook` pattern
rather than introducing a separate data-path resolution mechanism.
Depends-On: DES-AIDS-003

## DES-AIDS-038: Bounded Jupyter MCP dependency pins / Jupyter MCP依存バージョンの範囲固定
Responsibilities: Narrow `pyproject.toml`'s `mcp` and `jupyter-mcp-server`
dependency specifiers to the specific minor-version range already verified
to interoperate (`mcp>=2.2,<2.3`, `jupyter-mcp-server>=2.2,<2.3`), replacing
the previously open-ended `jupyter-mcp-server>=2.2` and wider `mcp>=2,<3`.
Add a small `dependency_pins` module that textually parses
`pyproject.toml`'s `[project].dependencies` array (no new TOML-parsing
dependency) to return the raw declared specifier for a given package name,
and a test that uses it together with `packaging.requirements.Requirement`
and `importlib.metadata.version` to assert both specifiers are bounded on
both sides and that the versions actually installed in the environment
satisfy them.
Interfaces: dependency_pins.get_dependency_specifier(name: str) -> str
(raises KeyError if the package is not declared).
Constraints: Must not require installing a new TOML-parsing library (plain
text scanning of the dependencies array is sufficient and avoids a
Python-3.10-compatibility concern with stdlib `tomllib`, which only ships
from 3.11); must not change behavior of any other declared dependency.
Requirements: REQ-AIDS-050
ADRs: none — a conservative, already-verified version-range narrowing, not a
new installation mechanism.
Depends-On: none

## DES-AIDS-039: Run lifecycle registry / ランライフサイクルレジストリ
Responsibilities: A new `lifecycle` module holding a process-wide,
thread-safe registry of `RunState` records keyed by caller-supplied
`run_id`. Exposes `register_run(run_id, notebook_path)`,
`mark_execution_start/end(run_id)`, `mark_write_start/end(run_id)`,
`request_cancel(run_id, reason)`, `is_cancel_requested(run_id)`,
`mark_completed/failed(run_id)`, `get_run_status(run_id)`, and
`wait_for_quiescence(run_id, timeout_s)` (polling loop with a short sleep
interval, returning the last observed status either once quiescent or once
the timeout elapses). `mcp_gateway.execute_cell`/`run_and_record` and
`project_manager.enqueue_write` accept an optional `run_id` keyword
(default `None`, fully backward compatible); when provided they call the
matching `mark_*` hooks around their existing work so tracked counts stay
accurate without changing default (no `run_id`) behavior at all.
Interfaces: lifecycle.register_run(run_id, notebook_path) -> None;
lifecycle.request_cancel(run_id, reason) -> None (idempotent, no raise for
unknown/completed run_id); lifecycle.get_run_status(run_id) -> RunStatus
(state, active_cell_executions, pending_notebook_writes, locks_held,
notebook_path, last_modified, reason); lifecycle.wait_for_quiescence(run_id,
timeout_s) -> RunStatus.
Constraints: Must not introduce a new process/thread model; counts are
in-memory and process-local (consistent with the existing per-notebook
`threading.Lock` registry in project_manager). Cancellation is cooperative:
`request_cancel` only sets a flag inspected by execute_cell before starting
a new cell; it cannot interrupt a kernel cell already in flight (documented
limitation, matches the issue's cooperative-cancellation framing).
Requirements: REQ-AIDS-051
ADRs: none — in-process cooperative tracking extending the existing single-writer lock pattern, not a new architectural decision.
Depends-On: DES-AIDS-003, DES-AIDS-004

## DES-AIDS-040: Data-definition manifest with field confidence / データ定義マニフェストとフィールド信頼度
Responsibilities: A new `data_definition` module providing a `FieldValue`
value object (`value`, `status` in {"verified","inferred","reported",
"unknown"}, optional `source`) and a `DataDefinitionManifest` dataclass
(source, dataset_scope, variables, transformations) built via
`build_manifest(...)`. `unresolved_fields()` is derived, not caller-set:
computed by scanning every `FieldValue` in the manifest and collecting
those whose status is "unknown". `FieldValue` is frozen so a status, once
constructed, cannot be mutated in place to "verified" by later code; only
constructing a brand-new `FieldValue` can change it, and that is always an
explicit caller action, not an automatic promotion. A second derived
query, `inferred_fields()`, mirrors the same three-scan traversal
(source/dataset_scope/variables) and collects those whose status is
"inferred" instead of "unknown", so a field never appears in both result
sets and neither method's result depends on evaluation order.
Interfaces: data_definition.FieldValue(value, status, source=None);
data_definition.build_manifest(source, dataset_scope, variables,
transformations=()) -> DataDefinitionManifest; manifest.unresolved_fields()
-> list[tuple[str, FieldValue]] (dotted path + field, status == "unknown"
only); manifest.inferred_fields() -> list[tuple[str, FieldValue]] (dotted
path + field, status == "inferred" only).
Constraints: No implicit status inference logic is added in this module
(the caller/agent decides inferred vs verified when constructing a
`FieldValue`); the module's job is to make that distinction structurally
enforceable and queryable, not to guess it. `inferred_fields()` must not
mutate or reclassify any field; it is a read-only filter over the same
stored data `unresolved_fields()` reads.
Requirements: REQ-AIDS-052
ADRs: ADR-0011
Depends-On: none

## DES-AIDS-041: Visual-readability audit phase / ビジュアル可読性監査フェーズ
Responsibilities: Extend `notebook_audit` with an opt-in
`audit_visual_outputs(notebook, chart_cell_indices)` phase, invoked from
`audit_notebook(path, visual_audit=False)` only when requested (default
`False` preserves prior behavior exactly, satisfying the backward-
compatibility acceptance criterion). For each chart cell it reads
chart-authoring metadata the cell's code-cell `metadata["chart"]` dict may
carry (`missing_glyphs`, `title`, `xlabel`, `ylabel`, `legend`) — written
by callers such as `visualization.record_chart` — plus a lightweight
pixel-level near-empty check (decode the `image/png` base64 payload with
the stdlib-available `zlib`/manual PNG IDAT heuristic is out of scope;
instead reuse `PIL` only if already a transitive dependency — since it is
not, perform the near-empty check by reading the PNG dimensions from its
header bytes and flagging a suspiciously tiny byte-size-per-pixel payload
as a proxy for near-empty, documented as an approximation).
Interfaces: notebook_audit.audit_visual_outputs(notebook,
chart_cell_indices) -> tuple[VisualAuditFinding, ...];
notebook_audit.audit_notebook(path, visual_audit: bool = False).
Constraints: Must not add a hard dependency (no OCR, no imaging library);
the glyph/label checks rely on authoring-time metadata rather than re-
rendering or OCR-scanning the image, which the issue's own "Implementation
options" lists as an acceptable approach ("record chart semantics at
creation time"). Note: as of this change, no current caller (including
`visualization.record_chart`) writes `cell["metadata"]["chart"]`; until a
caller is updated to populate it, every chart-bearing cell audited by this
phase is expected to surface as "unaudited" rather than as a false "pass",
which is the intended, correct behavior per REQ-AIDS-053's new acceptance
clause. A chart-bearing cell (an `image/png` output present) whose
`metadata["chart"]` key is absent, an empty mapping, or a non-mapping value
yields a distinct `VisualAuditFinding(code="unaudited", severity="warning",
...)`, checked and returned before the existing `missing_glyphs`/label
checks run (those checks are otherwise unchanged); this finding is
informational only and does not by itself flip the mandatory
(non-visual-audit) `ok` status this module already governs.
Requirements: REQ-AIDS-053
ADRs: ADR-0012
Depends-On: DES-AIDS-033

## DES-AIDS-046: Non-clipped chart text layout / グラフ描画文字の非クリッピング・レイアウト
Responsibilities: In `visualization.render_chart`, after plotting and
setting title/xlabel/ylabel but before saving the PNG, call matplotlib's
`Figure.tight_layout()` (falling back to `constrained_layout` if
`tight_layout` raises, e.g. for 3D axes) and pass `bbox_inches="tight"` to
`savefig`, so the title, axis labels, and tick labels are
repositioned/padded to fit within the saved canvas instead of being
clipped. Applies on every call, not only when labels are detected as long,
so behavior is deterministic and does not depend on a heuristic length
threshold. `bbox_inches="tight"` changes the saved PNG's pixel dimensions
to fit the tightened bounding box (the current implementation saves a
fixed-size canvas with no existing `bbox_inches`/`dpi` argument); no
requirement or existing test depends on a fixed output size, so this is an
intentional, acceptable side effect, not a regression — the verifying test
must call `fig.canvas.draw()`, then compute each `Text` artist's
`get_window_extent()` using the renderer obtained after the same
`tight_layout`/`savefig(bbox_inches="tight")` call sequence, so the
asserted bounding boxes use the same bbox/DPI convention as the saved PNG,
rather than comparing against the original, un-tightened canvas extent.
Interfaces: visualization.render_chart(..., ) -> bytes (PNG), unchanged
public signature; the layout call is an internal step before `savefig`.
Constraints: Must not change the plotted data, legend, or color palette;
must not regress REQ-AIDS-046's bundled-Japanese-font configuration (the
layout call must run after font configuration and after title/axis-label
text is set, since `tight_layout` measures already-rendered text metrics).
Requirements: REQ-AIDS-058
ADRs: ADR-0013
Depends-On: DES-AIDS-009, DES-AIDS-034

## DES-AIDS-047: Documented Jupyter MCP concurrent-write risk / Jupyter MCP同時書込みリスクの文書化
Responsibilities: Add an explicit risk/mitigation note to SKILL.md's
notebook-write workflow step and to `project_manager.enqueue_write`'s
docstring, stating that a direct `enqueue_write` call against a notebook
file that is simultaneously open in a Jupyter MCP session can be
overwritten when that MCP session later saves, and recommending routing
writes through the active MCP session (or pausing MCP-side saves) instead.
Interfaces: none — documentation only; no function signature or behavior
changes.
Constraints: Must not alter `enqueue_write`'s runtime behavior; this is a
documentation-only design element with no TDD cycle, consistent with
REQ-AIDS-059's "no code behavior change" acceptance clause.
Requirements: REQ-AIDS-059
ADRs: ADR-0014
Depends-On: DES-AIDS-003

## DES-AIDS-048: Rendering-result object carrying chart authoring metadata / 描画結果オブジェクトによるチャート生成メタデータの保持
Responsibilities: In `visualization`, add a frozen `ChartMetadata`
dataclass (`title: str | None`, `xlabel: str | None`, `ylabel: str | None`,
`legend: bool`, `missing_glyphs: tuple[str, ...]`) and a `RenderedChart(bytes)`
subclass whose instances carry an additional `chart_metadata: ChartMetadata`
attribute set at construction time, plus read-only `title`, `xlabel`,
`ylabel`, `legend`, and `missing_glyphs` properties that forward directly
to the corresponding `chart_metadata` field — satisfying REQ-AIDS-060's
acceptance that the returned object itself "exposes a `title`, `xlabel`,
`ylabel`, `legend`, and `missing_glyphs` attribute" (`chart_metadata`
remains available as the single structured bundle DES-AIDS-049 serializes
from). `render_chart`'s control flow becomes: (1) determine the
Japanese-content trigger and configure the font per DES-AIDS-052 (runs
first, before any plotting), (2) create the figure and plot, (3) wrap the
plot/`savefig` sequence in `warnings.catch_warnings(record=True)` with an
explicit `simplefilter("always")` scoped to that block — the warning
context starts before `df.plot`/label assignment/`tight_layout` and ends
only after `savefig` returns, so no glyph warning raised anywhere in that
sequence can escape capture, (4) scan captured warnings whose message
matches matplotlib's `"Glyph \d+ .* missing from (?:current )?font"`
pattern, extracting each referenced codepoint as its decimal Unicode code
point string, de-duplicating while preserving first-seen order, and
re-emitting every non-matching captured warning via `warnings.warn_explicit`
with its original category/message/filename/lineno so no unrelated warning
is swallowed, (5) detect legend presence via `ax.get_legend() is not None`,
(6) construct a `ChartMetadata` from the rendered axes' actual
`ax.get_title()`, `ax.get_xlabel()`, `ax.get_ylabel()` (not merely the
caller-supplied `title`/`xlabel`/`ylabel` parameters, since pandas'
`df.plot(...)` can auto-generate a label — e.g. `ylabel` from the plotted
column name — when the caller passes `None`), the detected legend flag,
and the deduplicated missing-glyph codepoints, and (7) return
`RenderedChart(png_bytes, chart_metadata=metadata)` instead of plain
`bytes`. Because `RenderedChart` is a real `bytes` subclass, every
existing caller that treats the return value via ordinary `bytes`
operations (`base64.b64encode`, equality, slicing, hashing) continues to
work unmodified; this does not extend to callers that assert `type(value)
is bytes` exactly or rely on `bytes`-specific pickling/serialization,
which this design does not claim to preserve (none exist in this
repository today).
Interfaces: visualization.ChartMetadata(title, xlabel, ylabel, legend,
missing_glyphs) (frozen dataclass); visualization.RenderedChart(bytes)
subclass exposing `.chart_metadata: ChartMetadata` plus forwarding
`.title`, `.xlabel`, `.ylabel`, `.legend`, `.missing_glyphs` read-only
properties; render_chart(...) -> RenderedChart, replacing the prior
`-> bytes` return annotation (a behavior-preserving, caller-compatible
refactor for every existing in-repository call path, since `RenderedChart`
is-a `bytes`).
Constraints: This design itself (metadata capture and result-type
wrapping) must not change the PNG bytes/pixel content produced today for
any given set of plotting inputs and font configuration — any pixel
difference for a specific chart is attributable solely to DES-AIDS-052's
widened font trigger, not to this design; must not require call-site
changes at any existing `render_chart` caller that uses ordinary `bytes`
operations; must not suppress or swallow any non-glyph warning raised
during rendering. Depends on DES-AIDS-052 having already configured the
font before this design's plotting/`savefig` step runs, so the warning
capture reflects the final, correctly-configured font — DES-AIDS-052 does
not depend back on this design, keeping the dependency direction one-way.
Requirements: REQ-AIDS-060
ADRs: ADR-0067
Depends-On: DES-AIDS-009, DES-AIDS-034, DES-AIDS-052

## DES-AIDS-049: record_chart auto-persists chart metadata into cell output / record_chartによるチャートメタデータの自動永続化
Responsibilities: Update `record_chart` to check `isinstance(png_bytes,
RenderedChart)`; when true, serialize its `.chart_metadata` (title, xlabel,
ylabel, legend, missing_glyphs as a list) into the newly created code
cell's `cell["metadata"]["chart"]` mapping before appending the cell to the
notebook. When `png_bytes` is plain `bytes` (not a `RenderedChart`),
`cell["metadata"]["chart"]` is left unset exactly as today, preserving
`notebook_audit`'s existing "unaudited" finding and missing-glyph/near-
empty/missing-label detection for that case (DES-AIDS-041 unchanged). This
is an intentional, documented semantic extension of `record_chart`'s
contract, not a value-preserving change for every conceivable external
consumer: a caller that previously always saw an absent
`cell["metadata"]["chart"]` key will now see it populated whenever it
passes a `RenderedChart`.
Interfaces: visualization.record_chart(handle, code, png_bytes: bytes) ->
int, public annotation unchanged (left as `bytes` since `RenderedChart`
is a subtype); internally the function performs an `isinstance` check to
recognize a `RenderedChart` instance and extract its `chart_metadata`.
Constraints: Must not require `visualization.record_chart`'s callers to
pass chart metadata as a separate argument; must not write
`cell["metadata"]["chart"]` when given plain bytes, since
`notebook_audit.audit_visual_outputs` (DES-AIDS-041) relies on that
absence to surface "unaudited" for non-conforming callers.
Requirements: REQ-AIDS-061
ADRs: ADR-0068
Depends-On: DES-AIDS-048, DES-AIDS-041

## DES-AIDS-050: Dataset-comparison agreement rate as float | None / 一致率のfloat | None型による明確化
Responsibilities: In `dataset_validation`, change `ColumnComparison`'s
`agreement_rate` field type annotation from `float` to `float | None`,
documenting `None` as "not computable: no eligible joined rows for this
comparison" (an intentional semantic extension that existing and future
consumers of `agreement_rate` must handle by branching on `None`, not a
value-preserving change for arbitrary external numeric consumers). In
`compare_datasets`, before building `primary_key_values`/
`candidate_key_values`, filter each side's key-column rows to those with
no null key-column value, by computing two full-row eligibility frames —
`eligible_primary = primary.dropna(subset=primary_keys)` and
`eligible_candidate = candidate.dropna(subset=candidate_keys)` — which
retain every column (not only the key columns). Derive
`primary_key_values`/`candidate_key_values` from the key-column
projections of `eligible_primary`/`eligible_candidate`
(`eligible_primary[primary_keys]` and the candidate equivalent), so that
`matched_keys`/`primary_only_keys`/`candidate_only_keys` never count a
null-key row as matched or unmatched on either side — this corrects the
current implementation's pandas set-equality behavior, under which two
null keys (e.g. both `None`) compare equal and are incorrectly counted as
a match today. Likewise, build `merged` from `eligible_primary` and
`eligible_candidate` (an inner merge over already-non-null keys, with all
value-mapped columns still present on both sides), so no null-matches-null
row reaches the per-column comparison either, and every existing
`primary_col_name`/`candidate_col_name` value-column lookup continues to
resolve against `merged` exactly as today. For each compared column, keep
the existing `matched_rows`/`mismatched_rows`/`total` computation over
`merged` exactly as today (now implicitly restricted to eligible,
non-null-key joined rows by the upstream filter, with no separate
eligibility mask needed). When a column's `total` is zero, set
`agreement_rate = None`; otherwise keep the existing `matched_rows /
total` computation unchanged.
Interfaces: dataset_validation.ColumnComparison.agreement_rate: float |
None (was `float`); dataset_validation.compare_datasets(...) ->
DatasetComparisonReport, unchanged public signature.
Constraints: Must not change `agreement_rate`'s numeric value or meaning
for any column with at least one eligible joined row; must not change
`matched_keys`/`primary_only_keys`/`candidate_only_keys` for any dataset
pair where every key-column value is already non-null on both sides
(the null-row filter is a no-op in that case); for a pair containing at
least one null-key row, the corrected (filtered) `matched_keys` count is
the intended fix, not a regression, per REQ-AIDS-062's explicit null-key
exclusion acceptance.
Requirements: REQ-AIDS-062
ADRs: ADR-0069
Depends-On: DES-AIDS-045

## DES-AIDS-051: Significance-gated correlation interpretation / 有意性に基づく相関解釈の分岐
Responsibilities: In `stats_analysis`, add a `significance_threshold:
float = 0.05` parameter to `correlation`, threaded into `_interpret(r,
p_value, language, significance_threshold)`. `_interpret` first checks
`p_value >= significance_threshold`; when true, it returns a fixed
sentence template that still reports the computed `r` and the
DES-AIDS-053-formatted p-value display (`p_display`, shared by both
branches), but replaces the strength/direction clause with a distinct
"no statistically clear correlation is observed" wording — e.g. `en`:
`"The correlation coefficient is {r:.4f} ({p_display}), and no
statistically clear correlation is observed."`; `ja`:
`"相関係数は {r:.4f} ({p_display}) で、統計的に明確な相関は見られません。"`
— regardless of `r`'s magnitude or sign, bypassing the existing
strength/direction phrase (not the numeric report) entirely for that
case. When `p_value < significance_threshold`, the existing magnitude/
direction-based wording path runs unchanged (still using the shared
`p_display`). `significance_threshold` values outside `[0.0, 1.0]` are
rejected by raising `ValueError` before any interpretation is computed.
Interfaces: stats_analysis.correlation(..., significance_threshold: float
= 0.05) -> StatResult, additive optional parameter (fully backward
compatible for existing callers that omit it; return type is the
existing `StatResult` dataclass, unchanged); stats_analysis._interpret(r,
p_value, language, significance_threshold) -> str (internal, signature
change is non-breaking since `_interpret` is module-private).
Constraints: Must not alter the existing magnitude/direction wording or
thresholds for any `p_value < significance_threshold` case; the
non-significant sentence must be textually distinct from (not a weakened
variant of) the existing "weak" wording, so it cannot be confused with a
low-but-significant correlation; both branches must share one `p_display`
computation (DES-AIDS-053) so the displayed p-value is never inconsistent
between them.
Requirements: REQ-AIDS-063
ADRs: ADR-0070
Depends-On: DES-AIDS-053

## DES-AIDS-052: Bundled Japanese font applied for the full rendering lifetime / レンダリング全体への日本語フォント適用
Responsibilities: In `visualization.render_chart`, widen the font-trigger
condition by keeping the existing `_contains_non_ascii(title) or
_contains_non_ascii(xlabel) or _contains_non_ascii(ylabel)` check exactly
as today (preserving REQ-AIDS-046's existing acceptance that any non-ASCII
character in a caller-supplied title/axis label, not only Japanese,
triggers the bundled font), and OR-ing it with a new, separate check over
the exact values matplotlib will render as tick labels or legend entries:
for `kind == "hist"`, the `x` column's values (`df[x]`) and the
DataFrame's index if it supplies tick labels; for other kinds, the
selected `x` column's values, the selected `y` column's values (`df[y]`,
since a categorical/string `y` column can be rendered as y-axis tick
labels, not only as a legend entry), and for the legend label
specifically: when `y` is given explicitly, the selected `y` column
name(s); when `y` is `None`, the names of every column pandas will
implicitly plot for that `kind` (every column of `df` other than `x` when
`x` is set, or every column of `df` when `x` is unset) — and the
DataFrame's index when `x` is unset and the index supplies tick labels.
This check additionally covers every pandas-auto-generated axis-label
source distinct from the caller-supplied `xlabel`/`ylabel` parameters
already covered by the preserved check above: the selected `x` column
name itself (pandas renders it as the x-axis label whenever `xlabel` is
not explicitly supplied); the selected `y` column name(s) wherever pandas
renders them as the y-axis label (not solely where they are a legend
source) when `ylabel` is not explicitly supplied; and `df.index.name`
whenever `x` is `None` (pandas renders the index name as the x-axis label
whenever `xlabel` is not explicitly supplied). These column-name and
index-name sources are inspected unconditionally (independent of whether
an explicit `xlabel`/`ylabel` was supplied), since checking them only
costs a cheap string test and keeps the trigger correct even if a caller
supplies `xlabel`/`ylabel` for one axis but not the other.
Values are stringified (`str(value)`) before inspection; non-string,
non-stringifiable values are treated as not containing Japanese text. A
column present in `df` but not selected by `x`/`y` for this plot is never
inspected and must not trigger the font via this new check (it may still
trigger the font via the unchanged title/xlabel/ylabel check above). This
new check uses a narrower `_contains_japanese` predicate, narrower than
`_contains_non_ascii`, per REQ-AIDS-064's scoping to Japanese-derived
plotted data, matching any code point in the following Unicode blocks:
Hiragana (U+3040–U+309F), Katakana (U+30A0–U+30FF), Katakana Phonetic
Extensions (U+31F0–U+31FF), Halfwidth and Fullwidth Forms' halfwidth
Katakana subrange (U+FF65–U+FF9F), CJK Symbols and Punctuation
(U+3000–U+303F, covering the ideographic iteration mark `々` and
Japanese punctuation), CJK Unified Ideographs (U+4E00–U+9FFF), CJK
Unified Ideographs Extension A (U+3400–U+4DBF), and CJK Compatibility
Ideographs (U+F900–U+FAFF). This block list is applied only to the above
plotted-value/index/legend-source values — it does not replace or narrow
the existing title/xlabel/ylabel
check, which keeps using `_contains_non_ascii` unchanged. When either the
unchanged title/xlabel/ylabel check or this new plotted-data check is
true, `_ensure_japanese_font()` is called before the figure is created and
plotted (unchanged call site relative to today, just with a widened,
OR-combined trigger condition), so `matplotlib.rcParams["font.family"]` is
set to the bundled font for the entire plot/draw/savefig sequence,
covering tick labels and legend text derived from that data.
Interfaces: visualization._contains_japanese(text: str | None) -> bool
(new predicate, additive alongside the existing, unmodified
`_contains_non_ascii`, which continues to gate the title/xlabel/ylabel
check exactly as today); render_chart(...) internal trigger logic only —
public signature unchanged.
Constraints: Must not regress REQ-AIDS-046's existing acceptance (any
non-ASCII character — not only Japanese — in title/xlabel/ylabel
continues to trigger the bundled font exactly as today; ASCII-only
title/xlabel/ylabel combined with ASCII-only plotted/index/legend data
continues to not require the bundled font); must run before the figure is
created and plotted, i.e. before DES-AIDS-048's plot/`savefig`/glyph-
warning-capture step, so that step observes the final, correctly-
configured font; must not inspect columns of `df` that are not selected
for plotting by this call.
Requirements: REQ-AIDS-064
ADRs: ADR-0071
Depends-On: DES-AIDS-009, DES-AIDS-034

## DES-AIDS-053: Bounded display of a sub-threshold p-value / 閾値未満p値の上限表記
Responsibilities: In `stats_analysis`, introduce a shared `p_display(
p_value)` helper used by `_interpret`'s both the significant and
non-significant sentence branches (DES-AIDS-051): when `p_value < 1e-4`,
`p_display` returns the literal string `"p < 1e-4"`; when `p_value >=
1e-4` (including exactly `1e-4`), it returns the existing `f"p={p_value
:.4g}"` formatted numeric value unchanged. This check is independent of,
and always computed before, DES-AIDS-051's significance branch, so a
sub-threshold p-value is displayed identically regardless of whether the
significant or non-significant sentence template is ultimately selected
(in practice `p_value < 1e-4` always implies `p_value <
significance_threshold` for the default `0.05`, but `p_display`'s
behavior does not depend on that implication holding).
Interfaces: stats_analysis.p_display(p_value: float) -> str (new,
module-private helper); stats_analysis._interpret(...) calls this helper
instead of inlining `:.4g` formatting — no public signature change.
Constraints: Must not change formatting for any `p_value >= 1e-4`; must
apply identically in both `ja` and `en` language branches and in both the
significant and non-significant sentence templates.
Requirements: REQ-AIDS-065
ADRs: ADR-0072
Depends-On: none
Change: CHANGE-004

## DES-AIDS-042: Analysis-assumption manifest with risk surfacing / 分析前提マニフェストとリスク表面化
Responsibilities: A new `analysis_assumptions` module providing an
`Assumption` dataclass (id, statement, status, evidence_cell=None,
impact_if_false=None, conclusion_critical=False) and an
`AnalysisAssumptionManifest` dataclass (analysis_scope: dict, assumptions:
tuple[Assumption,...], causal_scope: one of
"descriptive"/"associational"/"causal", sampling: dict|None). A
`check_manifest(manifest)` function returns findings: a finding when
`causal_scope=="causal"` and no assumption with status in {"tested",
"verified"} exists; a finding per conclusion-critical assumption whose
status is "assumed" or "rejected" (also collected into
`manifest.unresolved_risks()`); a finding when `sampling` is set but lacks
both "n" and "seed" keys.
Interfaces: analysis_assumptions.Assumption(...);
analysis_assumptions.AnalysisAssumptionManifest(...);
analysis_assumptions.check_manifest(manifest) ->
tuple[AssumptionFinding, ...]; manifest.unresolved_risks() ->
tuple[Assumption, ...].
Constraints: Pure data/validation module; does not itself run or detect
statistical tests — the caller/agent supplies assumption statuses based on
its own analysis.
Requirements: REQ-AIDS-054
ADRs: none — a pure validation/data-structure module with no architectural decision to record.
Depends-On: none

## DES-AIDS-043: Semantic anomaly detection and overlap validation / 意味的異常検知と重複検証
Responsibilities: A new `data_quality` module (distinct from the existing
statistical-outlier-only `anomaly_detection` module) providing
`detect_anomalies(df, schema)` — schema maps a column name to a constraint
dict supporting `lte_column` (cross-column comparison) and
`missing_sentinels` (list of raw values that mean missing) — returning an
`AnomalyReport` (tuple of `AnomalyFinding(row_index, column, code,
details)`) without mutating `df`. Also provides `validate_anomalies(primary,
reference, keys, columns, tolerance)` returning an `OverlapValidation`
(matched_keys, primary_only_keys, reference_only_keys, per-column max/mean
absolute difference among matched keys, and the specific keys whose
difference exceeds the declared tolerance for any compared column).
Interfaces: data_quality.detect_anomalies(df, schema: dict) -> AnomalyReport;
data_quality.validate_anomalies(primary, reference, keys: list[str],
columns: dict[str, str], tolerance: dict[str, float]) -> OverlapValidation.
Constraints: Never mutates or drops rows from either input dataframe
(copies before any internal manipulation); disposition (retain/exclude/
correct) is left entirely to the caller, matching the issue's "do not
automatically delete anomalous rows" safety requirement.
Requirements: REQ-AIDS-055
ADRs: none — a new, isolated module with no cross-cutting dependency or architectural trade-off.
Depends-On: none

## DES-AIDS-044: Bounded sensitivity-analysis plan execution / 境界付き感度分析プラン実行
Responsibilities: A `sensitivity` module providing `SensitivityPlan`
(`target_claim: str`, `parameter_grid: dict[str, list[Any]]`,
`max_runs: int = 100`) and `run_sensitivity(plan, analysis_fn,
stability_tolerance=0.2, absolute_tolerance=None)`.
`plan.specifications()` first computes the Cartesian product of
`parameter_grid` and raises `SensitivityBudgetExceededError` before
invoking `analysis_fn` at all if that count exceeds `plan.max_runs`.
Otherwise `run_sensitivity` calls `analysis_fn(**specification)` for every
combination, catching any exception per-specification (recorded on that
`SensitivityResult` as `failed=True`/`error=str(exc)`, not aborting the
rest), and classifies the run's overall conclusion by comparing every
successful result's sign and magnitude against the first successful
(baseline) specification:
"reversed" if any successful value's sign differs from another's,
"not_comparable" if the baseline value is `0` and no `absolute_tolerance`
was given (a relative deviation would be undefined), if every
specification failed, or if the grid itself produced zero specifications
(e.g. a dimension with an empty alternatives list); "stable" if all
non-zero successful values share a sign and the maximum deviation is
within tolerance, otherwise "attenuated". The magnitude
criterion is `absolute_tolerance` (checked against
`max_absolute_deviation`) when the caller supplies one, else
`stability_tolerance` (checked against `max_relative_deviation`); which
one was used is recorded on the report as `magnitude_criterion`, and
whether all non-zero successful values shared a sign (a value of exactly
`0` never breaks sign agreement) is recorded as `sign_consistent`.
`plan.target_claim` is preserved verbatim on every `SensitivityResult` and
on the aggregate `SensitivityReport`, so a detached result tuple or report
still identifies which scientific/business claim its metric values were
testing.
(GitHub #53: this correction keeps the pre-existing `stable: bool` field,
now `True` exactly when `classification == "stable"` — including the
"not_comparable"/empty-grid and all-failed cases, where `stable` is
`False` — for backward compatibility).
Interfaces: sensitivity.SensitivityPlan(target_claim, parameter_grid,
max_runs=100);
sensitivity.run_sensitivity(plan, analysis_fn: Callable[..., float],
stability_tolerance=0.2, absolute_tolerance: float | None = None) ->
SensitivityReport(target_claim, results: tuple[SensitivityResult, ...],
baseline_value, stable, max_relative_deviation, classification,
max_absolute_deviation, sign_consistent, magnitude_criterion), where
SensitivityResult carries target_claim, specification, value, failed,
error.
Constraints: `analysis_fn` is entirely caller-supplied (no built-in
statistical models); the module only orchestrates the bounded grid and
classifies stability, keeping it generic across the issue's many example
domains (clustering, regression, preprocessing toggles). Classification
must never report "stable" when successful values disagree in sign, and
must never derive a relative deviation from a zero baseline without an
explicit `absolute_tolerance`; `stable` must never be `True` when
`classification != "stable"`. `target_claim` must be a non-empty string;
blank/whitespace-only values are rejected before any specification
enumeration or evaluation begins. Because `target_claim` becomes part of
the public dataclass shape for `SensitivityPlan`, `SensitivityReport`, and
`SensitivityResult`, direct constructor callers must be updated to supply
that field explicitly during migration, and any shape-based consumer
(`dataclasses.asdict`, tuple conversion, snapshot/schema assertions, or
JSON derived from those representations) must account for the added field.
Requirements: REQ-AIDS-056
ADRs: ADR-0057
This change is intended to close GitHub #59's pre-existing target-claim
gap, noted during CHANGE-014 review, by making that claim an explicit part
of the plan/report shape instead of leaving it implicit in caller naming
conventions. (Note, post-merge: CHANGE-018 was merged into `main` after
CHANGE-013's PR #60 landed; this design was re-recorded against that
merged baseline with no semantic change to the responsibilities above.
A second re-record pass was needed after discovering a TDD-evidence
ordering mistake in the first pass's `tdd red`/`change-record` sequencing;
this line's wording was adjusted once more to produce the fresh
fingerprint delta that pass required.)
Depends-On: none

## DES-AIDS-045: Independent-dataset overlap comparison / 独立データセット重複比較
Responsibilities: A new `dataset_validation` module providing
`compare_datasets(primary, candidate, key_mapping, value_mapping,
candidate_relationship="unknown")`. Renames columns per `key_mapping`/
`value_mapping`, merges on the mapped key with an outer join to compute
matched vs. each side's unmatched keys, then for matched rows computes per
mapped value-column Spearman rank correlation and absolute-difference
statistics (mean, max). `candidate_relationship` must be one of
"independent", "same-upstream", or "unknown" and is always taken verbatim
from the caller — the function never infers "independent" from the
candidate simply having a different owner/slug than the primary; omitting
it defaults to "unknown", never "independent". `discover_validation_dataset`
candidate search (actual Kaggle querying) is explicitly out of scope for
this module — see constraints below — leaving `compare_datasets` as the
sole in-repo-actionable piece, consistent with the ask_user-selected
"proceed with feasible scope" decision for this issue.
Interfaces: dataset_validation.compare_datasets(primary, candidate,
key_mapping: dict[str,str], value_mapping: dict[str,str],
candidate_relationship: str = "unknown") -> OverlapComparison
(matched_keys, primary_only_keys, candidate_only_keys, per-column
rank_correlation and abs_difference stats, candidate_relationship).
Constraints: No network access, no Kaggle API client, and no dataset
discovery/search heuristic are implemented in this repository: this
codebase has no existing Kaggle integration to extend (confirmed by
inspecting `ingestion.py`), and building a live external-search feature
exceeds this repository's dependency/secrets footprint. `compare_datasets`
covers every acceptance criterion that depends only on already-loaded
dataframes; `discover_validation_datasets` remains a documented, not
implemented, extension point.
Requirements: REQ-AIDS-057
ADRs: none — a new, isolated module; no shared state or cross-cutting concern introduced.
Depends-On: none

## DES-AIDS-054: Insight body text cross-checked against its cited value / Insight本文と引用値の整合確認
Responsibilities: In `notebook_audit`, add a helper
`_strip_evidence_fences(markdown_source) -> str` that removes every
evidence-fenced block (the existing "evidence" code-fence convention, via
`_EVIDENCE_FENCE_PATTERN.sub`) and returns the remaining text. Add a helper
`_body_mentions_value(body_text: str, cited_value: str) -> bool` that first
checks a plain substring match; when `cited_value` parses as a `float`, it
additionally scans `body_text` for decimal-looking numbers (`re.findall`
against `-?\d+\.\d+`), and for each candidate rounds both the candidate and
`cited_value` to the candidate's own number of decimal places, returning
`True` on any match (satisfying REQ-AIDS-066's documented-rounding
tolerance, e.g. body "0.95" matching cited "0.954" at 2 decimal places).
In `audit_notebook`'s insight-validation loop, once an evidence block's
primary `cited_value` is confirmed to resolve against a real executed cell
(the existing `_find_evidence_cell` check), call
`_body_mentions_value(_strip_evidence_fences(source), cited_value)`; when
`False`, append a warning-severity `NotebookAuditFinding` naming the cell
index and the unmentioned cited value. This check applies only to each
evidence block's primary `cited_value` (REQ-AIDS-066's scope); it runs once
per resolved evidence block when DES-AIDS-057 extends validation to
multiple blocks, but deliberately does *not* run against
`supporting_evidence` entries' `cited_value`s, which DES-AIDS-057 validates
only for evidence-resolution, not body-text mention. This never affects
`report.ok`, since it is `warning`-severity only (REQ-AIDS-066 explicitly
scopes this to a warning, not an error, to avoid false positives on
reasonable paraphrases that still contain the precise figure as text).
Interfaces: notebook_audit._strip_evidence_fences(markdown_source: str) -> str
(module-private); notebook_audit._body_mentions_value(body_text: str,
cited_value: str) -> bool (module-private).
Constraints: Must not change `report.ok` for any existing passing notebook
(warning-only); must not require a second notebook read or re-parsing
beyond the markdown source already in memory; numeric rounding comparison
only applies when `cited_value` is float-parseable, falling back to plain
substring matching otherwise (covers non-numeric claim types such as
"OK"/categorical labels).
Requirements: REQ-AIDS-066
ADRs: ADR-0060
Depends-On: DES-AIDS-010, DES-AIDS-033, DES-AIDS-035

## DES-AIDS-055: Explicit non-computable correlation interpretation for NaN statistics / NaN統計量に対する算出不能の明示
Responsibilities: In `stats_analysis.correlation`'s `_interpret` helper, add
`import math` to the module's existing imports, then add an early
`math.isnan(coefficient) or math.isnan(p_value)` guard before the
existing significance-threshold branch (DES-AIDS-051); when it fires,
return the language-appropriate "correlation could not be computed"
sentence (mirroring the existing `language="ja"`/`"en"` branching
convention already used for the significance and magnitude/direction
sentences) instead of falling into the `p_value >= significance_threshold`
comparison, which is always `False` for NaN in Python and would otherwise
silently fall through to a spurious magnitude/direction claim (the root
cause of GitHub #47). This guard must run before any NaN p-value reaches
the existing p-value display/formatting step (DES-AIDS-053's bounded
display), since that step is not meant to format a non-numeric result.
The numeric `coefficient`/`p_value` fields returned by `correlation` are
untouched (still whatever `scipy_stats.pearsonr` produced, including NaN)
— only the generated interpretation text changes.
Interfaces: no public signature change; `stats_analysis.correlation`'s
internal `_interpret` control flow gains one additional guarded branch
evaluated before DES-AIDS-051's existing significance check; module gains
a top-level `import math`.
Constraints: Must not alter behavior for any finite coefficient/p_value
pair (DES-AIDS-051/REQ-AIDS-063's existing significance-gated behavior is
preserved unchanged for all non-NaN inputs); must check NaN on both
`coefficient` and `p_value` independently (either alone can be NaN
depending on which scipy code path produced it).
Requirements: REQ-AIDS-067
ADRs: ADR-0061
Depends-On: DES-AIDS-051, DES-AIDS-053

## DES-AIDS-056: Delimiter-sniffing CSV ingestion with mismatch warning / 区切り文字検出付きCSV取込と不一致警告
Responsibilities: In `ingestion.ingest`'s CSV branch, before calling
`pandas.read_csv`, read a new, bounded text sample (e.g. the file's first
few kilobytes/lines, decoded as UTF-8 with errors replaced — a fresh,
locally-scoped read introduced by this design, not a reuse of any existing
REQ-AIDS-032 remote-fetcher dataframe-row-limit mechanism, which applies
only after a dataframe already exists) and run
`csv.Sniffer().sniff(sample, delimiters=",\t;")` inside a
`try/except csv.Error`. Track whether sniffing succeeded. On success, pass
the sniffed delimiter as `read_csv(..., sep=sniffed_delimiter)`. On
`csv.Error` (ambiguous sample), fall back to the existing default
comma-separated `read_csv` call unchanged, and record that fallback
occurred. After the dataframe is produced, append a mismatch warning (e.g.
f"CSV was parsed with the comma fallback as a single column named
{name!r}; the file may use a tab or semicolon delimiter instead.") to the
result's new `warnings` field only when all three hold: sniffing fell back
(did not
succeed), the comma-parsed fallback produced exactly one column, and that
column's header name contains a literal tab (`"\t"`) or semicolon (`";"`)
character — a successfully sniffed, confidently-parsed result (even a
single genuine column) never receives this warning. Add a new
`warnings: tuple[str, ...] = ()` field to the `IngestionResult` dataclass
(additive, keyword-defaulted — preserves every existing positional/keyword
construction call site).
Interfaces: `IngestionResult.warnings: tuple[str, ...]` (new field,
default `()`); no change to `ingest`'s public signature.
Constraints: Must not change ingestion behavior for any non-CSV source
kind; must not change the dataframe produced for a genuinely comma- or
semicolon- or tab-delimited file beyond correctly splitting its columns
(no row-count/value changes); the delimiter set considered is fixed to
comma/tab/semicolon (REQ-AIDS-068's named set) — no generalized arbitrary-
delimiter configuration is introduced by this design; the mismatch warning
is gated strictly on sniff-fallback, never emitted after a successful
sniff.
Requirements: REQ-AIDS-068
ADRs: ADR-0062
Depends-On: none (introduces a new, self-contained sampling/sniffing step)

## DES-AIDS-057: Exhaustive evidence-manifest validation within a single insight cell / 単一Insightセル内の全エビデンス網羅検証
Responsibilities: Replace `notebook_audit._extract_evidence_manifest`'s
single `.search()` call with a new
`_extract_evidence_manifests(markdown_source) -> list[dict | None]`
that uses `_EVIDENCE_FENCE_PATTERN.finditer()` to collect every fenced
block's parsed JSON payload in appearance order, yielding `None` (not
silently skipping the block) for a block that fails `json.loads` or
parses to a non-dict — the audit loop below turns each `None` entry into
an error-severity finding rather than treating it as absent, so a
malformed block can never be mistaken for "no block present". In
`audit_notebook`'s insight loop, iterate every block returned (instead of
only the first): a block whose payload is `None` produces an error-severity
"malformed evidence block" finding tagged with its 0-based block index;
a well-formed block's payload runs through the existing required-keys/
evidence-resolution checks (and DES-AIDS-054's primary-citation
body-mention check), each finding likewise tagged with its block index
when more than one block exists. For each well-formed manifest,
additionally read an optional `supporting_evidence` field; when present,
require it to be a `list` whose every entry is a `dict` with an `int`
`execution_count` and a non-empty `str` `cited_value` — any entry failing
this shape check produces an error-severity finding ("malformed
supporting_evidence entry") identifying the cell and entry index;
well-formed entries are resolved via the same `_find_evidence_cell` call
used for the primary citation, producing the same "evidence not found"
error finding on failure. A cell with zero evidence fences at all still
produces the existing single "missing evidence manifest" finding
unchanged (only a cell with at least one fence enters this per-block
validation). `insight_cell_count` continues to increment once per
qualifying cell (not per block), matching existing report semantics.
Interfaces: notebook_audit._extract_evidence_manifests(markdown_source: str)
-> list[dict | None] (module-private, replaces the single-result
`_extract_evidence_manifest` call site within `audit_notebook`; the old
singular helper is kept only if still referenced elsewhere, otherwise
removed in the same change to avoid dead code).
Constraints: Must preserve current behavior exactly for a cell with
exactly one well-formed evidence block and no `supporting_evidence` field;
must never silently drop a malformed block's error from the report; must
not assume `supporting_evidence` entries appear in any file this
repository does not already construct in its own test fixtures (no
backward-compatibility burden for an undocumented field).
Requirements: REQ-AIDS-069
ADRs: ADR-0063
Depends-On: DES-AIDS-033, DES-AIDS-054

## DES-AIDS-058: Heading-prefixed result paragraphs recognized as insight candidates / 見出し付き結論段落のInsight候補認定
Responsibilities: Rewrite `notebook_audit._looks_like_insight_candidate` so
that, for a heading-prefixed cell (`stripped.startswith("#")`), it strips
every leading heading line (lines matching `^#+\s*.*$` from the start of
the stripped text, consuming consecutive heading lines and the blank
lines directly between them) and recurses the *same* candidacy decision
(the existing evidence-fence-present-or-non-heading-remainder logic) on
whatever non-heading text remains, rather than returning `False`
unconditionally once an evidence fence is absent. When the remainder after
stripping heading lines is empty, the cell is not a candidate (preserves
pure section-heading cells, e.g. "## 結果" alone). This directly reuses
the pre-existing non-heading-cell heuristic instead of introducing new,
broader candidacy criteria, bounding the requirement's scope to exactly
what REQ-AIDS-070 and GitHub #43 describe.
Interfaces: no public signature change;
`notebook_audit._looks_like_insight_candidate(markdown_source: str) -> bool`
internal control flow gains heading-stripping plus a recursive/iterative
check on the remainder.
Constraints: Must not change the existing #30 behavior (a heading-prefixed
cell that already carries an evidence fence remains a candidate); must not
treat a heading-only cell (no body after the heading) as a candidate.
Requirements: REQ-AIDS-070
ADRs: ADR-0064
Depends-On: DES-AIDS-033, DES-AIDS-036

## DES-AIDS-059: Output-level chart metadata persisted by build_image_output / build_image_outputによる出力側チャートメタデータ永続化
Responsibilities: Update `visualization.build_image_output` to accept its
existing single `png_bytes` parameter and, when `isinstance(png_bytes,
RenderedChart)`, construct the same title/xlabel/ylabel/legend/
missing_glyphs dict shape DES-AIDS-049's `record_chart` already builds for
cell-level metadata (extracted into a shared module-private
`_chart_metadata_dict(chart_metadata: ChartMetadata) -> dict` helper reused
by both call sites to avoid duplicating the field list), and pass it as
`metadata={"chart": ...}` to `nbformat.v4.new_output(...)`. For plain
`bytes` input, `metadata` is omitted (empty), preserving current behavior.
`record_chart` is unchanged by this design (it already calls
`build_image_output` and separately sets cell-level metadata; it now
additionally benefits from output-level metadata "for free" since
`build_image_output` sets it internally) — this is a deliberate shared-
helper reuse, not a behavior change to `record_chart` itself.
Interfaces: visualization.build_image_output(png_bytes: bytes) -> NotebookNode
(signature unchanged; return value's `.metadata["chart"]` is now populated
when `png_bytes` is a `RenderedChart`); visualization._chart_metadata_dict
(chart_metadata: ChartMetadata) -> dict (new, module-private, shared with
DES-AIDS-049's `record_chart` path).
Constraints: Must not change the PNG/base64 payload already written to
`data["image/png"]`; must not require call-site changes at any existing
`build_image_output` caller (additive metadata only).
Requirements: REQ-AIDS-071
ADRs: ADR-0065
Depends-On: DES-AIDS-048, DES-AIDS-049

## DES-AIDS-060: Per-image chart-metadata matching during visual audit / 視覚監査における画像単位でのチャートメタデータ照合
Responsibilities: Rewrite `notebook_audit.audit_visual_outputs`'s per-cell
loop to iterate image outputs individually (`enumerate(cell.get("outputs",
[]))`, filtering to those with `data["image/png"]`) instead of computing
one `chart_metadata` value per cell. For each image output at index
`output_index`, resolve its metadata as: (1) `output.get("metadata",
{}).get("chart")` when that is a non-empty `dict`; else (2), only when the
cell contains exactly one qualifying image output and that output's own
`metadata` has no `"chart"` key at all (distinct from an empty/invalid one,
per REQ-AIDS-072's explicit no-fallback-on-malformed-output-metadata rule),
the existing cell-level `cell.get("metadata", {}).get("chart")`; else (3)
`None`. When resolution yields `None` (or an invalid non-dict/empty
value), emit the existing "unaudited" finding tagged with
`(cell_index, output_index)` instead of a bare cell index, and treat the
metadata as `{}` for the subsequent missing_glyphs/label checks (unchanged
logic, now run per-output instead of per-cell). The near-empty-image byte
scan already iterates per-output and is unaffected structurally; it is
simply tagged with the same `(cell_index, output_index)` pair for
consistency. `VisualAuditFinding` gains an additive `output_index: int |
None = None` field (defaulted, so every existing test construction and
comparison of `VisualAuditFinding(...)` without this field continues to
work unchanged).
Interfaces: notebook_audit.VisualAuditFinding gains `output_index: int |
None = None` (additive, backward-compatible field); 
notebook_audit.audit_visual_outputs(notebook, chart_cell_indices) ->
tuple[VisualAuditFinding, ...] (signature unchanged, internal per-cell loop
replaced with a per-output loop as described).
Constraints: Must preserve every existing single-image-per-cell test's
finding content and count unchanged (output_index populated but not
previously asserted); must not apply one image's valid metadata to a
sibling image in the same cell under any circumstance.
Requirements: REQ-AIDS-072
ADRs: ADR-0066
Depends-On: DES-AIDS-041, DES-AIDS-059

Note: this design, together with DES-AIDS-059, is exactly the mechanism
REQ-AIDS-053's updated acceptance text now cross-references ("an image
output whose own output-level `metadata["chart"]` ... and whose enclosing
code cell's `metadata["chart"]` are both absent, empty, or non-mapping").



## DES-AIDS-073: Extended render_chart kind dispatch / render_chart種類ディスパッチ拡張
Responsibilities: Extend `visualization.render_chart`'s kind dispatcher and `_SUPPORTED_KINDS` to add `box`, `barh`, and `heatmap` while preserving the current `scatter`/`line`/`bar`/`hist` code path when no new parameters are used. `box` renders grouped distributions from `x` category values to `y` numeric values by materializing one box per distinct `x` value (or falls back to a single-series/all-numeric boxplot when grouping columns are omitted). `barh` reuses the existing pandas/matplotlib bar plotting path but selects the horizontal orientation explicitly. `heatmap` computes a numeric matrix before plotting: when `x` and `y` are both supplied it uses those named numeric columns' correlation matrix; otherwise it first detects the common "already a square labeled matrix" case (square numeric dataframe whose index labels equal its column labels) and renders those values directly, falling back to the correlation matrix of all numeric columns only when the input is not already a labeled matrix; the matrix is rendered with `Axes.imshow`, labeled ticks, and a colorbar on the same figure.
Interfaces: `render_chart(df, kind="scatter"|"line"|"bar"|"barh"|"box"|"hist"|"heatmap", ...) -> RenderedChart` (public signature extended only by later DES-AIDS-074/075 optional keyword arguments; existing positional and keyword call sites remain valid).
Constraints: Existing calls for `scatter`/`line`/`bar`/`hist` without the new keyword arguments must preserve today's behavior and PNG-bytes compatibility; `heatmap` ignores legend/error-bar logic entirely and instead derives axis labels from the rendered matrix; numeric-column selection failures still raise a clear `ValueError` rather than emitting a misleading empty image.
Requirements: REQ-AIDS-085
ADRs: ADR-0095
Depends-On: DES-AIDS-009, DES-AIDS-048
Implementation: `CODE-AIDS-111`-`CODE-AIDS-118` in
`src/ai_data_scientist/visualization.py` (CHANGE-012); test IDs
`TEST-AIDS-195`-`202` (renumbered from the original draft's
`TEST-AIDS-177`-`184` to avoid a collision with CHANGE-011's
`TEST-AIDS-177`).

## DES-AIDS-074: Hue-driven series splitting and legend-title capture / hueによる系列分割と凡例タイトル取得
Responsibilities: Add optional `hue: str | None = None` and `legend_title: str | None = None` parameters to `visualization.render_chart`, plus a small internal plotting path that activates only when hue-driven grouping or explicit legend-title override is requested. For `scatter`, `line`, and `hist`, iterate `df.groupby(hue, sort=False)` and draw one matplotlib series per distinct hue value with `label=str(group_value)` so a legend is produced deterministically in input order. For `bar` and `barh`, reshape to a pivoted table indexed by `x`, columned by `hue`, and valued by `y`, then hand that table to pandas plotting so each hue level becomes a separate legend series; before pivoting, normalize missing hue values to a guaranteed-noncolliding sentinel so they survive the reshape and are then relabeled back to the visible `"NaN"` legend entry. After plotting any chart kind, if a legend exists and `legend_title` is provided, set that rendered legend title; otherwise, when hue was used, set the legend title to the hue column name. Extend `ChartMetadata` with an additive `legend_title: str | None = None` field and expose a forwarding `RenderedChart.legend_title` property so authoring metadata records the rendered legend title alongside the existing boolean `legend` field.
Interfaces: `render_chart(..., hue: str | None = None, legend_title: str | None = None) -> RenderedChart`; `ChartMetadata(..., legend_title: str | None = None, missing_glyphs=...)`; `RenderedChart.legend_title -> str | None`.
Constraints: The no-`hue`, no-`legend_title` path for pre-existing chart kinds must stay byte-compatible with the prior implementation flow; legend labels are derived only from explicit dataframe columns already being plotted (no implicit aggregation names or guessed titles); grouped `bar`/`barh` input must be unique per `(x, hue)` pair (or pre-aggregated by the caller) and a duplicate pair raises `ValueError` instead of silently discarding later rows; kinds that do not create a legend keep `legend == False` and `legend_title is None`.
Requirements: REQ-AIDS-086
ADRs: ADR-0096
Depends-On: DES-AIDS-073

## DES-AIDS-075: Symmetric and asymmetric error-range normalization / 対称・非対称誤差範囲の正規化
Responsibilities: Add optional `xerr` and `yerr` parameters to `visualization.render_chart` for scatter/line/bar/barh charts. Normalize each argument through one shared helper that accepts `None`, a single column name (symmetric error, returning that column's numeric sequence), or a 2-tuple/list of column names (asymmetric error, returning a two-row lower/upper sequence in matplotlib's expected shape). For `scatter` and `line`, draw the points/line via `Axes.errorbar`; for `bar`/`barh`, pass the normalized arrays through pandas/matplotlib's existing bar plotting support (`yerr=` or `xerr=` depending on orientation). When `hue` also reshapes a bar/barh chart to a pivoted table, derive matching pivoted error tables from the same `(x, hue)` key, using the same missing-hue sentinel normalization as DES-AIDS-074 so the `"NaN"` series and its error ranges remain aligned through the reshape. The helper validates that every referenced column exists before any plotting occurs.
Interfaces: `render_chart(..., xerr: str | tuple[str, str] | list[str] | None = None, yerr: str | tuple[str, str] | list[str] | None = None) -> RenderedChart`; module-private `_resolve_error_values(df, spec) -> list[float] | list[list[float]] | None`.
Constraints: Omitting both arguments preserves the current rendering path unchanged; asymmetric errors must preserve caller order as `(lower, upper)` rather than being sorted or absolutized; grouped `bar`/`barh` error data shares DES-AIDS-074's uniqueness constraint on `(x, hue)` pairs and raises the same `ValueError` on duplicates rather than silently taking the first row; invalid column references fail fast with `ValueError` instead of silently dropping error bars.
Requirements: REQ-AIDS-087
ADRs: ADR-0097
Depends-On: DES-AIDS-073

## DES-AIDS-076: Figure-to-ChartMetadata introspection helper / FigureからのChartMetadata抽出補助
Responsibilities: Add `visualization.chart_metadata_from_figure(fig, *, missing_glyphs=()) -> ChartMetadata`, selecting the figure's first axes as the authoritative plotted axes, reading `get_title()`, `get_xlabel()`, `get_ylabel()`, and `get_legend()`, and returning a `ChartMetadata` whose `legend` boolean reflects whether a legend exists and whose `legend_title` is the rendered legend-title text (or `None` when absent/empty). This helper is intentionally metadata-only: callers that hand-draw a figure still save PNG bytes themselves, then wrap those bytes as `RenderedChart(png_bytes, chart_metadata_from_figure(fig))` so the existing `build_image_output` / `record_chart` metadata-persistence path can audit them unchanged.
Interfaces: `chart_metadata_from_figure(fig: matplotlib.figure.Figure, *, missing_glyphs: tuple[str, ...] | list[str] = ()) -> ChartMetadata`.
Constraints: Must not mutate the figure or require a canvas redraw beyond what the caller already performed to save it; defaults `missing_glyphs` to an empty tuple because glyph warnings cannot be recovered reliably from an already-rendered figure after the fact; uses the first axes only, so auxiliary colorbar axes added by `heatmap` do not displace the main plotting axes.
Requirements: REQ-AIDS-088
ADRs: ADR-0098
Depends-On: DES-AIDS-048, DES-AIDS-049, DES-AIDS-059
