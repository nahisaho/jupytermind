---
schemaVersion: 1
feature: ai-scientist
---
# Requirements / 要求 (MVP)

Feature: GitHub Copilot Agent Skill "AI Scientist" that guides a user through
a single continuous research-project session covering eight lifecycle
phases — research planning, literature review, experimental design, data
analysis, manuscript writing, peer review, reproducibility check, and
presentation — in Japanese or English. The skill is a single SKILL.md whose
heavy logic (phase-state tracking, gate evaluation, artifact generation)
lives in versioned Python modules (`src/ai_scientist`), mirroring the
`ai-data-scientist` skill's architecture so phase code never needs to be
re-read into the agent context. Every workspace and artifact path is derived
from the validated project handle's stable root (REQ-AIDS-044), never from a
literal relative path, so phase artifacts stay consistent across a kernel or
process working-directory change. Data-analysis and three other phases
delegate rather than duplicating logic: data-analysis calls
`ai-data-scientist`'s own in-repository `ai_data_scientist.project_manager`
Python functions directly (this project's own sibling package, versioned
with this repository — not a separately-installed Agent Skill requiring
registry pinning — reusing its project-identifier validation and
workspace-root contract, REQ-AIDS-028/044); manuscript-writing
delegates to kotonoha's `tech-writer` skill, which owns Markdown document
structure only (it has no Markdown/LaTeX format parameter), so ai-scientist's
own renderer performs any Markdown-to-LaTeX conversion after tech-writer
completes its Markdown output; peer-review delegates to kotonoha's
`japanese-prose` skill in its `review` mode for a Japanese manuscript, or to
kotonoha's `tech-writer` skill in its `review` mode for an English
manuscript, as a separate invocation whose findings are recorded as
peer-review evidence distinct from manuscript-writing evidence; and
presentation delegates to kotonoha's `presentation-planner` skill. Literature
search and other domain-tool access go through Model Context Protocol (MCP)
servers (e.g. ToolUniverse, or a custom MCP server), which may be either
launched/managed by this skill or already running externally.

## REQ-AISCI-001: Bilingual instruction support / 日英両対応の指示理解
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user submits a research instruction in Japanese or English, the system shall respond in the same language as that instruction.
Acceptance: A test feeds 10 paired Japanese/English prompts across different phases and asserts the assistant response language matches the input language in all 10 cases.

## REQ-AISCI-002: Shared project identifier validation / 共有プロジェクト識別子検証
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall validate every project identifier using the ai-data-scientist feature's existing project-resolution contract (REQ-AIDS-028 slug rules, REQ-AIDS-044 stable workspace root) instead of an independent validation rule.
Acceptance: A test supplies a project name with path traversal segments or disallowed characters and asserts it is rejected via the same error path as ai-data-scientist's resolve_project, with no file system write performed.

## REQ-AISCI-003: Project-scoped research workspace creation / プロジェクト単位の研究ワークスペース作成
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user starts research work for a validated project with no existing workspace, the system shall create phase subdirectories (planning/, literature/, design/, manuscript/, review/, reproducibility/, presentation/) under the validated project handle's stable workspace root before recording any phase artifact, leaving the data-analysis phase's evidence in the ai-data-scientist notebook path (<root>/notebooks/<project_name>.ipynb) rather than a separate subdirectory.
Acceptance: Starting research on a new project name creates all seven listed subdirectories exactly once under the resolved workspace root, starting again on the same project reuses the existing workspace instead of recreating it, and a test that changes the process working directory between the two invocations asserts both resolve to the same root.
Formal: {"kind":"conditional","condition":"workspace_missing","consequence":"create_workspace"}

## REQ-AISCI-004: Eight-phase lifecycle state tracking / 8フェーズのライフサイクル状態追跡
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall track, per project, which one of the eight phases (research-planning, literature-review, experimental-design, data-analysis, manuscript-writing, peer-review, reproducibility-check, presentation) is active and which are completed, persisted across separate CLI invocations within the same project, starting a newly created project with research-planning active and all other phases incomplete.
Acceptance: A test completes phases 1-3 in one invocation, starts a new process, queries phase state, and asserts phases 1-3 report completed and phase 4 (data-analysis) reports active; a second test queries a brand-new project and asserts research-planning is active with all others incomplete.

