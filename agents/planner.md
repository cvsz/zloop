# Planner Agent

## Purpose
Convert discovery evidence into a finite, testable execution plan. Runs during the `PLAN` stage.

## Role name
`"planner"` — mapped via `LoopEngine.ROLE_FOR_STATE[State.PLAN]`

## Inputs
| Input | Source |
|-------|--------|
| Goal | `state.goal` |
| Acceptance criteria | `state.acceptance_criteria` |
| Discovery evidence | `state.evidence` |
| Prior history | `state.history` |

## Plan requirements
Every step must include:
| Field | Required | Description |
|-------|----------|-------------|
| `action` | Yes | What to do |
| `scope` | Yes | Files/systems affected |
| `preconditions` | Yes | What must be true before |
| `expected_result` | Yes | Observable outcome |
| `validation` | Yes | How to verify success |
| `rollback` | For mutations | How to undo |
| `mutation_risk` | Yes | `READ_ONLY` / `LOCAL_MUTATION` / `REMOTE_MUTATION` / `HIGH_IMPACT` |
| `responsible_agent` | Yes | Which role executes |

## Rules
- Prefer smallest vertical slice — each step should be independently verifiable
- Do not create speculative work not tied to acceptance criteria
- Separate mandatory work from optional improvements
- Define a concrete stop condition before execution begins
- Estimate budget class (small/medium/large) for the overall plan

## Output example
```python
def run(self, role: str, state: LoopState) -> AgentResult:
    if role != "planner":
        return AgentResult(status="OK", summary="Not my role")

    return AgentResult(
        status="OK",
        summary="Plan: 3 steps — validate input, add tests, update docs",
        evidence=[
            "step1: ADD input validation to src/handler.py:42-58",
            "   scope: src/handler.py",
            "   validation: pytest tests/test_handler.py::test_validation PASSES",
            "   rollback: git checkout src/handler.py",
            "   risk: LOCAL_MUTATION",
            "step2: ADD tests/test_handler.py::test_edge_cases",
            "   scope: tests/test_handler.py",
            "   validation: pytest tests/test_handler.py PASSES",
            "   rollback: git checkout tests/test_handler.py",
            "   risk: LOCAL_MUTATION",
            "step3: UPDATE docs/api.md with new validation rules",
            "   scope: docs/api.md",
            "   validation: grep 'validation' docs/api.md",
            "   rollback: git checkout docs/api.md",
            "   risk: LOCAL_MUTATION",
        ],
        risks=["Step 1 touches shared handler — run full regression after"],
        next_action="Begin step 1: add input validation to src/handler.py",
    )
```

## Budget estimation
| Class | `max_iterations` | `max_repairs` | `token_budget` |
|-------|------------------|---------------|----------------|
| Small | 5 | 2 | 50,000 |
| Medium | 10 | 4 | 200,000 |
| Large | 20 | 6 | 500,000 |

## Forbidden behavior
- Do not plan open-ended work — every plan must be finite
- Do not skip rollback definitions for mutating steps
- Do not plan HIGH_IMPACT actions without approval mechanism
- Do not ignore acceptance criteria — every criterion must map to a step
