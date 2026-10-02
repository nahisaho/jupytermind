---
name: ai-scientist
description: "Use when a user asks, in Japanese or English, to guide a single research project through planning, literature review, experimental design, data analysis, manuscript writing, peer review, reproducibility checks, and presentation. 研究プロジェクトを研究計画から発表まで単一セッションで進める際に使用。"
---
# AI Scientist / AIサイエンティスト

Respond in the user's input language (日本語 / English) for every user-facing
message. Guide one project through eight fixed phases in order:
research-planning, literature-review, experimental-design, data-analysis,
manuscript-writing, peer-review, reproducibility-check, and presentation.

## Workflow / 手順
1. **Resolve the shared project handle** — call
   `ai_scientist.project_handle.resolve_research_project(name)` so workspace
   paths reuse `ai_data_scientist.project_manager.resolve_project`'s validated,
   stable root contract.
2. **Check language and phase state** — call
   `ai_scientist.language.detect_language(instruction)` and
   `ai_scientist.phase_state.load_phase_state(handle)`; when the requested phase
   differs from the active one, enforce `ai_scientist.phase_gate.check_gate(...)`
   before dispatch.
3. **Run the phase handler declared in the manifest** — load
   `.github/skills/ai-scientist/manifest.json` with
   `ai_scientist.manifest.load_phase_manifest()` and dispatch only to the
   declared module function for that phase.
4. **Delegate specialized phases instead of duplicating logic**:
   - `data-analysis` → `ai_scientist.data_analysis.delegate_data_analysis(...)`
     which reuses `ai_data_scientist.project_manager.resolve_project` /
     `ensure_notebook` and `ai_data_scientist.mcp_gateway.run_and_record(...)`.
   - `manuscript-writing` → `ai_scientist.manuscript.write_manuscript(...)`,
     which invokes the pinned `tech-writer` sibling skill through a provided
     `SkillInvoker`, records manuscript language metadata, and optionally
     renders LaTeX from the returned Markdown.
   - `peer-review` → `ai_scientist.peer_review.review_manuscript(...)`, which
     routes to `japanese-prose` for `ja` manuscripts or `tech-writer` for `en`
     manuscripts using the persisted manuscript metadata.
   - `presentation` → `ai_scientist.presentation.build_presentation(...)`,
     which invokes the pinned `presentation-planner` sibling skill.
5. **Route literature or domain-tool lookups through MCP only** — use
   `ai_scientist.mcp_gateway.McpGateway.call_tool(...)`; managed MCP servers are
   started on demand via `ai_scientist.mcp_managed.ensure_managed_server(...)`,
   and external endpoints are connected via
   `ai_scientist.mcp_external.connect_external_server(...)`.
6. **Record evidence before completion** — every phase artifact must be written
   through `ai_scientist.evidence_registry.record_evidence(...)`; only then may
   `ai_scientist.phase_state.mark_phase_complete(...)` advance the lifecycle.

## Constraints / 制約
- Do not implement manuscript prose, peer-review prose, or presentation
  structuring inside this skill's Python code; use the pinned sibling skills
  declared in the manifest.
- Do not make direct domain-tool network calls from phase handlers; use the MCP
  gateway/client abstraction.
- The default Python-side `DefaultSkillInvoker` intentionally raises
  `NotImplementedError`: the live Copilot runtime must supply the real sibling
  skill invocation mechanism when executing this skill outside the test suite.

## Source layout / 実装
- `src/ai_scientist/orchestrator.py`
- `src/ai_scientist/project_handle.py`
- `src/ai_scientist/phase_state.py`
- `src/ai_scientist/phase_gate.py`
- `src/ai_scientist/evidence_registry.py`
- `src/ai_scientist/data_analysis.py`
- `src/ai_scientist/manuscript.py`
- `src/ai_scientist/peer_review.py`
- `src/ai_scientist/presentation.py`
- `src/ai_scientist/mcp_*.py`
- `.github/skills/ai-scientist/manifest.json`
