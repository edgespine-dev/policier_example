# policy_assembly

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/policy_pipeline.py`

## Purpose
Bygga återanvändbar human-readable policy från materialiserade snippets.

## Why this component exists
Separat policyartefakt gör promptbygge enklare, förbättrar explainability och minskar AI-körningar.

## Scope
- Konsumera snippets.
- Generera policytext + struktur.
- Spara policyartefakt med lineage.

## Out of scope
- Avancerad semantisk normalisering.
- Historisk policy-diffanalys över tid.

## Reuse from existing implementation
- Återanvänd befintligt `rules`-spår som övergångsinput där relevant.
- Återanvänd merge-idéer från `policy_pipeline.py`.

## Deployment boundary
- Kan deployas separat som policy-agent.
- Minsta deploy-enhet: policy create/read/ensure.

## Inputs
- `run_id`
- `topic`
- `snippet_set_id` eller `snippet_ids[]`
- `assembly_version`
- `force_refresh`

## Outputs
- `policy_id`
- `policy_text`
- `sections`
- `source_snippet_ids[]`

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"policy_assembly",
  "status":"completed|failed",
  "artifact_ids":{"policy_id":"..."},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"fingerprint_match","fingerprint":"pol_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"policy_assembly",
  "status":"available|not_found|stale",
  "artifacts":{"policy_id":"...","policy_text":"..."},
  "validity":{"is_valid":true,"reason":"policy_present","fingerprint":"pol_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `sections`
- `source_snippet_ids`

## REST/API contracts
- `POST /v1/policies:create`
- `GET /v1/policies?run_id=<id>&topic=<topic>`
- `POST /v1/policies:ensure`
- `GET /v1/policies/{policy_id}`

## Data model / DB interaction
Läser:
- `policy_snippets`

Skriver:
- `policy_assemblies` (ny)
- `policy_step_traces`
- `policy_cache_entries`

## Dependencies
- `snippet_extraction`
- `persistence_invalidation`

## Build-order dependency
- Efter låst snippetkontrakt.

## Runtime dependency
- Kräver snippets från `snippet_extraction`.

## Caching / reuse
- Återanvänd policy om snippet-fingerprint + assembly_version matchar.

## Validity / invalidation
- Ogiltig om snippets/topichash/assembly_version ändras.

## Error handling
- Saknade snippets -> `dependency_missing`.
- Tom policyoutput -> `policy_empty`.

## Test-first execution plan
Fas 1:
- JSON kontraktstester för policy create/read/ensure.
- Exakt jämförelse för deterministisk policystruktur där rimligt.

Fas 2:
- Koppla full kedja från snippets och säkerställ cachebeteende.

## Example test I/O
Input (`tests/io/policy/create.json`):
```json
{"run_id":"r1","topic":"secrets_bootstrap_dr","snippet_set_id":"s1"}
```
Expected (`tests/io/policy/create.expected.json`):
```json
{"status":"completed","step":"policy_assembly","artifact_ids":{"policy_id":"*"}}
```

## Implementation outline
1. Definiera policy-tabell.
2. Implementera assembler.
3. Implementera create/read/ensure.
4. Lägg till validity och traces.

## Deliverables
- Policy-agent API
- Materialiserad policyartefakt
- Kontraktstester

## What can be implemented in parallel
- Kan byggas parallellt med `prompt_generation` efter låst policykontrakt.

## Open questions / assumptions
1. **Assumption:** Deterministisk assembly prioriteras i v1.
2. **Assumption:** Eventuellt lätt AI-stöd för läsbarhet utvärderas först efter v1.
