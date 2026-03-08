
# test_policy.md

## Purpose

This document defines how test-generating and test-executing agents must behave when working on systems that combine deterministic software components with stochastic AI/LLM-based reasoning.

The policy is intentionally general, but uses **artifact-based AI pipelines** as the main reference model.

The goal is to ensure that:
- test generation starts from architecture and contracts, not implementation guesses
- deterministic and stochastic parts are tested differently
- explainability and lineage are treated as first-class test targets
- test suites remain stable even when AI models improve
- implementation happens only after tests and contracts are sufficiently defined

This policy is intended to support **test-first development** for AI-enabled systems.

---

## Core Principle

AI systems should not be tested as a single opaque input→output black box when they can instead be decomposed into a pipeline of inspectable intermediate artifacts.

Preferred system shape:

```text
input
  ↓
artifact 1
  ↓
artifact 2
  ↓
artifact 3
  ↓
final decision / output
```

Examples of artifacts:
- selected files
- ingested documents
- snippets
- policies
- prompts
- evaluations
- findings
- recommendations

This decomposition improves:
- inspectability
- explainability
- debugging
- testability
- reuse/caching

---

## Architectural Assumption

This policy assumes the system under test can be described as a set of **pipeline steps**.

Each step should be modeled using the same abstract shape:

- **input**
- **output**
- **transformation**
- **persistence**
- **interfaces**
- **AI or non-AI classification**
- **error modes**
- **non-functional constraints**

Each step must be classified as one of:

1. **Deterministic**
   - expected to return the same result for the same input
   - examples: file filtering, hashing, schema validation, REST contracts, DB writes

2. **Stochastic**
   - includes model reasoning or other non-deterministic behavior
   - examples: extraction, semantic summarization, evaluation, recommendation generation

3. **Hybrid**
   - contains a deterministic shell around a stochastic core
   - examples: prompt construction + model call + schema validation

---

## Deterministic Shell vs Stochastic Core

The system should be understood as:

- a **deterministic shell**
- surrounding a **stochastic core**

### Deterministic shell
The deterministic shell includes:
- orchestration
- REST/API behavior
- database interaction
- caching
- invalidation
- lineage/provenance
- schema validation
- artifact storage
- dependency resolution
- prompt assembly logic where deterministic

### Stochastic core
The stochastic core includes:
- LLM-based extraction
- semantic synthesis
- semantic evaluation
- recommendation generation
- judge-based acceptance in non-deterministic cases

### Testing implication

Deterministic shell:
- test with exact verification

Stochastic core:
- test with probabilistic and semantic evaluation

This separation matches current best practice in LLM-system evaluation, where systems are increasingly evaluated as full pipelines rather than isolated model responses.

---

## Inputs a Test-Generating Agent Must Read

Before generating or updating tests, a test-generating agent must read, in this order when available:

1. `architecture.md` or equivalent canonical architecture document
2. `agent_orchestration.md` or equivalent dependency/order document
3. the component plan for the target component
4. API contracts / artifact contracts
5. any existing test matrix or benchmark spec
6. any project-specific test policy
7. relevant skill descriptions or skill references, if the workflow uses skill-scoped responsibilities

A test-generating agent must not generate tests purely from code structure if authoritative architecture/contracts exist.

If the architecture and component plan disagree, the test-generating agent must flag this explicitly instead of guessing.

---

## Test Dimensions

All tests must be designed along **two explicit levels** plus a cross-cutting concern:

### Level 1: Deterministic vs Stochastic
Every test target must first be classified as:
- deterministic
- stochastic
- hybrid

This determines the primary test method.

### Level 2: Test Scope
Every test must then be classified as one or more of:
- unit
- integration
- system
- acceptance

### Cross-cutting concern: Non-functional
Non-functional properties must be evaluated across all scopes where relevant:
- latency
- cost
- robustness
- cache effectiveness
- reproducibility
- explainability
- observability
- failure recovery

---

## Mapping of Test Scope to Modern AI Systems

### Unit
Use for:
- local deterministic logic
- schema validation
- hashing
- template rendering
- cache-key construction
- dependency resolution
- local lineage rules

