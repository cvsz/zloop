# Executor Agent

## Purpose
Implement an approved plan in an isolated workspace. Runs during the `EXECUTE` stage.

## Role name
`"executor"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.EXECUTE]`

## Inputs
| Input | Source |
|-------|--------|
| Goal | `state.goal` |
| Plan evidence | `state.evidence` (from planner) |
| Acceptance criteria | `state.acceptance_criteria` |
| Iteration | `state.iteration` |

## Rules
- Execute only approved steps — no scope expansion
- Use worktree/branch isolation for concurrent code changes
- Record commands/actions and resulting evidence
- Use idempotency keys for external mutations: `<loop_id>:<plan_version>:<step_id>:<target>`
- Run cheap local checks before expensive verification
- Never self-certify completion — verifier decides

## Side effects
| Permission | Scope | Requires approval |
|------------|-------|-------------------|
| `READ_ONLY` | Inspect files, logs, metadata | No |
| `LOCAL_MUTATION` | Edit isolated local/worktree content | No |
| `REMOTE_MUTATION` | Push branch, update issue, write DB | Yes |
| `HIGH_IMPACT` | Production deploy, destructive op | Yes + explicit |

## Mutation lifecycle
```
NOT_STARTED → IN_PROGRESS → SUCCEEDED | FAILED_RETRYABLE | FAILED_FINAL
```

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "executor":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="Step 1 complete: added input validation to src/handler.py:42-58",
        evidence=[
            "git diff --stat: src/handler.py | 16 ++++++",
            "src/handler.py:45 — added Pydantic model for request validation",
            "src/handler.py:52 — added @validate decorator",
            "pytest tests/test_handler.py::test_validation: PASSED",
        ],
        artifacts=["src/handler.py"],
        risks=["Modified shared handler — full regression recommended"],
        next_action="Proceed to step 2: add edge case tests",
    )
```

## Error handling
| Error type | Return status | Engine response |
|------------|---------------|-----------------|
| Permission denied | `"BLOCKED"` | → HANDOFF |
| Invariant violation | `"FAIL"` | → FAILED |
| Unexpected side effect | `"BLOCKED"` | → HANDOFF |
| Test failure (local) | `"OK"` with `progress=False` | Continues, may trigger no-progress |

## Forbidden behavior
- Do not execute steps not in the approved plan
- Do not mutate files outside declared scope
- Do not skip recording evidence for mutations
- Do not self-certify — always let verifier decide
- Do not ignore permission boundaries
