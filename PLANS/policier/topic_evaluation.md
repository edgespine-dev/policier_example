# topic_evaluation

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/policy_runner.py`

## Purpose
Köra generell topic-evaluation och materialisera resultat med findings/recommendations.

## Why this component exists
Detta är kontrollsteget som användaren vill ha svar från: vad är fel, varför, och vad bör göras.

## Scope
- Konsumera aktuell prompt.
- Köra evaluation mot modell.
- Spara evaluation + findings/recommendations.
- Exponera read/create/ensure.

## Out of scope
- Tvingad djup normalisering av findings/recommendations i v1.
- Topic-specifika separata kodvägar som standard.

## Reuse from existing implementation
- Återanvänd loop- och verifieringsmönster från `policy_runner.py`.
- Återanvänd `/policy` som wrapper-spår under migrering.

## Deployment boundary
- Kan deployas separat som evaluation-agent.
- Minsta deploy-enhet: evaluation create/read/ensure.

## Inputs
- `run_id`
- `topic`
- `prompt_id`
- `model`
- `force_refresh`

## Outputs
- `evaluation_id`
- `result`
- `findings`
- `recommendations`

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"topic_evaluation",
  "status":"completed|failed|timed_out|partial",
  "artifact_ids":{"evaluation_id":"..."},
  "used_cache":true,
  "validity":{"is_valid":true,"reason":"fingerprint_match","fingerprint":"eval_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"topic_evaluation",
  "status":"available|not_found|stale",
  "artifacts":{"evaluation_id":"...","result":{},"findings":[],"recommendations":[]},
  "validity":{"is_valid":true,"reason":"evaluation_present","fingerprint":"eval_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `acceptance_notes`
- `judge_summary` (om judge-test används)

## REST/API contracts
- `POST /v1/evaluations:create`
- `GET /v1/evaluations?run_id=<id>&topic=<topic>`
- `POST /v1/evaluations:ensure`
- `GET /v1/evaluations/{evaluation_id}`
- `GET /v1/evaluations/{evaluation_id}/findings`
- `GET /v1/evaluations/{evaluation_id}/recommendations`

Wrapper/kompatibilitet:
- `/policy` mappas gradvis till `evaluations:ensure`.

## Data model / DB interaction
Läser:
- `policy_prompts`
- `policy_assemblies`

Skriver:
- `policy_evaluations` (ny)
- `policy_findings_recommendations` (ny, enkel JSONB/struktur i v1)
- `policy_step_traces`
- `policy_cache_entries`

## Dependencies
- `prompt_generation`
- `persistence_invalidation`

## Build-order dependency
- Efter låst promptkontrakt.

## Runtime dependency
- Kräver promptartefakt.

## Caching / reuse
- Återanvänd evaluation när prompt/model/step-fingerprint matchar.

## Validity / invalidation
- Ogiltig om prompt ändras, modell ändras eller stepversion ändras.

## Error handling
- Modelltimeout -> `timed_out`.
- Parse/formatfel -> `partial` + error.
- Saknad prompt -> `dependency_missing`.

## Test-first execution plan
Fas 1:
- JSON kontraktstester.
- Judge-baserad acceptans för icke-deterministisk output.
- Exakta assertions för obligatoriska fält.

Fas 2:
- Integrera skarp modellkörning och cache.

## Example test I/O
Input (`tests/io/evaluation/create.json`):
```json
{"run_id":"r1","topic":"secrets_bootstrap_dr","prompt_id":"pr1","model":"qwen2.5:7b"}
```
Expected (`tests/io/evaluation/create.expected.json`):
```json
{"status":"completed","step":"topic_evaluation","artifact_ids":{"evaluation_id":"*"}}
```

## Implementation outline
1. Definiera evaluation-tabeller (enkel v1).
2. Implementera create/read/ensure.
3. Integrera modeladapter + felhantering.
4. Lägg till wrapper för `/policy`.

## Deliverables
- Evaluation-agent API
- Materialiserade evaluationartefakter
- Kontraktstester + judge-strategi

## What can be implemented in parallel
- Kan utvecklas parallellt med `explainability_api_ui` efter låst evaluation-kontrakt.

## Open questions / assumptions
1. **Open question:** Hur mycket findings/recommendations som ska normaliseras senare.
2. **Assumption:** Enkel JSONB/strukturerad payload är rätt v1-nivå.
