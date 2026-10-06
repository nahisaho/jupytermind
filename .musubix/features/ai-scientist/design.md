---
schemaVersion: 1
feature: ai-scientist
---
# Design / 設計 (MVP)

## DES-AISCI-001: Skill entry orchestrator / スキルエントリ・オーケストレータ
Responsibilities: Expose the GitHub Copilot Agent Skill entry point
(.github/skills/ai-scientist/SKILL.md), detect the instruction's language,
parse the requested phase and optional override reason from the
instruction, resolve the active phase for the current project via
DES-AISCI-003, evaluate the phase gate (DES-AISCI-004) with the parsed
requested phase and override before any dispatch, look up the active (or
override-permitted) phase's handler in the manifest (DES-AISCI-015), and
dispatch the instruction to it, assembling the user-facing response in the
same language as the instruction.
Interfaces: SKILL.md instructions consumed by the Copilot agent runtime;
detectLanguage(instruction: str) -> "ja" | "en" (used both to select the
response language here and reused verbatim by DES-AISCI-007); internal
dispatch(instruction, projectName, requestedPhase?: string, override?:
{reason: string}) -> PhaseResult | GateBlockedResult. When `requestedPhase`
is omitted, it defaults to the project's current active phase (no gate
check needed in that case).
Constraints: Must not implement any phase's domain logic itself; every
phase's handler is the single importable `src/ai_scientist` module function
declared for it in the manifest (DES-AISCI-015) — any sibling-skill
invocation happens only inside that module function, through one of its
declared pinned skill dependencies, never as a manifest entry dispatched
to directly. Must call DES-AISCI-004.checkGate before manifest lookup
whenever `requestedPhase` differs from the active phase. Must follow the
same structural conventions as `ai-data-scientist`'s SKILL.md.
Requirements: REQ-AISCI-001
ADRs: ADR-0073
Depends-On: DES-AISCI-002, DES-AISCI-003, DES-AISCI-004, DES-AISCI-015

## DES-AISCI-002: Shared project handle resolver / 共有プロジェクトハンドル解決
Responsibilities: Validate a project identifier and resolve its stable
workspace root by calling ai-data-scientist's real
`ai_data_scientist.project_manager.resolve_project` function directly (not
re-implementing slug validation), then create the seven ai-scientist phase
subdirectories under that root on first use.
Interfaces: resolve_research_project(name) -> ResearchProjectHandle{name,
root, notebook_path, planning_dir, literature_dir, design_dir,
manuscript_dir, review_dir, reproducibility_dir, presentation_dir}; the
`name`, `root`, and `notebook_path` fields are copied verbatim from the
`ai_data_scientist.project_manager.ProjectHandle` returned by
`ai_data_scientist.project_manager.resolve_project(name)`.
Constraints: Must reject any project name ai-data-scientist's
`resolve_project` would reject, via the same error path (no independent
validation regex). Must create each phase subdirectory at most once per
workspace and must be idempotent across process-working-directory changes.
Requirements: REQ-AISCI-002, REQ-AISCI-003
ADRs: ADR-0074
Depends-On: none

