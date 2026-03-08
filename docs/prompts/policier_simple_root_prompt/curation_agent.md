# Component Plan: curation_agent

## 1. Scope
Perform per-file extract -> verify -> revise loops and classify relevance.

Based on current logic in `policy_pipeline.py` (`curate_topic_per_file`) and `policy_runner.py`.

## 2. Responsibilities
- load topic config and prompts
- execute curation loop with bounded iterations/timeouts
- mark each file as relevant/non-relevant
- emit structured curation payload and step traces

## 3. Endpoint Set
1. `POST /v1/agents/curation/run`
- request: `run_id`, `topic`, `model`, `max_iterations`, `budget_seconds`, `per_call_timeout_seconds`, `max_file_chars`, `force_refresh`
- response: curated list + stats

2. `POST /v1/agents/curation/file`
- request: one file snapshot + topic/model
- response: one curated payload

3. `GET /v1/agents/curation/run/{run_id}`
- response: persisted curation rows and trace summary

Compatibility wrappers:
- map existing `/policy_pipeline/curate`, `/policy_extract`, `/policy_verify`, `/policy_revise`.

## 4. DB Schema and Tables
Schema owner: `curation_agent` agent schema per test run.

Tables:
- `policy_step_traces` (existing): `curate_extract`, `curate_verify`, `curate_revise`
- `policy_cache_entries` (existing): stage `curate`
- `policy_curations` (new): normalized per-file curation outputs

`policy_curations` columns:
- `id bigserial pk`
- `run_id uuid`
- `file_path text`
- `file_hash text`
- `candidate_json jsonb`
- `verification_json jsonb`
- `relevant boolean`
- `iteration_count int`
- `timed_out boolean`
- `created_at timestamptz`

## 5. Input/Output Contracts
Output row shape per file:
```json
{
  "file": "/docs/X.md",
  "topic": "secrets_bootstrap_dr",
  "candidate": {
    "relevant": true,
    "summary": "...",
    "evidence": ["..."]
  },
  "verification": {
    "status": "COMPLETE",
    "relevant": true,
    "missing_items": []
  }
}
```

## 6. Test Cases
1. `tc_curation_complete_first_pass`
- verifier returns `COMPLETE` without revise

2. `tc_curation_requires_revise`
- at least one revise iteration before `COMPLETE`

3. `tc_curation_timeout`
- time budget hit sets `timed_out=true`

4. `tc_curation_parse_non_json_model_output`
- parser fallback extracts JSON block safely

5. `tc_curation_cache_hit`
- second run uses cache entries

## 7. Done Criteria
- every file has traceability for extract/verify/revise
- timeout behavior is deterministic and tested
- relevance classification is persisted and queryable
