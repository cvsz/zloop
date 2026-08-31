# AGENTS.md — Loop Engineering Execution Contract

## Mission

Deliver verified outcomes through bounded autonomous feedback loops.

## Version

1.0.0 — Production-ready. All invariants enforced by `LoopEngine`.

## Mandatory lifecycle

1. Discover
2. Plan
3. Execute
4. Verify
5. Review
6. Repair if required
7. Re-verify
8. Ship or hand off

Skipping verification is prohibited. The engine enforces this — `State.SHIPPED` is only reachable via `State.REVIEW` with `verification_passed=True` and `blocking_review_findings=False`.

## Global invariants

| Invariant | Enforced by |
|-----------|-------------|
| Never run an unbounded loop | `max_iterations`, `max_repairs`, `wall_clock_budget_seconds` |
| Never silently expand scope | Executor must declare scope in plan |
| Never allow the executor to be the sole verifier | Verifier is a separate role; `verification_passed` gate |
| Never mutate external systems without explicit permission | Permission classes: `READ_ONLY`, `LOCAL_MUTATION`, `REMOTE_MUTATION`, `HIGH_IMPACT` |
| Never expose secrets in logs, prompts, artifacts, or summaries | Memory policy forbids secrets |
| Never overwrite another agent's workspace | File locking + worktree isolation |
| Never repeat a side effect without idempotency protection | Idempotency key: `<loop_id>:<plan_version>:<step_id>:<target>` |
| Persist progress after every stage transition | `MemoryStore.save()` after every transition |
| Stop immediately on policy violation | `State.POLICY_VIOLATION` terminal |
| Human escalation is a valid terminal state | `State.HANDOFF` for ambiguous/blocked states |

## Required budgets

Every loop must define all six budgets:

| Budget | Field | Default | Terminal on exhaustion |
|--------|-------|---------|----------------------|
| Iteration cap | `max_iterations` | 12 | `BUDGET_EXHAUSTED` |
| Repair cap | `max_repairs` | 4 | `BUDGET_EXHAUSTED` |
| No-progress cap | `max_consecutive_no_progress` | 2 | `HANDOFF` |
| Token budget | `token_budget` | 500,000 | `BUDGET_EXHAUSTED` |
| Cost budget | `cost_budget` | $25.00 | `BUDGET_EXHAUSTED` |
| Wall-clock budget | `wall_clock_budget_seconds` | 7200 | `BUDGET_EXHAUSTED` |

Budgets are checked **before** and **after** each adapter call. Missing budgets use safe defaults from `Budgets()`.

## State machine

```
DISCOVER → PLAN → EXECUTE → VERIFY → REVIEW → SHIPPED
                              ↓        ↓
                              └── REPAIR ←┘
                                    ↓
                                    └── VERIFY
```

## Terminal states

| State | Meaning | Reachable from |
|-------|---------|----------------|
| `SHIPPED` | All gates passed | `REVIEW` with no blocking findings |
| `HANDOFF` | Human input required | Any state via `BLOCKED`/`INCONCLUSIVE` or no-progress |
| `BUDGET_EXHAUSTED` | Hard limit reached | Any state via budget check |
| `POLICY_VIOLATION` | Security/permission violated | Any state |
| `FAILED` | Unrecoverable error | Non-verify/review states via `FAIL` status |

## Agent roles

### Orchestrator
**Implementation**: `LoopEngine` class
- Owns state transitions via `_transition()`
- Enforces budgets via `_budget_reason()`
- Delegates to one role at a time via `ROLE_FOR_STATE`
- Persists state after every transition via `MemoryStore.save()`

### Discoverer
**Role name**: `"discoverer"`
- Collects relevant facts, repository state, requirements, constraints
- Checks prior attempts from memory
- Reports unknowns that materially affect correctness

### Planner
**Role name**: `"planner"`
- Produces finite executable plan with acceptance criteria
- Attaches validation and rollback to each step
- Separates mandatory work from optional improvements

### Executor
**Role name**: `"executor"`
- Performs only approved plan actions
- Uses worktree/branch isolation for concurrent changes
- Records commands/actions and resulting evidence
- Uses idempotency keys for external mutations

### Verifier
**Role name**: `"verifier"`
- Runs objective checks and returns structured evidence
- Must be independent from executor (enforced by separate role)
- Returns `verification_passed: bool` — engine uses this for transition

### Reviewer
**Role name**: `"reviewer"`
- Performs correctness, security, maintainability, scope review
- Classifies findings as `blocking`, `major`, `minor`, `note`
- Returns `blocking_review_findings: bool` — engine uses this for transition

### Repairer
**Role name**: `"repairer"`
- Uses verifier/reviewer findings to propose smallest bounded correction
- Tracks repair attempts via `state.repair_attempts`
- Compares new failure signature against prior failures

### Memory Manager
**Implementation**: `MemoryStore` protocol, `JsonlMemoryStore` default
- Persists decisions, attempts, evidence, blockers, lessons
- File-locked for concurrent safety
- Schema validation on save

### Cost/Context Governor
**Implementation**: `LoopEngine._budget_reason()`
- Tracks consumption across six dimensions
- Triggers escalation before hard exhaustion
- Blocks wasteful retries via no-progress detection

## Handoff conditions

Escalate when:
- The same failure repeats without measurable progress (`consecutive_no_progress >= max`)
- Required credentials or approvals are unavailable (`BLOCKED` status)
- Verification is ambiguous (`INCONCLUSIVE` status)
- Scope conflicts with policy
- Budget is near exhaustion (< 20% remaining)
- Destructive or irreversible action is requested without explicit authority

## Permission classes

| Class | Scope | Requires approval |
|-------|-------|-------------------|
| `READ_ONLY` | Inspect files, logs, metadata | No |
| `LOCAL_MUTATION` | Edit isolated local/worktree content | No |
| `REMOTE_MUTATION` | Push branch, update issue, write DB | Yes |
| `HIGH_IMPACT` | Production deploy, destructive op | Yes + explicit |

## Idempotency

External mutations require stable idempotency key:
```
<loop_id>:<plan_version>:<step_id>:<target>
```

Lifecycle: `NOT_STARTED → IN_PROGRESS → SUCCEEDED | FAILED_RETRYABLE | FAILED_FINAL`

## Memory policy

**Store**: decisions, attempt history, verification evidence, blockers, architecture constraints, reusable lessons, artifact locations, unresolved follow-ups

**Do not store**: secrets, raw credentials, unnecessary private data, transient chain-of-thought

## Output contract

All agents return `AgentResult` with:
- `status`: `"OK"`, `"FAIL"`, `"BLOCKED"`, or `"INCONCLUSIVE"`
- `summary`: Concise factual summary
- `evidence`: List of findings with source locations
- `next_action`: Recommended next step
- `risks`: Identified risks
- `artifacts`: Changed/created artifacts
- `memory_updates`: Additional memory entries
- `usage.tokens`: Tokens consumed this stage
- `usage.cost`: Cost incurred this stage
- `progress`: Whether measurable progress was made
- `verification_passed`: (verifier only) Whether all criteria pass
- `blocking_review_findings`: (reviewer only) Whether blocking issues found