Unit tests must avoid live AI calls.

### Integration
Use for:
- step-to-step artifact contracts
- API and DB interactions
- lineage continuity across component boundaries
- create/read/ensure behavior
- dependency propagation
- cache-hit/calc paths

AI calls may be stubbed or replaced with recorded artifacts unless the purpose is explicitly semantic integration.

### System
Use for:
- full pipeline execution
- artifact flow through the complete system
- end-to-end dependency resolution
- explainability visibility
- correctness of orchestration under realistic conditions

System tests should prefer invariant-based verification over exact-output matching.

### Acceptance
Use for:
- semantic usefulness
- domain relevance
- support by evidence
- practical correctness of AI-generated outputs

Acceptance tests may use:
- benchmark datasets
- metamorphic relations
- differential comparisons
- LLM-as-a-Judge
- human review when needed

---

## Approved Test Methods by Step Type

### A. Deterministic steps
Preferred methods:
- exact assertions
- contract testing
- property/invariant testing
- fuzzing on structured inputs
- static analysis
- linting
- code review checklists

Examples:
- response schema must match contract
- excluded files must never appear in included set
- cache-hit path must avoid recomputation
- every stored artifact must have required metadata

### B. Stochastic steps
Preferred methods:
- schema validation
- invariant checking
- metamorphic testing
- differential testing
- benchmark-based evaluation
- judge-based evaluation

Exact expected string matching should be avoided unless the output is explicitly constrained to deterministic formatting.

### C. Hybrid steps
Use:
- exact checks for shell behavior
- semantic checks for AI reasoning behavior

Example:
- prompt generation may be deterministic in structure but evaluated semantically for completeness and traceability

---

## Invariant-Based Testing

Invariant-based testing is mandatory for all artifact-based AI systems.

Examples of valid invariants:
- every finding must reference evidence
- every prompt must reference its policy or source artifact
- every artifact must be attributable to its upstream inputs
- excluded inputs must not influence downstream artifacts
- ensure must not silently skip invalid dependencies
- each artifact must be valid for its declared topic/scope

Invariant tests should be preferred over brittle exact-output comparisons whenever possible.

---

## Metamorphic Testing

Metamorphic testing is the preferred method when the oracle problem makes exact expected outputs impractical.

A metamorphic test defines a transformation on the input and an expected relation between outputs.

Examples:
- reorder documents → output should remain materially stable
- add irrelevant document → relevant result should not change significantly
- add formatting noise → semantic output should remain stable
- remove irrelevant section → topic-specific output should remain stable

---

## Differential Testing

Differential testing is recommended when:
- comparing prompt versions
- comparing model versions
- comparing pipeline versions
- comparing local vs remote model behavior

The goal is not to demand identical outputs, but to detect suspicious divergence.

Differential testing should be used to answer questions such as:
- does a new model reduce semantic quality?
- does a prompt change increase hallucination risk?
- does a new pipeline version break stability?

---

## LLM-as-a-Judge Policy

LLM-as-a-Judge is allowed, but only under constraints.

### Judge use is appropriate for:
- acceptance testing of semantic outputs
- evaluating relevance, support, clarity, or utility
- judging outputs when exact oracle labels are unavailable

### Judge use is not sufficient by itself for:
- API contracts
- schemas
- DB state
- lineage completeness
- status codes
- exact side effects

### Judge requirements
A judge-based test must:
- specify the evaluation rubric explicitly
- provide the relevant input/output/context
- record the judge prompt
- record the judge result
- record the acceptance threshold

Judge outputs must be treated as evaluative signals rather than absolute oracles.

---

## Deterministic vs Non-Deterministic Expected Outputs

### Deterministic expected outputs
Use exact expected JSON where feasible for:
- contracts
- schemas
- DB-visible deterministic results
- orchestration states
- lineage structures
- cache behavior
- error codes

### Non-deterministic expected outputs
For AI-driven semantic steps:
- expected outputs may still be stored as JSON
- but acceptance may be based on:
  - structural constraints
  - required fields
  - required evidence links
  - judge-based scoring
  - benchmark thresholds
  - metamorphic stability

The test oracle in these cases is not exact string equality but **acceptability under policy**.

