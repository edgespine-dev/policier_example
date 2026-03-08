# nonfunctional_policy.md

## Purpose

This document defines the non-functional policy for artifact-based AI systems and mixed deterministic/stochastic software pipelines.

The goal is to ensure that systems are not only functionally correct and safely executed, but also operationally fit for real use.

This policy is orthogonal to:
- `test_policy.md`, which governs correctness verification
- `ai_code_safety_policy.md`, which governs safe generation and execution of code and actions

`nonfunctional_policy.md` governs whether the system is sufficiently:
- performant
- cost-efficient
- robust
- reproducible
- observable
- explainable
- operationally manageable

---

## Core Principle

A system is not operationally ready merely because:
- it passes functional tests
- it produces semantically acceptable outputs
- it runs safely in a sandbox

Operational readiness requires that the system can do so:
- within acceptable latency and cost
- with predictable behavior under perturbation and failure
- with sufficient observability and traceability
- with reproducible and explainable execution paths

---

## Scope

This policy applies to:
- individual pipeline steps
- full end-to-end runs
- repeated runs across time and versions
- release gates for AI-enabled systems
- benchmark and workload evaluation
- production-readiness assessments

It applies to both:
- deterministic shell components
- stochastic reasoning components

---

## Orthogonal Role

This policy is intentionally cross-cutting.

It applies across:
- APIs
- orchestration
- persistence
- caching
- lineage
- model calls
- benchmark execution
- explainability views
- release decisions

It must not be treated as a final add-on after feature work is complete.

---

## Non-Functional Dimensions

The following dimensions must be considered explicitly.

### 1. Performance
How fast the system responds and completes work.

### 2. Cost
How much compute, model usage, or operational expense the system consumes.

### 3. Robustness
How well the system tolerates noise, irrelevant inputs, perturbation, or partial failure.

### 4. Reproducibility
How reliably runs can be replayed, compared, and explained.

### 5. Explainability completeness
How fully outputs can be traced through intermediate artifacts and evidence.

### 6. Observability
How well operators can inspect state, failures, and progress.

### 7. Operational recoverability
How well the system handles retries, backfills, stale artifacts, and degraded modes.

---

## Performance Policy

Performance requirements should be defined at both:
- step level
- end-to-end level

Examples:
- max latency for deterministic endpoints
- max latency for AI-backed steps
- max end-to-end latency for representative runs
- throughput expectations under realistic load

Performance policy should distinguish:
- user-facing latency
- background processing latency
- cold-run vs cache-hit latency
- single-run vs repeated workload latency

Performance targets must be explicit enough to serve as gates or alerts.

---

## Cost Policy

AI-enabled systems must treat cost as a first-class operational concern.

Relevant cost signals include:
- number of model calls
- cache hit rate
- recomputation avoided
- tokens or estimated inference cost
- benchmark execution cost
- operational infrastructure cost where measurable

The system should prefer:
- persisted intermediate artifacts
- selective recomputation
- explicit fingerprint-driven reuse
- benchmark subsets where appropriate for CI
- full benchmark or expensive eval only when justified

A system that is correct but too expensive to run repeatedly is not operationally ready.

---

## Robustness Policy

The system must be evaluated under realistic variation and disturbance.

Robustness checks may include:
- irrelevant document injection
- reordering of inputs
- formatting noise
- partial data loss
- timeouts
- missing intermediate artifacts
- degraded model responses
- boundary-case payloads

The goal is not that outputs remain identical, but that the system:
- remains stable within defined acceptance bounds
- fails clearly when necessary
- avoids silent corruption
- preserves invariants where required

---

## Reproducibility Policy

The system should support reproducible reasoning and replay through artifacts.

Reproducibility requires:
- persisted intermediate artifacts where appropriate
- explicit fingerprints or version identifiers
- visible cache-hit vs recomputation behavior
- reproducible benchmark setup
- recoverable run context and status
- explicit thresholds and rubrics where semantic evaluation is used

Perfect bit-for-bit reproducibility is not always possible for stochastic steps, but procedural reproducibility should still hold.

---

## Explainability Completeness Policy

Explainability is not just a debugging convenience. It is an operational quality dimension.

The system should be able to show, at the appropriate level:
- what inputs were considered
- what intermediate artifacts were generated
- what evidence supported downstream outputs
- what prompt or reasoning envelope was used
- what dependencies were materialized
- why a result is considered valid, stale, or recomputed

Explainability completeness may vary by step, but gaps must be intentional and documented.

---

## Observability Policy

The system must expose enough information for operators and developers to answer:
- what is running?
- what finished?
- what failed?
- why did it fail?
- what was reused?
- what was recomputed?
- what changed between versions or runs?

Observability should include:
- run identifiers
- step status
- timings
- warnings and errors
- cache status
- artifact identifiers
- lineage visibility where relevant

