# orchestrator_run_control

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/api.py`

## Purpose
Koordinera run-livscykel och skapa en tydlig ingång för create/read/ensure över hela artefaktkedjan.

## Why this component exists
Utan en orchestrator blir beroendehantering, status och bakåtmaterialisering otydlig och svår att testa.

## Scope
- Starta run via REST.
- Köra stegvis eller full kedja.
- Hantera `:ensure` från sent steg.
- Skriva run/stegstatus.

## Out of scope
- Schemaläggning (cron/extern scheduler).
- Avancerad changed-run-motor.
- Modellspecifik promptoptimering.

## Reuse from existing implementation
- `GET /policy_pipeline*` och `GET /policy` som wrapper-bas.
- FastAPI-lager i `app/templates/agent/policier/api.py`.

## Deployment boundary
- Kan deployas som egen modul/tjänst.
- Minsta deploy-enhet: run-controller API + access till gemensam DB-modell.

## Inputs
- `topic`
- `trigger_type`
- `run_id` (vid resume/cancel/step)
- `target_step`
- `force_refresh`
- tidsbudget

## Outputs
- run-status
- stegstatus
- artifact_ids per steg
- warnings/errors

## Artifact contracts
Gemensam create/ensure-bas:
```json
{
  "run_id": "uuid",
  "step": "orchestrator_run_control",
  "status": "completed|failed|timed_out|partial",
  "artifact_ids": {},
  "used_cache": false,
  "validity": {"is_valid": true, "reason": "orchestrator_state", "fingerprint": "run_state_v1"},
  "warnings": [],
  "errors": []
}
```

Gemensam read-bas:
```json
{
  "run_id": "uuid",
  "step": "orchestrator_run_control",
  "status": "available|not_found|stale",
  "artifacts": {"run": {}},
  "validity": {"is_valid": true, "reason": "state_present", "fingerprint": "run_state_v1"},
  "warnings": []
}
```

Steg-specifik extension:
- `stage_map`
- `next_actions`

## REST/API contracts
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `POST /v1/runs/{run_id}/steps/{step}:create`
- `POST /v1/runs/{run_id}/steps/{step}:ensure`
- `POST /v1/runs/{run_id}/resume`
- `POST /v1/runs/{run_id}/cancel`

Wrapper/kompatibilitet:
- `/policy_pipeline*` och `/policy` lever vidare som wrappers.

## Data model / DB interaction
Läser:
- `policy_runs`
- `policy_step_traces`
- alla stegtabeller för read/ensure-status

Skriver:
- `policy_runs`
- `policy_step_traces`

## Dependencies
- `persistence_invalidation`
- samtliga stegkomponenter i artefaktkedjan

## Build-order dependency
- Bygger efter att create/read/ensure-kontrakt och stegkontrakt är låsta.
- Slutintegration efter att stegkomponenter har kontraktstester.

## Runtime dependency
- Kan starta direkt på sent steg men kräver att den kan kalla respektive `:ensure` uppströms.

## Caching / reuse
- Ingen egen domäncache.
- Aggreggerar `used_cache` från underliggande steg.

## Validity / invalidation
- Förlitar sig på stegens validitetsbedömning.
- Orchestrator-validitet gäller run-state, inte domänartefakters innehåll.

## Error handling
- Standardiserade `errors[]` med `error_code`.
- Klassificering: `validation_error`, `dependency_missing`, `timeout`, `storage_error`, `ai_error`.

## Test-first execution plan
Fas 1:
- Lås endpointkontrakt för `runs/create/read/ensure/resume/cancel`.
- JSON testinput/expected för statusflöden.
- Stubs för stegkomponenter.

Fas 2:
- Integrera verkliga steg tills tester går grönt i tre nivåer.

## Example test I/O
Input (`tests/io/orchestrator/run_create.json`):
```json
{"topic":"secrets_bootstrap_dr","trigger_type":"manual","target_step":"topic_evaluation"}
```
Expected (`tests/io/orchestrator/run_create.expected.json`):
```json
{"status":"completed","step":"orchestrator_run_control"}
```

## Implementation outline
1. Implementera run state-machine.
2. Implementera create/read/ensure dispatch.
3. Lägg till wrapper-mappning för legacy endpoints.
4. Integrera fel-/timeout-hantering.

## Deliverables
- Orchestrator API-kontrakt
- Run-statehantering
- Kompatibilitetswrappers
- Tester (endpoint + komponent)

## What can be implemented in parallel
- Kan utvecklas parallellt med `explainability_api_ui` och `test_harness`.
- Slutkoppling mot steg görs efter att stegkontrakt är låsta.

## Open questions / assumptions
1. **Assumption:** Synkron run-körning via REST räcker i v1.
2. **Assumption:** Asynkron kö är uttryckligen utanför v1 och hanteras först efter att kärnflödet är grönt.
