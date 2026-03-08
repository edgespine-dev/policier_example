# Agent Orchestration (Canonical)

## Purpose
Definiera exakt hur Policier-agenter/komponenter förhåller sig till varandra för test-first implementation och senare separerbar deployment.

## Canonical agents
1. `orchestrator_run_control`
2. `config_catalog`
3. `file_selection_ingest`
4. `snippet_extraction`
5. `policy_assembly`
6. `prompt_generation`
7. `topic_evaluation`
8. `explainability_api_ui`
9. `persistence_invalidation`
10. `test_harness`

## Agent matrix (purpose, consumes, produces)
| Agent | Purpose | Consumes | Produces |
|---|---|---|---|
| `config_catalog` | Exponera topics/filter och versionhash | topics/filter-filer | `topic_catalog`, `file_selection_rules`, hashar |
| `file_selection_ingest` | Materialisera filurval och dokument | config-hashar, filesystem | `file_decisions`, `documents/source_blobs`, `source_set_hash` |
| `snippet_extraction` | AI-extrahera relevanta snippets | documents, topic config | `snippets`, snippet-lineage |
| `policy_assembly` | Bygga policy från snippets | snippets | `policy` |
| `prompt_generation` | Bygga aktuell prompt från policy | policy, topics/templates | `prompt`, `prompt_lineage` |
| `topic_evaluation` | Köra topic-runner och bedömning | prompt, model config | `evaluation`, `findings/recommendations` |
| `explainability_api_ui` | Visa kedjan input->output | alla artefakter ovan | explainability-vyer/UI-data |
| `orchestrator_run_control` | Styra run och ensure-kedja | step contracts/resultat | run-status, step-status |
| `persistence_invalidation` | DB/migration/validity-bas | DB env + migrations | giltighetsregler, schema/tables |
| `test_harness` | Test-first validering | kontrakt + testdata | testreports, assertions |

## Agent roles and artifact flow
- `config_catalog`
: producerar aktiv config och versionshashar för topics/filter.
- `file_selection_ingest`
: producerar file selection decisions och document blobs.
- `snippet_extraction`
: producerar materialiserade snippets.
- `policy_assembly`
: producerar policyartefakter från snippets.
- `prompt_generation`
: producerar aktuella prompts från policy.
- `topic_evaluation`
: producerar evaluations och findings/recommendations.
- `explainability_api_ui`
: producerar explainability-views från tidigare artefakter.
- `orchestrator_run_control`
: producerar run-status och stegkoordination.
- `persistence_invalidation`
: producerar migrationsstatus och giltighetsregler.
- `test_harness`
: producerar testreports och testassertions.

## Upstream and downstream dependencies (explicit)
- `config_catalog`
: upstream `none`, downstream `file_selection_ingest`, `snippet_extraction`, `prompt_generation`, `topic_evaluation`.
- `file_selection_ingest`
: upstream `config_catalog`, `persistence_invalidation`; downstream `snippet_extraction`, `explainability_api_ui`.
- `snippet_extraction`
: upstream `file_selection_ingest`, `config_catalog`, `persistence_invalidation`; downstream `policy_assembly`, `explainability_api_ui`.
- `policy_assembly`
: upstream `snippet_extraction`, `persistence_invalidation`; downstream `prompt_generation`, `explainability_api_ui`.
- `prompt_generation`
: upstream `policy_assembly`, `config_catalog`, `persistence_invalidation`; downstream `topic_evaluation`, `explainability_api_ui`.
- `topic_evaluation`
: upstream `prompt_generation`, `persistence_invalidation`; downstream `explainability_api_ui`, `orchestrator_run_control`.
- `explainability_api_ui`
: upstream `all artifact producers`, `persistence_invalidation`; downstream `none`.
- `orchestrator_run_control`
: upstream `all step components`, `persistence_invalidation`; downstream `none`.
- `persistence_invalidation`
: upstream `none`; downstream `all`.
- `test_harness`
: upstream `all`; downstream `none`.

## Hard build-order dependencies
Detta är obligatorisk byggordning för implementation (inte runtime):
1. `persistence_invalidation`
2. `config_catalog`
3. `test_harness` (fas 1: kontraktstester/stubbar)
4. `file_selection_ingest`
5. `snippet_extraction`
6. `policy_assembly`
7. `prompt_generation`
8. `topic_evaluation`
9. `orchestrator_run_control`
10. `explainability_api_ui`

Notering:
- `test_harness` startar tidigt men fortsätter löpande tills systemtest är gröna.

## Runtime dependency order
Kanonisk runtime-kedja för full `ensure` till sent steg:
1. `config_catalog` read
2. `file_selection_ingest` ensure
3. `snippet_extraction` ensure
4. `policy_assembly` ensure
5. `prompt_generation` ensure
6. `topic_evaluation` ensure
7. `explainability_api_ui` read

`orchestrator_run_control` kan starta på steg 2-7 och materialisera bakåt enligt create/read/ensure.

## Contracts that must be locked before implementation
Måste låsas i fas 1:
1. gemensam create/read/ensure response base
2. artifact contracts för alla steg
3. fingerprint/validity fält
4. run/step status values
5. explainability minimum payload
6. error/warning format

## Dependencies that can be mocked/stubbed first
- AI-modellanrop i `snippet_extraction` och `topic_evaluation`.
- DB-lager kan initialt mockas i rena kontraktstester.
- `orchestrator_run_control` kan stubba stegresultat innan full komponentimplementation finns.
- `explainability_api_ui` kan börja mot seedad testdata.

## What can be implemented in parallel
Efter att kontrakt är låsta:
1. `file_selection_ingest` och `config_catalog`
2. `snippet_extraction` och `policy_assembly` (med låst snippet-kontrakt)
3. `prompt_generation` och `topic_evaluation` (med låst prompt-kontrakt)
4. `explainability_api_ui` parallellt med alla steg så snart read-kontrakt finns
5. `orchestrator_run_control` parallellt, men slutintegration sker sist

## What can be deployed separately
- Varje agent kan deployas separat när dess API-kontrakt är stabilt.
- Minsta deploy-enhet: en komponent med eget API-lager och DB-access till gemensam schema-/tabellmodell.

## Agent deployment model
- Varje agent ska senare kunna köras/deployas från sin egen planfil.
- Minsta deploy-enhet är en komponent från kanoniska modellen ovan.
- Varje agent måste läsa följande gemensamma referenser:
  - `PLANS/policier/policier_architecture.md`
  - `PLANS/policier/agent_orchestration.md`
- Varje agentplan ska dessutom ha egna artifact- och API-kontrakt i sin planfil.

## Open questions / assumptions
1. **Assumption:** V1 kan köras i en tjänst med tydliga komponentgränser i kod och tester.
2. **Assumption:** Eventuell uppdelning i separata tjänster görs först efter att kontrakt och tester är stabila.
