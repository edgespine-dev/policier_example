# STORY-01-01 Selection/Ingest Contract Lock

## Header
- Story ID: STORY-01-01
- Epic: EPIC-01
- Orchestrator / Team Lead (Agent O): Agent-O
- Test Author (Agent T): Agent-T
- Test Auditor (Agent V): Agent-V
- Implementer (Agent I): Agent-I
- Sprint: Sprint 1
- Status: spec_locked

## Story goal
- Lock request/response contracts for file selection and document ingest create/read/ensure.

## Scope anchor
- `PLANS/policier/file_selection_ingest.md`
- `PLANS/policier/config_catalog.md`
- `PLANS/testing/test_policy.md`

## Task packet (context-minimized)
- included docs: `file_selection_ingest.md`, `config_catalog.md`
- included policy refs: `test_policy.md`, `ai_code_safety_policy.md`, `nonfunctional_policy.md`
- included contract/fixture refs: `contracts/selection/*`, `contracts/documents/*`
- explicitly excluded context: unrelated epic plan files

## Definition of ready checklist
- [x] scope/objective is specific and testable
- [x] contract lock slice is described
- [ ] fixture plan is described
- [ ] deterministic test matrix is described
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
- Blocking reasons (if denied): test slices not completed
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
- dependencies: STORY-06-01 migration/validity contract lock
- follow-up stories: STORY-01-02
