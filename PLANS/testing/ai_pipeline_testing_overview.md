# Decomposed Artifact‑Based Pipelines and Modern AI System Testing

## 1. Modern Model for AI Systems (2023--2025)

Most serious AI systems today are described as:

**LLM pipelines with structured intermediate artifacts**\
or\
**decomposed reasoning systems**.

### Core idea

    input
      ↓
    intermediate artifacts
      ↓
    reasoning steps
      ↓
    final decision

Artifacts may include:

-   retrieved documents
-   extracted facts
-   summaries
-   plans
-   tool outputs
-   evaluations

Benefits:

-   inspectable
-   debuggable
-   testable
-   cost‑efficient (cacheable intermediate steps)

------------------------------------------------------------------------

# 2. Major Developments in the Last Few Years

## A. Evaluation Pipelines (Evals)

Traditional testing used exact expected outputs:

    expected output

Modern AI systems instead use evaluation pipelines:

    dataset
       ↓
    pipeline run
       ↓
    judge evaluation
       ↓
    score aggregation

Examples:

-   OpenAI **Evals**
-   Anthropic evaluation frameworks
-   DeepMind evaluation pipelines

------------------------------------------------------------------------

## B. Metamorphic Testing for LLMs

Because exact ground truth is often unavailable, systems test
**relationships between inputs**.

Example:

    input A
    input B = reorder(A)

    f(A) ≈ f(B)

Or:

    add irrelevant document

The system output should remain stable.

This area is currently an active research topic.

------------------------------------------------------------------------

## C. LLM‑as‑Judge (with caution)

LLMs can evaluate:

-   correctness
-   relevance
-   factuality

But research shows judge models must:

-   be calibrated
-   be validated
-   sometimes use ensembles

Otherwise evaluation may become biased.

------------------------------------------------------------------------

# 3. Deterministic Shell Concept

A useful architectural pattern:

    deterministic infrastructure
    +
    stochastic reasoning

Example deterministic components:

-   pipeline orchestration
-   databases
-   caching
-   contracts
-   APIs

Example stochastic components:

-   LLM reasoning
-   summarization
-   extraction
-   evaluation

The deterministic shell enables strong verification even when reasoning
steps are probabilistic.

------------------------------------------------------------------------

# 4. Traceable Reasoning

Modern AI systems emphasize **traceability**.

Systems should be able to show:

    output
    ↑
    reasoning
    ↑
    evidence
    ↑
    sources

This enables:

-   explainability
-   debugging
-   auditing
-   evaluation

------------------------------------------------------------------------

# 5. Typical Modern Architecture

                     Evaluation Layer
                            |
                      judge / metrics
                            |
                    -------------------
                            |
                      Reasoning Layer
                (LLM steps / tool calls)
                            |
                    -------------------
                            |
                      Artifact Layer
             (documents / snippets / plans)
                            |
                    -------------------
                            |
                    Deterministic Shell
          (pipeline, cache, storage, APIs)

This architecture separates reasoning from infrastructure and makes
systems more testable.

------------------------------------------------------------------------

# 6. Key References

## OpenAI Evals

https://github.com/openai/evals

Framework for evaluating AI systems using datasets and judges.

## Anthropic Evaluation Methodology

Anthropic blog posts and papers discussing evaluation of model outputs.

## METAL -- Metamorphic Testing for LLMs

ICST research on metamorphic testing techniques applied to LLM systems.

## DeepMind Evaluation Work

DeepMind research on benchmark datasets, automated judging, and
evaluation pipelines.

## Survey Papers on LLM Evaluation

Recent research surveys summarize methods including:

-   benchmark datasets
-   automated judges
-   human evaluation
-   automated metrics

------------------------------------------------------------------------

# 7. Example Description for Policier Architecture

A concise way to describe a system like Policier:

> Policier is implemented as a decomposed artifact‑based reasoning
> pipeline.\
> The system transforms an opaque AI decision problem into a sequence of
> inspectable intermediate artifacts\
> (documents → snippets → policies → prompts → evaluations).\
> Each stage is independently testable and traceable.\
> Deterministic infrastructure (pipeline orchestration, storage,
> lineage, caching) forms a deterministic shell\
> around stochastic reasoning steps implemented with LLMs.\
> This enables invariant‑based verification, metamorphic testing of
> reasoning steps and benchmark‑driven evaluation of system behaviour.

------------------------------------------------------------------------

# 8. Key Insight

The most important architectural pattern:

    AI reasoning
    ↓
    materialized artifacts
    ↓
    traceability
    ↓
    testability

This transformation---from opaque reasoning to structured artifacts---is
the foundation of modern AI engineering and evaluation.
