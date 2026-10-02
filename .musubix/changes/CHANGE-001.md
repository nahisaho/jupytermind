# CHANGE-001: Add ai-scientist Agent Skill

## Summary

Introduce a new `ai-scientist` Agent Skill that orchestrates an 8-phase
research lifecycle (research-planning, literature-review,
experimental-design, data-analysis, manuscript-writing, peer-review,
reproducibility-check, presentation) within a single continuous session,
delegating to sibling skills (`ai-data-scientist`, `tech-writer`,
`japanese-prose`, `presentation-planner`) and to configurable MCP servers
(e.g. ToolUniverse) for literature/domain-tool search.

## Scope

- New feature slug: `ai-scientist`.
- New requirements: REQ-AISCI-001 through REQ-AISCI-024.
- No existing feature's requirements are modified.

## Affected Requirements

REQ-AISCI-001, REQ-AISCI-002, REQ-AISCI-003, REQ-AISCI-004, REQ-AISCI-005,
REQ-AISCI-006, REQ-AISCI-007, REQ-AISCI-008, REQ-AISCI-009, REQ-AISCI-010,
REQ-AISCI-011, REQ-AISCI-012, REQ-AISCI-013, REQ-AISCI-014, REQ-AISCI-015,
REQ-AISCI-016, REQ-AISCI-017, REQ-AISCI-018, REQ-AISCI-019, REQ-AISCI-020,
REQ-AISCI-021, REQ-AISCI-022, REQ-AISCI-023, REQ-AISCI-024.

## Rationale

A single-skill-plus-modules architecture (reusing the `ai-data-scientist`
pattern) was chosen over a large set of fine-grained sub-skills, to reduce
context overhead and reuse the existing stable-workspace-root and
project-handle validation contracts already proven in `ai-data-scientist`.