A functionally correct system with poor observability is operationally weak.

---

## Operational Recoverability Policy

The system should support controlled recovery from:
- partial failures
- stale artifacts
- missing dependencies
- timeout conditions
- interrupted orchestration
- benchmark interruptions
- model-side transient failures

Recovery policy should define:
- retryable vs terminal failures
- when `ensure` is allowed to backfill
- when stale outputs may be surfaced
- when recomputation is required
- when human intervention is needed

Operational recoverability is distinct from correctness and should be evaluated explicitly.

---

## Step-Level and System-Level Evaluation

Non-functional assessment must happen at multiple scopes.

### Step-level
Useful for:
- latency outliers
- expensive model steps
- cache effectiveness
- explainability completeness per step
- local robustness issues

### System-level
Useful for:
- end-to-end latency
- aggregate cost
- whole-pipeline reproducibility
- release readiness
- operational bottlenecks
- benchmark and trend analysis

Both scopes are required.

---

## Relationship to Test Policy

`test_policy.md` determines:
- what kind of correctness verification to use
- how to classify steps
- what oracle types apply
- how to test deterministic vs stochastic behavior

`nonfunctional_policy.md` determines:
- what operational qualities must be measured
- what thresholds and scorecards are required
- what release readiness means beyond correctness

These are complementary policies.

---

## Relationship to Safety Policy

`ai_code_safety_policy.md` determines:
- what generated code/actions are allowed to run
- under what permissions and containment
- what actions require approval

`nonfunctional_policy.md` determines:
- whether the system is practical and reliable to operate

A system may be safe but too slow, too expensive, or too opaque.
A system may be fast but operationally fragile.
Both policies are required.

---

## Default Metrics and Signals

Where project-specific metrics are not yet defined, this policy recommends tracking at least:

### Performance
- latency per step
- end-to-end latency
- cache-hit latency vs cold-run latency

### Cost
- model call count per run
- cache hit rate
- recomputation rate
- benchmark execution cost estimate

### Robustness
- pass rate under perturbation sets
- timeout rate
- partial-failure recovery rate

### Reproducibility
- replay success rate
- consistency of cache/recompute decisioning
- benchmark reproducibility

### Explainability
- percentage of outputs with complete lineage
- percentage of runs with reconstructable step flow

### Observability
- percentage of failures with actionable error context
- percentage of runs with complete trace metadata

---

## Threshold Policy

Thresholds should be:
- explicit
- versioned
- tied to scenarios
- reviewable over time

Thresholds may vary by:
- environment
- component criticality
- workflow type
- benchmark profile

Where precise thresholds are unknown in early phases, the system should still:
- capture baseline measurements
- compare deltas over time
- record assumptions explicitly

---

## Non-Functional Gate Model

Recommended gate model:

### Informational
Metrics are recorded but do not yet block.

### Advisory
Metrics may trigger warnings and review.

### Blocking
Metrics can fail merge, release, or rollout decisions.

Projects should explicitly state which dimensions are:
- informational
- advisory
- blocking

This prevents hidden, inconsistent expectations.

---

## Role of Benchmarks and Workloads

Benchmarks are a primary tool for non-functional assessment.

Representative workloads should be used to evaluate:
- latency
- cost
- trend regressions
- stability under realistic use
- explainability completeness at scale

Micro-tests are not sufficient by themselves for non-functional readiness.

---

## Policy for Test-Generating and Evaluation Agents

Agents generating non-functional tests or evaluations must:

1. identify which non-functional dimensions matter for the target system
2. define measurable signals, not vague aspirations
3. distinguish step-level vs system-level measurements
4. make thresholds explicit where known
5. record whether each dimension is informational, advisory, or blocking
6. avoid conflating semantic acceptance with operational readiness
7. include cache, recomputation, and explainability measures where relevant

---

## Minimal Default Posture

At minimum, an artifact-based AI system should be able to answer:

- how long did each step take?
- how much expensive AI work was reused vs recomputed?
- can outputs be traced back through artifacts?
- can failed runs be diagnosed?
- can a representative run be replayed?
- does the system remain useful under reasonable perturbations?

If these questions cannot be answered, operational readiness is incomplete.

---

## What This Policy Does Not Assume

This policy does not assume:
- a specific observability stack
- a specific benchmark framework
- a specific model vendor
- a specific cost accounting model
- that all thresholds are known on day one

It does assume:
- non-functional quality must be explicit
- operational readiness is measurable
- cost matters in AI systems
- explainability and reproducibility are operational concerns
- release decisions should consider more than correctness

---

## Short Version

Passing tests is necessary, not sufficient.

Measure:
- speed
- cost
- robustness
- reproducibility
- explainability
- observability

Or, more formally:

- correctness proves the system can work
- safety proves it can be trusted to run
- non-functional policy proves it is fit to operate
