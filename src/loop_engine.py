"""zLoop Engine — bounded autonomous feedback loop state machine."""

from __future__ import annotations

import fcntl
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Protocol, Optional

try:
    from .validation import is_valid_loop_state
except ImportError:
    from validation import is_valid_loop_state

logger = logging.getLogger("zloop")


class State(str, Enum):
    DISCOVER = "DISCOVER"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REVIEW = "REVIEW"
    REPAIR = "REPAIR"
    SHIPPED = "SHIPPED"
    HANDOFF = "HANDOFF"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    FAILED = "FAILED"


TERMINAL = {
    State.SHIPPED,
    State.HANDOFF,
    State.BUDGET_EXHAUSTED,
    State.POLICY_VIOLATION,
    State.FAILED,
}


@dataclass
class Budgets:
    max_iterations: int = 12
    max_repairs: int = 4
    max_consecutive_no_progress: int = 2
    token_budget: int = 500_000
    cost_budget: float = 25.0
    wall_clock_budget_seconds: int = 7200


@dataclass
class Usage:
    tokens: int = 0
    cost: float = 0.0


@dataclass
class AgentResult:
    status: str
    summary: str
    evidence: List[str] = field(default_factory=list)
    next_action: Optional[str] = None
    risks: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    memory_updates: List[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    progress: bool = True
    verification_passed: bool = False
    blocking_review_findings: bool = False


@dataclass
class LoopState:
    loop_id: str
    goal: str
    acceptance_criteria: List[str]
    budgets: Budgets
    state: State = State.DISCOVER
    iteration: int = 0
    repair_attempts: int = 0
    consecutive_no_progress: int = 0
    usage: Usage = field(default_factory=Usage)
    evidence: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)


class AgentAdapter(Protocol):
    def run(self, role: str, state: LoopState) -> AgentResult: ...


class MemoryStore(Protocol):
    def save(self, state: LoopState) -> None: ...


class JsonlMemoryStore:
    """Thread/process-safe JSONL memory store with file locking."""

    def __init__(self, path: str = ".zloop/memory.jsonl", validate: bool = True) -> None:
        self.path = path
        self.validate = validate
        self._lock_path = f"{path}.lock"

    def save(self, state: LoopState) -> None:
        record = asdict(state)
        record["state"] = state.state.value
        record["budgets"] = asdict(state.budgets)
        record["usage"] = asdict(state.usage)

        if self.validate and not is_valid_loop_state(record):
            logger.warning(
                "Loop state for %s failed schema validation — saving anyway",
                state.loop_id,
            )

        line = json.dumps(record, ensure_ascii=False) + "\n"

        lock_fd = open(self._lock_path, "w")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()