## REQ-AISCI-005: Automatic phase activation on completion / 完了時の自動フェーズ遷移
Priority: must
Type: functional
Pattern: event-driven
Statement: When the currently active phase is marked complete and no override is in effect, the system shall activate the next phase in the fixed eight-phase order.
Acceptance: A test marks research-planning complete and asserts literature-review becomes active; a test marks the final phase (presentation) complete and asserts no further phase becomes active.

## REQ-AISCI-006: Sequential phase-gate enforcement / 順序付きフェーズゲート
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user requests work for a phase other than the project's current active phase, the system shall block execution and report which prior phase is incomplete, unless the user supplies an explicit override.
Acceptance: A test requests experimental-design work while literature-review is incomplete and asserts the system blocks with an explicit message naming literature-review.
Formal: {"kind":"conditional","condition":"requested_phase_not_active_and_no_override","consequence":"block_with_named_phase"}

## REQ-AISCI-007: Override-gated out-of-order execution scoped to a single request / 明示オーバーライドによる単発順不同実行
Priority: must
Type: functional
Pattern: event-driven
Statement: When a user supplies an explicit override for a phase other than the current active phase, the system shall execute that single request without changing the active phase, without marking the requested phase complete, and without changing any predecessor phase's completion status, recording the override reason and the named incomplete predecessor phases.
Acceptance: A test overrides into experimental-design while literature-review is incomplete, asserts the experimental-design request executes, asserts an override record naming literature-review is stored, asserts the active phase remains literature-review afterward, and asserts a subsequent non-override request for literature-review is still permitted (not blocked).

## REQ-AISCI-008: Data-analysis phase delegation to ai-data-scientist's package / データ分析フェーズのai-data-scientistパッケージ委譲
Priority: must
Type: functional
Pattern: event-driven
Statement: When the active phase is data-analysis, the system shall call the ai-data-scientist feature's own in-repository `ai_data_scientist.project_manager` Python functions (`resolve_project`, `ensure_notebook`) with the validated project handle's project name, forwarding execution to that feature's documented workflow (REQ-AIDS-002/003 notebook creation and Jupyter MCP execution) instead of performing any independent analysis logic or a separately-installed Agent Skill invocation.
Acceptance: A test starts the data-analysis phase for a project and asserts `ai_data_scientist.project_manager.resolve_project`/`ensure_notebook` are invoked with the same project name, the resulting notebook path equals that handle's own notebook_path (<validated stable root>/notebooks/<project_name>.ipynb, not a hard-coded projects/ prefix), and no parallel ai-scientist-only analysis code path executes.

## REQ-AISCI-009: Manuscript-writing phase delegation to tech-writer / 論文執筆フェーズのtech-writer委譲
Priority: must
Type: functional
Pattern: event-driven
Statement: When the active phase is manuscript-writing, the system shall invoke kotonoha's tech-writer skill with the validated project handle and the project's recorded research evidence to produce a Markdown manuscript, instead of generating manuscript prose with independent ai-scientist logic.
Acceptance: A test starts the manuscript-writing phase and asserts the tech-writer skill is invoked with the project's evidence manifest, asserts a Markdown manuscript artifact is produced, and asserts no independent ai-scientist prose-generation code path executes.

## REQ-AISCI-010: Manuscript language metadata persistence / 原稿言語メタデータの永続化
Priority: must
Type: functional
Pattern: event-driven
Statement: When the manuscript-writing phase's tech-writer delegation (REQ-AISCI-009) completes, the system shall persist the manuscript's language as `ja` or `en`, using the same language detection as REQ-AISCI-001 applied to the instruction that produced the manuscript, as evidence metadata attached to the manuscript artifact.
Acceptance: A test completes manuscript-writing from a Japanese instruction and asserts the persisted manuscript language metadata equals `ja`; a second test with an English instruction asserts it equals `en`.

