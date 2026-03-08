# prompt_generation

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/topic_catalog.py`
- `app/templates/agent/policier/topics.json`

## Purpose
Bygga och materialisera den aktuella prompten från policyartefakten med tydlig lineage.

## Why this component exists
Prompten är bryggan mellan policy och evaluation. Utan materialisering blir kostnad och explainability sämre.

## Scope
- Rendera prompts från policy + topic/template.
- Spara aktuell prompt med metadata.
- Exponera read/create/ensure.

## Out of scope
- Full prompt-historik över tid (inte krav i v1).
- Avancerad promptoptimering per modellfamilj.

## Reuse from existing implementation
- Återanvänd templatehantering i `topic_catalog.py`.
- Återanvänd promptfält och `/topics?prompts=true` som bas.

## Deployment boundary
- Kan deployas separat som prompt-agent.
- Minsta deploy-enhet: prompt create/read/ensure.

## Inputs
- `run_id`
- `topic`
- `policy_id`
- `template_version`
- `model_target` (valfritt)
- `force_refresh`

## Outputs
- `prompt_id`
- `prompt_text` (faktiskt skickad)
- `prompt_lineage`

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"prompt_generation",
  "status":"completed|failed",
  "artifact_ids":{"prompt_id":"..."},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"fingerprint_match","fingerprint":"prm_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"prompt_generation",
  "status":"available|not_found|stale",
  "artifacts":{"prompt_id":"...","prompt_text":"..."},
  "validity":{"is_valid":true,"reason":"prompt_present","fingerprint":"prm_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `prompt_lineage` (policy_id, snippet_ids, source_refs, template_version)

## REST/API contracts
- `POST /v1/prompts:create`
- `GET /v1/prompts?run_id=<id>&topic=<topic>`
- `POST /v1/prompts:ensure`
- `GET /v1/prompts/{prompt_id}`

## Data model / DB interaction
Läser:
- `policy_assemblies`
- `policy_snippets` (för lineage)

Skriver:
- `policy_prompts` (ny)
- `policy_step_traces`
- `policy_cache_entries`

## Dependencies
- `policy_assembly`
- `config_catalog`
- `persistence_invalidation`

## Build-order dependency
- Efter låst policykontrakt.

## Runtime dependency
- Kräver policyartefakt från `policy_assembly`.

## Caching / reuse
- Återanvänd prompt om policy/template/topic/model-fingerprint matchar.

## Validity / invalidation
- Ogiltig om policyhash, templateversion, topichash eller modellprofil ändras.

## Error handling
- Saknad policy -> `dependency_missing`.
- Template-renderfel -> `template_render_error`.

## Test-first execution plan
Fas 1:
- JSON kontraktstester för prompt create/read/ensure.
- Exakt validering av obligatoriska lineage-fält.

Fas 2:
- Integrera med evaluation och `/explain`.

## Example test I/O
Input (`tests/io/prompts/create.json`):
```json
{"run_id":"r1","topic":"secrets_bootstrap_dr","policy_id":"p1"}
```
Expected (`tests/io/prompts/create.expected.json`):
```json
{"status":"completed","step":"prompt_generation","artifact_ids":{"prompt_id":"*"}}
```

## Implementation outline
1. Definiera `policy_prompts`.
2. Implementera template->prompt rendering.
3. Implementera create/read/ensure.
4. Lägg till lineage-fält i svar och lagring.

## Deliverables
- Prompt-agent API
- Aktuell prompt + lineage i DB
- Kontraktstester

## What can be implemented in parallel
- Kan byggas parallellt med `topic_evaluation` efter låst promptkontrakt.

## Open questions / assumptions
1. **Open question:** Behövs små modellspecifika promptvarianter i on-prem.
2. **Assumption:** Prompt-historik över tid är inte krav i v1.
