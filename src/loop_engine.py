from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Protocol
import json
import time
import uuid


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


TERMINAL = {State.SHIPPED, State.HANDOFF, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION, State.FAILED}


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
    next_action: str | None = None
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
    def __init__(self, path: str = ".loop-memory.jsonl") -> None:
        self.path = path

    def save(self, state: LoopState) -> None:
        record = asdict(state)
        record["state"] = state.state.value
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class LoopEngine:
    ROLE_FOR_STATE = {
        State.DISCOVER: "discoverer",
        State.PLAN: "planner",
        State.EXECUTE: "executor",
        State.VERIFY: "verifier",
        State.REVIEW: "reviewer",
        State.REPAIR: "repairer",
    }

    def __init__(self, adapter: AgentAdapter, memory: MemoryStore) -> None:
        self.adapter = adapter
        self.memory = memory

    def _budget_reason(self, s: LoopState) -> str | None:
        if s.iteration >= s.budgets.max_iterations:
            return "max_iterations"
        if s.repair_attempts > s.budgets.max_repairs:
            return "max_repairs"
        if s.consecutive_no_progress >= s.budgets.max_consecutive_no_progress:
            return "no_progress"
        if s.usage.tokens >= s.budgets.token_budget:
            return "token_budget"
        if s.usage.cost >= s.budgets.cost_budget:
            return "cost_budget"
        if time.time() - s.started_at >= s.budgets.wall_clock_budget_seconds:
            return "wall_clock_budget"
        return None

    def _transition(self, s: LoopState, r: AgentResult) -> State:
        if r.status in {"BLOCKED", "INCONCLUSIVE"}:
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

    def run(self, goal: str, acceptance_criteria: List[str], budgets: Budgets | None = None) -> LoopState:
        if not acceptance_criteria:
            raise ValueError("acceptance_criteria must not be empty")
        s = LoopState(str(uuid.uuid4()), goal, acceptance_criteria, budgets or Budgets())
        self.memory.save(s)
        while s.state not in TERMINAL:
            reason = self._budget_reason(s)
            if reason:
                s.state = State.HANDOFF if reason == "no_progress" else State.BUDGET_EXHAUSTED
                s.blockers.append(reason)
                self.memory.save(s)
                break
            role = self.ROLE_FOR_STATE[s.state]
            r = self.adapter.run(role, s)
            s.iteration += 1
            s.usage.tokens += r.usage.tokens
            s.usage.cost += r.usage.cost
            s.evidence.extend(r.evidence)
            s.consecutive_no_progress = 0 if r.progress else s.consecutive_no_progress + 1
            if s.state == State.REPAIR:
                s.repair_attempts += 1
            s.history.append({"iteration": s.iteration, "role": role, "status": r.status, "summary": r.summary, "evidence": r.evidence})
            s.state = self._transition(s, r)
            self.memory.save(s)
        return s


class DemoAdapter:
    def __init__(self) -> None:
        self.verify_count = 0

    def run(self, role: str, state: LoopState) -> AgentResult:
        if role == "verifier":
            self.verify_count += 1
            passed = self.verify_count > 1
            return AgentResult("OK", "verification complete", ["demo:verify"], usage=Usage(1000, 0.01), verification_passed=passed)
        if role == "reviewer":
            return AgentResult("OK", "review complete", ["demo:review"], usage=Usage(500, 0.005), blocking_review_findings=False)
        return AgentResult("OK", f"{role} complete", [f"demo:{role}"], usage=Usage(500, 0.005))


if __name__ == "__main__":
    result = LoopEngine(DemoAdapter(), JsonlMemoryStore("/tmp/zloop-demo.jsonl")).run(
        "Demonstrate bounded self-correction", ["verification passes", "review passes"]
    )
    print(json.dumps({"state": result.state.value, "iterations": result.iteration, "repairs": result.repair_attempts}, indent=2))