## DES-AISCI-003: Phase state store / フェーズ状態ストア
Responsibilities: Persist, per project, the eight-phase order, which phase
is active, and which are completed, in a JSON state file under the
project's workspace root; initialize a new project with research-planning
active and all others incomplete; before persisting a completion, call
DES-AISCI-017.validateCompletionEvidence and reject the transition if it
returns false; advance to the next phase automatically when the active
phase is marked complete and no override is in effect.
Interfaces: load_phase_state(handle) -> PhaseState; mark_phase_complete(handle,
phase, evidence_refs) -> PhaseState (internally calls
DES-AISCI-017.validateCompletionEvidence(handle, phase) before persisting);
active_phase(handle) -> str.
Constraints: Must be read-modify-write safe across separate CLI invocations
(single-writer discipline, reusing the same enqueue pattern as
ai-data-scientist's notebook writer). Must never skip a phase in the fixed
order when advancing automatically. Must never persist a completion whose
evidence check failed.
Requirements: REQ-AISCI-004, REQ-AISCI-005
ADRs: ADR-0075
Depends-On: DES-AISCI-002, DES-AISCI-017

## DES-AISCI-004: Phase-gate enforcer / フェーズゲート制御
Responsibilities: Before dispatching any phase handler, compare the
requested phase against the active phase from DES-AISCI-003; block and
report the first incomplete predecessor phase unless the request carries an
explicit override; when an override is present, execute the single request
without mutating active-phase or completion state, and persist the override
reason and named incomplete predecessors as a durable audit entry in the
phase state store (DES-AISCI-003), keyed by a generated request ID and
timestamp, queryable afterward.
Interfaces: checkGate(handle, requestedPhase, override?: {reason: string})
-> GateDecision{allowed: bool, blockedOn?: string}; on an allowed override,
DES-AISCI-003.record_override(handle, requestId, timestamp, requestedPhase,
reason, incompletePredecessors) -> OverrideRecord persists the audit entry
before the request proceeds; list_overrides(handle) -> OverrideRecord[]
retrieves prior entries.
Constraints: An override must never alter active_phase or any phase's
completion status persisted by DES-AISCI-003; it is scoped to exactly one
dispatch call. Every override record must be persisted before the gated
request is dispatched, not only returned to the caller.
Requirements: REQ-AISCI-006, REQ-AISCI-007
ADRs: ADR-0076
Depends-On: DES-AISCI-003

## DES-AISCI-005: ai-data-scientist delegation adapter / ai-data-scientist委譲アダプタ
Responsibilities: When the active phase is data-analysis, call
ai-data-scientist's real `ai_data_scientist.project_manager.resolve_project(
handle.name)` to obtain that feature's own `ProjectHandle` (asserting its
`root`/`notebook_path` equal the research handle's corresponding values
computed by DES-AISCI-002), then pass that returned `ProjectHandle` to
`ai_data_scientist.project_manager.ensure_notebook` and to ai-data-scientist's
Jupyter MCP execution path — never a shared or reconstructed handle object —
and record the resulting notebook path as this phase's evidence, performing
no independent analysis logic.
Interfaces: delegateDataAnalysis(researchHandle, instruction) -> PhaseResult;
internally: `aidsHandle = ai_data_scientist.project_manager.resolve_project(
researchHandle.name)`; `notebook_path =
ai_data_scientist.project_manager.ensure_notebook(aidsHandle)`; the
resulting notebook_path must equal
`<researchHandle.root>/notebooks/<project_name>.ipynb`.
Constraints: Must call ai-data-scientist's real `resolve_project`/
`ensure_notebook` Python functions directly (an in-repo package import, not
a separately-installed Agent Skill invocation) rather than duplicating
their path computation; this phase's manifest entry (DES-AISCI-015)
therefore declares zero sibling-skill dependencies, since no external
skill-registry pinning applies to this repository's own
`ai_data_scientist` package; must assert
`aidsHandle.root == researchHandle.root` and
`aidsHandle.notebook_path == researchHandle.notebook_path` before use, and
fail the delegation if they diverge rather than silently proceeding.
Requirements: REQ-AISCI-008
ADRs: ADR-0077
Depends-On: DES-AISCI-002, DES-AISCI-003, DES-AISCI-016

## DES-AISCI-006: tech-writer delegation adapter (manuscript-writing) / tech-writer委譲アダプタ（論文執筆）
Responsibilities: When the active phase is manuscript-writing, invoke
kotonoha's `tech-writer` skill with the validated project handle and the
project's recorded research evidence manifest (gathered from
planning/literature/design/data-analysis phase evidence) to produce a
Markdown manuscript artifact under manuscript_dir, performing no
independent prose-generation logic.
Interfaces: delegateManuscriptWriting(handle, evidenceManifest) ->
ManuscriptArtifact{path, format: "markdown"}, invoked via skill-invocation
of `tech-writer` per the pinned manifest entry (DES-AISCI-015).
Constraints: Must always request Markdown output from tech-writer (it has
no format parameter); any non-Markdown final format is produced only by
DES-AISCI-018, never requested from tech-writer itself.
Requirements: REQ-AISCI-009
ADRs: ADR-0078
Depends-On: DES-AISCI-002, DES-AISCI-003, DES-AISCI-016

## DES-AISCI-007: Manuscript language metadata recorder / 原稿言語メタデータ記録
Responsibilities: Immediately after DES-AISCI-006 completes, determine the
manuscript's language (`ja` or `en`) using the same detection function as
DES-AISCI-001's instruction-language detection, applied to the instruction
that triggered manuscript-writing, and persist it as metadata attached to
the manuscript artifact record (not inferred later from the manuscript
text itself).
Interfaces: recordManuscriptLanguage(manuscriptArtifact, sourceInstruction)
-> ManuscriptArtifact{..., language: "ja" | "en"}.
Constraints: Must reuse DES-AISCI-001's detectLanguage function; must not
introduce a second, independently-tuned language classifier.
Requirements: REQ-AISCI-010
ADRs: ADR-0079
Depends-On: DES-AISCI-001, DES-AISCI-006

## DES-AISCI-008: Peer-review language router / 査読フェーズ言語ルーター
Responsibilities: When the active phase is peer-review, read the
manuscript's persisted language metadata (DES-AISCI-007); if `ja`, invoke
kotonoha's `japanese-prose` skill in its `review` mode against the
manuscript file; if `en`, invoke kotonoha's `tech-writer` skill in its
`review` mode against the manuscript file; if the metadata is missing or
any other value, block the request and report that supported manuscript
language metadata is required. Record findings from either branch as
peer-review phase evidence, distinct from manuscript-writing evidence.
Interfaces: delegatePeerReview(handle, manuscriptArtifact) -> PhaseResult |
BlockedResult{reason: "missing_or_unsupported_language"}.
Constraints: The `ja`/`en` branch choice must be a deterministic lookup on
the persisted metadata field, never a re-detection or heuristic guess; no
third branch silently falls back to either skill.
Requirements: REQ-AISCI-011, REQ-AISCI-012, REQ-AISCI-013
ADRs: ADR-0080
Depends-On: DES-AISCI-003, DES-AISCI-007, DES-AISCI-016

## DES-AISCI-009: presentation-planner delegation adapter / presentation-planner委譲アダプタ
Responsibilities: When the active phase is presentation, invoke kotonoha's
`presentation-planner` skill with the project's final manuscript path and
recorded research evidence manifest, and record the resulting
brief/scenario/slide-outline as presentation phase evidence, performing no
independent presentation-structuring logic.
Interfaces: delegatePresentation(handle, manuscriptArtifact, evidenceManifest)
-> PhaseResult, invoked via skill-invocation of `presentation-planner` per
the pinned manifest entry.
Constraints: Must pass the manuscript path produced by the manuscript-writing
phase (post-format-rendering if LaTeX was configured is not required —
presentation-planner only needs the content, not the rendered format).
Requirements: REQ-AISCI-014
ADRs: ADR-0081
Depends-On: DES-AISCI-002, DES-AISCI-003, DES-AISCI-006, DES-AISCI-016

## DES-AISCI-010: MCP tool-call gateway / MCPツール呼び出しゲートウェイ
Responsibilities: Route every external domain-tool/literature-search
request issued by any phase handler through the project's configured MCP
client (resolved by DES-AISCI-011/012/013), always tagging the call with
the requesting phase, and translating an unreachable server into a
classified error via DES-AISCI-014 rather than allowing any direct outbound
network call from ai-scientist code.
Interfaces: callMcpTool(serverName, toolName, args, phase: str) ->
ToolResult, raises MCPUnavailableError{serverName, phase} (via
DES-AISCI-014) on connection failure.
Constraints: Must be the sole code path phases use for domain-tool access;
no phase handler may hold its own HTTP/socket client; `phase` is required
on every call so DES-AISCI-014 can always report it.
Requirements: REQ-AISCI-015
ADRs: ADR-0082
Depends-On: DES-AISCI-011, DES-AISCI-012, DES-AISCI-013, DES-AISCI-014

## DES-AISCI-011: MCP server configuration loader / MCPサーバー設定ローダー
Responsibilities: Load and validate each configured MCP server entry,
requiring a name, a mode of `managed` or `external`, and mode-specific
connection data: for `managed`, a `launchCommand` template containing a
literal `{port}` placeholder (the manager substitutes the chosen free port
before spawning the process), an `endpointTemplate` containing the same
`{port}` placeholder (e.g. `http://127.0.0.1:{port}`) used to form the
usable client endpoint, and a `healthCheckPath` (e.g. `/health`) appended to
the substituted endpoint whose request must return HTTP 200 for the server
to be considered healthy; for `external`, an endpoint URL; fail
configuration loading with a message naming the first missing required
field (including a `launchCommand`/`endpointTemplate` missing its `{port}`
placeholder, or a managed entry missing `healthCheckPath`).
Interfaces: loadMcpConfig(configPath) -> McpServerConfig[] | raises
McpConfigError(missingField); McpServerConfig for managed mode includes
`launchCommand`, `endpointTemplate`, and `healthCheckPath`, all consumed by
DES-AISCI-012.
Constraints: Validation must run fully before any server is started or
connected to; validation must reject a managed entry whose `launchCommand`
or `endpointTemplate` does not contain the literal `{port}` placeholder.
Requirements: REQ-AISCI-016
ADRs: ADR-0083
Depends-On: none

