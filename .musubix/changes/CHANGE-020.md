# CHANGE-020: Narrow two overclaimed ai-scientist design guarantees to match actual implementation (#65, #68)

## Summary

Documentation-only correction for two gaps found during CHANGE-001's #62
debt-remediation ADR rubber-duck review (ADR-0087, ADR-0090) and tracked as
dedicated follow-up issues: #65 (`manifest.py`'s skill-registry verification
scope) and #68 (`latex_renderer.py`'s content-preservation guarantee scope).
Both issues found that a requirement/design text's stated guarantee was
broader than what the shipped implementation actually does or needs to do.
After confirming with the design owner (`nahisaho`), both are resolved by
narrowing the requirement/design text to match the implementation, rather
than changing the implementation to match the broader text. No source code
is touched by this change.

## Scope

- Existing feature: `ai-scientist`.
- Touches: `.musubix/features/ai-scientist/requirements.md` (REQ-AISCI-023
  acceptance text only), `.musubix/features/ai-scientist/design.md`
  (DES-AISCI-015 and DES-AISCI-018 only), `.musubix/decisions/ADR-0087.md`
  and `.musubix/decisions/ADR-0090.md` ("Known limitation" sections,
  renamed to "Resolved scope note").
- No source code changes: `src/ai_scientist/manifest.py` and
  `src/ai_scientist/latex_renderer.py` are unmodified; their existing
  behavior is what the corrected text now accurately describes.
- Classification: documentation-only change (no observable behavior
  changes). TDD is not applicable — no new or changed test obligations.
- REQ-AISCI-023's stable ID is preserved (its acceptance text is narrowed
  to match already-implemented behavior, not a new obligation).
  DES-AISCI-015/018's design text is likewise corrected in place.

## Affected Requirements

Requirements: REQ-AISCI-023

(REQ-AISCI-021/022, the other requirements DES-AISCI-018 traces to, are
unaffected — the narrowed text only clarifies constraint scope, it does not
touch their statement/acceptance.)

## Design

- **DES-AISCI-015** (`manifest.py`): Responsibilities/Constraints corrected
  from "the host Copilot CLI's installed skill registry" to "the
  repository-declared skill registry (this repository's own
  `.github/skills/*/SKILL.md` and `VENDORED.md` tree — not the host Copilot
  CLI's live installed-skill registry, which this component does not
  query)". This matches `scan_repo_skill_registry()`'s actual scope exactly.
- **DES-AISCI-018** (`latex_renderer.py`): Constraints corrected to state
  the "no content dropped" guarantee is scoped to section/paragraph-level
  content (heading and paragraph text, and their relative order), excluding
  line-level whitespace (leading/trailing spaces, intentional indentation,
  blank lines at the document boundary), which the renderer may normalize.
  This matches `render_latex(...)`'s actual `.strip()`-based behavior
  exactly.
- **ADR-0087**: "Known limitation" section renamed to "Resolved scope
  note", explaining the requirement/design correction and that a host CLI
  running a stale/version-skewed skill relative to this repository is out
  of scope for this verifier (to be caught by other means).
- **ADR-0090**: "Known limitation" section renamed to "Resolved scope
  note", explaining the design correction and that LaTeX itself is
  whitespace-insensitive at the character level within paragraphs, so
  preserving line-level whitespace was judged unnecessary for this
  renderer's scope.

ADRs: ADR-0087 (amended), ADR-0090 (amended) — no new ADRs; both decisions
were already documented, only their "Known limitation" framing is updated
to reflect the now-resolved scope.

## Implementation Plan

1. Narrow REQ-AISCI-023's acceptance text (requirements.md). Validate:
   `requirements validate` — 0 diagnostics. Rubber-duck review of the
   combined requirements/design/ADR edits: PASS (no issues found). Record
   `requirements` approval.
2. Narrow DES-AISCI-015 and DES-AISCI-018 (design.md); update ADR-0087 and
   ADR-0090's limitation notes. Validate: `design validate` — 0
   diagnostics. Record `design` approval.
3. Rebuild `trace`: 0 diagnostics.
4. No TDD phase: documentation-only change, no implementation code
   touched, no new/changed test obligations.
5. `change-record CHANGE-020 impact/requirements/design` recorded
   successfully (fingerprints differ phase-to-phase as expected).
   `change-record CHANGE-020 quality` cannot be recorded: the CLI
   hard-requires a fresh Red/Green cycle scoped to this change for every
   listed requirement ID before accepting a `quality` phase.

   **Known, explicit deviation from the sdd-change skill's literal rule**
   ("each requirement whose acceptance changes needs fresh Red and Green"):
   no fresh Red/Green cycle is recorded for REQ-AISCI-023. Two independent
   rubber-duck review passes both confirmed this is a real policy
   deviation, not a permitted documentation exemption, specifically
   because: (a) a genuine Red phase cannot be produced — the acceptance
   text only narrows wording to match code that is already correct, so
   there is no failing behavior to reproduce; and (b) the previously-cited
   pre-existing tests are only partial evidence — `TEST-AISCI-023`
   exercises the repository-local-registry success path, but does not
   cover the loader's failure paths, and `TEST-AISCI-036` is unrelated
   (orchestrator dispatch, not registry semantics). The full 580-test
   suite was re-confirmed passing as general regression evidence only,
   not as a substitute scoped Green artifact.

   This deviation is accepted as a **user-approved exception**: the design
   owner (`nahisaho`) was presented with both rubber-duck findings in full
   and explicitly chose to proceed without a fresh Red/Green cycle, with
   this note serving as the permanent record of that decision and its
   rationale, per release approval covering this exact exception alongside
   the file/hash set.
6. Run `gate --json`: confirm no new CHANGE-020-attributable diagnostics
   (repo-wide pre-existing diagnostics unrelated to this change, e.g.
   `workflow`/`tdd`/`approval`/`commands` checks failing for unrelated
   reasons, are out of scope — consistent with established precedent
   across prior changes this session).
7. Full test suite: expected unchanged (580/580), since no source code was
   touched. Confirmed: 580 passed.
8. Human release approval (`nahisaho`) requested for the exact file set
   and `approval prepare release --json` hash at merge time.

## Status

DRAFT — pending release approval.
