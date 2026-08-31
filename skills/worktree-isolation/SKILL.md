---
name: worktree-isolation
description: Use when multiple agents or concurrent tasks may mutate a repository and need isolated branches, worktrees, or file ownership boundaries
---

# Worktree Isolation

## Purpose
Prevent concurrent coding agents from overwriting one another.

## When to use
- Multiple zLoop instances running in parallel
- Fleet loops with `parallelism > 1`
- Any concurrent mutation scenario

## Procedure

1. **Assign unique worktree per agent**
   ```bash
   git worktree add .worktrees/agent-<loop_id> -b agent/<loop_id>
   ```

2. **Define file ownership**
   - Map modules to agents when practical
   - Detect overlapping diffs before integration
   - Use `git diff --stat` to identify conflicts early

3. **Sync from known base**
   - All agents start from same base revision
   - Rebase on shared main before merge
   - Never merge unverified work

4. **Merge after verification**
   - Only merge when `state == State.SHIPPED`
   - Run full regression on merged result
   - Clean up worktrees after successful merge

## Required outputs
| Field | Description |
|-------|-------------|
| `workspace_id` | Unique identifier (loop_id or worktree path) |
| `base_revision` | Commit SHA all work derives from |
| `branch` | Agent-specific branch name |
| `changed_files` | List of mutated files |
| `integration_status` | MERGED / PENDING / CONFLICT |

## Concurrent memory safety
`JsonlMemoryStore` uses file locking:
```python
store = JsonlMemoryStore(".zloop/memory.jsonl")
# Safe for concurrent use — fcntl.LOCK_EX serializes writes
```

## Integration with zLoop
```python
import os
from zloop import LoopEngine, JsonlMemoryStore

loop_id = str(uuid.uuid4())
worktree_path = f".worktrees/agent-{loop_id}"

# Create isolated workspace
subprocess.run([
    "git", "worktree", "add", worktree_path,
    "-b", f"agent/{loop_id}"
], check=True)

# Run loop in worktree
os.chdir(worktree_path)
engine = LoopEngine(adapter, JsonlMemoryStore(".zloop/memory.jsonl"))
result = engine.run(goal, criteria)

# Cleanup
os.chdir("..")
subprocess.run(["git", "worktree", "remove", worktree_path])
```

## Safety / quality gates
- Never share working directories between concurrent agents
- Always verify before merging
- Detect overlapping diffs before integration
- Clean up worktrees after use to avoid repository bloat
