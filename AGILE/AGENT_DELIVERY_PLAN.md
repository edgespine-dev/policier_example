# Agent Delivery Plan

## Purpose
Turn the current Policier planning baseline into executable Agile delivery that can be followed by both agents and humans.

## Source of truth
- `PLANS/policier/*`
- `PLANS/testing/*`
- `docs/APP_DB_POLICY.md`
- `AGILE/IMPL/AGENT_COMMUNICATION_PROTOCOL.md`

## Roles for a test-first multi-agent setup
- Agent O (Orchestrator / Team Lead): sequencing, context packaging, integration gating, and final go/no-go decisions.
- Agent T (Test Author): contracts + fixtures + deterministic test authoring.
- Agent V (Test Auditor): verifies tests against skills and policies before implementation.
- Agent I (Implementer): implementation + integration wiring after explicit unblock.

Hard rule:
- Agent I must not start implementation before Agent V marks test compliance as `approved`.
- Agent O is the only role that may move a story to `implementation_unblocked` or `done`.

## EPIC model
Use one epic per canonical component chain:

1. Source and document ingestion
2. Snippet extraction
3. Policy and prompt generation
4. Topic evaluation
5. Explainability
6. Persistence and invalidation
7. Test harness and contract gates

## Story/slice model (mandatory order)
Every story should use these slices:

1. Contract lock
- lock request/response shape and status vocabulary.

2. JSON fixtures
- add request/expected fixtures for happy path and core errors.

3. Deterministic tests
- add contract/invariant tests that run without live model variance where possible.

4. Implementation
- implement to pass deterministic tests first.

5. Integration gate
- run cross-component checks and mark gate pass/fail explicitly.

## Compliance gates before implementation
Agent V must explicitly verify each story against:
- `PLANS/policier/*` scope anchors and component intent
- `agent-backbone` skill expectations relevant to the epic
- `PLANS/testing/test_policy.md` (correctness)
- `PLANS/testing/ai_code_safety_policy.md` (execution safety)
- `PLANS/testing/nonfunctional_policy.md` (operational readiness)
- `AGILE/*` process rules (slice order, handoff protocol, status flow)

Implementation unblock condition:
- status must be `tests_audited`
- compliance verdict must be `approved`
- gate evidence must be linked in the story file under `AGILE/IMPL/`
- Agent O must confirm dependency order and set `implementation_unblocked`.

## Orchestrated workflow (single story)
1. Agent O creates minimal task packet and sets story to `spec_locked`.
2. Agent T delivers contract lock + fixtures + deterministic tests and sets `tests_written`.
3. Agent V audits against skills/policies and sets `tests_audited` (`approved` or `rejected`).
4. Agent O either blocks or unblocks implementation.
5. Agent I implements and runs required checks.
6. Agent O + Agent V run integration gate and decide `done` or `blocked`.

## Agent communication model
- Communication protocol is defined in `AGILE/IMPL/AGENT_COMMUNICATION_PROTOCOL.md`.
- Agent O enforces protocol use and rejects undocumented handoffs.
- Transport can be Redis (or similar), but durable truth remains story files + handoff log.

## Context minimization rule
Each task packet should include only:
- one story file
- the smallest relevant subset of `PLANS/policier/*`
- required policy anchors from `PLANS/testing/*`
- exact fixture/contract paths needed for the slice

Avoid broad repo scans when a targeted packet exists.

## Sprint model
Use short, gate-oriented sprints (recommended: 1 week).

Sprint 0: Setup and lock
- lock epic backlog, story IDs, and gate definitions.

Sprint 1: Foundation
- EPIC 6 (Persistence and invalidation)
- EPIC 1 (Source and document ingestion)

Sprint 2: AI extraction core
- EPIC 2 (Snippet extraction)

Sprint 3: Synthesis chain
- EPIC 3 (Policy and prompt generation)

Sprint 4: Decision + explain
- EPIC 4 (Topic evaluation)
- EPIC 5 (Explainability)

Sprint 5: Hardening and readiness
- EPIC 7 (Test harness and contract gates)
- end-to-end stabilization across all epics

## Required tracking artifacts
Agents must keep these up to date in `AGILE/IMPL/`:
- epic backlog status
- story spec queue and readiness state
- story-level slice checklists
- sprint scope and sprint close outcome
- gate result log (pass/fail + reason)
- handoff log between agents (who handed off, what changed, which gates ran)

## Story readiness before broad testing
Every story/slice must be fully specified before broad testing starts:
- objective and scope anchor
- contract shape
- fixture plan
- deterministic test matrix
- expected integration dependencies

If any of these is missing, status stays `draft` and the story is not testable.

## Definition of done (for each story)
- contract locked
- fixtures committed
- test compliance audited and approved
- deterministic tests green
- implementation merged
- integration gate passed