## DES-AISCI-012: Managed MCP process manager / 管理対象MCPプロセス管理
Responsibilities: Maintain a session-scoped registry of managed-server
runtimes keyed by configured server name; for a `managed`-mode MCP server
entry with no running runtime registered under its name, choose a free
127.0.0.1 port, substitute it into the entry's `launchCommand` and
`endpointTemplate` placeholders, start the server process on demand on
first use via the substituted launch command, poll
`<substitutedEndpoint><healthCheckPath>` until it returns HTTP 200 within a
configured startup timeout (raising MCPUnavailableError via DES-AISCI-014
and deregistering any partially started state on timeout), register that
runtime under the entry's server name, keep it available for the remainder
of the session, and expose per-name status/stop operations — mirroring
ai-data-scientist's DES-AIDS-025 Jupyter MCP runtime manager pattern.
Interfaces: ensureManagedServer(entry, timeoutMs) -> RuntimeInfo{pid, port,
endpoint}; status(serverName) -> RuntimeInfo | None; stop(serverName) ->
None.
Constraints: Must not start a second process for a server name whose
process is already registered and running in the same session; must bind
only to 127.0.0.1; must not mark a runtime healthy/reusable until its
health check returns HTTP 200; `stop(serverName)` must terminate only the
process registered under that name.
Requirements: REQ-AISCI-017
ADRs: ADR-0084
Depends-On: DES-AISCI-011, DES-AISCI-014

