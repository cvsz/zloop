# Coding Loop Example

## Goal
Implement one bounded feature or bug fix with full verification.

## Configuration

```python
from zloop import Budgets

budgets = Budgets(
    max_iterations=10,
    max_repairs=3,
    max_consecutive_no_progress=2,
    token_budget=200_000,
    cost_budget=10.0,
    wall_clock_budget_seconds=1800,
)
```

## Flow

| Stage | Role | Output |
|-------|------|--------|
| 1. Discover | `discoverer` | Project instructions, relevant code, tests, CI failures |
| 2. Plan | `planner` | Smallest vertical slice with acceptance criteria |
| 3. Execute | `executor` | Implementation in isolated worktree |
| 4. Verify | `verifier` | Test/static analysis results per criterion |
| 5. Review | `reviewer` | Correctness/security/maintainability assessment |
| 6. Repair | `repairer` | Fix blocking findings (within budget) |
| 7. Re-verify | `verifier` | Confirm all criteria pass |
| 8. Ship | — | Merge worktree, cleanup |

## Example acceptance criteria

```python
criteria = [
    "target behavior implemented",
    "regression test exists",
    "lint/type/test gates pass",
    "no new critical security finding",
    "public interface remains backward compatible",
]
```

## Implementation

```python
from zloop import LoopEngine, JsonlMemoryStore, State, AgentResult, Usage

class CodingAdapter:
    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "discoverer":
            return self._discover(state)
        elif role == "planner":
            return self._plan(state)
        elif role == "executor":
            return self._execute(state)
        elif role == "verifier":
            return self._verify(state)
        elif role == "reviewer":
            return self._review(state)
        elif role == "repairer":
            return self._repair(state)
        return AgentResult(status="OK", summary="Unknown role")

    def _discover(self, state: LoopState) -> AgentResult:
        # Inspect project, find relevant files
        return AgentResult(
            status="OK",
            summary="Found 3 relevant modules, existing tests at 78% coverage",
            evidence=[
                "src/handler.py:42 — primary entry point",
                "tests/test_handler.py — 8 tests present",
                "ci.yml — runs pytest + ruff",
            ],
        )

    def _plan(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Plan: add input validation, add tests",
            evidence=[
                "step1: modify src/handler.py:42-58 (LOCAL_MUTATION)",
                "step2: add tests/test_handler.py::test_validation (LOCAL_MUTATION)",
            ],
        )

    def _execute(self, state: LoopState) -> AgentResult:
        # Implement the plan
        return AgentResult(
            status="OK",
            summary="Implementation complete",
            evidence=["src/handler.py modified: 16 lines added"],
            artifacts=["src/handler.py"],
        )

    def _verify(self, state: LoopState) -> AgentResult:
        # Run tests, lint, security checks
        return AgentResult(
            status="OK",
            summary="All acceptance criteria pass",
            evidence=[
                "pytest: 42 passed",
                "ruff: 0 errors",
                "bandit: no issues",
            ],
            verification_passed=True,
        )

    def _review(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Review complete: no blocking findings",
            evidence=["correctness: PASS", "security: PASS"],
            blocking_review_findings=False,
        )

    def _repair(self, state: LoopState) -> AgentResult:
        # Fix any blocking findings
        return AgentResult(
            status="OK",
            summary="Fixed: added error handling",
            evidence=["src/handler.py:67 — added try/except"],
            progress=True,
        )

# Run the loop
engine = LoopEngine(
    adapter=CodingAdapter(),
    memory=JsonlMemoryStore(".zloop/memory.jsonl"),
)
result = engine.run(
    goal="Add input validation to /api/endpoint",
    acceptance_criteria=[
        "target behavior implemented",
        "regression test exists",
        "lint/type/test gates pass",
        "no new critical security finding",
        "public interface remains backward compatible",
    ],
    budgets=budgets,
)

print(f"Result: {result.state}")
print(f"Iterations: {result.iteration}")
print(f"Evidence: {result.evidence}")
```

## Stop conditions

| Condition | Terminal state |
|-----------|----------------|
| All criteria pass + review clean | `SHIPPED` |
| Human approval needed | `HANDOFF` |
| Budget exhausted | `BUDGET_EXHAUSTED` |
| Unrecoverable error | `FAILED` |
