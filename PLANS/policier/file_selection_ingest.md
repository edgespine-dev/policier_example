# file_selection_ingest

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/policy_collector.py`
- `app/templates/agent/policier/sql/002_add_source_blob_and_rules.sql`

## Purpose
Materialisera filurval och dokument i DB som start på artefaktkedjan.

## Why this component exists
Nedströms AI-steg måste få ett stabilt och spårbart dokumentunderlag.

## Scope
- File selection (included/excluded + reasons).
- Document ingest (fulltext + metadata i DB).
- Koppla run till documents.

## Out of scope
- Full changed-run-optimering.
- Multi-format-ingest utöver rimlig v1-nivå.

## Reuse from existing implementation
- Återanvänd scanning/filter i `policy_collector.py`.
- Återanvänd nuvarande `policy_source_blobs`-spår i SQL.

## Deployment boundary
- Kan deployas separat som selection/ingest-agent.
- Minsta deploy-enhet: file selection + document ingest endpoints.

## Inputs
- `run_id`
- `base_dir`
- `file_selection_rules_hash`
- `trigger_type`
- `force_refresh`

## Outputs
- `selection_id`
- included/excluded listor
- dokumentreferenser (`source_blob_id`, `file_path`, `file_hash`)
- `source_set_hash`

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"file_selection_ingest",
  "status":"completed|failed|partial",
  "artifact_ids":{"selection_id":"...","source_blob_ids":["..."]},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"fingerprint_match","fingerprint":"sel_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"file_selection_ingest",
  "status":"available|not_found|stale",
  "artifacts":{"included":[],"excluded":[],"documents":[]},
  "validity":{"is_valid":true,"reason":"selection_present","fingerprint":"sel_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `excluded[].reasons`
- `source_set_hash`

## REST/API contracts
- `POST /v1/files/selection:create`
- `GET /v1/files/selection?run_id=<id>`
- `POST /v1/files/selection:ensure`
- `POST /v1/documents:create`
- `GET /v1/documents?run_id=<id>`
- `POST /v1/documents:ensure`

Wrapper/kompatibilitet:
- `/policy_files`, `/policy_files/excluded`, `/policy_pipeline/files`.

## Data model / DB interaction
Läser:
- `policy_runs`
- `policy_source_blobs`

Skriver:
- `policy_file_decisions` (ny)
- `policy_source_blobs` (befintlig)
- `policy_run_sources` (befintlig)
- `policy_step_traces`

## Dependencies
- `config_catalog`
- `persistence_invalidation`

## Build-order dependency
- Efter `config_catalog` och `persistence_invalidation`.

## Runtime dependency
- Körs före `snippet_extraction`.

## Caching / reuse
- Blob-dedup via `file_path + file_hash`.
- Återanvänd tidigare blobs när hash matchar.

## Validity / invalidation
- Ogiltig vid ändrad filterhash eller ändrad dokumenthash.
- `force_refresh` får köra om selection utan att duplicera blobs.

## Error handling
- Saknad `base_dir` -> `not_found`/felkod.
- I/O/decode-problem -> warning där möjligt, fail endast vid blockerande fel.

## Test-first execution plan
Fas 1:
- JSON testinput/expected för selection/documents create/read/ensure.
- Assertioner för exkluderingsorsaker och source_set_hash.

Fas 2:
- Integrera scanning + DB persistens.

## Example test I/O
Input (`tests/io/file_selection/create.json`):
```json
{"run_id":"r1","base_dir":"/workspace"}
```
Expected (`tests/io/file_selection/create.expected.json`):
```json
{"status":"completed","step":"file_selection_ingest","artifact_ids":{"selection_id":"*"}}
```

## Implementation outline
1. Definiera `policy_file_decisions`.
2. Implementera selection med reasons.
3. Implementera document ingest till `policy_source_blobs`.
4. Implementera read/create/ensure endpoints.

## Deliverables
- Selection/ingest API
- Artefaktpersistens
- Kontraktstester

## What can be implemented in parallel
- Kan byggas parallellt med `snippet_extraction` efter att artifact contract låsts.

## Open questions / assumptions
1. **Assumption:** `.md` räcker som initialt scope i v1.
2. **Assumption:** Eventuellt stöd för fler filtyper tas i senare fas och påverkar inte v1-kontrakten.