## DES-AISCI-013: External MCP connector / 外部MCPコネクタ
Responsibilities: For an `external`-mode MCP server entry, connect to the
pre-supplied endpoint URL without starting or stopping any process.
Interfaces: connectExternalServer(entry) -> McpClient.
Constraints: Must never spawn a process for an external-mode entry.
Requirements: REQ-AISCI-018
ADRs: ADR-0085
Depends-On: DES-AISCI-011

## DES-AISCI-014: MCP unavailability classifier / MCP接続断分類器
Responsibilities: Given a server name, the requesting phase, and a
connection failure, construct a classified `MCPUnavailableError{serverName,
phase}` for the caller (DES-AISCI-010 or DES-AISCI-012) to raise/report,
naming both the unreachable server and the requesting phase instead of
silently skipping the request or allowing a result with no recorded
evidence.
Interfaces: classifyMcpFailure(serverName, phase, error) ->
MCPUnavailableError{serverName, phase}. This is a pure, side-effect-free
formatter; it does not itself call any MCP server or gateway.
Constraints: Must never allow a phase to record completion evidence derived
from a failed MCP call; must not depend on DES-AISCI-010 (callers depend on
this component, not the reverse, to avoid a dependency cycle).
Requirements: REQ-AISCI-019
ADRs: ADR-0086
Depends-On: none

