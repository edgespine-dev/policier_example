# config_catalog

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/topic_catalog.py`
- `app/templates/agent/policier/topics.json`
- `app/templates/agent/policier/policy_collector.py`

## Purpose
Leverera topics, prompttemplates och file-selection-regler som stabil katalogdata med version/hash.

## Why this component exists
Alla andra steg behöver samma configkälla för konsekventa beslut och validitet.

## Scope
- Läsa topics från fil.
- Läsa include/exclude-regler från fil.
- Exponera config via REST.
- Beräkna versionshashar.

## Out of scope
- Config-CRUD i Postgres.
- Avancerad confighistorik.

## Reuse from existing implementation
- Återanvänd parserlogik i `topic_catalog.py`.
- Återanvänd filterladdning från `policy_collector.py`.

## Deployment boundary
- Kan deployas separat som ren config-tjänst.
- Minsta deploy-enhet: read-only config API.

## Inputs
- `app/templates/agent/policier/topics.json`
- `.agent/merge_policy_exclude.json` eller motsvarande
- `base_dir` (valfritt)

## Outputs
- topics
- prompttemplates per topic
- active filter config
- `topic_catalog_hash`
- `file_selection_rules_hash`

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"config_catalog",
  "status":"completed|failed",
  "artifact_ids":{"config_version":"hash"},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"config_loaded","fingerprint":"cfg_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"config_catalog",
  "status":"available|not_found",
  "artifacts":{"topics":[],"file_selection_rules":{}},
  "validity":{"is_valid":true,"reason":"config_present","fingerprint":"cfg_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `topic_catalog_hash`
- `file_selection_rules_hash`

## REST/API contracts
- `GET /v1/config/topics`
- `GET /v1/config/topics/{topic}`
- `GET /v1/config/topics/{topic}/prompts`
- `GET /v1/config/file-selection`
- `GET /v1/config/version`

## Data model / DB interaction
- Primärt filbaserat i v1.
- DB-interaktion: inte nödvändig i v1.
- Om DB används senare: endast snapshot/audit.

## Dependencies
- `persistence_invalidation` endast för gemensam hash/validity-util om den centraliseras.

## Build-order dependency
- Tidigt i buildordning, före steg som kräver topichash/filterhash.

## Runtime dependency
- Körs/läses före `file_selection_ingest` och AI-steg.

## Caching / reuse
- In-memory cache per process.
- Hash används som versionsnyckel mot nedströms artefakter.

## Validity / invalidation
- Config giltig per processlivstid i v1.
- Byte av filinnehåll ger ny hash och ogiltigförklarar nedströms artefakter.

## Error handling
- Ogiltig config -> `validation_error`.
- Saknad policyfil -> fallback/default + warning.

## Test-first execution plan
Fas 1:
- JSON tests för topics/filter/version-endpoints.
- Testfall för loose JSON i filterfil.

Fas 2:
- Runtime-koppling till stegkomponenter.

## Example test I/O
Input (`tests/io/config/topics.read.json`):
```json
{"request":"GET /v1/config/topics"}
```
Expected (`tests/io/config/topics.read.expected.json`):
```json
{"status":"available","step":"config_catalog"}
```

## Implementation outline
1. Extrahera och stabilisera parserfunktioner.
2. Lägg till hashberäkning.
3. Implementera read-endpoints och kontraktstester.

## Deliverables
- Config API
- Hash/version-kontrakt
- Tester för config-laddning

## What can be implemented in parallel
- Kan implementeras parallellt med `persistence_invalidation` och `test_harness`.

## Open questions / assumptions
1. **Assumption:** Topics och filter ligger kvar i filer i v1.
2. **Assumption:** Config reload sker via processrestart i v1.
