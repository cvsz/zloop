# Fleet Loop Example

## Goal
Coordinate multiple specialist agents working in parallel on a shared goal.

## Architecture

```text
                    Orchestrator (LoopEngine)
            ┌──────────┼──────────┐
            ↓          ↓          ↓
       Research     Engineer       QA
       (discoverer)  (executor)    (verifier)
            ↓          ↓          ↓
       evidence    worktree     verification
                       ↓
                    reviewer
                       ↓
                    repair
```

## Fleet rules

| Rule | Implementation |
|------|----------------|
| Orchestrator owns global budget | Single `LoopEngine` instance |
| Specialists receive scoped subgoals | Separate `AgentAdapter.run()` branches |
| Mutating specialists use isolated worktrees | Git worktree per agent |
| Shared memory is authoritative | `JsonlMemoryStore` with file locking |
| Cross-agent file conflicts detected before merge | `git diff --stat` comparison |
| QA/verifier independent of implementation | Separate roles in `ROLE_FOR_STATE` |
| Parallelism capped | `max_iterations` budget enforcement |

## Configuration

```python
from zloop import Budgets

fleet_budgets = Budgets(
    max_iterations=20,
    max_repairs=6,
    max_consecutive_no_progress=3,
    token_budget=500_000,
    cost_budget=50.0,
    wall_clock_budget_seconds=14400,
)

specialist_budgets = Budgets(
    max_iterations=8,
    max_repairs=2,
    max_consecutive_no_progress=1,
    token_budget=100_000,
    cost_budget=10.0,
    wall_clock_budget_seconds=1800,
)
```

## Implementation

```python
import subprocess
import uuid
from zloop import (
    LoopEngine, JsonlMemoryStore, Budgets,
    LoopState, AgentResult, State, Usage
)

class FleetOrchestrator:
    """Coordinates multiple specialist loops with shared memory."""

    def __init__(self, memory_path: str):
        self.memory_path = memory_path
        self.worktrees = {}

    def create_worktree(self, agent_id: str) -> str:
        """Create isolated worktree for an agent."""
        worktree_path = f".worktrees/agent-{agent_id}"
        branch_name = f"agent/{agent_id}"

        subprocess.run([
            "git", "worktree", "add", worktree_path,
            "-b", branch_name
        ], check=True)

        self.worktrees[agent_id] = {
            "path": worktree_path,
            "branch": branch_name,
        }
        return worktree_path

    def cleanup_worktree(self, agent_id: str):
        """Remove worktree after agent completes."""
        if agent_id in self.worktrees:
            wt = self.worktrees[agent_id]
            subprocess.run(
                ["git", "worktree", "remove", wt["path"]],
                check=True,
            )
            del self.worktrees[agent_id]

    def run_specialist(
        self,
        agent_id: str,
        adapter: "AgentAdapter",
        goal: str,
        criteria: list[str],
        budgets: Budgets,
    ) -> LoopState:
        """Run a single specialist agent in isolation."""
        # Create isolated worktree
        worktree_path = self.create_worktree(agent_id)
        try:
            # Run loop in worktree directory
            import os
            original_dir = os.getcwd()
            os.chdir(worktree_path)
            try:
                engine = LoopEngine(
                    adapter=adapter,
                    memory=JsonlMemoryStore(self.memory_path),
                )
                result = engine.run(
                    goal=goal,
                    acceptance_criteria=criteria,
                    budgets=budgets,
                )
                return result
            finally:
                os.chdir(original_dir)
        finally:
            # Cleanup worktree if shipped
            if result.state == State.SHIPPED:
                self.cleanup_worktree(agent_id)

    def merge_results(self, results: dict[str, LoopState]) -> bool:
        """Check for conflicts before merging."""
        # Detect overlapping file changes
        changed_files = {}
        for agent_id, result in results.items():
            for artifact in result.artifacts:
                if artifact in changed_files:
                    return False  # Conflict detected
                changed_files[artifact] = agent_id
        return True


class ResearchAdapter:
    """Specialist adapter for research tasks."""
    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "discoverer":
            return AgentResult(
                status="OK",
                summary="Research: found 5 relevant sources",
                evidence=["source1: paper", "source2: benchmark"],
            )
        return AgentResult(
            status="OK",
            summary=f"{role}: research stage complete",
        )


class EngineerAdapter:
    """Specialist adapter for implementation tasks."""
    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "executor":
            return AgentResult(
                status="OK",
                summary="Engineer: implementation complete",
                artifacts=["src/feature.py"],
            )
        return AgentResult(
            status="OK",
            summary=f"{role}: engineering stage complete",
        )


class QAAdapter:
    """Specialist adapter for verification tasks."""
    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "verifier":
            return AgentResult(
                status="OK",
                summary="QA: all tests pass",
                verification_passed=True,
            )
        return AgentResult(
            status="OK",
            summary=f"{role}: QA stage complete",
        )


# Run fleet
fleet = FleetOrchestrator(".zloop/fleet-memory.jsonl")

research_result = fleet.run_specialist(
    agent_id="research-001",
    adapter=ResearchAdapter(),
    goal="Research best practices for bounded loops",
    criteria=["5+ authoritative sources", "conflicts documented"],
    budgets=specialist_budgets,
)

engineer_result = fleet.run_specialist(
    agent_id="engineer-001",
    adapter=EngineerAdapter(),
    goal="Implement bounded loop engine",
    criteria=["tests pass", "lint clean", "no security issues"],
    budgets=specialist_budgets,
)

qa_result = fleet.run_specialist(
    agent_id="qa-001",
    adapter=QAAdapter(),
    goal="Verify implementation meets criteria",
    criteria=["all acceptance criteria verified", "no blocking findings"],
    budgets=specialist_budgets,
)

# Merge if all shipped
results = {
    "research": research_result,
    "engineer": engineer_result,
    "qa": qa_result,
}

if all(r.state == State.SHIPPED for r in results.values()):
    if fleet.merge_results(results):
        print("All specialists shipped, no conflicts — ready to merge")
    else:
        print("Conflict detected — human resolution required")
else:
    failed = [k for k, v in results.items() if v.state != State.SHIPPED]
    print(f"Specialists did not ship: {failed}")
```

## Stop conditions

| Condition | Terminal state |
|-----------|----------------|
| All specialists ship + no conflicts | `SHIPPED` |
| File conflict detected | `HANDOFF` |
| Any specialist exhausts budget | `BUDGET_EXHAUSTED` |
| Unrecoverable error | `FAILED` |

## Concurrency safety

`JsonlMemoryStore` uses `fcntl.LOCK_EX` for file-safe concurrent writes from multiple agents.