## REQ-AISCI-011: Peer-review phase delegation for a Japanese manuscript / 日本語原稿の査読フェーズ委譲
Priority: must
Type: functional
Pattern: event-driven
Statement: When the active phase is peer-review and the manuscript's persisted language metadata is `ja`, the system shall invoke kotonoha's japanese-prose skill in its review mode against that manuscript file as a separate invocation from manuscript-writing.
Acceptance: A test starts the peer-review phase for a manuscript with `ja` metadata and asserts japanese-prose is invoked in review mode with that manuscript's file path, and asserts its findings are recorded as peer-review phase evidence distinct from manuscript-writing evidence.

## REQ-AISCI-012: Peer-review phase delegation for an English manuscript / 英語原稿の査読フェーズ委譲
Priority: must
Type: functional
Pattern: event-driven
Statement: When the active phase is peer-review and the manuscript's persisted language metadata is `en`, the system shall invoke kotonoha's tech-writer skill in its review mode against that manuscript file as a separate invocation from manuscript-writing.
Acceptance: A test starts the peer-review phase for a manuscript with `en` metadata and asserts tech-writer is invoked in review mode with that manuscript's file path, and asserts its findings are recorded as peer-review phase evidence distinct from manuscript-writing evidence.

## REQ-AISCI-013: Peer-review blocked for missing or unsupported manuscript language / 言語メタデータ欠落・非対応時の査読ブロック
Priority: must
Type: functional
Pattern: unwanted-behavior
Statement: If the active phase is peer-review and the manuscript has no persisted language metadata or a value other than `ja` or `en`, then the system shall block the peer-review request and report that supported manuscript language metadata is required before peer-review can proceed.
Acceptance: A test starts peer-review for a manuscript with missing language metadata and asserts the request is blocked with a message requiring language metadata; a second test with an unsupported value (e.g. `fr`) asserts the same blocking behavior.

## REQ-AISCI-014: Presentation phase delegation to presentation-planner / 発表フェーズのpresentation-planner委譲
Priority: must
Type: functional
Pattern: event-driven
Statement: When the active phase is presentation, the system shall invoke kotonoha's presentation-planner skill with the project's manuscript and recorded research evidence, instead of generating a presentation structure with independent ai-scientist logic.
Acceptance: A test starts the presentation phase and asserts the presentation-planner skill is invoked with the manuscript path and evidence manifest, and asserts the resulting presentation brief/outline is recorded as presentation phase evidence.

## REQ-AISCI-015: MCP-backed literature and domain-tool search / MCP経由の文献・専門ツール検索
Priority: must
Type: functional
Pattern: event-driven
Statement: When the literature-review phase or another phase requires external domain-tool access (e.g. literature search), the system shall route the request through the project's configured MCP client rather than issuing any direct outbound network call from ai-scientist code.
Acceptance: A test instruments both the configured MCP client and the process's outbound network layer during a literature-review request and asserts every external domain-tool lookup is observed on the MCP client and zero direct network calls originate from ai-scientist modules.

## REQ-AISCI-016: MCP server configuration schema / MCPサーバー設定スキーマ
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall require each configured MCP server entry to declare a name and a mode of either managed or external, requiring for managed mode a launch-command template and an endpoint-URL template that each contain a literal port placeholder plus a health-check path, and requiring for external mode an endpoint URL.
Acceptance: A test loads a configuration missing the mode field, missing the launch-command template for a managed entry, missing the port placeholder in a managed entry's launch-command or endpoint-URL template, missing the health-check path for a managed entry, or missing the endpoint URL for an external entry, and asserts configuration loading fails in each case with a message naming the missing or malformed field.

## REQ-AISCI-017: Managed MCP server on-demand startup / 管理対象MCPサーバーのオンデマンド起動
Priority: must
Type: functional
Pattern: event-driven
Statement: When the configured MCP server entry specifies managed mode, the system shall start the MCP server on demand on first use and keep that same process available for the remainder of the session.
Acceptance: A test with a managed-mode config asserts a server process is started on first use and the same process (same PID) is reused for subsequent calls within the same session.

## REQ-AISCI-018: External MCP server connection without lifecycle control / 外部MCPサーバーへの非管理接続
Priority: must
Type: functional
Pattern: event-driven
Statement: When the configured MCP server entry specifies external mode, the system shall connect to the pre-supplied endpoint without starting or stopping any process.
Acceptance: A test with an external-mode config asserts no process is spawned and the client connects to the supplied URL.

