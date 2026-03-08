# EPIC Backlog

## Current state
- Epic scope is defined.
- Concrete story files are not instantiated yet.
- Create story files from `STORY_SLICE_TEMPLATE.md` before any implementation starts.
- Agent I implementation is blocked until each story reaches `tests_audited` with `approved` compliance verdict.

## EPIC-01 Source and document ingestion
- Scope anchor: `PLANS/policier/file_selection_ingest.md`, `PLANS/policier/config_catalog.md`
- Candidate stories:
  - contract lock for selection + ingest endpoints
  - JSON fixtures for include/exclude/source blobs
  - deterministic tests for hashing, filtering, and response contracts
  - implementation of selection/create/read/ensure
  - integration gate with persistence and orchestrator

## EPIC-02 Snippet extraction
- Scope anchor: `PLANS/policier/snippet_extraction.md`
- Candidate stories:
  - contract lock for snippet create/read/ensure
  - JSON fixtures for snippet set outputs and failure cases
  - deterministic tests for structure/invariants/cache flags
  - implementation of extract/verify/revise orchestration
  - integration gate with ingestion + policy assembly

## EPIC-03 Policy and prompt generation
- Scope anchor: `PLANS/policier/policy_assembly.md`, `PLANS/policier/prompt_generation.md`
- Candidate stories:
  - contract lock for policy and prompt artifacts
  - JSON fixtures for policy sections and prompt lineage
  - deterministic tests for required fields and lineage pointers
  - implementation for assembly + prompt rendering
  - integration gate with snippets + topic evaluation

## EPIC-04 Topic evaluation
- Scope anchor: `PLANS/policier/topic_evaluation.md`
- Candidate stories:
  - contract lock for evaluation/findings/recommendations
  - JSON fixtures for acceptable and rejected outputs
  - deterministic tests for envelope/status/metadata
  - implementation for evaluation create/read/ensure
  - integration gate with prompt generation + explainability

## EPIC-05 Explainability
- Scope anchor: `PLANS/policier/explainability_api_ui.md`
- Candidate stories:
  - contract lock for explain read endpoints
  - JSON fixtures for run/step/artifact projections
  - deterministic tests for lineage projection completeness
  - implementation of explain API and UI tabs
  - integration gate across full artifact chain

## EPIC-06 Persistence and invalidation
- Scope anchor: `PLANS/policier/persistence_invalidation.md`, `docs/APP_DB_POLICY.md`
- Candidate stories:
  - contract lock for migration/validity/invalidation endpoints
  - JSON fixtures for schema-ready and failure responses
  - deterministic tests for migration idempotency and fingerprint validity
  - implementation of db adapter + migration runner
  - integration gate with all component DB reads/writes

## EPIC-07 Test harness and contract gates
- Scope anchor: `PLANS/policier/test_harness.md`, `PLANS/testing/test_policy.md`
- Candidate stories:
  - contract lock for test runner outputs
  - JSON fixtures for endpoint/component/system test cases
  - deterministic tests for harness lifecycle/reporting
  - implementation of rerun-failed + judge summary hooks
  - integration gate for release-readiness baseline
