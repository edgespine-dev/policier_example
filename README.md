# policier_example

Repository for generating and evolving the final Policier agent swarm.

## Top-level structure
```text
policier_example/
├─ README.md
├─ AGILE/
├─ PLANS/
├─ app/
├─ tests/
├─ contracts/
└─ docs/
```

## What lives where
- `PLANS/`: canonical planning and policy source docs.
  - `PLANS/policier/`: architecture/component plans.
  - `PLANS/testing/`: normative policy anchors (`test_policy`, `ai_code_safety_policy`, `nonfunctional_policy`).
- `AGILE/`: Agile operating model and implementation planning artifacts for agent-driven delivery.
  - `AGILE/DELIVERY/`: traceable execution workspace (stories, handoffs, gates, activity logs, evidence).
- `app/`: implementation area for generated swarm code.
  - `app/templates/agent/policier/`: experimental reference templates (API, Postgres SQL, pipeline code).
- `.agent/merge_policy_exclude.json`: shared policy merge exclusion config used by Policier source collection.
- `tests/`: executable test suites and harness code as they are implemented.
- `contracts/`: API/artifact contracts and validation fixtures.
- `docs/`: human-oriented docs and prompt seeds.
  - `docs/prompts/policier_simple_root_prompt/`: seed prompt templates for decomposition.

## Working model
- Final swarm artifacts should be generated in `app/` and validated via `contracts/` + `tests/`.
- Keep correctness (`test_policy.md`), safety (`ai_code_safety_policy.md`), and non-functional readiness (`nonfunctional_policy.md`) separate and explicit.
