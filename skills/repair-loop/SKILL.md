---
name: repair-loop
description: Use when verification or review finds failures that need bounded root-cause analysis, correction, and re-verification
---

# Repair Loop

## Purpose
Correct verified failures with bounded retries during the REPAIR stage.

## When to use
- VERIFY fails (state transitions VERIFY → REPAIR)
- REVIEW finds blocking findings (state transitions REVIEW → REPAIR)
- Within `max_repairs` budget

## Procedure

1. **Cluster failures by root cause**
   - Group related failures to avoid duplicate repairs
   - Identify highest-priority blocker (security > correctness > style)

2. **Choose smallest repair**
   - Prefer minimal diffs that address root cause
   - Avoid speculative refactors during repair
   - One repair batch per iteration

3. **Apply and re-verify**
   - Apply repair in isolated workspace
   - Re-run affected verification only (not full suite)
   - Compare failure signature with previous — detect regression

4. **Update counters**
   - `repair_attempts += 1` (engine handles this)
   - If no measurable progress: `progress=False` (engine tracks `consecutive_no_progress`)
   - If `repair_attempts >= max_repairs`: engine transitions to BUDGET_EXHAUSTED

## Required outputs
```python
# In your AgentAdapter.run() when role == "repairer":
return AgentResult(
    status="OK",
    summary="Replaced insecure PRNG with secrets.token_bytes",
    evidence=[
        "git diff: src/crypto.py:15-18",
        "bandit: B303 no longer detected",
        "pytest tests/test_crypto.py: 8 passed",
    ],
    progress=True,  # Measurable progress made
    next_action="Re-run full verification",
)
```

## Repair decision tree
```
Failure identified
├── Root cause clear?
│   ├── YES → Apply targeted fix
│   └── NO → Return INCONCLUSIVE → HANDOFF
├── Fix within scope?
│   ├── YES → Apply and re-verify
│   └── NO → Return BLOCKED → HANDOFF
└── Progress made?
    ├── YES → Continue (progress=True)
    └── NO → Increment no_progress counter
```

## Safety / quality gates
- Never exceed `max_repairs` budget (enforced by engine)
- Each repair must show measurable progress or increment no-progress counter
- No silent scope expansion during repair
- Destructive repairs require explicit approval
- Update persistent loop memory after each repair attempt
