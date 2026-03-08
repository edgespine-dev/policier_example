# Sprint Plan (Agent-driven)

## Cadence
- Recommended sprint length: 1 week
- End of sprint gate: integration gate summary is mandatory

## Sprint 0 - Planning lock
- lock epic IDs and story IDs
- lock gate definitions and pass/fail criteria
- create initial story files from template

## Sprint 1 - Data foundation
- EPIC-06 Persistence and invalidation
- EPIC-01 Source and document ingestion
- Exit gate:
  - migrations deterministic
  - selection/ingest contracts green

## Sprint 2 - Extraction core
- EPIC-02 Snippet extraction
- Exit gate:
  - snippet contract + invariant tests green
  - integration from ingestion -> snippets green

## Sprint 3 - Synthesis chain
- EPIC-03 Policy and prompt generation
- Exit gate:
  - policy/prompt contracts green
  - lineage fields complete

## Sprint 4 - Evaluation and explainability
- EPIC-04 Topic evaluation
- EPIC-05 Explainability
- Exit gate:
  - evaluation outputs contract-valid
  - explain views reconstruct end-to-end chain

## Sprint 5 - Hardening and release gate
- EPIC-07 Test harness and contract gates
- Cross-epic stabilization
- Exit gate:
  - endpoint/component/system suites green
  - unresolved blocker defects = 0
