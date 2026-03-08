# Policier Architecture (Canonical)

## Purpose
Bygga en enkel, genomförbar och test-first arkitektur för Policier med fokus på:
- AI-agentkedjan
- materialiserade artefakter
- lineage/explainability
- låg AI-kostnad genom återanvändning

**Decision:** Detta dokument är överordnad sanningskälla för v1-planen i `PLANS/policier/`.

## Canonical component model
Detta är den kanoniska komponentmodellen för v1:
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

## Hard decisions (v1)
1. **Decision:** Dokument lagras i databasen i sin helhet.
2. **Decision:** Filerna är små, så enkelhet prioriteras över överoptimering.
3. **Decision:** Topics är katalogdata och `topic` är argument till en generell topic-runner.
4. **Decision:** Topics behöver inte initialt ligga i Postgres.
5. **Decision:** Inclusion/exclusion-regler behöver inte initialt ligga i Postgres.
6. **Decision:** Snippet-extraktion är ett materialiserat AI-mellanlager och ett av de viktigaste/dyraste stegen.
7. **Decision:** Snippets ska sparas och återanvändas.
8. **Decision:** Policies och prompts ska kunna sparas och återanvändas.
9. **Decision:** Systemet designas för låg AI-kostnad och hög återanvändning.
10. **Decision:** Pipelinen triggas via REST.
11. **Decision:** Det ska gå att starta från sent steg och materialisera beroenden bakåt.
12. **Decision:** Prompt-historik över tid är inte ett krav i v1.
13. **Decision:** Det viktiga i v1 är att kunna förklara hur aktuell prompt blev till.
14. **Decision:** Explainability ska visa prompten som faktiskt skickades till AI och dess källkedja.
15. **Decision:** Källspårning behöver inte vara perfekt rad-för-rad i v1; source-lista är acceptabel när rimligt.
16. **Decision:** Changed-run överdesignas inte i v1.
17. **Decision:** Hash/last-changed + lineage räcker som grund för framtida changed-run.
18. **Decision:** Testning ska kunna använda JSON input och JSON expected output där rimligt.
19. **Decision:** Icke-deterministiska AI-steg får använda judge-baserad acceptansbedömning.
20. **Decision:** Först låses plan/kontrakt/tester, implementation kommer efteråt.

## Canonical pipeline and artifact chain
Kärnflödet i v1:
1. `file_selection` (inkluderade + exkluderade filer med skäl)
2. `documents` (fulltext + metadata i DB)
3. `snippets` (materialiserade topic-relevanta extrakt)
4. `policy` (human-readable policy från snippets)
5. `prompts` (aktuella prompts från policy)
6. `evaluations` (topic-runner output)
7. `findings_recommendations` (enkel struktur, initialt JSONB/tydlig payload)
8. `explainability_views` (stegvis input/output/lineage)

**Decision:** AI körs i första hand i `snippet_extraction` och `topic_evaluation`; övriga steg ska vara så deterministiska som möjligt.

## Shared create/read/ensure contract
Gemensam minimibas för alla steg.

### Create/Ensure response base
```json
{
  "run_id": "uuid",
  "step": "snippet_extraction",
  "status": "completed|failed|timed_out|partial",
  "artifact_ids": {
    "snippet_ids": ["..."],
    "snippet_set_id": "..."
  },
  "used_cache": true,
  "validity": {
    "is_valid": true,
    "reason": "fingerprint_match",
    "fingerprint": "..."
  },
  "warnings": [],
  "errors": []
}
```

### Read response base
```json
{
  "run_id": "uuid",
  "step": "snippet_extraction",
  "status": "available|not_found|stale",
  "artifacts": {
    "snippet_ids": ["..."],
    "items": []
  },
  "validity": {
    "is_valid": true,
    "reason": "fingerprint_match",
    "fingerprint": "..."
  },
  "warnings": []
}
```

**Decision:** Extra stegfält är tillåtna, men ovan fält är obligatorisk gemensam bas.

## REST/API principles
- `GET` = read-only, inga dolda tunga AI-körningar.
- `POST ...:create` = explicit materialisering av ett steg.
- `POST ...:ensure` = materialisera steg + nödvändiga uppströmsberoenden.
- Alla steg ska returnera den gemensamma create/read/ensure-basen.

**Recommendation:** Behåll befintliga endpoints under migrering som wrappers mot kanoniska kontrakt.

## Two-phase delivery model

### Fas 1: test- och kontraktsfas
Skapa och lås:
- endpointkontrakt
- artifact contracts
- JSON inputfiler
- JSON expected output-filer
- assertions
- testordning
- stubs/judging där behövs

Validera i fas 1 att:
- create/read/ensure är konsekvent
- agentgränserna håller
- artefaktkedjan håller
- explainability får rätt underlag

### Fas 2: implementation
Implementera tills tester är gröna på tre nivåer:
1. endpointtester
2. komponenttester
3. systemtester

