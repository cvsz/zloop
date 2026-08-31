# zLoop

**Production-grade framework for bounded autonomous engineering feedback loops.**

Version 1.0.0 — stable, tested, ready for deployment.

## Core lifecycle

```
DISCOVER → PLAN → EXECUTE → VERIFY → REVIEW → REPAIR → VERIFY → SHIPPED
```

Every run is constrained by explicit budgets, stop conditions, tool permissions, idempotency rules, independent verification, persistent memory, and human handoff.

## Design principles

1. Closed loops first.
2. Maker and checker separation.
3. No unbounded retries.
4. Every mutation requires explicit authorization.
5. Persist state outside model context.
6. Every action is auditable and idempotent.
7. Verification decides completion, not the executor.
8. Cost/context are first-class resources.
9. Parallel agents use isolated workspaces/worktrees.
10. Escalate when confidence, progress, or budget falls below policy.

## Features

| Feature | Status |
|---------|--------|
| Six-dimensional budget enforcement | ✅ Pre/post stage checks |
| File-locked concurrent persistence | ✅ `fcntl.LOCK_EX` |
| JSON Schema validation | ✅ `validation.py` |
| Structured logging | ✅ `logging` module |
| Reusable demo adapter | ✅ `reset()` method |
| 22 unit tests | ✅ All passing |
| CLI entry point | ✅ `zloop` command |
| Python package | ✅ `pip install -e .` |

## Repository layout

```text
zloop/
├── AGENTS.md                    # Execution contract
├── README.md                    # This file
├── MANIFEST.in                  # Source distribution manifest
├── setup.py                     # Package configuration
├── config/
│   └── loop.example.yaml        # Example configuration
├── agents/                      # Agent role specifications
│   ├── orchestrator.md
│   ├── discoverer.md
│   ├── planner.md
│   ├── executor.md
│   ├── verifier.md
│   ├── reviewer.md
│   ├── repairer.md
│   ├── memory-manager.md
│   └── cost-context-governor.md
├── skills/                      # Skill definitions
│   ├── loop-orchestration/SKILL.md
│   ├── repository-discovery/SKILL.md
│   ├── execution-planning/SKILL.md
│   ├── bounded-execution/SKILL.md
│   ├── independent-verification/SKILL.md
│   ├── repair-loop/SKILL.md
│   ├── persistent-memory/SKILL.md
│   ├── worktree-isolation/SKILL.md
│   └── cost-governance/SKILL.md
├── schemas/                     # JSON Schema definitions
│   ├── loop-state.schema.json
│   ├── agent-result.schema.json
│   └── verification-result.schema.json
├── policies/                    # Policy documents
│   ├── stop-conditions.md
│   ├── permissions.md
│   ├── idempotency.md
│   └── memory-policy.md
├── examples/                    # Usage examples
│   ├── coding-loop.md
│   ├── research-loop.md
│   ├── content-loop.md
│   └── fleet-loop.md
└── src/                         # Python source
    ├── __init__.py
    ├── loop_engine.py           # Core engine
    ├── validation.py            # Schema validation
    ├── test_loop_engine.py      # Unit tests
    └── schemas/                 # Schemas copied for runtime
```

## Quick start

```bash
# Install
pip install -e .

# Run tests
python3 -m unittest src.test_loop_engine -v

# Run demo
zloop
```

## Usage

```python
from zloop import LoopEngine, JsonlMemoryStore, Budgets, State

# Define your adapter
class MyAdapter:
    def run(self, role, state):
        # Implement role-specific behavior
        return AgentResult(
            status="OK",
            summary=f"{role} completed",
            evidence=[f"{role}:done"],
        )

# Run a loop
engine = LoopEngine(
    adapter=MyAdapter(),
    memory=JsonlMemoryStore(".zloop/memory.jsonl"),
)
result = engine.run(
    goal="Implement feature X",
    acceptance_criteria=["tests pass", "lint clean", "no security issues"],
    budgets=Budgets(max_iterations=10, token_budget=200_000),
)

# Check result
if result.state == State.SHIPPED:
    print("Success!")
elif result.state == State.HANDOFF:
    print("Needs human:", result.blockers)
else:
    print("Failed:", result.state)
```

## Budget defaults

| Budget | Default | Description |
|--------|---------|-------------|
| `max_iterations` | 12 | Total loop iterations |
| `max_repairs` | 4 | Maximum repair attempts |
| `max_consecutive_no_progress` | 2 | Handoff after N no-progress iterations |
| `token_budget` | 500,000 | Cumulative token limit |
| `cost_budget` | $25.00 | Cumulative monetary limit |
| `wall_clock_budget_seconds` | 7200 | Wall-clock time limit (2 hours) |

## Acceptance rule

A loop may ship only when all required verification gates pass and no mandatory review is pending. The executor cannot mark its own output as complete.

## Production deployment

- **Persistence**: Use `JsonlMemoryStore` for single-machine, or implement `MemoryStore` for PostgreSQL/SQLite
- **Concurrency**: File locking via `fcntl.LOCK_EX` for parallel agents
- **Observability**: Structured logging via Python `logging` module
- **Validation**: JSON Schema validation on persisted state
- **Isolation**: Git worktrees for concurrent mutations
- **Governance**: Six-dimensional budget enforcement with escalation

## License

MIT