---

## JSON-Based Test Assets

This policy recommends storing tests as explicit artifacts.

### Required where practical
- JSON input files
- JSON expected output files
- JSON benchmark cases
- JSON metamorphic transformation specs
- JSON judge result records

### Benefits
- reproducibility
- low-context execution
- easier CI integration
- separation of test design from implementation code
- easier reuse across model/pipeline versions

---

## Non-Functional Testing Policy

Non-functional tests are mandatory for AI-enabled systems.

The following dimensions must be considered:

### Performance
- latency per step
- latency per full pipeline
- throughput where relevant

### Cost
- model calls per run
- cache hit rate
- recomputation avoided
- estimated token or compute cost

### Robustness
- resilience to irrelevant documents
- resilience to formatting/noise
- graceful degradation on timeouts or partial failures

### Explainability
- ability to trace outputs back to sources
- visibility of intermediate artifacts
- inspectability of prompt construction

### Reproducibility
- ability to rerun with same artifacts
- ability to explain cache-hit behavior
- ability to identify invalidation causes

---

## Test-Generating Agent Behavior

A test-generating agent must behave as follows:

1. Read canonical architecture before generating tests.
2. Identify pipeline steps.
3. Classify each step as deterministic, stochastic, or hybrid.
4. For each step, derive:
   - local invariants
   - artifact contracts
   - likely error modes
   - relevant non-functional concerns
5. For each step, propose tests at the appropriate scope:
   - unit
   - integration
   - system
   - acceptance
6. Prefer exact deterministic assertions where possible.
7. Use metamorphic/differential/judge-based methods only where deterministic oracle methods are insufficient.
8. Explicitly state the oracle type used by each test:
   - exact
   - invariant
   - metamorphic
   - differential
   - judge-based
   - human-reviewed
9. Never silently substitute semantic judge tests for deterministic contract tests.
10. Record assumptions when architecture/contracts are incomplete.

---

## Required Output of a Test-Generating Agent

For each component or step, the agent should produce:

- step classification: deterministic / stochastic / hybrid
- scope classification: unit / integration / system / acceptance
- artifact contract summary
- invariant list
- deterministic test cases
- semantic/metamorphic/differential/judge tests where needed
- non-functional tests
- example JSON input
- example JSON expected output or acceptance rubric
- oracle type for each test
- justification for why this test method was chosen

---

## Minimal Example Test Structure

```yaml
test_id: tc_example
step: snippet_extraction
classification:
  step_type: stochastic
  scope: integration
oracle_type: metamorphic
input_file: tests/input/example.json
expected_file: tests/expected/example.json
acceptance:
  invariants:
    - every snippet has source_blob_id
    - all snippets match the requested topic
  metamorphic_relation:
    transform: reorder_documents
    expectation: semantic_output_stable
  judge:
    enabled: true
    rubric: relevance_and_source_support
```

---

## Policier as Reference Use Case

In Policier-like systems, a typical decomposition is:

- file selection
- document ingest
- snippet extraction
- policy assembly
- prompt generation
- topic evaluation
- explainability projection

Recommended primary methods:

- file selection → exact + invariant
- document ingest → exact + invariant
- snippet extraction → schema + invariant + metamorphic + judge
- policy assembly → invariant + semantic evaluation
- prompt generation → exact structure + lineage checks
- topic evaluation → benchmark + judge + differential
- explainability → exact lineage + integration checks

This use case should be treated as an example of an **artifact-based AI pipeline**, not as a special exception.

---

## What This Policy Does Not Assume

This policy does not require:
- a specific model vendor
- a specific judge model
- perfect determinism in AI outputs
- full prompt history over time
- complete row-level provenance in every step

It does require:
- explicit artifact boundaries
- explicit contracts
- explicit lineage expectations
- explicit oracle selection
- explicit distinction between deterministic and stochastic test logic

---

## Short Version

Test the machine exactly.  
Test the meaning probabilistically.  
Measure the non-functional properties continuously.

Or, more formally:

- deterministic shell → exact verification
- stochastic core → semantic and probabilistic evaluation
- whole system → end-to-end invariants, benchmarks, and operational checks
