# STORY-01-02 Selection Fixtures and Deterministic Tests

## Header
- Story ID: STORY-01-02
- Epic: EPIC-01
- Orchestrator / Team Lead (Agent O): Agent-O
- Test Author (Agent T): Agent-T
- Test Auditor (Agent V): Agent-V
- Implementer (Agent I): Agent-I
- Sprint: Sprint 1
- Status: draft

## Story goal
- Add JSON fixtures and deterministic contract/invariant tests for selection and documents endpoints.

## Scope anchor
- `PLANS/policier/file_selection_ingest.md`
- `PLANS/policier/test_harness.md`
- `PLANS/testing/test_policy.md`

## Task packet (context-minimized)
- included docs: `file_selection_ingest.md`, `test_harness.md`
- included policy refs: `test_policy.md`
- included contract/fixture refs: `tests/io/selection/*`, `tests/io/documents/*`
- explicitly excluded context: AI evaluation plans

## Definition of ready checklist
- [x] scope/objective is specific and testable
- [ ] contract lock slice is described
- [x] fixture plan is described
- [x] deterministic test matrix is described
- [x] integration dependencies are listed

## Slice checklist
- [ ] Contract lock
  - response/request schema locked
  - status vocabulary locked
- [ ] JSON fixtures
  - happy-path fixture
  - failure fixture(s)
- [ ] Deterministic tests
  - contract tests
  - invariant tests
- [ ] Implementation
  - code merged
  - local checks green
- [ ] Integration gate
  - upstream/downstream integration check
  - gate result logged

## Skills and policy compliance (Agent V)
- [ ] relevant `agent-backbone` skills are referenced
- [ ] `PLANS/testing/test_policy.md` checks satisfied
- [ ] `PLANS/testing/ai_code_safety_policy.md` checks satisfied
- [ ] `PLANS/testing/nonfunctional_policy.md` checks satisfied
- Compliance verdict: approved | rejected
- Auditor notes:

## Test feedback to implementer (when rejected)
- failing checks:
- violated references (skills/policies):
- required code/design changes:
- acceptance condition for re-audit:

## Implementation unblock
- Unblock status: denied
- Blocking reasons (if denied): fixtures/tests not yet authored and audited
- Evidence links:
- Unblocked by (Agent O):

## Gate result
- Gate status: fail
- Evidence:
- Remaining risks:

## Handoff record
- from:
- to:
- message type:
- changed files:
- checks run:
- result summary:

## Notes
- dependencies: STORY-01-01
- follow-up stories: implementation story in Sprint 1
