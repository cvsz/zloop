---
name: loop-orchestration
description: Use when running a bounded autonomous engineering loop with discovery, planning, execution, verification, repair, and handoff decisions
---

# Loop Orchestration

## Purpose
Orchestrate a bounded Discover → Plan → Execute → Verify → Review → Repair → Ship feedback cycle using the zLoop engine.

## When to use
- Running multi-stage engineering tasks with verification gates
- Tasks requiring bounded retries with budget enforcement
- Work that needs maker/checker separation (executor vs verifier)

## Procedure

1. **Initialize**
   - Define `goal` (non-empty string) and `acceptance_criteria` (non-empty list of strings)
   - Configure `Budgets` with: `max_iterations`, `max_repairs`, `max_consecutive_no_progress`, `token_budget`, `cost_budget`, `wall_clock_budget_seconds`
   - Instantiate `LoopEngine` with an `AgentAdapter` and `MemoryStore`

2. **Run loop**
   - Call `engine.run(goal, acceptance_criteria, budgets)`
   - Engine enforces state machine: DISCOVER → PLAN → EXECUTE → VERIFY → REVIEW → SHIPPED/HANDOFF/BUDGET_EXHAUSTED/FAILED

3. **Handle terminal states**
   - `SHIPPED`: All verification and review gates passed
   - `HANDOFF`: Human input required or no progress detected
   - `BUDGET_EXHAUSTED`: Hard limit reached (check `blockers` for reason)
   - `FAILED`: Unrecoverable error outside verify/review
   - `POLICY_VIOLATION`: Security/permission invariant violated

## Integration

```python
from zloop import LoopEngine, JsonlMemoryStore, Budgets, DemoAdapter

engine = LoopEngine(
    adapter=MyAgentAdapter(),
    memory=JsonlMemoryStore(".zloop/memory.jsonl"),
)
result = engine.run(
    goal="Implement feature X",
    acceptance_criteria=["tests pass", "no security regressions", "lint clean"],
    budgets=Budgets(max_iterations=10, token_budget=200_000),
)
print(result.state)  # State.SHIPPED
```

## Required outputs
- `loop_state`: Full `LoopState` dataclass with evidence, history, usage
- `transition decision`: Next state from `_transition()`
- `evidence references`: Collected in `state.evidence` and `state.history`
- `terminal reason`: `state.blockers` if budget/handoff, else `state.state`

## Safety / quality gates
- All six budgets enforced before AND after each adapter call
- File-locked persistence via `JsonlMemoryStore` for concurrent safety
- Schema validation on persisted state (logs warnings on violation)
- Verifier and reviewer are independent roles; executor cannot self-verify
- Budgets treated as hard limits — never silently exceeded
