# STORY-07-01 Harness Output Contract and Rerun Flow

## Header
- Story ID: STORY-07-01
- Epic: EPIC-07
- Orchestrator / Team Lead (Agent O): Agent-O
- Test Author (Agent T): Agent-T
- Test Auditor (Agent V): Agent-V
- Implementer (Agent I): Agent-I
- Sprint: Sprint 5
- Status: draft

## Story goal
- Lock test harness result contract and rerun-failed behavior before hardening sprint.

## Scope anchor
- `PLANS/policier/test_harness.md`
- `PLANS/testing/test_policy.md`
- `PLANS/testing/nonfunctional_policy.md`

## Task packet (context-minimized)
- included docs: `test_harness.md`
- included policy refs: `test_policy.md`, `nonfunctional_policy.md`
- included contract/fixture refs: `contracts/tests/*`, `tests/io/harness/*`
- explicitly excluded context: component-level implementation files

## Definition of ready checklist
- [x] scope/objective is specific and testable
- [x] contract lock slice is described
- [x] fixture plan is described
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
- Blocking reasons (if denied): pending tests_audited
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
- dependencies: base component stories delivered
- follow-up stories: release gate aggregation
