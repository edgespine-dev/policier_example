# explainability_api_ui

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`
- `app/templates/agent/policier/api.py` (`/explain` baseline)

## Purpose
Visa hur resultatet blev till: input -> artefakter -> prompt -> evaluation.

## Why this component exists
Explainability är ett kärnkrav. Utan detta blir artefaktkedjan svår att lita på och demonstrera pedagogiskt.

## Scope
- API för run/steg/artefaktvyer.
- UI som speglar pipeline-steg.
- Visa faktiskt skickad prompt och dess lineage.

## Out of scope
- Komplett historikbrowser över alla promptversioner.
- Avancerad BI/analysplattform.

## Reuse from existing implementation
- Bygg vidare på befintlig `/explain` sida i `api.py`.
- Återanvänd befintligt endpointupplägg för snabb stegvis debug.

## Deployment boundary
- Kan deployas separat som read-only explain-service.
- Minsta deploy-enhet: `/v1/explain/*` + UI-route.

## Inputs
- `run_id`
- valfritt filter: `topic`, `status`, tid

## Outputs
- run-översikt
- stegdetaljer
- artefaktlineage
- UI-flikar

## Artifact contracts
Create/ensure-bas:
- Ej primärt relevant för denna read-tunga komponent i v1.
- **Explicit not relevant:** Explainability API skapar normalt inte domänartefakter.

Read-bas:
```json
{
  "run_id":"uuid",
  "step":"explainability_api_ui",
  "status":"available|not_found|partial",
  "artifacts":{"run":{},"steps":[],"artifacts":[]},
  "validity":{"is_valid":true,"reason":"projection_current","fingerprint":"exp_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `prompt_lineage`
- `source_trace`

## REST/API contracts
- `GET /v1/explain/runs`
- `GET /v1/explain/runs/{run_id}`
- `GET /v1/explain/runs/{run_id}/steps/{step}`
- `GET /v1/explain/runs/{run_id}/artifacts/{artifact_type}`
- `GET /v1/explain/runs/{run_id}/prompt-lineage`
- `GET /v1/explain/ui`

Wrapper/kompatibilitet:
- Befintlig `/explain` lever kvar som baslinje och mappar till nya read-endpoints.

## Data model / DB interaction
Läser:
- `policy_runs`
- `policy_step_traces`
- `policy_file_decisions`
- `policy_source_blobs`
- `policy_snippets`
- `policy_assemblies`
- `policy_prompts`
- `policy_evaluations`
- `policy_findings_recommendations`

Skriver:
- **Explicit not relevant i v1:** Ingen domändataskrivning krävs.

## Dependencies
- Alla producerande artefaktkomponenter.
- `persistence_invalidation` för effektiva readmönster/index.

## Build-order dependency
- Efter att read-kontrakt för artefakter är låsta.

## Runtime dependency
- Endast beroende av att artefakter finns.

## Caching / reuse
- Kortlivad read-cache är tillåten.
- Inga nya AI-körningar i explain-lagret.

## Validity / invalidation
- Följer underliggande artefakters validitet.
- Om data saknas ska status vara `partial`/`not_found`, inte dold fallback.

## Error handling
- Robust partial rendering.
- Tydlig felpanel i UI med `warnings` och `errors`.

## Test-first execution plan
Fas 1:
- JSON expected för run/steg/artifact endpoints.
- UI-smoke mot seedad testdata.

Fas 2:
- Koppla full artefaktkedja och verifiera lineage-visning.

## Example test I/O
Input (`tests/io/explain/run.read.json`):
```json
{"request":"GET /v1/explain/runs/r1"}
```
Expected (`tests/io/explain/run.read.expected.json`):
```json
{"status":"available","step":"explainability_api_ui"}
```

## Implementation outline
1. Lås read-kontrakt per flik.
2. Implementera `/v1/explain/*`.
3. Refaktorera befintlig `/explain` till kanonisk stegvis vy.

## Deliverables
- Explainability API
- Uppdaterad `/explain` UI
- Kontraktstester + UI-smoke

## What can be implemented in parallel
- Kan byggas parallellt med nästan alla komponenter så snart read-kontrakt finns.

## Open questions / assumptions
1. **Open question:** Om prompttext behöver maskeras i framtida miljöer.
2. **Assumption:** Full prompttext kan visas internt i v1.
