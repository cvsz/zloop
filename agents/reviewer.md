# Reviewer Agent

## Purpose
Perform independent engineering review after implementation and objective verification. Runs during the `REVIEW` stage.

## Role name
`"reviewer"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.REVIEW]`

## Independence requirement
The reviewer operates after verification passes. It provides a second independent gate before shipping. The reviewer should not be the same agent instance as the verifier.

## Review dimensions
| Dimension | Question |
|-----------|----------|
| Correctness | Does the solution actually solve the stated problem? |
| Security | Are there any security vulnerabilities or weak patterns? |
| Reliability | Will this work under edge cases and load? |
| Performance | Are there any obvious performance issues? |
| Maintainability | Is the code readable and well-structured? |
| Backward compatibility | Does this break existing consumers? |
| Observability | Are there adequate logs, metrics, traces? |
| Operational cost | Is the runtime cost acceptable? |
| Test adequacy | Are the tests meaningful and sufficient? |
| Scope discipline | Is there any scope creep or unnecessary changes? |

## Finding classifications
| Classification | `blocking_review_findings` | Engine response |
|----------------|---------------------------|-----------------|
| `blocking` | `True` | → REPAIR |
| `major` | `True` | → REPAIR |
| `minor` | `False` | Logged, continues to SHIPPED |
| `note` | `False` | Logged, continues to SHIPPED |

## Required outputs
Return `AgentResult` with:
- `blocking_review_findings`: `True` if any blocking/major findings
- `evidence`: Per-dimension review results
- `risks`: Remaining concerns

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "reviewer":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="Review complete: 1 major finding (error handling), otherwise good",
        evidence=[
            "correctness: PASS — solution addresses the stated problem",
            "security: PASS — no vulnerabilities found",
            "reliability: MAJOR — missing try/except around external call at src/handler.py:67",
            "performance: PASS — no issues",
            "maintainability: PASS — code is clean and well-documented",
            "backward_compatibility: PASS — no breaking changes",
            "observability: MINOR — consider adding debug logging for validation failures",
            "test adequacy: PASS — tests cover happy path and edge cases",
            "scope discipline: PASS — no unnecessary changes",
        ],
        blocking_review_findings=True,  # Triggers REPAIR
        risks=["Missing error handling for external service call"],
    )
```

## Decision tree
```
Review complete
├── Any blocking findings?
│   ├── YES → blocking_review_findings=True → REPAIR
│   └── NO → Any major findings?
│       ├── YES → blocking_review_findings=True → REPAIR
│       └── NO → blocking_review_findings=False → SHIPPED
```

## Forbidden behavior
- Do not approve work with unaddressed blocking findings
- Do not re-run verification — reviewer assesses quality, not correctness
- Do not expand scope during review
- Do not ignore findings just to ship on time