## DES-AISCI-015: Phase-handler manifest and sibling-skill registry verifier / フェーズハンドラ一覧とスキルレジストリ検証
Responsibilities: Declare, for each of the eight phases, one importable
`src/ai_scientist` module-function entry (e.g. research-planning's own
module, DES-AISCI-005 for data-analysis, DES-AISCI-006 composed with
DES-AISCI-007/DES-AISCI-018 for manuscript-writing, DES-AISCI-008 for
peer-review, DES-AISCI-009 for presentation), each entry further declaring
zero or more exact pinned sibling-skill identifier+version dependencies
that the module function invokes internally: zero dependencies for
research-planning, literature-review, experimental-design, data-analysis
(DES-AISCI-005 calls ai-data-scientist's own in-repo `ai_data_scientist`
Python package directly — versioned with this repository, not a
separately-installed Agent Skill — so it declares no registry-pinned skill
dependency), and reproducibility-check; exactly one dependency for
manuscript-writing (tech-writer) and presentation (presentation-planner);
and exactly two dependencies for peer-review only, keyed by manuscript
language `ja` (japanese-prose) and `en` (tech-writer); at startup, verify
every declared module function is importable and every declared
sibling-skill dependency's identifier+version is discoverable in the
repository-declared skill registry (this repository's own
`.github/skills/*/SKILL.md` and `VENDORED.md` tree — not the host Copilot
CLI's live installed-skill registry, which this component does not
query), failing startup with a named missing entry if not.
Interfaces: loadPhaseManifest(path) -> PhaseManifest{[phase: string]:
HandlerEntry} where HandlerEntry = {modulePath: string, functionName:
string, skillDependencies: SkillDependency[] | {ja: SkillDependency, en:
SkillDependency}} and SkillDependency = {skillId: string, version: string}.
The loader rejects an entry missing modulePath/functionName, a
`{ja, en}`-shaped skillDependencies value on any phase other than
peer-review, and a peer-review entry whose skillDependencies is not
`{ja, en}`-shaped.
verifyManifestAgainstRegistry(manifest, registry) -> void | raises
ManifestVerificationError(missingIdentifier).
Constraints: Verification must run once at startup, before any phase
dispatch, must attempt to import every declared module function, and must
check both the `ja` and `en` entries of peer-review's skillDependencies.
Requirements: REQ-AISCI-023
ADRs: ADR-0087
Depends-On: none

## DES-AISCI-016: Evidence registry / 証跡レジストリ
Responsibilities: Provide the single durable store every phase handler
(DES-AISCI-005, DES-AISCI-006, DES-AISCI-008, DES-AISCI-009, and any
`src/ai_scientist` module handler) writes through to record an evidence
artifact's project, phase, creation timestamp, and artifact path/kind,
under the project's workspace root; expose a phase-scoped query used by
DES-AISCI-017 to check completion eligibility.
Interfaces: record_evidence(handle, phase, artifactPath, artifactKind,
timestamp) -> EvidenceRecord; query_evidence(handle, phase) ->
EvidenceRecord[].
Constraints: Writes must be atomic (write-temp-then-rename or an
equivalent single-writer discipline, reusing ai-data-scientist's
single-writer pattern) so a crash mid-write cannot corrupt the registry;
every phase handler must call `record_evidence` for its own produced
artifact(s) before reporting the phase's work as done.
Requirements: REQ-AISCI-020
ADRs: ADR-0088
Depends-On: DES-AISCI-002

