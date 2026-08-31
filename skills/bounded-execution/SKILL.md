---
name: bounded-execution
description: Use when executing approved implementation or operational plan steps that mutate files, services, repositories, or external state
---

# Bounded Execution

## Purpose
Perform approved actions during the EXECUTE stage without expanding scope.

## When to use
- After PLAN completes (state transitions PLAN → EXECUTE)
- When mutating files, services, or external state
- Within an isolated workspace/worktree

## Procedure

1. **Workspace setup**
   - Use isolated worktree when multiple agents may run concurrently
   - Verify base revision matches plan assumptions
   - Confirm permissions for intended mutations

2. **Step execution**
   - Execute one plan step at a time
   - Record outputs and evidence for each step
   - Stop immediately on unexpected destructive changes

3. **Mutation recording**
   - Log: actor, target, action, scope, approval source, idempotency key, timestamp, result
   - Use idempotency key format: `<loop_id>:<plan_version>:<step_id>:<target>`

4. **Error handling**
   - Permission error → return `status="BLOCKED"` (triggers HANDOFF)
   - Invariant violation → return `status="FAIL"` (triggers FAILED)
   - Unexpected side effect → stop and report

## Required outputs
```python
# In your AgentAdapter.run() when role == "executor":
return AgentResult(
    status="OK",
    summary="Step 1 complete: modified src/handler.py:42-58",
    evidence=[
        "git diff --stat: src/handler.py | 15 +++++",
        "local test: pytest tests/test_handler.py::test_fix PASSED",
    ],
    artifacts=["src/handler.py"],
    risks=["modified shared handler — full regression recommended"],
    next_action="Proceed to step 2: add test",
)
```

## Mutation lifecycle
```
NOT_STARTED → IN_PROGRESS → SUCCEEDED | FAILED_RETRYABLE | FAILED_FINAL
```

## Safety / quality gates
- Operate within declared scope — no speculative changes
- Produce evidence for material claims (diffs, test results)
- Never bypass stop conditions or permission boundaries
- Prefer reversible changes; flag irreversible for approval
- Update persistent loop memory after meaningful progress
