# Component Plan: explain_api_ui

## 1. Scope
Expose explainability APIs and a pedagogical UI that mirrors pipeline stages.

Current baseline exists as `/explain` in `api.py`; this plan upgrades it to stage tabs and DB-backed details.

## 2. Responsibilities
- provide API responses for run overview and stage details
- render tabbed UI for pipeline in->out explanations
- surface timings, statuses, evidence, and errors

## 3. Endpoint Set
1. `GET /v1/explain/runs`
- list recent runs with topic/status/timing

2. `GET /v1/explain/runs/{run_id}`
- full run overview + stage summaries

3. `GET /v1/explain/runs/{run_id}/stage/{stage}`
- detailed payload for `files|curate|rules|merge|final`

4. `GET /v1/explain/runs/{run_id}/evidence`
- evidence snippets and source references

5. `GET /v1/explain/ui`
- serves the UI (can alias existing `/explain`)

## 4. UI Requirements
Tabs (first-level pipeline):
1. Run Setup
2. Files
3. Curate
4. Rules
5. Merged Rules
6. Evidence
7. Errors

Per tab show:
- request in
- response out
- status + latency
- links to source/evidence

Interaction requirements:
- stage can be triggered independently (for debugging)
- explicit error panel with retry action
- copyable JSON payloads for reproducibility

## 5. DB Reads
Read from:
- `policy_runs`
- `policy_step_traces`
- `policy_run_sources`
- `policy_source_blobs`
- `policy_rules`
- `policy_rule_evidence`
- `policy_merged_rules`

Optional read from explain views:
- `v_policy_run_overview`
- `v_policy_claim_explain`
- `v_policy_rules_explain`

## 6. Test Cases
1. `tc_explain_run_list`
- latest runs endpoint returns deterministic sorting

2. `tc_explain_stage_payloads`
- each stage endpoint returns required fields

3. `tc_explain_evidence_join`
- evidence endpoint joins rules and sources correctly

4. `tc_explain_ui_smoke`
- UI loads, tabs switch, and data fetch succeeds

5. `tc_explain_ui_timeout_visualization`
- timeout states visibly marked and explained

## 7. Done Criteria
- `/v1/explain/*` endpoints stable and documented
- UI represents the pipeline exactly as executed
- user can understand why each rule exists
