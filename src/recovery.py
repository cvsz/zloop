from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict
import time

from .loop_engine import Budgets, LoopState, State, Usage


LEGAL_TRANSITIONS = {
    State.DISCOVER: {State.PLAN, State.HANDOFF, State.FAILED, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
    State.PLAN: {State.EXECUTE, State.HANDOFF, State.FAILED, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
    State.EXECUTE: {State.VERIFY, State.HANDOFF, State.FAILED, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
    State.VERIFY: {State.REVIEW, State.REPAIR, State.HANDOFF, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
    State.REVIEW: {State.SHIPPED, State.REPAIR, State.HANDOFF, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
    State.REPAIR: {State.VERIFY, State.HANDOFF, State.FAILED, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION},
}


def assert_legal_transition(current: State, next_state: State) -> None:
    if current in {State.SHIPPED, State.HANDOFF, State.BUDGET_EXHAUSTED, State.POLICY_VIOLATION, State.FAILED}:
        raise ValueError("terminal state cannot transition")
    if next_state not in LEGAL_TRANSITIONS[current]:
        raise ValueError(f"illegal transition: {current.value} -> {next_state.value}")


def serialize_state(state: LoopState) -> Dict[str, Any]:
    data = asdict(state)
    data["state"] = state.state.value
    return data


def restore_state(data: Dict[str, Any]) -> LoopState:
    try:
        return LoopState(
            loop_id=data["loop_id"],
            goal=data["goal"],
            acceptance_criteria=list(data["acceptance_criteria"]),
            budgets=Budgets(**data["budgets"]),
            state=State(data["state"]),
            iteration=int(data.get("iteration", 0)),
            repair_attempts=int(data.get("repair_attempts", 0)),
            consecutive_no_progress=int(data.get("consecutive_no_progress", 0)),
            usage=Usage(**data.get("usage", {})),
            evidence=list(data.get("evidence", [])),
            blockers=list(data.get("blockers", [])),
            history=list(data.get("history", [])),
            started_at=float(data.get("started_at", time.time())),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid checkpoint") from exc


def deadline_exceeded(deadline_epoch: float | None) -> bool:
    return deadline_epoch is not None and time.time() >= deadline_epoch