class LoopEngine:
    """Bounded feedback loop state machine.

    Enforces budgets, maker/checker separation, and terminal conditions.
    """

    ROLE_FOR_STATE = {
        State.DISCOVER: "discoverer",
        State.PLAN: "planner",
        State.EXECUTE: "executor",
        State.VERIFY: "verifier",
        State.REVIEW: "reviewer",
        State.REPAIR: "repairer",
    }

    def __init__(
        self,
        adapter: AgentAdapter,
        memory: MemoryStore,
        *,
        enable_logging: bool = True,
    ) -> None:
        self.adapter = adapter
        self.memory = memory
        self.enable_logging = enable_logging

    def _log(self, level: int, msg: str, *args: Any) -> None:
        if self.enable_logging:
            logger.log(level, msg, *args)

    def _budget_reason(self, s: LoopState) -> Optional[str]:
        elapsed = time.time() - s.started_at
        if s.iteration >= s.budgets.max_iterations:
            return "max_iterations"
        if s.repair_attempts >= s.budgets.max_repairs:
            return "max_repairs"
        if s.consecutive_no_progress >= s.budgets.max_consecutive_no_progress:
            return "no_progress"
        if s.usage.tokens >= s.budgets.token_budget:
            return "token_budget"
        if s.usage.cost >= s.budgets.cost_budget:
            return "cost_budget"
        if elapsed >= s.budgets.wall_clock_budget_seconds:
            return "wall_clock_budget"
        return None

    def _transition(self, s: LoopState, r: AgentResult) -> State:
        if r.status == "BLOCKED":
            return State.HANDOFF
        if r.status == "INCONCLUSIVE":
            return State.HANDOFF
        if r.status == "FAIL" and s.state not in {State.VERIFY, State.REVIEW}:
            return State.FAILED

        if s.state == State.DISCOVER:
            return State.PLAN
        if s.state == State.PLAN:
            return State.EXECUTE
        if s.state == State.EXECUTE:
            return State.VERIFY
        if s.state == State.VERIFY:
            return State.REVIEW if r.verification_passed else State.REPAIR
        if s.state == State.REVIEW:
            return State.REPAIR if r.blocking_review_findings else State.SHIPPED
        if s.state == State.REPAIR:
            return State.VERIFY
        return State.FAILED

    def run(
        self,
        goal: str,
        acceptance_criteria: List[str],
        budgets: Optional[Budgets] = None,
    ) -> LoopState:
        """Execute a bounded feedback loop.

        Args:
            goal: The objective to achieve.
            acceptance_criteria: Non-empty list of conditions that must pass.
            budgets: Optional budget overrides.

        Returns:
            Final LoopState with terminal status.

        Raises:
            ValueError: If acceptance_criteria is empty.
        """
        if not acceptance_criteria:
            raise ValueError("acceptance_criteria must not be empty")

        s = LoopState(
            loop_id=str(uuid.uuid4()),
            goal=goal,
            acceptance_criteria=acceptance_criteria,
            budgets=budgets or Budgets(),
        )
        self.memory.save(s)
        self._log(
            logging.INFO,
            "Loop %s started: %s",
            s.loop_id,
            s.goal,
        )

        while s.state not in TERMINAL:
            reason = self._budget_reason(s)
            if reason:
                terminal = State.HANDOFF if reason == "no_progress" else State.BUDGET_EXHAUSTED
                self._log(
                    logging.WARNING,
                    "Loop %s stopping: %s",
                    s.loop_id,
                    reason,
                )
                s.state = terminal
                s.blockers.append(reason)
                self.memory.save(s)
                break

            role = self.ROLE_FOR_STATE[s.state]
            self._log(
                logging.INFO,
                "Loop %s iteration %d: running %s",
                s.loop_id,
                s.iteration + 1,
                role,
            )

            stage_start = time.time()
            r = self.adapter.run(role, s)
            stage_elapsed = time.time() - stage_start

            s.iteration += 1
            s.usage.tokens += r.usage.tokens
            s.usage.cost += r.usage.cost
            s.evidence.extend(r.evidence)
            s.consecutive_no_progress = 0 if r.progress else s.consecutive_no_progress + 1
            if s.state == State.REPAIR:
                s.repair_attempts += 1

            s.history.append({
                "iteration": s.iteration,
                "role": role,
                "status": r.status,
                "summary": r.summary,
                "evidence": r.evidence,
                "stage_seconds": round(stage_elapsed, 3),
            })

            self._log(
                logging.INFO,
                "Loop %s iteration %d: %s completed in %.2fs (status=%s, progress=%s)",
                s.loop_id,
                s.iteration,
                role,
                stage_elapsed,
                r.status,
                r.progress,
            )

            s.state = self._transition(s, r)
            self.memory.save(s)

            if s.state in TERMINAL:
                break

            reason = self._budget_reason(s)
            if reason:
                self._log(
                    logging.WARNING,
                    "Loop %s post-stage budget check: %s",
                    s.loop_id,
                    reason,
                )
                s.state = State.HANDOFF if reason == "no_progress" else State.BUDGET_EXHAUSTED
                s.blockers.append(reason)
                self.memory.save(s)
                break

        elapsed_total = time.time() - s.started_at
        self._log(
            logging.INFO,
            "Loop %s finished: state=%s, iterations=%d, repairs=%d, tokens=%d, cost=%.4f, elapsed=%.2fs",
            s.loop_id,
            s.state.value,
            s.iteration,
            s.repair_attempts,
            s.usage.tokens,
            s.usage.cost,
            elapsed_total,
        )
        return s


class DemoAdapter:
    """Deterministic demo adapter — replace with real model/tool adapters.

    Reusable across multiple loops. Call reset() between runs if needed.
    """

    def __init__(self, *, fail_first_verify: bool = True) -> None:
        self.fail_first_verify = fail_first_verify
        self.verify_count = 0

    def reset(self) -> None:
        """Reset internal state for reuse."""
        self.verify_count = 0

    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "verifier":
            self.verify_count += 1
            if self.fail_first_verify and self.verify_count == 1:
                return AgentResult(
                    status="OK",
                    summary="Verification found one correctable issue.",
                    evidence=["demo:test_failure"],
                    verification_passed=False,
                    usage=Usage(tokens=1000, cost=0.01),
                )
            return AgentResult(
                status="OK",
                summary="All acceptance criteria pass.",
                evidence=["demo:tests_pass"],
                verification_passed=True,
                usage=Usage(tokens=1000, cost=0.01),
            )

        if role == "reviewer":
            return AgentResult(
                status="OK",
                summary="Independent review has no blocking findings.",
                evidence=["demo:review_pass"],
                blocking_review_findings=False,
                usage=Usage(tokens=500, cost=0.005),
            )

        return AgentResult(
            status="OK",
            summary=f"{role} completed bounded stage.",
            evidence=[f"demo:{role}"],
            usage=Usage(tokens=500, cost=0.005),
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    engine = LoopEngine(DemoAdapter(), JsonlMemoryStore("/tmp/loop-demo-memory.jsonl"))
    result = engine.run(
        goal="Demonstrate a bounded self-correcting engineering loop",
        acceptance_criteria=["verification passes", "review has no blocking findings"],
    )
    print(json.dumps({
        "loop_id": result.loop_id,
        "state": result.state.value,
        "iterations": result.iteration,
        "repairs": result.repair_attempts,
        "tokens": result.usage.tokens,
        "cost": result.usage.cost,
        "evidence": result.evidence,
    }, indent=2))


if __name__ == "__main__":
    main()
