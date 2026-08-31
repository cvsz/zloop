# Research Loop Example

## Goal
Produce an evidence-backed synthesis with verified claims.

## Configuration

```python
from zloop import Budgets

budgets = Budgets(
    max_iterations=8,
    max_repairs=2,
    max_consecutive_no_progress=1,
    token_budget=100_000,
    cost_budget=5.0,
    wall_clock_budget_seconds=900,
)
```

## Flow

| Stage | Role | Output |
|-------|------|--------|
| 1. Discover | `discoverer` | Question scope, authoritative sources |
| 2. Plan | `planner` | Research plan with claim criteria |
| 3. Execute | `executor` | Gather evidence, extract findings |
| 4. Verify | `verifier` | Independent fact checker verifies claims |
| 5. Review | `reviewer` | Synthesis quality assessment |
| 6. Repair | `repairer` | Fix unsupported claims |
| 7. Ship | — | Final synthesis with evidence trail |

## Example acceptance criteria

```python
criteria = [
    "all material claims have traceable evidence",
    "source conflicts are explicitly disclosed",
    "synthesis addresses the original question",
    "confidence level stated per claim",
    "no fabricated or hallucinated sources",
]
```

## Implementation

```python
from zloop import LoopEngine, JsonlMemoryStore, State, AgentResult, Usage

class ResearchAdapter:
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
            summary="Question scoped: 5 authoritative sources identified",
            evidence=[
                "source1: IEEE paper on topic X (2024)",
                "source2: Industry benchmark report",
                "source3: Official documentation",
            ],
            risks=["Source2 may have vendor bias"],
        )

    def _plan(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Plan: extract claims, compare, draft synthesis",
            evidence=[
                "step1: extract key claims from each source",
                "step2: compare conflicting findings",
                "step3: draft synthesis with evidence citations",
            ],
        )

    def _execute(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Evidence extracted from 5 sources",
            evidence=[
                "claim1: supported by source1, source3",
                "claim2: source2 conflicts with source4",
                "claim3: supported by all sources",
            ],
        )

    def _verify(self, state: LoopState) -> AgentResult:
        # Verify each claim has real, accessible sources
        return AgentResult(
            status="OK",
            summary="4/5 claims verified — claim2 source conflict noted",
            evidence=[
                "claim1: VERIFIED (DOI: 10.1234/abc)",
                "claim2: INCONCLUSIVE (conflicting sources)",
                "claim3: VERIFIED (official docs)",
            ],
            verification_passed=False,  # Triggers repair for claim2
        )

    def _review(self, state: LoopState) -> AgentResult:
        return AgentResult(
            status="OK",
            summary="Review: synthesis structure is sound",
            evidence=["structure: PASS", "citations: PASS"],
            blocking_review_findings=False,
        )

    def _repair(self, state: LoopState) -> AgentResult:
        # Disclose the conflict explicitly
        return AgentResult(
            status="OK",
            summary="Added conflict disclosure for claim2",
            evidence=["synthesis.md: added 'Conflicting Evidence' section"],
            progress=True,
        )

# Run the loop
engine = LoopEngine(
    adapter=ResearchAdapter(),
    memory=JsonlMemoryStore(".zloop/research-memory.jsonl"),
)
result = engine.run(
    goal="Synthesize findings on topic X from authoritative sources",
    acceptance_criteria=[
        "all material claims have traceable evidence",
        "source conflicts are explicitly disclosed",
        "synthesis addresses the original question",
        "confidence level stated per claim",
        "no fabricated or hallucinated sources",
    ],
    budgets=budgets,
)
```

## Stop conditions

| Condition | Terminal state |
|-----------|----------------|
| All claims verified + conflicts disclosed | `SHIPPED` |
| Cannot verify key claims | `HANDOFF` |
| Budget exhausted | `BUDGET_EXHAUSTED` |
| Unrecoverable error | `FAILED` |
