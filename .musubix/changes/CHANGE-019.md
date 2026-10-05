# CHANGE-019: Fix three ai-scientist robustness defects found during CHANGE-001's #62 remediation review (#64, #66, #67)

## Summary

Defect-correction batch for three implementation gaps found during
CHANGE-001's #62 debt-remediation ADR rubber-duck review and tracked as
dedicated follow-up issues:

- #64 — `phase_state.py` lacks a cross-process concurrency guard, so two
  separate CLI invocations racing on the same project's phase-state file can
  clobber each other's writes (last-writer-wins), violating DES-AISCI-003's
  existing "read-modify-write safe across separate CLI invocations"
  constraint.
- #66 — `mcp_managed.py` has a port-allocation TOCTOU window and an
  unsynchronized module-level runtime registry, and never validates that a
  managed server's `endpointTemplate` host is loopback, violating
  DES-AISCI-012's existing "must bind only to 127.0.0.1" and "must not start
  a second process for a server name whose process is already registered"
  constraints.
- #67 — `tdd_gate.py` detects skipped tests only via a narrow console-text
  regex (`\b\d+\s+skipped\b`), which is wording-fragile and has no mechanism
  to allow an explicitly approved skip, contradicting DES-AISCI-019's
  "zero *unapproved* skipped tests" wording (the regex cannot distinguish
  approved from unapproved skips at all).

All three are classified as **defect corrections**: the already-approved
requirement/design text already states the stronger guarantee; only the
implementation was non-compliant. No `requirements.md`/`design.md` text
changes are made by this change.

## Scope

- Existing feature: `ai-scientist`.
- Touches: `src/ai_scientist/phase_state.py`, `src/ai_scientist/mcp_managed.py`,
  `src/ai_scientist/tdd_gate.py`, and their respective test files
  (`tests/test_ai_scientist_phase_state.py`, `tests/test_ai_scientist_mcp.py`,
  `tests/test_ai_scientist_tdd_gate.py`).
- No `requirements.md`/`design.md` text changes; ADR-0075, ADR-0084, and
  ADR-0091 were amended to record resolution of their previously-documented
  "Known limitation" sections (see Design, below).

Requirements: REQ-AISCI-004 REQ-AISCI-017 REQ-AISCI-024

## Design

No `design.md` text changes (defect correction; existing constraints already
state the stronger guarantees). ADRs amended to record resolution of their
previously-documented "Known limitation" sections: ADR-0075 (DES-AISCI-003),
ADR-0084 (DES-AISCI-012), ADR-0091 (DES-AISCI-019) — each now has a
"Resolved" note describing the fix and pointing at its covering TDD
evidence, mirroring CHANGE-020's precedent for amending ADRs rather than
adding new ones when a defect fix directly closes an ADR's own previously
accepted limitation.

## Fixes

### 1. `phase_state.py` — cross-process lock (issue #64, REQ-AISCI-004/005)

Added an OS-level advisory file lock (`fcntl.flock` on POSIX,
`msvcrt.locking` on Windows) on a sibling `.lock` file next to each
project's phase-state file, via a new `_locked(handle)` context manager.
Both `mark_phase_complete` and `record_override` now wrap their entire
read-modify-write cycle inside this lock, so two concurrent callers (same
or different process) can no longer interleave a stale read with a write,
which previously allowed one operation's effect to silently clobber the
other's.

A documented no-op test seam, `_after_locked_read_hook()`, is called
immediately after the locked read so tests can deterministically force a
rendezvous attempt between two concurrent callers and assert it does *not*
succeed (proving serialization) without relying on timing-sensitive sleeps.

Note: DES-AISCI-003's constraint text only requires reusing the same
general "single-writer discipline" shape as ai-data-scientist's existing
patterns; it does not require, and this change does not add, any
process-local `threading.Lock`. A process-local lock alone cannot provide
cross-process safety, so this change backs the read-modify-write cycle with
a real OS-level file lock instead, which is what the already-stated
cross-process constraint requires.

### 2. `mcp_managed.py` — registry lock + loopback validation (issue #66, REQ-AISCI-017)

