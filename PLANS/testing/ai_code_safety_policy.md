# ai_code_safety_policy.md

## Purpose

This document defines the safety policy for systems that use AI to generate, modify, execute, or evaluate code, configurations, scripts, or infrastructure changes.

The goal is to ensure that AI-generated or AI-selected actions are treated as **untrusted by default** and are only allowed to run within explicit technical and procedural guard rails.

This policy is orthogonal to functional testing:
- `test_policy.md` answers whether the system is **correctly verified**
- `ai_code_safety_policy.md` answers whether the system is **safe to execute, integrate, or release**
- `nonfunctional_policy.md` answers whether the system is **operationally ready**

This policy is intended to support:
- safe AI-assisted coding
- safe agent execution
- safe test and build automation
- safe code review and release gating

---

## Core Principle

AI-generated code, scripts, commands, and configuration changes must be treated as **untrusted third-party output** until they have passed the required safety gates.

No system should rely on:
- model intentions
- prompt wording alone
- informal trust in prior successful runs

Instead, safety must be established through:
- containment
- least privilege
- explicit policy
- verification
- auditability
- human approval where risk is high

---

## Scope

This policy applies whenever AI is used to:
- generate source code
- generate shell commands
- propose file modifications
- install or update dependencies
- generate deployment manifests
- modify infrastructure or runtime configuration
- run tests, scripts, or build commands
- access project data, secrets, or external systems
- generate operational instructions likely to be executed

It applies to:
- local development
- CI
- agentic code-generation workflows
- sandbox execution
- review and merge gates

---

## Orthogonal Role

This policy is intentionally orthogonal to the rest of the architecture.

It cuts across:
- deterministic shell
- stochastic core
- build pipelines
- runtime orchestration
- test execution
- release gates

Security and execution safety must not be added at the end as an afterthought. They must constrain all layers of the system.

---

## Threat Model

The system must assume that AI-generated code or commands may be:

1. **Incorrect**
   - wrong behavior
   - broken assumptions
   - unsafe side effects

2. **Over-permissioned**
   - broader file access than needed
   - network access not required by the task
   - unnecessary dependency installation

3. **Operationally dangerous**
   - destructive deletion
   - unsafe service modification
   - privilege escalation
   - persistence mechanisms

4. **Supply-chain risky**
   - fetching code or binaries from untrusted locations
   - dependency confusion
   - hidden install scripts
   - post-install execution

5. **Potentially malicious**
   - exfiltration attempts
   - ransomware-like destructive actions
   - credential harvesting
   - hidden backdoors

The policy must defend against both accidental and adversarial outcomes.

---

## Safety Model

The preferred safety model is:

```text
AI proposes
↓
system classifies risk
↓
low-risk actions may run in sandbox
↓
high-risk actions require stronger gates
↓
dangerous actions are denied by policy
```

This means the AI is not a trusted executor. It is a proposal source constrained by policy.

---

## Safety Layers

### 1. Pre-execution policy
Before any AI-generated action runs, it must be checked against explicit policy.

### 2. Contained execution
If allowed, it must run in a constrained environment.

### 3. Post-execution verification
After execution, effects must be inspected and audited.

### 4. Merge and release gates
Even successful execution does not imply safe merge or release.

---

## Allowed-by-Policy Mindset

This policy prefers **allowlists** over broad blocklists.

It is not sufficient to say:
- "do not run dangerous commands"

Instead the system should define:
- what kinds of actions are allowed
- in which environment
- under which permissions
- with which approval level
- against which directories or resources

---

## Action Classes

Every AI-generated action should be classified before execution.

### Class A — Safe low-risk actions
Typically allowed in sandbox by default.

Examples:
- formatting code
- adding tests
- editing local source files inside workspace
- generating documentation
- running lint/typecheck/test commands in sandbox
- creating local JSON fixtures

### Class B — Medium-risk actions
Allowed only with stricter policy and explicit logging.

