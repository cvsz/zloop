# ZLoop Execution Planning

This document is the implementation contract for moving ZLoop from the current reference runtime to a production-grade closed-loop platform.

## Current baseline

- Provider-neutral Python loop engine exists.
- Loop lifecycle is bounded and explicit.
- Independent verifier/reviewer roles are defined.
- JSON schemas cover loop state and verification results.
- JSONL persistence provides a reference memory backend.
- CI, CodeQL, Dependency Review, and Dependabot are configured.

## Execution order

### EP-01 Durable state and recovery

**Goal:** a run can survive process interruption without losing correctness.

Deliverables:
- `StateStore` interface with atomic load/save/update semantics.
- SQLite backend for local use.
- PostgreSQL backend contract for production.
- run checkpoints after every state transition.
- resume-from-checkpoint API.
- cancellation/deadline state.
- durable idempotency records for mutating actions.

Acceptance gates:
- restart during every non-terminal state resumes safely;
- duplicate side effects are rejected/reconciled;
- corrupted/incomplete checkpoints fail closed;
- state transition tests cover all legal and illegal transitions.

### EP-02 Model router and context governor

**Goal:** make loops affordable and provider-neutral.

Deliverables:
- model provider adapter protocol;
- per-role model profiles;
- cheap-first routing with bounded fallback;
- token/cost ledger;
- context compaction;
- structured-output schema validation;
- provider failure classification.

Acceptance gates:
- hard budget cannot be exceeded silently;
- retries do not repeat identical expensive context;
- invalid structured output is repaired or escalated;
- fallback cannot bypass policy or permissions.

### EP-03 Isolated execution runtime

**Goal:** mutating agents cannot collide or escape assigned scope.

Deliverables:
- worktree manager;
- workspace ownership model;
- command runner boundary;
- timeout/resource limits;
- action audit events;
- mutation permission checks.

Acceptance gates:
- parallel workers cannot overwrite one another;
- unauthorized mutations fail closed;
- every external side effect has an idempotency key;
- cancellation terminates active execution cleanly.

### EP-04 Verification pipeline

**Goal:** completion is decided by evidence, not by the maker.

Deliverables:
- acceptance criteria representation;
- verifier adapter registry;
- test/build/type/security check adapters;
- reviewer severity model;
- evidence fingerprints;
- no-progress detector;
- bounded repair planner.

Acceptance gates:
- executor cannot set SHIPPED directly;
- INCONCLUSIVE never becomes PASS;
- repeated failure signature triggers handoff;
- regression verification is mandatory after repair.

### EP-05 GitHub closed loop

**Goal:** first real connector-backed vertical slice: fix a PR until required checks pass or escalation is required.

Flow:
`discover PR → inspect checks → plan smallest repair → worktree edit → test → push → observe checks → repair or ship`

Deliverables:
- GitHub read adapter;
- scoped branch mutation adapter;
- check-status adapter;
- PR summary/update adapter;
- approval boundary for high-impact changes.

Acceptance gates:
- never pushes to an unauthorized branch;
- never merges when required checks/review gates are unmet unless explicit policy permits it;
- stale head SHA is detected before mutation;
- all mutations are auditable and idempotent.

### EP-06 Fleet orchestration

**Goal:** bounded specialist parallelism without uncontrolled fan-out.

Deliverables:
- specialist registry;
- scoped child budgets;
- max depth/fan-out policy;
- worktree-per-mutating-agent;
- merge/conflict coordinator;
- independent QA role.

Acceptance gates:
- child agents cannot exceed parent scope or remaining budget;
- fan-out limits are enforced;
- overlapping diffs are detected before integration;
- global verifier owns final acceptance.

### EP-07 Production observability and security

**Goal:** every loop can be operated and audited in production.

Deliverables:
- structured audit schema;
- OpenTelemetry traces;
- metrics for duration, retries, failures, tokens, cost, handoffs;
- secret redaction;
- RBAC/tenant boundaries;
- SBOM/provenance/release evidence.

Acceptance gates:
- secrets do not appear in logs/state/artifacts;
- every terminal state has a reason and evidence trail;
- SLO-relevant metrics are queryable;
- production mutation permissions are deny-by-default.

## Definition of done

No execution package is complete until:
1. implementation is present;
2. deterministic tests pass;
3. failure paths are covered;
4. security/permission boundaries are reviewed;
5. docs and examples are updated;
6. verification evidence is attached;
7. rollback/handoff behavior is defined.

## Non-goals for early releases

- unbounded autonomous exploration;
- unrestricted production mutation;
- autonomous budget increases;
- self-modifying acceptance criteria;
- verifier bypasses;
- unlimited subagent spawning.
