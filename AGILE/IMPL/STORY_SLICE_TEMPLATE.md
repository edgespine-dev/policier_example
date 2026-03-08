# Story Slice Template

## Header
- Story ID:
- Epic:
- Owner agent:
- Sprint:
- Status: `planned | in_progress | blocked | done`

## Story goal
- one-sentence outcome

## Scope anchor
- linked plan docs (paths)

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

## Gate result
- Gate status: `pass | fail`
- Evidence:
- Remaining risks:

## Notes
- dependencies
- follow-up stories
