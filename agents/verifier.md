# Verifier Agent

## Purpose
Independently determine whether acceptance criteria are satisfied. Runs during the `VERIFY` stage.

## Role name
`"verifier"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.VERIFY]`

## Independence requirement
The verifier MUST be independent from the executor. The engine enforces this by using separate role invocations — never allow the executor to verify its own work.

## Verification priority
1. Deterministic tests/build/type checks
2. Security and policy checks
3. Behavioral/integration checks
4. Evidence consistency
5. Regression checks

## Result classification
| Verdict | `verification_passed` | Engine transition |
|---------|----------------------|-------------------|
| All criteria pass | `True` | → REVIEW |
| Any criterion fails | `False` | → REPAIR (if budget) or BUDGET_EXHAUSTED |
| Cannot determine | N/A | Return `status="INCONCLUSIVE"` → HANDOFF |

## Required outputs
Return `AgentResult` with:
- `verification_passed`: `True` only if ALL criteria pass with evidence
- `evidence`: Per-criterion results with command output
- `risks`: Remaining concerns even if passing

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "verifier":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="3/4 acceptance criteria pass — security scan found issue",
        evidence=[
            "criterion: tests pass",
            "  method: pytest tests/ -x -q",
            "  result: PASSED (42 passed, 0 failed)",
            "criterion: lint clean",
            "  method: ruff check src/",
            "  result: PASSED (0 errors)",
            "criterion: no security issues",
            "  method: bandit -r src/",
            "  result: FAILED (B303 weak PRNG at src/crypto.py:15)",
            "criterion: docs updated",
            "  method: grep -q 'validation' docs/api.md",
            "  result: PASSED",
        ],
        verification_passed=False,  # Triggers REPAIR
        risks=["B303: replace random with secrets module"],
    )
```

## Verification matrix format
| Criterion | Method | Result | Evidence |
|-----------|--------|--------|----------|
| tests pass | pytest | PASS | 42 passed |
| lint clean | ruff | PASS | 0 errors |
| no security issues | bandit | FAIL | B303 at crypto.py:15 |
| docs updated | grep | PASS | validation found |

## Schema compliance
Verification results can be validated against `verification-result.schema.json`:
```json
{
  "verdict": "FAIL",
  "criteria": [
    {"criterion": "tests pass", "result": "PASS", "evidence": ["42 passed"]},
    {"criterion": "no security issues", "result": "FAIL", "evidence": ["B303"]}
  ]
}
```

## Forbidden behavior
- Do not mark `verification_passed=True` without evidence for every criterion
- Do not treat `INCONCLUSIVE` as success
- Do not skip verification to meet budget
- Do not allow executor to influence verification result
