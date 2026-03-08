# Component Plan: source_collector

## 1. Scope
Collect policy markdown files using exclusion policy, then produce file/hash/source snapshots.

Based on current logic in `policy_collector.py` and `/policy_pipeline/files`.

## 2. Responsibilities
- detect base dir (`POLICY_BASE_DIR` or explicit)
- apply merge exclusion policy
- return included/excluded file lists
- snapshot source blobs for downstream agents

## 3. Endpoint Set
1. `GET /v1/agents/source/files`
- params: `base_dir?`
- response: included file list, count

2. `GET /v1/agents/source/files/excluded`
- params: `base_dir?`
- response: excluded file list

3. `POST /v1/agents/source/snapshot`
- request: `run_id`, `test_case_id`, `base_dir?`, `repo_commit?`
- response: `source_blob_ids`, file metadata

4. `GET /v1/agents/source/snapshot/{run_id}`
- response: snapshot rows for run

Compatibility wrappers:
- map existing `/policy_files`, `/policy_files/excluded`, `/policy_pipeline/files`.

## 4. DB Schema and Tables
Schema owner: `source_collector` agent schema per test run.

Tables:
- `policy_run_sources` (existing)
- `policy_source_blobs` (existing)

Data stored:
- file path, file hash, size, include reason
- full file content snapshot in `policy_source_blobs.content_text`
- optional `repo_commit` in metadata

## 5. Input/Output Contracts
Input:
```json
{
  "run_id": "uuid",
  "test_case_id": "tc_source_smoke",
  "base_dir": "/workspace"
}
```

Output:
```json
{
  "run_id": "uuid",
  "files_count": 42,
  "source_blobs": [
    {"source_blob_id": "uuid", "file_path": "/docs/A.md", "file_hash": "..."}
  ]
}
```

## 6. Test Cases
1. `tc_source_respects_exclusions`
- excluded files never appear in included list

2. `tc_source_blob_dedup`
- same file/hash not duplicated

3. `tc_source_unicode_decode`
- invalid utf-8 handled with replacement, no crash

4. `tc_source_large_repo_limit`
- performance under many markdown files

5. `tc_source_snapshot_repeatability`
- same input produces same hashes

## 7. Done Criteria
- deterministic file ordering
- deterministic hashing
- snapshot rows are queryable by run id
