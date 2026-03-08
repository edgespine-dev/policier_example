# Component Plan: persistence_postgres

## 1. Scope
Provide deterministic Postgres schema lifecycle for agent isolation, migrations, and retention.

Cluster wiring already exists via:
- `docs/APP_DB_POLICY.md`
- ConfigMap `policier-db-config`
- ExternalSecret `policier-db-creds`

## 2. Responsibilities
- build DB connection from env:
  - `POLICIER_DB_HOST`
  - `POLICIER_DB_PORT`
  - `POLICIER_DB_NAME`
  - `POLICIER_DB_USER`
  - `POLICIER_DB_PASSWORD`
  - `POLICIER_DB_SSLMODE`
- create/drop per-agent schemas per test run
- apply migrations to target schema (`SET search_path`)
- enforce cleanup/retention policy

## 3. Schema Lifecycle Contract
Create at run start:
- `ag_orchestrator__<tc>__<run8>`
- `ag_source__<tc>__<run8>`
- `ag_curation__<tc>__<run8>`
- `ag_rules__<tc>__<run8>`
- `ag_test__<tc>__<run8>`

Teardown:
- success: drop all schemas
- fail: keep schemas for triage only when `retain_on_fail=true`

## 4. Table Inventory
Existing SQL tables to be instantiated as needed:
- `policy_runs`
- `policy_run_sources`
- `policy_claims`
- `policy_evidence`
- `policy_step_traces`
- `policy_cache_entries`
- `policy_source_blobs`
- `policy_rules`
- `policy_rule_evidence`

New tables:
- `policy_agent_handoffs`
- `policy_curations`
- `policy_merged_rules`
- `policy_test_cases`
- `policy_test_runs`
- `policy_test_assertions`

## 5. Migration Strategy
1. keep existing SQL files as baseline
2. add `003_*` migration for new control/test tables
3. apply migrations idempotently (`CREATE TABLE IF NOT EXISTS`)
4. execute migration set per schema in deterministic order

## 6. Concurrency and Safety
- use advisory lock during migration per schema
- validate schema ownership before DDL/DROP
- never drop schemas outside naming convention

## 7. Test Cases
1. `tc_db_migration_idempotent`
- run migrations twice, no failures

2. `tc_db_parallel_schema_create`
- create 20 schemas concurrently

3. `tc_db_retention_cleanup`
- cleanup removes only expected old schemas

4. `tc_db_wrong_schema_protection`
- invalid schema name rejected

5. `tc_db_sslmode_env`
- dev (`disable`) and prod (`require`) both connect

## 8. Done Criteria
- schema isolation guaranteed for parallel testcases
- migration runner deterministic and safe
- DB objects align with explainability needs
