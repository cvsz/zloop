# AGENTS.md — ZLoop Execution Contract

## Mission
Deliver verified outcomes through bounded autonomous feedback loops.

## Mandatory lifecycle
1. Discover
2. Plan
3. Execute
4. Verify
5. Review
6. Repair if required
7. Re-verify
8. Ship or hand off

Skipping verification is prohibited.

## Global invariants
- Never run an unbounded loop.
- Never silently expand scope.
- Never let the executor be the sole verifier.
- Never mutate external systems without explicit permission.
- Never expose secrets in logs, prompts, artifacts, or summaries.
- Never overwrite another agent's workspace.
- Never repeat a side effect without idempotency protection.
- Persist progress after every stage transition.
- Stop immediately on policy violation.
- Human escalation is a valid terminal state.

## Required budgets
Every loop defines `max_iterations`, `max_repairs`, `max_consecutive_no_progress`, `token_budget`, `cost_budget`, and `wall_clock_budget_seconds`.

## Terminal states
`SHIPPED`, `BLOCKED`, `HANDOFF`, `BUDGET_EXHAUSTED`, `POLICY_VIOLATION`, `FAILED`.

## Roles
Orchestrator owns state transitions and budgets; Discoverer collects evidence; Planner creates a finite plan; Executor performs approved work; Verifier independently checks acceptance criteria; Reviewer performs correctness/security review; Repairer makes the smallest evidenced correction; Memory Manager persists durable facts; Cost/Context Governor prevents runaway consumption.
