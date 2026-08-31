---
name: persistent-memory
description: Use when a loop or long-running task must persist factual state, decisions, evidence, blockers, or next actions outside model context
---

# Persistent Memory

## Purpose
Maintain durable factual project memory across loop runs using `MemoryStore`.

## When to use
- Every zLoop run (engine auto-saves via `JsonlMemoryStore`)
- After each stage transition (engine handles this automatically)
- When recovering from HANDOFF or resuming interrupted work

## Built-in persistence
The zLoop engine automatically saves `LoopState` after every transition:
- `JsonlMemoryStore` writes JSONL (one JSON object per line)
- File-locked with `fcntl.LOCK_EX` for concurrent safety
- Optional schema validation on save (logs warnings)

```python
from zloop import JsonlMemoryStore

# Default: validates against schema, file-locked
store = JsonlMemoryStore(".zloop/memory.jsonl")

# Disable validation for performance
store = JsonlMemoryStore(".zloop/memory.jsonl", validate=False)
```

## What is persisted
| Field | Content |
|-------|---------|
| `loop_id` | Unique UUID per run |
| `goal` | Normalized objective |
| `acceptance_criteria` | Required success conditions |
| `state` | Current lifecycle state |
| `iteration` | Current iteration count |
| `repair_attempts` | Repair count |
| `consecutive_no_progress` | No-progress streak |
| `usage.tokens` | Cumulative tokens used |
| `usage.cost` | Cumulative cost |
| `evidence` | Collected evidence list |
| `blockers` | Reasons for stop/handoff |
| `history` | Per-iteration record with timing |
| `started_at` | Unix timestamp |

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

## Required outputs
- Durable state record (via `MemoryStore.save()`)
- Concise memory update with evidence references

## Forbidden memory
Never persist:
- Credentials, tokens, API keys
- Unnecessary personal data
- Hidden reasoning or chain-of-thought
- Unredacted secrets

## Safety / quality gates
- Schema validation on save (warnings only — never blocks)
- File locking prevents concurrent write corruption
- Secrets must never enter the memory store
- Compacted evidence preferred over full transcripts
