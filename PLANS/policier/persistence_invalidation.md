# persistence_invalidation

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/sql/001_init_policy_explain.sql`
- `app/templates/agent/policier/sql/002_add_source_blob_and_rules.sql`
- `app/templates/agent/policier/*`
- `docs/APP_DB_POLICY.md`

## Purpose
Säkra gemensam DB-bas, migrationsflöde och enkel fingerprint-baserad validitet för alla artefakter.

## Why this component exists
Utan stabil DB- och validitetsmodell kan inte create/read/ensure fungera konsekvent mellan agenter.

## Scope
- DB-anslutning och migrationer.
- Gemensamma tabeller/index.
- Fingerprint/validity-regler.
- Testschema-isolering.

## Out of scope
- Multi-database stöd.
- Komplex dataretentionpolicy i v1.

## Reuse from existing implementation
- Återanvänd SQL-bas i `001`/`002`.
- Återanvänd Postgres wiring i K8s overlays och ExternalSecret.
- Secret contract, bootstrap och security-regler är kanoniskt definierade i `docs/APP_DB_POLICY.md` och ska inte dupliceras här.

## Deployment boundary
- Kan vara separat intern modul/tjänst.
- Minsta deploy-enhet: migration + validity utility + DB-adapter.

## Inputs
- `POLICIER_DB_HOST`
- `POLICIER_DB_PORT`
- `POLICIER_DB_NAME`
- `POLICIER_DB_USER`
- `POLICIER_DB_PASSWORD`
- `POLICIER_DB_SSLMODE`
- schema-namn (runtime/test)

## Outputs
- migrerat schema
- validity beslut
- cache/invalidation metadata

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"persistence_invalidation",
  "status":"completed|failed",
  "artifact_ids":{"migration_batch":"..."},
  "used_cache":false,
  "validity":{"is_valid":true,"reason":"schema_ready","fingerprint":"db_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"persistence_invalidation",
  "status":"available|not_found",
  "artifacts":{"migrations":[],"validity_rules":{}},
  "validity":{"is_valid":true,"reason":"metadata_present","fingerprint":"db_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `applied_migrations`
- `schema_name`

## REST/API contracts
- `POST /v1/admin/migrations:apply`
- `GET /v1/admin/migrations`
- `GET /v1/admin/validity?artifact_type=...&artifact_id=...`
- `POST /v1/admin/cache:invalidate`

## Data model / DB interaction
Läser/skriver:
- existerande tabeller från `001`/`002`
- nya minimalt nödvändiga tabeller för kanonisk kedja:
  - `policy_file_decisions`
  - `policy_snippets`
  - `policy_assemblies`
  - `policy_prompts`
  - `policy_evaluations`
  - `policy_findings_recommendations`

## Dependencies
- Inga domänberoenden uppströms.
- Konsumeras av alla andra komponenter.

## Build-order dependency
- Först i buildordning.

## Runtime dependency
- Måste vara initierad innan övriga steg körs mot DB.

## Caching / reuse
- `policy_cache_entries` används som gemensam cache-registry.
- Validity bygger på fingerprints, inte på tidsbaserad gissning.

## Validity / invalidation
Minsta fingerprint-fält:
- `input_hash`
- `topic_version_hash`
- `template_version`
- `step_version`
- `model_id`

## Error handling
- DB-fel -> `storage_error`.
- Migrationsfel -> `migration_failed`.
- Ogiltigt schema -> `validation_error`.

## Test-first execution plan
Fas 1:
- kontraktstester för migration/validity endpoints.
- schemaisoleringstester med JSON testfall.

Fas 2:
- koppla full tabellmodell till stegkomponenter.

## Example test I/O
Input (`tests/io/persistence/migrate.json`):
```json
{"schema":"test_persist_a1"}
```
Expected (`tests/io/persistence/migrate.expected.json`):
```json
{"status":"completed","step":"persistence_invalidation"}
```

## Implementation outline
1. Implementera DB-adapter.
2. Implementera migrationsrunner.
3. Implementera validity utility.
4. Exponera admin-endpoints.

## Deliverables
- DB/migration-layer
- Validity/invalidation-regler
- Kontraktstester

## What can be implemented in parallel
- Kan byggas parallellt med `config_catalog` och `test_harness`.

## Open questions / assumptions
1. **Assumption:** PostgreSQL är enda persistent store i v1.
2. **Assumption:** Migrationer körs via explicit kontrollerat steg i v1.