- Added a per-server-name `threading.Lock` (`_lock_for`, mirroring
  `project_manager`'s per-path lock pattern) wrapping the entirety of
  `ensure_managed_server`'s check-then-start critical section, so two
  concurrent first-use callers for the same server name can no longer both
  observe "not running" and both start a second process. `status` and
  `stop` were updated to use the same per-name lock for consistency.
- Added `_require_loopback_endpoint`, called at the very top of
  `ensure_managed_server`, which parses the server's `endpointTemplate` and
  rejects any host that is not a loopback address. Host validation resolves
  the hostname via `_is_loopback_host` (checking a literal loopback IP
  first, then requiring every address `socket.getaddrinfo` resolves it to
  be loopback) rather than string-matching a fixed allowlist such as
  `{127.0.0.1, localhost, ::1}`, so a hosts-file/DNS override that maps
  `localhost` to a routable address cannot bypass the check (found and
  fixed during this change's rubber-duck review; see `TEST-AISCI-046`).
- The startup health-poll loop now checks `process.poll()` *before*
  trusting a health-check response, not after. Previously an external
  process that stole the allocated port could answer the health probe on
  behalf of our already-dead child and get cached as a legitimate managed
  runtime; reordering the check closes that (also found during rubber-duck
  review).

**Accepted residual risk (explicitly out of scope):** eliminating the
port-allocation TOCTOU window against an *external, non-ai_scientist*
process entirely would require socket-fd-passing/inheritance into the
spawned server process. Issue #66's own proposed-fix text only asks for the
registry-level lock and loopback validation implemented here, not full
fd-passing. The tiny residual window where an unrelated external process on
the same machine steals the allocated port between `_allocate_port()` and
`Popen`, and then answers the health probe itself before our own process
would have failed `poll()`, remains and is accepted as a known, documented
limitation rather than addressed by this change.

### 3. `tdd_gate.py` — structural skip detection + approved-skip allowlist (issue #67, REQ-AISCI-024)

`run_configured_test_suite` now accepts `approved_skips: frozenset[str] =
frozenset()`. For any command that invokes `pytest`, it transparently
appends `--json-report --json-report-file=<tmp>` (using the already-present
`pytest-json-report` dev dependency), runs the suite, and — after the
existing non-zero-exit-code check — parses the JSON report structurally for
`outcome == "skipped"` test nodeids. Only skipped nodeids **not** present in
`approved_skips` raise `TestSuiteGateError`; an approved skip no longer
fails the gate. Commands that do not invoke pytest fall back to the
original text-regex detection unchanged, so no existing caller is broken.
The pre-existing `TEST-AISCI-035` continues to pass unmodified.

`_is_pytest_invocation` recognizes only an actual pytest invocation — an
executable literally named `pytest`/`pytest-<suffix>`, or `-m pytest` — not
any command part that merely contains the substring "pytest" (e.g. a script
named `run_pytest_wrapper.sh` or a test file `test_pytest_helper.py`), which
the original substring-based detection would have misclassified as a
pytest invocation and corrupted with unsupported `--json-report` flags
(found and fixed during rubber-duck review; see `TEST-AISCI-047`).

## TDD Evidence

| Test | Requirement | Red | Green |
|---|---|---|---|
| TEST-AISCI-041 (phase_state concurrent completion+override) | REQ-AISCI-004 | recorded | recorded |
| TEST-AISCI-042 (mcp_managed rejects non-loopback endpoint) | REQ-AISCI-017 | recorded | recorded |
| TEST-AISCI-043 (mcp_managed concurrent first-use starts one process) | REQ-AISCI-017 | recorded | recorded |
| TEST-AISCI-044 (tdd_gate approved-skip allowlist) | REQ-AISCI-024 | recorded | recorded |
| TEST-AISCI-045 (tdd_gate structural skip detection) | REQ-AISCI-024 | recorded | recorded |
| TEST-AISCI-046 (mcp_managed rejects a hostname resolving only to non-loopback addresses) | REQ-AISCI-017 | recorded | recorded |
| TEST-AISCI-047 (tdd_gate pytest detection excludes substring-only matches) | REQ-AISCI-024 | recorded | recorded |

TEST-AISCI-046 and TEST-AISCI-047 were added in response to a native
`rubber-duck` review pass of this change's first implementation, which
found the `localhost`-only-by-string-match loopback check and the
substring-based `"pytest" in part` pytest-command detection were each
narrower than their constraint text required. Both were fixed and proven
with fresh Red/Green cycles before this document's current revision.

Each Red cycle was recorded against the pre-fix code (via a temporary
`git stash` of only the fix under test) to confirm a genuine failing
baseline, then the fix was restored and Green recorded against the same
test. Full suite: 587/587 passing (580 pre-existing + 7 new).

## Implementation Plan

1. No requirements/design changes — both already state the stronger
   guarantee; only the implementation was non-compliant.
2. Implement and TDD each of the three fixes independently (see table
   above).
3. `trace build` / `trace check --strict`: 0 diagnostics, full coverage.
4. `graph index` / `graph gate`: 0 diagnostics, no cycles.
5. `gate --json`: repo-wide pre-existing diagnostics (`workflow`, `tdd`,
   `change-history`, `change-completeness`, `test-identities`,
   `performance`, `approval`) persist identically on `main` itself before
   this change (confirmed by running the same command there) — out of
   scope for this change, consistent with established precedent across
   prior changes this session.
6. Human release approval (`nahisaho`) requested for the exact file/hash
   set at merge time.

## Status

DRAFT — pending release approval.
