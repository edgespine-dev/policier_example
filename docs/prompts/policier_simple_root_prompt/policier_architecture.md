# Policier Architecture Plan

## 1. Objective
Build a production-grade, explainable, multi-agent policy pipeline in `app/templates/agent/policier` where:
- each component has isolated REST endpoints,
- each agent writes to its own PostgreSQL schema per test case/run,
- the UI reflects the pipeline step-by-step (`/explain`),
- tests are fast, exhaustive, and can run in parallel.

This plan is based on the current implementation in:
- `app/templates/agent/policier/api.py`
- `app/templates/agent/policier/policy_collector.py`
- `app/templates/agent/policier/policy_runner.py`
- `app/templates/agent/policier/policy_pipeline.py`
- `app/templates/agent/policier/sql/001_init_policy_explain.sql`
- `app/templates/agent/policier/sql/002_add_source_blob_and_rules.sql`

## 2. Current Baseline (already in repo)
Current API already provides:
- health and discovery (`/healthz`, `/ls`)
- source discovery (`/human_policies`, `/policy_files`, `/policy_files/excluded`, `/policy_source`)
- loop endpoints (`/policy_extract`, `/policy_verify`, `/policy_revise`, `/policy`)
- compact pipeline endpoints (`/policy_pipeline/files`, `/policy_pipeline/curate`, `/policy_pipeline/rules`, `/policy_pipeline`, `/policy_pipeline/warm_cache`, `/policy_pipeline/cache_stats`)
- explain UI (`/explain`)

SQL migrations already define explainability/pipeline tables:
- `policy_runs`
- `policy_run_sources`
- `policy_claims`
- `policy_evidence`
- `policy_step_traces`
- `policy_cache_entries`
- `policy_source_blobs`
- `policy_rules`
- `policy_rule_evidence`

Today, DB tables exist as SQL assets but are not fully integrated in runtime code. This architecture adds operational DB usage and strict component boundaries.

## 3. Target Component Model

## 3.1 Components
1. `orchestrator`
- owns run lifecycle, budgets, retries, status transitions.

2. `source_collector`
- lists included files and creates source snapshots (path/hash/content metadata).

3. `curation_agent`
- per file extract -> verify -> revise loop for relevance and factuality.

4. `rules_agent`
- converts curated notes to machine-checkable rules and merged rule sets.

5. `explain_api_ui`
- exposes explainability endpoints and `/explain` UI tabs by pipeline step.

6. `persistence_postgres`
- schema creation, migrations, DB contracts, retention, isolation.

7. `test_harness`
- contract tests per endpoint, component tests, end-to-end pipeline tests.

## 3.2 Communication Flow
1. `orchestrator` creates run envelope.
2. `orchestrator` invokes `source_collector` endpoint set.
3. `source_collector` emits source references to `curation_agent`.
4. `curation_agent` emits curated output per file.
5. `rules_agent` builds per-file rules and merged rules.
6. `explain_api_ui` reads traces/evidence and renders tabbed step view.
7. `test_harness` can call each component in isolation or full run.

Inter-component payload contract (minimum):
```json
{
  "run_id": "uuid",
  "test_case_id": "string",
  "topic": "string",
  "model": "string",
  "verifier_model": "string|null",
  "agent_schema": "string",
  "input_ref": {},
  "output_ref": {}
}
```

## 4. Endpoint Strategy (isolatable by agent)
Keep current endpoints for backward compatibility, but add clear grouped routes:
- `/v1/orchestrator/*`
- `/v1/agents/source/*`
- `/v1/agents/curation/*`
- `/v1/agents/rules/*`
- `/v1/explain/*`
- `/v1/tests/*`

Each group must be runnable independently with an explicit payload and deterministic output.

## 5. PostgreSQL Strategy (agentic schema isolation)

## 5.1 Schema Naming Convention
Each agent creates its own schema per test run:
- `ag_<agent>__<test_case_slug>__<run8>`
- examples:
  - `ag_source__tc_smoke__a1b2c3d4`
  - `ag_curation__tc_timeout__a1b2c3d4`

Constraints:
- lowercase, digits, `_`
- max length 63
- schema is created at test start and dropped after test teardown (except when `retain_on_fail=true`).

## 5.2 Table Usage (high-level)
Shared baseline tables (existing SQL assets, instantiated per agent schema where relevant):
- run control: `policy_runs`
- source lineage: `policy_run_sources`, `policy_source_blobs`
- curation/rules traces: `policy_step_traces`, `policy_rules`, `policy_rule_evidence`
- output normalization: `policy_claims`, `policy_evidence`
- cache: `policy_cache_entries`

Additional control tables (new):
- `policy_agent_handoffs` (handoff payload references between agents)
- `policy_test_cases` (test definitions)
- `policy_test_runs` (per execution metadata and results)
- `policy_test_assertions` (assertion-level pass/fail)

Detailed DDL and ownership are defined in component docs.

## 6. Explainability UI/UX Target
`/explain` must map directly to pipeline stages with one tab per stage:
1. Run Setup
2. Files (input inventory)
3. Curate (extract/verify/revise)
4. Rules (per-file)
5. Merged Rules (final output)
6. Evidence & Traces
7. Errors/Timeouts

Every tab should show:
- input payload,
- output payload,
- latency,
- status,
- links to evidence rows (file path/snippet hash/run id).

UI work can be finalized after API/component contracts are stable.

## 7. Delivery Strategy (test-first)
Yes: start with tests and contracts first.

Implementation order:
1. finalize endpoint contracts and JSON schemas,
2. implement `test_harness` fixtures/assertions,
3. implement persistence/schema isolation,
4. implement/adjust source -> curation -> rules components,
5. integrate orchestrator,
6. wire explain API,
7. finalize `/explain` tabs.

Parallelization suggestion:
- Agent A: persistence + migration runner
- Agent B: source_collector + curation endpoints
- Agent C: rules endpoints + merge
- Agent D: test_harness
- Agent E: explain API/UI once contracts are stable

## 8. Acceptance Criteria
1. Every component has isolated endpoint set and passes contract tests.
2. Every test case can run in parallel without DB collisions.
3. Full pipeline run persists explainable traces in PostgreSQL.
4. `/explain` displays each pipeline stage with clear in->out mapping.
5. Legacy endpoints still function or are documented as deprecated wrappers.
