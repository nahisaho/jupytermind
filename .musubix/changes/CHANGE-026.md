# CHANGE-026: Cross-process stable project root for multi-kernel MCP sessions (fixes #72)

## Summary

Fixes GitHub issue #72, a regression of #15/REQ-AIDS-044: in a real
multi-hour `ai-data-scientist` skill session over Jupyter MCP, the
`projects/<slug>/notebooks/projects/<slug>` nested-directory bug
reappeared twice, requiring manual detection (`List Files`) and ad-hoc
cleanup. REQ-AIDS-044's existing fix (`_IMPORT_TIME_CWD`, captured once
per Python process at module import) only stabilizes
`resolve_project`'s default root *within a single already-initialized
process*. A real Jupyter MCP session routes different tool calls
(`Use Notebook` vs. ad-hoc `Execute Code`) through more than one
kernel/process, each of which may freshly import
`ai_data_scientist.project_manager` with its own, different,
possibly-already-drifted working directory, silently recreating the
nested tree.

This change extends the stability guarantee to span every
kernel/process sharing the same logical session, by deriving the
default projects root from on-disk directory structure (an ancestor
directory that already contains a `projects/` child) instead of relying
solely on a single process's own import-time cwd snapshot. The
environment-variable override remains the first, authoritative source
of truth when a caller wants to pin it explicitly.

## Scope

- Feature: `ai-data-scientist`
- Change type: defect correction (regression of #15 / REQ-AIDS-044)
- `.musubix/features/ai-data-scientist/requirements.md` — new
  REQ-AIDS-053 extending REQ-AIDS-044's stability guarantee across
  processes/kernels sharing a session.
- `.musubix/features/ai-data-scientist/design.md` — new DES-AIDS-077;
  new ADR-0111 recording the directory-anchored discovery strategy
  versus the rejected marker-file and mandatory-env-var alternatives.
- `src/ai_data_scientist/project_manager.py` — `_default_projects_root`
  gains an ancestor-directory search for an existing `projects/` sibling
  before falling back to the import-time-cwd default.
- `tests/test_project_manager.py` (or equivalent) — new regression test
  for the multi-process/fresh-cwd scenario.

## Affected Requirements

Requirements: REQ-AIDS-053

## Out of scope

- No change to REQ-AIDS-044 itself (its single-process guarantee and
  acceptance criteria are unchanged and still hold).
- No change to the Jupyter MCP server itself or to kernel lifecycle
  management.
