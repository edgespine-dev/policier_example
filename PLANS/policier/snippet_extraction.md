# snippet_extraction

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/policy_pipeline.py`
- `app/templates/agent/policier/policy_runner.py`

## Purpose
Materialisera topic-relevanta snippets från dokument med AI-loop (extract/verify/revise) och återanvänd dem.

## Why this component exists
Detta är kärnsteget för kvalitet och kostnad. Om snippets inte materialiseras tvingas AI köra om i onödan.

## Scope
- Konsumera document blobs.
- Köra AI-loop per dokument.
- Spara snippets + lineage.
- Exponera read/create/ensure.

## Out of scope
- Perfekt rad-för-rad-spårning i alla lägen.
- Avancerad topic-specifik speciallogik per topic.

## Reuse from existing implementation
- Återanvänd curationlogik från `policy_pipeline.py`.
- Återanvänd extract/verify/revise-mönster från `policy_runner.py`.

## Deployment boundary
- Kan deployas separat som snippet-agent.
- Minsta deploy-enhet: snippet create/read/ensure + modeladapter.

## Inputs
- `run_id`
- `topic`
- `model`
- `verifier_model` (valfritt)
- `source_blob_ids[]`
- `topic_version_hash`
- `step_version`
- `force_refresh`

## Outputs
- `snippet_ids[]`
- `snippet_set_id`
- summary (`processed_new`, `cache_hits`, `timed_out`)

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"snippet_extraction",
  "status":"completed|failed|timed_out|partial",
  "artifact_ids":{"snippet_set_id":"...","snippet_ids":["..."]},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"fingerprint_match","fingerprint":"snip_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"snippet_extraction",
  "status":"available|not_found|stale",
  "artifacts":{"snippet_set_id":"...","items":[]},
  "validity":{"is_valid":true,"reason":"snippets_present","fingerprint":"snip_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `items[].source_blob_id`
- `items[].source_refs` (lista källor; radintervall när rimligt)
- `items[].relevant`

## REST/API contracts
- `POST /v1/snippets:create`
- `GET /v1/snippets?run_id=<id>&topic=<topic>`
- `POST /v1/snippets:ensure`
- `GET /v1/snippets/{snippet_id}`

Wrapper/kompatibilitet:
- `/policy_pipeline/curate` mappas hit.

## Data model / DB interaction
Läser:
- `policy_source_blobs`
- `policy_run_sources`

Skriver:
- `policy_snippets` (ny)
- `policy_step_traces`
- `policy_cache_entries`

## Dependencies
- `file_selection_ingest`
- `config_catalog`
- `persistence_invalidation`

## Build-order dependency
- Efter att documents-kontrakt är låst och testat.

## Runtime dependency
- Kräver dokumentartefakter från `file_selection_ingest`.

## Caching / reuse
- Fingerprint på `topic + source_blob_hash + model + step_version`.
- Cache-hit ska hoppa över AI-körning.

## Validity / invalidation
- Ogiltig om input-hash, topichash, model eller stepversion ändras.

## Error handling
- Modell-timeout -> `partial`/`timed_out` där möjligt.
- Parsefel -> warning + fallback-parser.
- Kontraktsbrott i output -> error med tydlig felkod.

## Test-first execution plan
Fas 1:
- JSON kontraktstester för snippet create/read/ensure.
- Stubbat modellager.
- Judge-baserad acceptans för icke-deterministiska outputfall.

Fas 2:
- Aktivera verkligt modelanrop och optimera cacheträffar.

## Example test I/O
Input (`tests/io/snippets/create.json`):
```json
{"run_id":"r1","topic":"secrets_bootstrap_dr","model":"qwen2.5:7b"}
```
Expected (`tests/io/snippets/create.expected.json`):
```json
{"status":"completed","step":"snippet_extraction","artifact_ids":{"snippet_set_id":"*"}}
```

## Implementation outline
1. Definiera `policy_snippets`.
2. Flytta curation till DB-materialiserat flöde.
3. Implementera create/read/ensure + wrapper.
4. Lägg till trace och validity.

## Deliverables
- Snippet-agent API
- Materialiserade snippets med lineage
- Kontraktstester + AI-judge testfall

## What can be implemented in parallel
- Kan byggas parallellt med `policy_assembly` när snippet-contract är låst.

## Open questions / assumptions
1. **Open question:** Exakt modellstrategi per steg i on-prem.
2. **Assumption:** Source-lista är tillräcklig lineage i v1 när exakt radspårning saknas.
