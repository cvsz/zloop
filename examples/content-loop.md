# Content Loop Example

## Goal
Create publishable content against a defined rubric with bounded revisions.

## Configuration

```python
from zloop import Budgets

budgets = Budgets(
    max_iterations=6,
    max_repairs=3,
    max_consecutive_no_progress=1,
    token_budget=50_000,
    cost_budget=3.0,
    wall_clock_budget_seconds=600,
)
```

## Flow

| Stage | Role | Output |
|-------|------|--------|
| 1. Discover | `discoverer` | Audience, objective, rubric requirements |
| 2. Plan | `planner` | Content outline with acceptance criteria |
| 3. Execute | `executor` | Draft content |
| 4. Verify | `verifier` | Score against rubric |
| 5. Review | `reviewer` | Quality critique |
| 6. Repair | `repairer` | Rewrite to address findings |
| 7. Ship | — | Final content |

## Example acceptance criteria

```python
criteria = [
    "content addresses stated objective",
    "tone matches target audience",
    "all factual claims verified",
    "meets minimum length requirement",
    "passes style guide checklist",
]
```

## Implementation

```python
from zloop import LoopEngine, JsonlMemoryStore, State, AgentResult, Usage

class ContentAdapter:
    def run(self, role: str, state: LoopState) -> AgentResult:
        handlers = {
            "discoverer": self._discover,
            "planner": self._plan,
            "executor": self._execute,
            "verifier": self._verify,
            "reviewer": self._review,
            "repairer": self._repair,
        }
        handler = handlers.get(role)
        if handler:
            return handler(state)
        return AgentResult(status="OK", summary="Unknown role")

    def _discover(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Audience: technical leads. Objective: explain bounded loops.",
            evidence=[
                "audience: engineering team leads",
                "format: technical blog post",
                "length: 800-1200 words",
                "style: clear, concise, code examples",
            ],
        )

    def _plan(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Outline: intro, problem, solution, example, conclusion",
            evidence=[
                "section1: Introduction (100 words)",
                "section2: The problem with unbounded loops (200 words)",
                "section3: Bounded loop pattern (300 words)",
                "section4: Code example (400 words)",
                "section5: Conclusion (100 words)",
            ],
        )

    def _execute(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Draft complete: 950 words",
            evidence=[
                "draft.md: 5 sections, 950 words",
                "code example: included",
            ],
            artifacts=["draft.md"],
        )

    def _verify(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Rubric score: 4/5 — style issues in section 3",
            evidence=[
                "objective: PASS",
                "tone: PASS",
                "facts: PASS",
                "length: PASS (950 words)",
                "style: FAIL (passive voice in section 3)",
            ],
            verification_passed=False,
        )

    def _review(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Review: content is technically accurate, minor style issues",
            evidence=["accuracy: PASS", "clarity: PASS", "style: MINOR"],
            blocking_review_findings=False,
        )

    def _repair(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Rewrote section 3 to use active voice",
            evidence=["section 3: passive → active voice"],
            progress=True,
        )

# Run the loop
engine = LoopEngine(
    adapter=ContentAdapter(),
    memory=JsonlMemoryStore(".zloop/content-memory.jsonl"),
)
result = engine.run(
    goal="Write technical blog post about bounded feedback loops",
    acceptance_criteria=[
        "content addresses stated objective",
        "tone matches target audience",
        "all factual claims verified",
        "meets minimum length requirement",
        "passes style guide checklist",
    ],
    budgets=budgets,
)
```

## Stop conditions

| Condition | Terminal state |
|-----------|----------------|
| Rubric score passes + review clean | `SHIPPED` |
| Cannot meet rubric after repairs | `HANDOFF` |
| Budget exhausted | `BUDGET_EXHAUSTED` |
| Unrecoverable error | `FAILED` |

## Revision budget

Use `max_repairs` to bound rewrites. Do not endlessly rewrite for subjective marginal gains — once blocking findings are addressed, ship.
