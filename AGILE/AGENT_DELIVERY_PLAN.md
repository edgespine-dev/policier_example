# Agent Delivery Plan

## Purpose
Turn the current Policier planning baseline into executable Agile delivery that can be followed by both agents and humans.

## Source of truth
- `PLANS/policier/*`
- `PLANS/testing/*`
- `docs/APP_DB_POLICY.md`

## Roles for a two-agent setup
- Agent A: contracts + fixtures + deterministic test authoring.
- Agent B: implementation + integration wiring + gate fixes.

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
- story-level slice checklists
- sprint scope and sprint close outcome
- gate result log (pass/fail + reason)

## Definition of done (for each story)
- contract locked
- fixtures committed
- deterministic tests green
- implementation merged
- integration gate passed
