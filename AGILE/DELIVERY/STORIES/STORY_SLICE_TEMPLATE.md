# Story Slice Template

## Header
- Story ID:
- Epic:
- Orchestrator / Team Lead (Agent O):
- Test Author (Agent T):
- Test Auditor (Agent V):
- Implementer (Agent I):
- Sprint:
- Status: `draft | spec_locked | tests_written | tests_audited | implementation_unblocked | in_progress | blocked | done`

## Story goal
- one-sentence outcome

## Scope anchor
- linked plan docs (paths)

## Task packet (context-minimized)
- included docs:
- included policy refs:
- included contract/fixture refs:
- explicitly excluded context:

## Definition of ready checklist
- [ ] scope/objective is specific and testable
- [ ] contract lock slice is described
- [ ] fixture plan is described
- [ ] deterministic test matrix is described
- [ ] integration dependencies are listed

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
- [ ] scope matches `PLANS/policier/*` canonical component intent
- [ ] relevant `agent-backbone` skills are referenced
- [ ] `PLANS/testing/test_policy.md` checks satisfied
- [ ] `PLANS/testing/ai_code_safety_policy.md` checks satisfied
- [ ] `PLANS/testing/nonfunctional_policy.md` checks satisfied
- [ ] `AGILE/*` process constraints satisfied (slice order + handoff + status flow)
- Compliance verdict: `approved | rejected`
- Auditor notes:

## Test feedback to implementer (when rejected)
- failing checks:
- violated references (skills/policies):
- required code/design changes:
- acceptance condition for re-audit:

## Implementation unblock
- Unblock status: `granted | denied`
- Blocking reasons (if denied):
- Evidence links:
- Unblocked by (Agent O):

## Gate result
- Gate status: `pass | fail`
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
- dependencies
- follow-up stories
