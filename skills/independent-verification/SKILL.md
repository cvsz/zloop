---
name: independent-verification
description: Use when checking whether completed work meets acceptance criteria, especially when the implementer should not be the only verifier
---

# Independent Verification

## Purpose
Evaluate results independently from the agent that created them during the VERIFY stage.

## When to use
- After EXECUTE completes (state transitions EXECUTE → VERIFY)
- When the executor cannot be the sole verifier
- To enforce maker/checker separation

## Procedure

1. **Map criteria to verification methods**
   - Each acceptance criterion → at least one deterministic check
   - Prefer: unit tests, integration tests, static analysis, security scans
   - Avoid: subjective quality judgments without measurable thresholds

2. **Run narrow-to-broad**
   - Unit tests first (fast, isolated)
   - Integration tests second
   - Regression / broader checks last
   - Static analysis and security scans in parallel

3. **Classify results per criterion**
   - `PASS`: Criterion met with evidence
   - `FAIL`: Criterion not met — include failure signature
   - `INCONCLUSIVE`: Cannot determine — triggers HANDOFF

4. **Return structured evidence**
   - Use `verification_passed: bool` on `AgentResult`
   - Include command output, test results, log excerpts in `evidence`

## Required outputs
```python
# In your AgentAdapter.run() when role == "verifier":
return AgentResult(
    status="OK",
    summary="3/4 acceptance criteria pass — security scan found issue",
    evidence=[
        "pytest: 42 passed, 0 failed",
        "ruff: no lint errors",
        "bandit: B303 detected in src/crypto.py:15",
    ],
    verification_passed=False,  # Triggers REPAIR
    risks=["weak PRNG in crypto.py — replace with secrets module"],
)
```

## Verification matrix format
| Criterion | Method | Result | Evidence |
|-----------|--------|--------|----------|
| tests pass | pytest | PASS | 42 passed |
| lint clean | ruff | PASS | 0 errors |
| no security issues | bandit | FAIL | B303 at crypto.py:15 |
| docs updated | glob check | PASS | docs/api.md modified |

## Safety / quality gates
- Verifier must be independent from executor (different role/agent)
- Never override verifier failures merely to finish
- Evidence required for every FAIL/INCONCLUSIVE classification
- Ambiguous results → INCONCLUSIVE → HANDOFF (not silent pass)
