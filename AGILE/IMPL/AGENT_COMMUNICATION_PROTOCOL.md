# Agent Communication Protocol

## Purpose
Define how agents communicate in a traceable and context-minimized way during planning, testing, implementation, and integration.

## Core rule
Agents do not rely on informal chat as source of truth.
They communicate through auditable artifacts and structured handoff events.

## Communication surfaces
1. Story file (`STORY-*.md`)
- canonical per-story state and decisions.

2. `HANDOFF_LOG.md`
- canonical event log for cross-agent handoffs.

3. Gate evidence links
- test outputs, fixture paths, and check results linked from story file.

4. Optional transport automation
- Redis Streams or queue can be used as transport, but all final decisions must be persisted in story + handoff log.

## Standard message envelope
Use this JSON shape for any agent-to-agent handoff payload:

```json
{
  "story_id": "STORY-03-01",
  "from_agent": "Agent T",
  "to_agent": "Agent V",
  "message_type": "tests_written",
  "summary": "Prompt lineage contract tests are ready for audit.",
  "required_actions": [
    "audit test coverage against test_policy",
    "verify nonfunctional checks are represented"
  ],
  "references": [
    "AGILE/IMPL/STORY-03-01-policy-contract.md",
    "tests/io/prompts/create.expected.json"
  ],
  "created_at": "YYYY-MM-DDTHH:MM:SSZ"
}
```

## Allowed message types
- `story_spec_locked`
- `tests_written`
- `tests_rejected`
- `tests_approved`
- `implementation_unblocked`
- `implementation_update`
- `integration_gate_passed`
- `integration_gate_failed`

## Mandatory flow (test -> implementation)
1. Agent T publishes `tests_written` to Agent V.
2. Agent V audits and publishes either:
- `tests_rejected` with required fixes, or
- `tests_approved` with evidence links.
3. Agent O reviews dependency order and publishes `implementation_unblocked` to Agent I.
4. Agent I publishes `implementation_update` back to Agent O and Agent V.
5. Agent O and Agent V publish integration gate result (`passed`/`failed`).

## Test feedback packet requirements
When Agent V sends `tests_rejected`, the message must include:
- failing checks
- violated policy/skill references
- concrete change requests
- acceptance condition to become `tests_approved`

## Relevance filtering (context minimization)
Each agent should receive only:
- story file
- changed files list
- required checks for the next action
- minimal policy references needed for that action

Do not broadcast whole-repo context unless Agent O marks incident mode.
