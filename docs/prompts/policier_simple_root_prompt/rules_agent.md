# Component Plan: rules_agent

## 1. Scope
Transform curated outputs into machine-checkable rules and merged rule sets.

Based on current `build_rules_per_file` and `merge_rules` in `policy_pipeline.py`.

## 2. Responsibilities
- generate short imperative rules/checks/assumptions per relevant file
- deduplicate and merge across files
- persist rule lineage and evidence

## 3. Endpoint Set
1. `POST /v1/agents/rules/build`
- request: `run_id`, `topic`, `model`, curated payload reference
- response: `rules_per_file`

2. `POST /v1/agents/rules/merge`
- request: `run_id`
- response: merged rules/checks/assumptions

3. `GET /v1/agents/rules/run/{run_id}`
- response: per-file and merged rules with stats

Compatibility wrappers:
- map existing `/policy_pipeline/rules` and `/policy_pipeline`.

## 4. DB Schema and Tables
Schema owner: `rules_agent` agent schema per test run.

Tables:
- `policy_rules` (existing)
- `policy_rule_evidence` (existing)
- `policy_claims` (existing, optional normalization bridge)
- `policy_evidence` (existing, optional normalization bridge)
- `policy_cache_entries` (existing): stage `rules` and `merged`
- `policy_merged_rules` (new): final merged output per run

`policy_merged_rules` columns:
- `run_id uuid pk`
- `topic text`
- `model text`
- `rules_json jsonb`
- `checks_json jsonb`
- `assumptions_json jsonb`
- `created_at timestamptz`

## 5. Input/Output Contracts
`/build` output (per file):
```json
{
  "file": "/docs/X.md",
  "rules": ["..."],
  "checks": ["..."],
  "assumptions": ["..."]
}
```

`/merge` output:
```json
{
  "rules": ["..."],
  "checks": ["..."],
  "assumptions": ["..."]
}
```

## 6. Test Cases
1. `tc_rules_from_single_file`
- one relevant file produces non-empty rules

2. `tc_rules_skip_non_relevant_files`
- non-relevant files produce no rules

3. `tc_rules_merge_dedup_case_insensitive`
- duplicate rules merged once regardless of case

4. `tc_rules_cache_hit`
- second build run uses cache

5. `tc_rules_evidence_linkage`
- each stored rule can be traced back to source blob/file

## 7. Done Criteria
- merged output deterministic for same curated input
- rule lineage is queryable for explain UI
- all endpoints pass contract tests
