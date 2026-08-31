# Memory Manager Agent

## Purpose
Persist information required for future loop runs without depending on model context.

## Implementation
The memory manager is implemented by `MemoryStore` protocol. The default implementation is `JsonlMemoryStore` which writes JSONL with file locking.

## Role name
The memory manager is not a separate role — it's invoked automatically by the engine after every state transition via `memory.save(state)`.

## Store contents
| Category | Examples |
|----------|----------|
| Decisions | Why a particular approach was chosen |
| Attempt history | What was tried and what happened |
| Verification evidence | Test results, lint output, scan findings |
| Blockers | Budget exhaustion, permission errors, unknowns |
| Architecture constraints | Accepted patterns, forbidden approaches |
| Reusable lessons | What worked, what didn't |
| Artifact locations | File paths, commit SHAs, build IDs |
| Unresolved follow-ups | Items for future loops |

## Do not store
| Forbidden | Reason |
|-----------|--------|
| Secrets | Security risk |
| Raw credentials | Security risk |
| Unnecessary private data | Privacy violation |
| Transient chain-of-thought | Not factual, not reusable |

## Persistence format
```json
{
  "loop_id": "uuid",
  "goal": "Implement feature X",
  "acceptance_criteria": ["tests pass"],
  "state": "SHIPPED",
  "iteration": 7,
  "repair_attempts": 1,
  "usage": {"tokens": 4500, "cost": 0.045},
  "evidence": ["src/handler.py:42 — validation added"],
  "blockers": [],
  "history": [
    {"iteration": 1, "role": "discoverer", "status": "OK", "summary": "...", "stage_seconds": 0.1}
  ],
  "started_at": 1788152333.7286417
}
```

## Custom MemoryStore
```python
from zloop import MemoryStore, LoopState

class PostgresMemoryStore(MemoryStore):
    def __init__(self, dsn: str):
        self.conn = psycopg2.connect(dsn)

    def save(self, state: LoopState) -> None:
        self.conn.execute(
            """INSERT INTO loop_state (loop_id, data, updated_at)
               VALUES (%s, %s, NOW())
               ON CONFLICT (loop_id) DO UPDATE SET data = EXCLUDED.data""",
            (state.loop_id, json.dumps(asdict(state))),
        )
        self.conn.commit()
```

## Schema validation
Persisted state is validated against `schemas/loop-state.schema.json`. Validation warnings are logged but do not block persistence.

## Output contract
The memory manager does not return `AgentResult` — it persists the current `LoopState` directly. The `AgentResult.memory_updates` field is for the adapter to suggest additional memory entries.

## Integration
```python
from zloop import JsonlMemoryStore, LoopEngine

# Default: file-locked JSONL with schema validation
memory = JsonlMemoryStore(".zloop/memory.jsonl")

# Disable validation for performance
memory = JsonlMemoryStore(".zloop/memory.jsonl", validate=False)

engine = LoopEngine(adapter=MyAdapter(), memory=memory)
```

## Forbidden behavior
- Do not store credentials, tokens, or API keys
- Do not store raw chain-of-thought reasoning
- Do not store unnecessary personal data
- Do not bypass file locking in custom implementations