## REQ-AISCI-019: MCP unavailability handling / MCP接続断時の処理
Priority: must
Type: functional
Pattern: event-driven
Statement: When a configured MCP server is unreachable at the time a phase requests a tool call, the system shall report the unreachable server name and the affected phase instead of silently skipping the request or producing a result without evidence.
Acceptance: A test disables the MCP endpoint, requests a literature-review tool call, and asserts the response names the unreachable server and the literature-review phase, with no fabricated result recorded.

## REQ-AISCI-020: Phase-attributed evidence required for completion / フェーズ属性付き証跡によるフェーズ完了
Priority: must
Type: functional
Pattern: ubiquitous
Statement: The system shall refuse to mark any phase complete unless at least one evidence artifact recorded in the project workspace carries metadata identifying that project, that phase, and a creation timestamp.
Acceptance: A test attempts to mark a phase complete with zero recorded artifacts and asserts the system rejects the transition; a second test attempts completion using an artifact tagged for a different phase and asserts rejection; a third test records one correctly tagged artifact and asserts the transition succeeds.

## REQ-AISCI-021: Configurable manuscript output format / 原稿出力形式の設定可否
Priority: must
Type: functional
Pattern: event-driven
Statement: When the manuscript-writing phase completes, the system shall produce a final manuscript file in the project-configured format (Markdown or LaTeX), defaulting to Markdown when no format is configured.
Acceptance: A test configures LaTeX and asserts the final manuscript file has a .tex extension; a second test with no configuration asserts the final manuscript file has a .md extension equal to tech-writer's own output.

## REQ-AISCI-022: LaTeX rendering derived from tech-writer's Markdown output / tech-writer成果物からのLaTeXレンダリング
Priority: must
Type: functional
Pattern: event-driven
Statement: When the project-configured manuscript format is LaTeX, the system shall render the final .tex manuscript file using ai-scientist's own LaTeX template renderer applied to tech-writer's completed Markdown output, since tech-writer produces Markdown only.
Acceptance: A test configures LaTeX, runs the manuscript-writing phase, and asserts the final .tex file has valid LaTeX document structure whose section content matches tech-writer's Markdown section output.

## REQ-AISCI-023: Skill packaging with a verifiable phase-handler manifest / 検証可能なフェーズハンドラ一覧を伴うスキル提供
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall package the ai-scientist workflow as a single .github/skills/ai-scientist/SKILL.md file accompanied by a machine-readable manifest declaring, for each of the eight phases, one importable src/ai_scientist module function together with zero or more exact pinned sibling-skill identifier-and-version dependencies that function invokes, declaring two such dependencies keyed by manuscript language (`ja`, `en`) instead of one for the peer-review phase only.
Acceptance: A test loads the manifest, asserts all eight phases are present with an importable module function and asserts each is callable, asserts every declared sibling-skill dependency names an identifier and exact version string discoverable in the repository-declared skill registry (this repository's own `.github/skills/*/SKILL.md` and `VENDORED.md` tree, not the host Copilot CLI's live installed-skill registry) at startup, and asserts the peer-review entry declares both a `ja` and an `en` dependency with their own discoverable identifier and exact version; the loader shall fail startup if any declared module function is not importable or any declared identifier/version is not found in the registry.

## REQ-AISCI-024: Test-driven development coverage including cross-feature delegation / 委譲契約を含むTDD網羅
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: The system shall provide an automated test for every REQ-AISCI requirement's acceptance criteria, including an integration test that exercises the real ai-data-scientist delegation boundary (REQ-AISCI-008) against that feature's own notebook-creation and execution-routing requirements (REQ-AIDS-002/003), runnable via the project's configured test command.
Acceptance: Running the configured test command executes at least one passing test linked (via @verifies) to each REQ-AISCI requirement ID, including a passing integration test that asserts REQ-AIDS-002 and REQ-AIDS-003 behaviors hold when invoked through the ai-scientist data-analysis phase, with no skipped tests.