Examples:
- dependency installation in sandbox
- modifying build configuration
- editing deployment manifests
- generating migration files
- executing project-specific maintenance scripts

### Class C — High-risk actions
Require explicit human approval.

Examples:
- changing CI/CD pipelines
- changing infra/security config
- editing authn/authz behavior
- modifying container permissions
- changing secrets handling
- deleting non-generated files at scale
- running commands with elevated permissions

### Class D — Forbidden actions
Must be denied by policy.

Examples:
- `sudo` or privilege escalation by default
- destructive deletion outside sandbox/workspace
- direct modification of host system config
- silent network fetch + execute patterns
- modification of `sudoers`, ssh config, cron, systemd, boot config
- uncontrolled outbound exfiltration behavior
- persistence mechanisms outside allowed project scope

---

## Command Safety Policy

The following command categories must be treated as restricted or forbidden unless explicitly approved:

- recursive deletion of broad paths
- privileged system modification
- remote code download and immediate execution
- package manager operations against untrusted sources
- shell expansion against ambiguous or root-level paths
- file permission changes outside workspace
- background services or daemons
- destructive VCS history rewriting in shared branches
- raw disk/device operations
- uncontrolled subprocess fan-out

Examples of patterns that require special scrutiny:
- `sudo ...`
- `rm -rf ...`
- `curl ... | bash`
- `wget ... | sh`
- privilege-changing commands
- hidden post-install hooks
- commands targeting `/`, `/etc`, `/usr`, `/var`, `/boot`, or user home outside project scope

This list is not exhaustive. Policy must reason by action class, not only regex patterns.

---

## Filesystem Safety Policy

AI-generated code or commands must not have unrestricted filesystem access.

Preferred rules:
- run as non-root
- use isolated workspace per run
- read/write only inside approved project paths
- use read-only mounts where possible
- block writes to host-sensitive directories
- separate temp artifacts from source-controlled artifacts
- record file diff before and after execution

High-risk file operations must be gated by:
- path allowlist
- action type
- approval policy
- audit logging

---

## Network Safety Policy

AI-generated workflows must not receive unrestricted network access by default.

Preferred rules:
- default-deny outbound network for local execution
- allow only explicitly approved endpoints when needed
- prohibit arbitrary downloads during execution unless the task explicitly allows them
- log all outbound requests in higher-risk environments
- separate model access from general internet access where possible

If the task requires:
- package installation
- model calls
- artifact download

then the allowed domains, protocols, and tools must be explicit.

---

## Secret Handling Policy

AI-generated code and agents must not receive broad access to secrets by default.

Rules:
- do not expose production secrets to general code-generation or execution agents
- inject only task-specific scoped credentials if strictly required
- prefer short-lived credentials
- redact secrets from logs and judge artifacts
- forbid writing secrets into source files, fixtures, prompts, or benchmark datasets
- treat secret access as high-risk and auditable

A successful task must never depend on hidden ambient secret access.

---

## Sandbox Execution Policy

AI-generated code must run inside a constrained execution environment whenever possible.

Preferred sandbox properties:
- non-root user
- isolated temp workspace
- resource limits (cpu, memory, time)
- limited filesystem scope
- limited or no outbound network
- no host-level mounts beyond what is needed
- no privileged container flags
- no production secrets
- explicit cleanup or snapshot reset

The sandbox must be treated as a containment boundary, not as a convenience.

---

## Review and Approval Policy

Not all AI-generated changes should be auto-merged or auto-executed.

The system should distinguish between:

### Auto-allowed
Low-risk, local, sandboxed actions with predictable effects.

### Review-required
Changes that affect:
- contracts
- security
- infrastructure
- deployment
- persistence
- authentication/authorization
- filesystem or network permissions

### Forbidden
Actions disallowed by policy even if the AI suggests them.

Human review is mandatory for high-risk actions.

---

## Code Review Safety Focus

AI-generated changes must be reviewed not only for correctness but for safety.

