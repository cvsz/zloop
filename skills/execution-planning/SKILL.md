---
name: execution-planning
description: Use when requirements must become a finite executable plan with acceptance criteria, validation, rollback notes, and stop conditions
---

# Execution Planning

## Purpose
Produce an executable, finite vertical-slice plan during the PLAN stage of a zLoop.

## When to use
- After DISCOVER completes (state transitions DISCOVER → PLAN)
- When requirements are clear enough to break into ordered steps
- Before any mutation or execution occurs

## Procedure

1. **Translate requirements to acceptance criteria**
   - Each criterion must be independently verifiable
   - Use SMART format: Specific, Measurable, Achievable, Relevant, Time-bound
   - Map each criterion to a verification method (test, lint, manual check)

2. **Break work into ordered steps**
   - Vertical slice: each step should produce a verifiable increment
   - Identify dependencies between steps
   - Mark which steps are pure (read-only) vs mutating

3. **Attach validation and rollback**
   - For each mutating step: define how to validate success
   - Define rollback: git revert, feature flag off, database migration reversal
   - Identify irreversible operations — these require explicit approval

4. **Budget estimation**
   - Classify as small/medium/large based on blast radius
   - Set appropriate `max_iterations` and `max_repairs` in `Budgets`
   - Identify steps that can run in parallel vs must be sequential

## Required outputs
```python
# In your AgentAdapter.run() when role == "planner":
return AgentResult(
    status="OK",
    summary="Plan: 3 steps — implement fix, add test, update docs",
    evidence=[
        "step1: modify src/handler.py:42 (mutation)",
        "step2: add tests/test_handler.py::test_fix (mutation)",
        "step3: update docs/api.md (mutation)",
    ],
    risks=["step1 touches shared handler — run full regression"],
    next_action="Begin step 1: implement fix in src/handler.py",
)
```

## Plan structure
| Field | Required | Description |
|-------|----------|-------------|
| `steps` | Yes | Ordered list of discrete actions |
| `acceptance_criteria` | Yes | Verifiable success conditions |
| `validation` | Yes | How to verify each step |
| `rollback` | For mutations | How to undo each step |
| `approval_required` | For HIGH_IMPACT | Whether human sign-off needed |

## Safety / quality gates
- Plan must be finite — no open-ended "iterate until done"
- Every mutation has a corresponding rollback
- Budgets set before execution begins
- Destructive operations flagged for explicit approval