## Reuse from existing implementation
Följande ska återanvändas där rimligt:
- FastAPI-basen i `app/templates/agent/policier/api.py`
- topics-laddning från `app/templates/agent/policier/topic_catalog.py` och `app/templates/agent/policier/topics.json`
- nuvarande pipelinekod i `policy_pipeline.py`/`policy_runner.py` som startpunkt för steglogik
- `/policy_pipeline/*` som kompatibilitets-wrappers
- `/explain` som baseline-UI
- SQL-bas i `app/templates/agent/policier/sql/001_init_policy_explain.sql` och `002_add_source_blob_and_rules.sql`
- Postgres wiring och DB-credential policy via `docs/APP_DB_POLICY.md`
- deploymiljö med Traefik/ingressstruktur som redan finns i repot

## Migration / compatibility strategy

### Wrapper strategy
- Existerande endpoints lever kvar i v1 som wrappers.
- Ny intern kanonisk modell är create/read/ensure per artefaktsteg.

### Mapping old -> canonical
- `policy_pipeline/files` -> `file_selection` read/create
- `policy_pipeline/curate` -> `snippet_extraction` create/read
- `policy_pipeline/rules` -> mappas till `policy_assembly` + ev. enkel policy-derived checks i övergång
- `policy_pipeline` -> orchestrator `ensure` till slutsteg
- `policy` (loop) -> `topic_evaluation:ensure`

### Legacy rules track vs new artifacts
**Decision:** Undvik dubbelmodellering. `rules` behandlas som en övergångsrepresentation och mappas till den kanoniska artefaktkedjan (snippets -> policy -> prompts -> evaluations).

**Recommendation:** Behåll befintliga SQL-tabeller för rules som kompatibilitetslager tills nya artefakttabeller är implementerade.

## Prompt lineage (v1)
**Decision:** Fokus är lineage för den aktuella prompten, inte komplett historik.

Prompt lineage ska minst visa:
- vilken policy som användes
- vilka snippets som användes
- vilka source-dokument som låg bakom
- vilken template/version som användes
- exakt prompttext som skickades

## Changed-run kept simple (v1)
**Decision:** Ingen avancerad changed-run-motor i v1.

Pragmatisk modell i v1:
- spara dokumentmetadata (`hash`, `last_changed` där möjligt)
- spara lineage i artefakter
- låt framtida changed-run byggas ovanpå detta

## Data model (high-level)

### Explicit v1 requirements
- runs + step status
- file selection decisions (included/excluded + reason)
- document blobs (fulltext)
- snippets
- policy artifacts
- prompt artifacts
- evaluations
- findings/recommendations (enkel struktur)
- explainability read views

### Reuse of existing DB assets
Återanvänd/tabeller i repo:
- `policy_runs`
- `policy_run_sources`
- `policy_step_traces`
- `policy_cache_entries`
- `policy_source_blobs`
- `policy_rules`/`policy_rule_evidence` (kompatibilitet)
- `policy_claims`/`policy_evidence` (kompatibilitet)

### Recommendation (new minimal tables)
- `policy_file_decisions`
- `policy_snippets`
- `policy_assemblies`
- `policy_prompts`
- `policy_evaluations`
- `policy_findings_recommendations` (enkel JSONB/strukturerad payload i v1)

## Findings / recommendations in v1 (simple)
**Decision:** Starta enkelt med JSONB/tydlig strukturerad payload i stället för tung normalisering.
**Recommendation:** Normalisera mer först när det finns ett tydligt behov från queries/rapportering.

## Caching / reuse / invalidation
**Decision:** Fingerprint-baserad giltighet räcker i v1.

Minsta fingerprint-komponenter:
- input hash
- topic version hash
- template version
- step version
- model id (AI-steg)

**Recommendation:** TTL får vara sekundär fallback, inte primär giltighetsregel.

## Explainability / GUI principles
GUI ska visa stegvis input -> output för hela artefaktkedjan och explicit:
- vad som filtrerades bort och varför
- vilka snippets som extraherades
- vilken policy som byggdes
- vilken prompt som faktiskt skickades
- evaluation result + findings/recommendations

**Decision:** `/explain` i nuvarande kod är baseline och byggs vidare, inte ersätts abrupt.

## Test strategy summary
- Test-first enligt två-fas-modellen ovan.
- JSON input/expected används där rimligt.
- Deterministiska steg jämförs exakt där rimligt.
- Icke-deterministiska AI-steg bedöms med judge-step mot kontrakt.

## Open questions / assumptions
1. **Open question:** Exakt modellstrategi per steg i on-prem (extract/eval) är inte låst.
2. **Open question:** Om promptformat ska vara helt modellagnostiskt eller ha små modellspecifika variationer.
3. **Open question:** Hur långt normalisering av findings/recommendations ska drivas efter v1.
4. **Open question:** Om prompttext behöver maskeras i framtida miljöer med andra säkerhetskrav.
5. **Open question:** Om systemtester i CI ska vara stub-only som default.
6. **Assumption:** Synkrona REST-körningar räcker i v1 utan separat kö.