Safety review should explicitly inspect:
- permission escalation
- hidden side effects
- unsafe dependency additions
- suspicious subprocess usage
- unexpected network calls
- broad file deletion or modification
- secret leakage risk
- policy bypass attempts
- unexplained changes to execution environment or deployment

This safety review is complementary to functional review and test review.

---

## Dependency and Supply Chain Policy

Dependencies introduced by AI must be treated as supply-chain changes.

Rules:
- do not allow uncontrolled dependency additions
- require package source visibility
- inspect install scripts and post-install hooks where relevant
- pin versions where policy requires it
- scan for known vulnerabilities and policy violations
- separate "code change" from "dependency trust decision"

Dependency changes should never be treated as harmless implementation detail.

---

## Logging and Auditability

All AI-driven execution should leave an audit trail.

Minimum audit data should include:
- task identity
- prompt or request envelope identifier
- generated command or change summary
- risk classification
- execution environment
- files changed
- processes spawned
- network activity summary where relevant
- approval state
- result and policy decision

This is required for:
- debugging
- replay
- incident analysis
- trust calibration

---

## Post-Execution Verification

After execution, the system should inspect:
- file diffs
- newly created files
- deleted files
- dependency lockfile changes
- process behavior
- network behavior
- policy deviations
- mismatch between intended and observed effects

The goal is not only "did it work?" but also:
- "what did it do?"
- "what changed?"
- "was the change allowed?"

---

## Safety Gates in the Delivery Flow

Safety should appear explicitly in the implementation flow.

Recommended gate sequence:

1. Contract and test definition
2. AI-generated proposal
3. Static safety policy check
4. Sandbox execution
5. Post-execution inspection
6. Functional verification
7. Safety review for high-risk changes
8. Merge/release approval

This means safety is neither first-only nor last-only. It is present throughout.

---

## Relationship to Test Policy

`test_policy.md` governs:
- correctness verification
- deterministic vs stochastic test method selection
- oracle selection
- lineage as verification target
- benchmark/judge/metamorphic evaluation

`ai_code_safety_policy.md` governs:
- whether generated code or commands may run
- where they may run
- under what permissions
- under what review conditions
- what actions are forbidden

These policies complement each other and must not be conflated.

---

## Relationship to Non-Functional Policy

`nonfunctional_policy.md` governs:
- latency
- cost
- robustness
- reproducibility
- explainability completeness
- operational readiness

`ai_code_safety_policy.md` governs:
- execution risk
- containment
- approval
- least privilege
- action safety

Safety overlaps with non-functional concerns, but is not reducible to them.

---

## Policy for Test-Generating and Implementation Agents

Agents that generate code, scripts, or test harnesses must:

1. assume generated execution artifacts are untrusted until checked
2. avoid suggesting privileged execution unless explicitly required and approved
3. prefer deterministic, sandbox-friendly commands
4. separate low-risk local actions from high-risk infrastructure changes
5. flag risky operations explicitly instead of normalizing them
6. never rely on implicit access to host resources, secrets, or unrestricted network
7. produce changes that are easy to diff, review, and roll back

---

## Minimal Safe Defaults

The default safe posture should be:

- no root
- no sudo
- no unrestricted network
- no broad host filesystem access
- no ambient secrets
- no auto-merge for high-risk changes
- no silent dependency changes
- no auto-execution of destructive commands
- no hidden background services
- no production access from generic coding agents

Any deviation from these defaults must be explicit and justified.

---

## What This Policy Does Not Assume

This policy does not assume:
- a specific sandbox vendor
- a specific CI system
- a specific language or runtime
- perfect static detection of malicious behavior
- that all AI-generated code is malicious

It does assume:
- AI-generated code may be unsafe
- containment is mandatory
- policy must constrain execution
- auditability is required
- human approval is necessary for high-risk actions

---

## Short Version

Treat AI-generated code as untrusted.
Contain it.
Limit its permissions.
Inspect what it does.
Require approval for high-risk changes.

Or, more formally:

- untrusted by default
- least privilege by default
- sandbox by default
- audit by default
- approval for high-risk actions
