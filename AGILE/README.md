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
3. Agents write implementation planning and execution trace artifacts under `AGILE/DELIVERY/`.
4. Implementation is blocked until a test-auditor has approved story compliance against skills/policies.

## Folder map
- `AGENT_DELIVERY_PLAN.md`: operating model for multiple agents.
- `DELIVERY/BACKLOG/EPIC_BACKLOG.md`: epic inventory and story seeds.
- `DELIVERY/SPRINTS/SPRINT_PLAN.md`: sprint breakdown and gates.
- `DELIVERY/STORIES/STORY_SLICE_TEMPLATE.md`: template for per-story planning.
- `DELIVERY/STORIES/STORY_SPEC_QUEUE.md`: readiness queue for story instantiation and unblock flow.
- `DELIVERY/HANDOFFS/HANDOFF_LOG.md`: cross-agent handoff trace.
- `DELIVERY/GATES/GATE_LOG.md`: integration and quality gate decisions.
- `DELIVERY/ACTIVITY/AGENT_ACTIVITY_LOG.md`: chronological summary of agent actions.
- `DELIVERY/EVIDENCE/`: links/files proving what was run and why decisions were made.
