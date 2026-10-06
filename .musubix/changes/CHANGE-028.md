# CHANGE-028: Document the jupyter-mcp-server cache-coherency ordering constraint

## Summary

Fixes GitHub Issue #75. `ai_data_scientist.insight_engine.record_insight` /
`ai_data_scientist.visualization.record_chart` write directly to the notebook
file on disk, bypassing `jupyter-mcp-server`. When a direct-write call is
immediately followed by an MCP-mediated `insert_execute_code_cell` call, the
MCP server's in-memory cached notebook model can be stale relative to the
file it just missed, causing the next `insert_execute_code_cell` call to
report success without actually persisting the new cell (silent data loss),
and a caller that retries by polling cell count can end up inserting a
genuine duplicate cell once the cache catches up.

## Classification

Documentation-only change, per the issue's own suggested fix (c): "the skill
should document this ordering constraint explicitly so callers are not
required to discover it empirically." The underlying root cause is in the
external `jupyter-mcp-server` project's caching implementation, which is out
of scope for this repository to fix directly (suggested fixes (a) and (b) in
the issue both require changes on the `jupyter-mcp-server` side). No
requirement ID is added or changed; no implementation code changes. TDD is
not applicable, recorded per the `sdd-change` skill's documentation-only
exception.

## Scope

- `.github/skills/ai-data-scientist/SKILL.md`: step 3 (MCP-mediated
  execution) gains an explicit "Known ordering constraint" note describing
  the failure mode and the required workaround — complete all
  `insert_execute_code_cell` calls for a section of work before calling
  `record_insight`/`record_chart`, rather than interleaving them; if an
  insight must be recorded between two dependent live-execution steps,
  verify the on-disk cell count after the next `insert_execute_code_cell`
  call and retry once (not in a tight poll loop) if it did not increase.

## Requirements

No requirement IDs are added, changed, or reinterpreted by this change.

## Out of scope

- Any change to `jupyter-mcp-server` itself (separate project/repository).
- Any change to `insight_engine.py`/`visualization.py` write mechanics.
- A future fix to route `record_insight`/`record_chart` through
  jupyter-mcp-server, or to make `insert_execute_code_cell` detect/reject a
  stale cache, would require separate design and implementation work,
  potentially involving changes to jupyter-mcp-server itself, and is not
  part of this change.
