# Component Plan: test_harness

## 1. Scope
Define fast, exhaustive tests for endpoint contracts, component behavior, and full pipeline correctness.

This component is implemented first (test-first), then used to drive iterative agent loops until green.

## 2. Responsibilities
- maintain test case catalog
- provision per-test schemas and fixtures
- run endpoint/component/e2e tests
- store assertions and artifacts

## 3. Endpoint Set
1. `POST /v1/tests/cases`
- create or update testcase definition

2. `POST /v1/tests/runs`
- execute one testcase
- request includes: `test_case_id`, `parallelism`, `retain_on_fail`

3. `GET /v1/tests/runs/{test_run_id}`
- summary with assertion results

4. `POST /v1/tests/runs/{test_run_id}/rerun_failed`
- rerun only failed assertions

5. `GET /v1/tests/catalog`
- list all testcases by component and status

## 4. DB Schema and Tables
Schema owner: `test_harness` per test run.

Tables:
- `policy_test_cases`
- `policy_test_runs`
- `policy_test_assertions`

`policy_test_cases` minimum columns:
- `test_case_id text pk`
- `component text`
- `input_json jsonb`
- `expected_json jsonb`
- `tags text[]`

`policy_test_assertions` minimum columns:
- `id bigserial pk`
- `test_run_id uuid`
- `assertion_name text`
- `status text` (`pass|fail`)
- `actual_json jsonb`
- `expected_json jsonb`
- `diff_text text`

## 5. Test Suite Layers
Layer A: endpoint contract tests
- schema and status code validation for each endpoint

Layer B: component behavior tests
- deterministic behavior under normal/error/timeout/cache paths

Layer C: e2e pipeline tests
- full run from files to merged rules and explain UI checks

## 6. Minimum Initial Testcases
1. `tc_api_healthz`
2. `tc_source_files_and_exclusions`
3. `tc_curation_extract_verify_revise`
4. `tc_rules_build_merge`
5. `tc_pipeline_full_happy_path`
6. `tc_pipeline_timeout`
7. `tc_pipeline_force_refresh`
8. `tc_explain_stage_views`
9. `tc_parallel_no_schema_collision`
10. `tc_restart_endpoint_guard`

## 7. Loop-Until-Green Strategy
For each component implementation cycle:
1. run targeted testcase set
2. patch component
3. rerun failed assertions only
4. stop when all pass

This allows autonomous agent loops with measurable progress.

## 8. Done Criteria
- every endpoint has contract coverage
- every component has failure/timeout coverage
- full pipeline tests are stable in parallel execution