## DES-AISCI-017: Evidence-gated phase completion / 証跡によるフェーズ完了判定
Responsibilities: Determine whether a phase is eligible to be marked
complete, for DES-AISCI-003.mark_phase_complete to consult before
persisting a transition: eligible only if
`DES-AISCI-016.query_evidence(handle, phase)` returns at least one record
identifying that project, that exact phase, and a creation timestamp.
Interfaces: validateCompletionEvidence(handle, phase) -> bool; called by
DES-AISCI-003.mark_phase_complete before persisting the transition (caller
depends on this component, not the reverse, to avoid a dependency cycle).
Constraints: An artifact tagged for a different phase must not satisfy this
check; zero artifacts must not satisfy this check.
Requirements: REQ-AISCI-020
ADRs: ADR-0089
Depends-On: DES-AISCI-016

## DES-AISCI-018: Manuscript format configuration and LaTeX renderer / 原稿形式設定とLaTeXレンダラー
Responsibilities: Read the project's configured manuscript format
(Markdown, default, or LaTeX); when LaTeX is configured, render the final
.tex manuscript file using ai-scientist's own LaTeX template renderer
applied to tech-writer's completed Markdown output (DES-AISCI-006), since
tech-writer produces Markdown only; when unconfigured or Markdown is
configured, the final manuscript file is tech-writer's own Markdown output
unchanged.
Interfaces: renderManuscript(manuscriptArtifact, configuredFormat) ->
FinalManuscript{path, format}; renderLatex(markdownArtifact) ->
LatexManuscript{path} used only when configuredFormat == "latex".
Constraints: The LaTeX renderer must preserve tech-writer's section content
(heading and paragraph text, and their relative order: no section or
paragraph dropped or reordered); it must never be invoked with Markdown
configured. This guarantee is scoped to section/paragraph-level content;
it does not cover line-level whitespace (leading/trailing spaces,
intentional indentation, or blank lines at the document boundary), which
the renderer may normalize during LaTeX escaping/formatting.
Requirements: REQ-AISCI-021, REQ-AISCI-022
ADRs: ADR-0090
Depends-On: DES-AISCI-006

## DES-AISCI-019: TDD verification gate / TDD検証ゲート
Responsibilities: Require the configured test suite covering every
component above, including an integration test exercising the real
ai-data-scientist delegation boundary (DES-AISCI-005) against that
feature's own REQ-AIDS-002/003 behaviors, and at least one passing
`@verifies`-linked test for every REQ-AISCI requirement ID including a
REQ-AISCI-025 packaging test that asserts both the exact `package.json`
entries and the `npm pack --dry-run --json` packed-artifact contents
defined by DES-AISCI-020, to pass with zero failures and zero unapproved
skipped tests before any implementation change is considered complete.
Interfaces: runConfiguredTestSuite() -> TestRunResult consumed by CI/local
workflow gating.
Constraints: Zero failing and zero unapproved skipped tests; this gate does
not itself certify correctness beyond what the executed tests check.
Requirements: REQ-AISCI-024
ADRs: ADR-0091
Depends-On: DES-AISCI-005, DES-AISCI-020

## DES-AISCI-020: npm skill-package completeness guard / npmスキル同梱完全性ガード
Responsibilities: Preserve parity between the npm bootstrap package's
shipped ai-scientist skill payload and its importable Python sources by
asserting that `package.json` `files` contains both exact entries
`.github/skills/ai-scientist` and `src/ai_scientist/**/*.py`, and by
proving with an `npm pack --dry-run --json` listing that the packed
artifact contains `.github/skills/ai-scientist/SKILL.md`,
`.github/skills/ai-scientist/manifest.json`, and every current repository
file matching `src/ai_scientist/**/*.py`.
Interfaces: loadPackageManifest(path="package.json") -> PackageManifest;
listPackedFiles() -> set[str] from `npm pack --dry-run --json`;
assertAiScientistPackagingParity(packageManifest, packedFiles) -> None.
Constraints: The authoritative packaged-artifact proof is the dry-run pack
listing, not only static inspection of `package.json`. This guard covers
npm distribution completeness only; Python package discovery continues to
rely on setuptools auto-discovery from `pyproject.toml` `where = ["src"]`,
so no explicit static Python package list is required unless that project
configuration changes in the future.
Requirements: REQ-AISCI-025
ADRs: ADR-0087, ADR-0091
Depends-On: DES-AISCI-015
