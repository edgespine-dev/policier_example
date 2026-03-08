# Component Plan: orchestrator

## 1. Scope
Own end-to-end run lifecycle and coordinate agent steps with strict budgets.

## 2. Responsibilities
- create run context (`run_id`, `test_case_id`, `topic`, model params)
- create per-agent schemas
- invoke agents in order or single-step mode
- enforce budgets/timeouts/retry policy
- persist run status and handoff metadata

## 3. Endpoint Set
1. `POST /v1/orchestrator/runs`
- start a full run
- request fields: `topic`, `model`, `verifier_model?`, `test_case_id`, `budget_seconds`, `force_refresh`
- response: run envelope + initial status

2. `POST /v1/orchestrator/runs/{run_id}/step/{agent}`
- run one component (`source|curation|rules|explain`) in isolation

3. `GET /v1/orchestrator/runs/{run_id}`
- full run status, stage completion map, timing, error summary

4. `POST /v1/orchestrator/runs/{run_id}/resume`
- continue from failed/paused stage

5. `POST /v1/orchestrator/runs/{run_id}/cancel`
- cooperative cancellation

Compatibility wrappers:
- existing `/policy_pipeline*` routes can call this orchestrator internally.

## 4. DB Schema and Tables
Schema owner: `orchestrator` agent schema for test runs.

Primary tables:
- `policy_runs` (existing): one row per run
- `policy_agent_handoffs` (new): handoff payloads between agents
- `policy_step_traces` (existing): stage execution traces and errors

`policy_agent_handoffs` columns:
- `id bigserial pk`
- `run_id uuid`
- `from_agent text`
- `to_agent text`
- `handoff_type text`
- `payload_json jsonb`
- `created_at timestamptz`

## 5. Execution Model
- stage order: `files -> curate -> rules -> final`
- fail-fast on non-retryable errors
- retry only transient failures (LLM timeout/network)
- each stage writes a normalized status event

Status values:
- `running`, `completed`, `timed_out`, `failed`, `cancelled`

## 6. Test Cases
1. `tc_orch_smoke_success`
- full run returns `completed`

2. `tc_orch_timeout`
- tiny budget triggers `timed_out`

3. `tc_orch_resume_after_failure`
- force one stage failure then resume succeeds

4. `tc_orch_step_isolation`
- call one stage only and verify only that stage tables updated

5. `tc_orch_parallel_runs`
- 10 runs in parallel, no schema collision

## 7. Done Criteria
- all orchestrator endpoints pass contract tests
- run status transitions are deterministic
- stage timing and errors are queryable for `/explain`
