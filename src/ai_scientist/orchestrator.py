"""Top-level ai_scientist dispatch orchestration."""

from __future__ import annotations

import importlib
import inspect

from ai_scientist.language import detect_language
from ai_scientist.manifest import (
    load_phase_manifest,
    scan_repo_skill_registry,
    verify_manifest_against_registry,
)
from ai_scientist.mcp_gateway import McpGateway
from ai_scientist.phase_gate import check_gate
from ai_scientist.phase_state import active_phase
from ai_scientist.project_handle import resolve_research_project
from ai_scientist.skill_invocation import DefaultSkillInvoker

_PHASE_HINTS = (
    ("research-planning", ("research-planning", "research plan", "研究計画")),
    (
        "literature-review",
        ("literature-review", "literature review", "search the literature", "文献", "先行研究"),
    ),
    ("experimental-design", ("experimental-design", "experimental design", "実験設計")),
    ("data-analysis", ("data-analysis", "analyze", "analyse", "データ分析", "分析して")),
    ("manuscript-writing", ("manuscript-writing", "write the manuscript", "manuscript", "原稿")),
    ("peer-review", ("peer-review", "review the manuscript", "査読")),
    ("reproducibility-check", ("reproducibility-check", "reproducibility", "再現性")),
    ("presentation", ("presentation", "slides", "発表", "スライド")),
)


def _message(language: str, phase: str) -> str:
    if language == "ja":
        return f"{phase} フェーズを処理しました。"
    return f"Processed the {phase} phase."


def _gateway_for(mcp_client):
    if mcp_client is None:
        return None
    return McpGateway(clients={"default": mcp_client})


# @id CODE-AISCI-025
# @implements REQ-AISCI-001
# @design DES-AISCI-001
def _requested_phase_from_instruction(instruction: str) -> str | None:
    normalized = instruction.casefold()
    for phase, hints in _PHASE_HINTS:
        if any(hint in normalized or hint in instruction for hint in hints):
            return phase
    return None


# @id CODE-AISCI-026
# @implements REQ-AISCI-023
# @design DES-AISCI-015
def _dispatch_phase(
    phase: str,
    manifest: dict,
    handle,
    instruction: str,
    skill_invoker,
    mcp_client,
):
    entry = manifest.get(phase)
    if entry is None:
        raise ValueError(f"Unknown phase: {phase}")
    module = importlib.import_module(entry["modulePath"])
    handler = getattr(module, entry["functionName"])
    gateway = _gateway_for(mcp_client)
    available_args = {
        "handle": handle,
        "instruction": instruction,
        "invoker": skill_invoker,
        "mcp_client": mcp_client,
        "gateway": gateway,
        "server_name": "default" if gateway is not None else None,
    }
    signature = inspect.signature(handler)
    call_args = {
        name: value
        for name, value in available_args.items()
        if name in signature.parameters and value is not None
    }
    return handler(**call_args)


# @id CODE-AISCI-014
# @implements REQ-AISCI-001
# @design DES-AISCI-001
def dispatch(
    instruction: str,
    project_name: str,
    requested_phase: str | None = None,
    override_reason: str | None = None,
    projects_root=None,
    skill_invoker=None,
    mcp_client=None,
) -> dict:
    """Resolve the project, verify the manifest, gate phases, and dispatch."""
    language = detect_language(instruction)
    handle = resolve_research_project(project_name, projects_root=projects_root)
    manifest = load_phase_manifest()
    verify_manifest_against_registry(manifest, scan_repo_skill_registry())
    current_active = active_phase(handle)
    phase = requested_phase or _requested_phase_from_instruction(instruction) or current_active
    phase = phase or "research-planning"
    if phase != current_active:
        decision = check_gate(
            handle,
            phase,
            override={"reason": override_reason} if override_reason else None,
        )
        if not decision.allowed:
            return {"language": language, "message": decision.message, "phase": phase}
    result = _dispatch_phase(
        phase,
        manifest,
        handle,
        instruction,
        skill_invoker or DefaultSkillInvoker(),
        mcp_client,
    )
    return {
        "language": language,
        "message": _message(language, phase),
        "phase": phase,
        "result": result,
    }
