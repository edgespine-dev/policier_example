# AGILE

This folder defines how agent-driven implementation stays trackable in a familiar Agile format.

## Goal
- keep epics, stories/slices, and sprint scope visible
- keep agent output auditable and reviewable by humans
- keep delivery tied to canonical plans and test gates

## Working model
1. Epics are defined from canonical components/chains.
2. Each story is delivered as slices in this order:
   - contract lock
   - JSON fixtures
   - deterministic tests
   - implementation
   - integration gate
3. Agents write implementation planning artifacts under `AGILE/IMPL/`.
4. Implementation is blocked until a test-auditor has approved story compliance against skills/policies.

## Folder map
- `AGENT_DELIVERY_PLAN.md`: operating model for multiple agents.
- `IMPL/EPIC_BACKLOG.md`: epic inventory and story seeds.
- `IMPL/SPRINT_PLAN.md`: sprint breakdown and gates.
- `IMPL/STORY_SLICE_TEMPLATE.md`: template for per-story planning.
- `IMPL/STORY_SPEC_QUEUE.md`: readiness queue for story instantiation and unblock flow.
- `IMPL/README.md`: file naming and update rules.
