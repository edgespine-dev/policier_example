# STORY-02-01 Snippet Contract and Fixture Baseline

## Header
- Story ID: STORY-02-01
- Epic: EPIC-02
- Orchestrator / Team Lead (Agent O): Agent-O
- Test Author (Agent T): Agent-T
- Test Auditor (Agent V): Agent-V
- Implementer (Agent I): Agent-I
- Sprint: Sprint 2
- Status: draft

## Story goal
- Lock snippet extraction contract and create baseline fixtures before implementation.

## Scope anchor
- `PLANS/policier/snippet_extraction.md`
- `PLANS/testing/test_policy.md`

## Task packet (context-minimized)
- included docs: `snippet_extraction.md`
- included policy refs: `test_policy.md`, `nonfunctional_policy.md`
- included contract/fixture refs: `contracts/snippets/*`, `tests/io/snippets/*`
- explicitly excluded context: explainability UI details

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
- dependencies: EPIC-01 integration gate
- follow-up stories: snippet deterministic matrix + implementation
