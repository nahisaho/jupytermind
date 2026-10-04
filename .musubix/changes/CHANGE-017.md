# CHANGE-017: SKILL.md に長時間セルの分割・完了確認・再開手順を追記する (#55)

## Summary

Issue #55 is a documentation-only correction to
`.github/skills/ai-data-scientist/SKILL.md`. The runtime already provides the
relevant lifecycle helpers (`get_run_status`, `wait_for_quiescence`) and
already documents cooperative cancellation in REQ-AIDS-051 / DES-AIDS-039, but
the skill lacked an explicit operator procedure for the direct-Jupyter-MCP
case where `insert_execute_code_cell`-style tools stop waiting for output
after roughly 120 seconds while the kernel may still be executing. This change
adds that missing procedure: split likely-long jobs into restartable chunks,
never treat a host-side timeout as proof of kernel completion, confirm
completion before sending another cell, abandon the timed-out kernel/session
when no real idle signal is available, and resume from durable checkpoints or
caches after interruption.

## Scope

- Existing feature context consulted: `ai-data-scientist`.
- Files changed:
  - `.github/skills/ai-data-scientist/SKILL.md`
  - `.musubix/changes/CHANGE-017.md`
- Out of scope:
  - Runtime behavior changes in `src/ai_data_scientist/*`
  - New lifecycle helpers or MCP kernel-state APIs
  - Requirement/design text changes unless inspection had shown a genuine
    normative gap (it did not)

## Affected Requirements

Requirements: none.

Reasoning: the issue is a missing usage procedure in SKILL.md, not a new or
changed product obligation. The inspected requirements already cover the
library-managed timeout/lifecycle behaviors that this operator guidance must
respect:

- `REQ-AIDS-031` / `REQ-AIDS-042` describe timeout behavior for the managed
  `execute_cell` / `run_and_record` path.
- `REQ-AIDS-051` requires the lifecycle API to expose `get_run_status` and
  `wait_for_quiescence`.
- `DES-AIDS-039` defines those lifecycle interfaces and explicitly notes that
  cancellation cannot interrupt a kernel cell already in flight.

No requirement acceptance criteria needed extension because the system already
implements the helpers and managed-path semantics; only the operator guidance
for the separate direct-Jupyter-MCP fallback was missing. The new text is
careful **not** to overclaim that lifecycle status alone proves post-timeout
kernel completion in that fallback path, and it does **not** treat durable
checkpoint/result-file existence as proof of cell completion either because a
long-running cell may write those artifacts mid-run. Instead, the guidance
treats such durable artifacts as resume markers, and treats real kernel-idle
observation (when available) plus lifecycle quiescence only in orchestrations
that genuinely keep those counters aligned with real kernel completion as the
valid completion checks before another cell is submitted. If the environment
cannot expose a trustworthy idle/quiescent signal after a timeout, the
guidance now tells the operator not to reuse that kernel and to resume from
durable checkpoints in a fresh verified-clean execution context.

## Design

Design: none.

Reasoning: this change does not alter responsibilities, interfaces, data
shapes, or architecture. It documents how to apply already-existing behavior
and helpers safely in the direct-MCP execution path.

## Implementation Plan

- [x] Inspect constitution, `ai-data-scientist` requirements/design, current
  `SKILL.md`, and `src/ai_data_scientist/lifecycle.py`.
- [x] Confirm that `get_run_status(run_id)` and
  `wait_for_quiescence(run_id, timeout_s=...)` are real in-repo helpers and
  avoid inventing any nonexistent completion-check API.
- [x] Update SKILL.md step 3 and step 11 to document:
  - host/tool timeout ≠ kernel completion,
  - chunking long work into restartable units,
  - mandatory completion confirmation before any next cell, and
  - resume-from-checkpoint/cache guidance after interruption.
- [x] Document that this is a documentation-only change; TDD red/green is
  intentionally omitted because no runtime or observable system behavior is
  changed.
- [x] Review the documentation artifacts with the closest available native
  review tooling in this session (`task` / `code-review`), because the
  requested native `rubber-duck` agent type is not exposed by the current
  tool schema; iterative review found three real lifecycle-accuracy / scope
  issues, all fixed, and the final re-review returned clean.
- [x] Run applicable musubix trace/gate/status commands and prepare release
  approval evidence.
- [ ] Obtain explicit human release approval for the exact prepared artifact
  manifest hash before commit/push.
- [ ] Commit and push `change-017-skill-docs-long-cell-guidance`.

## Validation / Evidence

