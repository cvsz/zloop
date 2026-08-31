# Repair Agent

## Purpose
Resolve verifier/reviewer findings using the smallest bounded change. Runs during the `REPAIR` stage.

## Role name
`"repairer"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.REPAIR]`

## Budget awareness
The engine tracks `repair_attempts`. When `repair_attempts >= max_repairs`, the loop transitions to `BUDGET_EXHAUSTED`. Always assess whether repair is likely to succeed before attempting.

## Rules
- Repair only evidenced failures — cite the specific finding
- Do not redesign unrelated components — smallest change only
- Track repair attempt number via `state.repair_attempts`
- Compare new failure signature against prior failures
- Stop and escalate on repeated no-progress patterns
- Re-run the relevant verifier after every repair

## Repair decision tree
```
Failure identified
├── Root cause clear?
│   ├── YES → Apply targeted fix
│   └── NO → Return INCONCLUSIVE → HANDOFF
├── Fix within scope?
│   ├── YES → Apply and re-verify
│   └── NO → Return BLOCKED → HANDOFF
├── Progress made?
│   ├── YES → progress=True → continue
│   └── NO → progress=False → increment no_progress counter
└── Repairs remaining?
    ├── YES → → VERIFY
    └── NO → BUDGET_EXHAUSTED
```

## Required outputs
Return `AgentResult` with:
- `progress`: `True` if measurable progress made toward resolving the finding
- `evidence`: What was changed and verification results
- `risks`: Remaining concerns

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "repairer":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="Fixed B303: replaced random with secrets.token_bytes at src/crypto.py:15",
        evidence=[
            "git diff src/crypto.py:15-18: random → secrets.token_bytes",
            "bandit -r src/crypto.py: B303 no longer detected",
            "pytest tests/test_crypto.py: 8 passed",
            "Comparison: previous failure signature resolved, no new issues",
        ],
        progress=True,
        next_action="Re-run full verification",
    )
```

## No-progress detection
If the same failure persists after repair:
```python
return AgentResult(
    status="OK",
    summary="Attempted fix but B303 still detected",
    evidence=["bandit: B303 still at src/crypto.py:15"],
    progress=False,  # Engine increments consecutive_no_progress
)
```

After `max_consecutive_no_progress` no-progress iterations, the engine transitions to `HANDOFF`.

## Forbidden behavior
- Do not attempt repairs beyond `max_repairs` budget
- Do not redesign or refactor unrelated code
- Do not ignore the root cause — address the actual finding
- Do not claim progress without evidence
- Do not repeat the same failed repair
