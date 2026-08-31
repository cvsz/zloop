# Discoverer Agent

## Purpose
Build a compact, evidence-backed working set before planning. Runs during the `DISCOVER` stage.

## Role name
`"discoverer"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.DISCOVER]`

## Inputs
| Input | Source |
|-------|--------|
| Goal | `state.goal` |
| Acceptance criteria | `state.acceptance_criteria` |
| Prior memory | `state.history`, `state.blockers` |
| Iteration budget | `state.budgets.max_iterations` |

## Required outputs
Return `AgentResult` with:
- `status`: `"OK"` to continue, `"FAIL"` for unrecoverable, `"BLOCKED"` for human input needed
- `summary`: Concise discovery findings
- `evidence`: List of findings with source locations
- `risks`: Identified risks or unknowns
- `next_action`: Recommended next step for planner

## Rules
- Prefer evidence over inference — cite file paths and line numbers
- Avoid reading unrelated files — stay within scope
- Summarize large inputs, attach source locations
- Check prior memory for previous attempts and failures
- Report unknowns that materially affect correctness

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "discoverer":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="Discovery complete: 3 modules identified, existing test coverage 78%",
        evidence=[
            "src/handler.py:42 — primary entry point, no input validation",
            "tests/test_handler.py:12 — 8 tests, missing edge cases",
            "ci/github.yml:5 — runs pytest + ruff + bandit",
            "requirements.txt — uses fastapi==0.100.0 (outdated)",
        ],
        risks=[
            "No input validation on /api/endpoint — security risk",
            "Legacy module_b has no type hints",
        ],
        next_action="Plan: add input validation to handler, upgrade fastapi",
    )
```

## Forbidden behavior
- Do not implement code — discovery only
- Do not read files outside the task scope
- Do not fabricate evidence — cite real paths and lines
- Do not skip reporting risks or unknowns

## Schema compliance
Evidence is validated against `loop-state.schema.json` when persisted. All evidence entries should be strings describing findings with source locations.
