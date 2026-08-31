# Orchestrator Agent

## Purpose
Own the complete loop, enforce invariants, delegate stages, and decide whether to continue, ship, or hand off.

## Implementation
The orchestrator is implemented by `LoopEngine` in `src/zloop_engine.py`. It owns the state machine and enforces all invariants automatically.

## State machine
```
DISCOVER → PLAN → EXECUTE → VERIFY → REVIEW → SHIPPED
                 ↓           ↓        ↓
                 └── REPAIR ←┘        │
                       ↓             │
                       └── VERIFY ────┘
```

Terminal states: `SHIPPED`, `HANDOFF`, `BUDGET_EXHAUSTED`, `POLICY_VIOLATION`, `FAILED`

## Responsibilities

| Responsibility | Implementation |
|----------------|----------------|
| Load durable state | `MemoryStore.load()` or resume from JSONL |
| Validate budgets | `Budgets` dataclass with min/max constraints |
| Select next state | `_transition()` method enforces legal transitions |
| Delegate to roles | `ROLE_FOR_STATE` maps state → agent role |
| Require verification | `verification_passed` gate before SHIPPED |
| Detect no-progress | `consecutive_no_progress >= max_consecutive_no_progress` → HANDOFF |
| Persist state | `memory.save()` after every transition |
| Enforce terminals | `TERMINAL` set checked at loop top |

## Decision order
1. Policy violation? → `POLICY_VIOLATION`
2. Budget exhausted? → `BUDGET_EXHAUSTED` or `HANDOFF`
3. Human approval required? → `HANDOFF` (via `BLOCKED` status)
4. Verification passed? → continue to REVIEW
5. Repair budget available? → `REPAIR` or `BUDGET_EXHAUSTED`
6. New information required? → `HANDOFF` (via `INCONCLUSIVE`)
7. Continue with next bounded action

## Budget enforcement
```python
# Engine checks all six budgets before AND after each adapter call
budgets = Budgets(
    max_iterations=12,
    max_repairs=4,
    max_consecutive_no_progress=2,
    token_budget=500_000,
    cost_budget=25.0,
    wall_clock_budget_seconds=7200,
)
```

## Forbidden behavior
- Do not implement work directly when a specialist role exists
- Do not override verifier failures merely to finish
- Do not silently reset counters
- Do not bypass `_transition()` — all state changes go through it

## Integration
```python
from zloop import LoopEngine, JsonlMemoryStore, Budgets
from my_adapters import MyAgentAdapter

engine = LoopEngine(
    adapter=MyAgentAdapter(),
    memory=JsonlMemoryStore(".zloop/memory.jsonl"),
)
result = engine.run(
    goal="Implement feature X",
    acceptance_criteria=["tests pass", "lint clean"],
    budgets=Budgets(max_iterations=10),
)

if result.state == State.SHIPPED:
    print("Success:", result.evidence)
elif result.state == State.HANDOFF:
    print("Needs human:", result.blockers)
else:
    print("Failed:", result.state, result.blockers)
```

## Output contract
The orchestrator returns a `LoopState` dataclass with:
- `state`: Current terminal or non-terminal state
- `iteration`: Total iterations executed
- `repair_attempts`: Number of repair cycles
- `usage.tokens`: Cumulative tokens consumed
- `usage.cost`: Cumulative cost incurred
- `evidence`: All collected evidence
- `blockers`: Reasons for non-success terminal
- `history`: Per-iteration record with timing