- Inspected current `SKILL.md` in full.
- Confirmed there is no sibling `ai-data-scientist-ml` skill file carrying
  this procedure; the guidance belongs in the base `ai-data-scientist`
  skill because the issue concerns direct Jupyter MCP execution flow rather
  than ML-only explainability or evaluation APIs.
- Confirmed actual lifecycle helpers in
  `src/ai_data_scientist/lifecycle.py`:
  `register_run`, `mark_execution_start/end`, `mark_write_start/end`,
  `request_cancel`, `is_cancel_requested`, `mark_completed`, `mark_failed`,
  `get_run_status`, and `wait_for_quiescence`.
- Documentation review:
  - Iterative `task`/`code-review` passes caught three substantive issues:
    overclaiming lifecycle quiescence as proof of post-timeout kernel
    completion in the simple direct-tool fallback; omitting
    `locks_held == 0` from a lifecycle-based quiescence check; and
    overstating requirement coverage for the direct-tool fallback in the
    CHANGE rationale.
  - All three issues were fixed in SKILL.md and/or CHANGE-017.md.
  - Final re-review result: clean.
- Musubix command results:
  - `npx musubix3 trace impact REQ-AIDS-051 --json` returned the linked trace
    paths rooted in `REQ-AIDS-051` and `DES-AIDS-039`, which was the
    governing requirement/design chain inspected for this documentation
    update.
  - `npx musubix3 graph index --json` completed successfully.
  - `npx musubix3 graph impact src/ai_data_scientist/lifecycle.py --json`
    returned `src/ai_data_scientist/lifecycle.py` as the directly impacted
    code path inspected for completion-check helper behavior.
  - `npx musubix3 graph gate` passed.
  - `npx musubix3 trace build` completed, then `trace check --strict` failed
    only on pre-existing `ai-genomics-scientist` uncovered-trace warnings /
    coverage errors unrelated to CHANGE-017.
  - `npx musubix3 gate --changed --json` failed. Compared against a fresh
    full `gate --json` run on `main`, the only new CHANGE-017-specific
    diagnostic was `CHANGE_RECORD_MISSING` for this docs-only CHANGE because
    the current `change-record` CLI requires at least one `--requirement`.
    All other reported categories matched the repo-wide baseline on `main`
    (trace/formal/workflow/TDD/change-completeness/test identities/model
    correspondence/performance/approval/command-skips).
  - `npx musubix3 status --json` reported `gate.ready = false` and
    `approvals.release = missing`.
  - `npx musubix3 approval prepare release --json` succeeded and produced a
    release-manifest hash for the current tree; because this file is part of
    that manifest, the hash must be regenerated after any further edit.
- `change-record` applicability:
  - `CHANGE-017` has no entry in `.musubix/evidence/changes.json` yet, so this
    task had a clean docs-only change-record slate rather than a partially
    recorded chronology.
  - `npx musubix3 change-record CHANGE-017 impact --dry-run --json` refused to
    run without `--requirement`.
  - No prior docs-only CHANGE using `Requirements: none.` was found in this
    repo's change history, so there is no established in-repo precedent for a
    no-op chronology record.
  - Because this change intentionally modifies no normative requirement text
    (`Requirements: none.`), the current CLI offers no valid requirement set
    to record for staged change phases without violating the policy that only
    changed requirements may be listed. As a result, the present convention is
    to leave `change-record` unrun for this docs-only CHANGE and disclose the
    resulting `CHANGE_RECORD_MISSING` gate diagnostic.
  - `ask_user` is not exposed in this session's tool schema. Because this
    environment also forbids writing to `/tmp`, the human approval request was
    prepared instead at
    `.copilot-artifacts/change017/approval-request.md` with exact file hashes,
    diff hash, and release-manifest hash for relay.

## Status

Documentation content is ready for human release review, but overall release
readiness is still blocked in three layers:

1. repo-wide musubix gate readiness remains false (`status --json` reported
   `gate.ready = false`) because of pre-existing trace/workflow/TDD/change
   completeness and related diagnostics outside CHANGE-017;
2. this docs-only CHANGE still triggers one new gate diagnostic,
   `CHANGE_RECORD_MISSING`, because `change-record` cannot currently record a
   `Requirements: none.` change without an invented requirement ID; and
3. CHANGE-017 itself still lacks explicit human release approval for the final
   prepared manifest hash. `ask_user` is not exposed here, so the exact
   approval prompt was staged in
   `.copilot-artifacts/change017/approval-request.md` for manual relay. That
   approval request also discloses that the musubix release-manifest hash
   covers the whole current worktree state, which contains additional
   pre-existing diffs vs `main` outside this docs-only CHANGE.

Accordingly, approval recording, commit, and push were not completed
autonomously here.
