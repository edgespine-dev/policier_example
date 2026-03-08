# STORY-06-01 Migration/Validity Contract Lock

## Header
- Story ID: STORY-06-01
- Epic: EPIC-06
- Orchestrator / Team Lead (Agent O): Agent-O
- Test Author (Agent T): Agent-T
- Test Auditor (Agent V): Agent-V
- Implementer (Agent I): Agent-I
- Sprint: Sprint 1
- Status: spec_locked

## Story goal
- Lock migration, validity, and cache invalidation API contracts as foundation for all other epics.

## Scope anchor
- `PLANS/policier/persistence_invalidation.md`
- `docs/APP_DB_POLICY.md`
- `PLANS/testing/test_policy.md`

## Task packet (context-minimized)
- included docs: `persistence_invalidation.md`, `APP_DB_POLICY.md`
- included policy refs: `test_policy.md`, `ai_code_safety_policy.md`
- included contract/fixture refs: `contracts/persistence/*`, `tests/io/persistence/*`
- explicitly excluded context: explain UI and topic evaluation

## Definition of ready checklist
- [x] scope/objective is specific and testable
- [x] contract lock slice is described
- [ ] fixture plan is described
- [ ] deterministic test matrix is described
- [x] integration dependencies are listed

## Slice checklist
- [ ] Contract lock
- [ ] JSON fixtures
- [ ] Deterministic tests
- [ ] Implementation
- [ ] Integration gate

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
- Blocking reasons (if denied): tests not yet written and audited
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
- dependencies: none (foundation epic)
- follow-up stories: persistence fixtures/tests, migration runner implementation
