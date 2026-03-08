# test_harness

## Canonical references
- `PLANS/policier/policier_architecture.md`
- `PLANS/policier/agent_orchestration.md`

## Purpose
Vara den praktiska motor som låser kontrakt först och driver implementation tills hela kedjan blir grön.

## Why this component exists
Utan ett strikt testharness kan agent-swarm implementation divergera och skapa inkompatibla komponenter.

## Scope
- Definiera testordning och testlager.
- Stödja JSON input/expected.
- Stödja deterministisk och judge-baserad utvärdering.
- Hantera schemaisolerade testkörningar.

## Out of scope
- Last/prestandatestning som primärt mål i v1.
- Full CI-orkestrering av infra utanför Policier.

## Reuse from existing implementation
- Återanvänd befintliga endpointspår i `app/templates/agent/policier/api.py` för wrappertester.
- Återanvänd SQL-bas från repo för testschema-init.

## Deployment boundary
- Kan köras som separat testagent/CLI-jobb.
- Minsta deploy-enhet: test runner + schema setup utility.

## Inputs
- JSON testinputfiler
- JSON expected output-filer
- endpoint- och artifact-kontrakt
- testschema-prefix

## Outputs
- testreports
- assertionresultat
- lista över failade testfall

## Artifact contracts
Create/ensure-bas:
```json
{
  "run_id":"uuid",
  "step":"test_harness",
  "status":"completed|failed|partial",
  "artifact_ids":{"test_run_id":"..."},
  "used_cache":false,
  "validity":{"is_valid":true,"reason":"test_run_recorded","fingerprint":"test_v1"},
  "warnings":[],
  "errors":[]
}
```
Read-bas:
```json
{
  "run_id":"uuid",
  "step":"test_harness",
  "status":"available|not_found",
  "artifacts":{"test_run":{},"assertions":[]},
  "validity":{"is_valid":true,"reason":"report_present","fingerprint":"test_v1"},
  "warnings":[]
}
```
Steg-specifik extension:
- `failed_assertions`
- `judge_summary`

## REST/API contracts
- `POST /v1/tests/run`
- `POST /v1/tests/run/failed:rerun`
- `GET /v1/tests/runs/{test_run_id}`

Notering:
- Om testerna körs via CLI i stället är samma kontrakt och outputformat fortfarande kanoniska.

## Data model / DB interaction
Läser:
- samtliga domäntabeller beroende på testnivå

Skriver:
- `policy_test_runs` (rekommendation)
- `policy_test_assertions` (rekommendation)
- alternativt filbaserad report i tidig fas

## Dependencies
- `persistence_invalidation`
- alla stegkomponenters låsta kontrakt

## Build-order dependency
- Startar i fas 1 innan produktionsimplementation.
- Fortsätter under fas 2 tills alla nivåer är gröna.

## Runtime dependency
- Testkörning kan ske per komponent isolerat eller hela kedjan via orchestrator.

## Caching / reuse
- Ingen delad domäncache mellan tester.
- Varje test använder nytt schema för reproducerbarhet.

## Validity / invalidation
- Testdata gäller endast i eget testschema.
- Ny körning = nytt schema = ingen invalidation-krock.

## Error handling
- Setupfel klassas som `infrastructure_error`.
- Kontraktsbrott klassas som `contract_error`.
- AI-bedömningsfel klassas som `judge_rejected` när judge används.

## Test-first execution plan

### Fas 1: test- och kontraktsfas
Skapa först:
- endpointkontrakt
- artifact contracts
- JSON inputfiler
- JSON expected output-filer
- assertions
- testordning
- stubs där behövs

Verifiera i fas 1:
- create/read/ensure-konsekvens
- rimliga agentgränser
- fungerande artefaktkedja
- explainability-underlag

### Fas 2: implementering
Implementation börjar först när fas 1 är låst.

Fortsätt tills grönt på:
1. endpointtester
2. komponenttester
3. systemtester

## Example test I/O
Input (`tests/io/snippets/create.json`):
```json
{"run_id":"r1","topic":"secrets_bootstrap_dr","model":"stub-model"}
```
Expected (`tests/io/snippets/create.expected.json`):
```json
{"status":"completed","step":"snippet_extraction"}
```

Judge-input (`tests/io/evaluation/judge.input.json`):
```json
{"input":{},"output":{},"contract":{}}
```
Judge-expected (`tests/io/evaluation/judge.expected.json`):
```json
{"acceptable":true}
```

## Implementation outline
1. Implementera testschema-lifecycle helper.
2. Lägg kontraktstester för alla endpoints.
3. Lägg komponenttester per agent.
4. Lägg systemtester sist.
5. Lägg rerun-failed mekanism.

## Deliverables
- Testspecifikation (JSON I/O + assertions)
- Körbar test runner
- Judge-strategi för AI-steg
- Grön testmatris för endpoint/komponent/system

## What can be implemented in parallel
- Varje komponentteam kan skriva egna tester parallellt så länge kontrakten är låsta.

## Open questions / assumptions
1. **Open question:** Om systemtester i CI ska vara stub-only som default.
2. **Assumption:** Icke-deterministiska AI-steg testas med judge-baserad acceptans i v1.

## Deterministic vs non-deterministic test evaluation

### Deterministiska steg (bör jämföras exakt där rimligt)
- `config_catalog`
- `file_selection_ingest`
- `policy_assembly` (struktur)
- `prompt_generation` (obligatoriska fält + lineage)
- `orchestrator_run_control` statusmaskin
- `persistence_invalidation`

### Icke-deterministiska steg (accepteras via judge)
- `snippet_extraction`
- `topic_evaluation`

### Judge-baserad utvärdering (pragmatisk)
Judge får:
- test-input
- faktisk output
- förväntat kontrakt

Judge avgör:
- om output är acceptabel mot kontrakt och uppgift
- samt returnerar `acceptable: true|false` + kort motivering

Detta används där exakt string-jämförelse inte är robust.
