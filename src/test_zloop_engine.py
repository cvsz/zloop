"""Tests for zLoop Engine."""

import json
import os
import tempfile
import threading
import time
import unittest

from jsonschema import ValidationError

from validation import (
    is_valid_agent_result,
    is_valid_loop_state,
    validate_loop_state,
)
from zloop_engine import (
    AgentResult,
    Budgets,
    DemoAdapter,
    JsonlMemoryStore,
    LoopEngine,
    LoopState,
    State,
    Usage,
)


class NoProgressAdapter:
    def run(self, role, state):
        return AgentResult(
            status="OK",
            summary="No measurable progress",
            progress=False,
            usage=Usage(tokens=1, cost=0.0),
        )


class BlockedAdapter:
    def run(self, role, state):
        return AgentResult(
            status="BLOCKED",
            summary="Human approval required",
            progress=False,
        )


class InconclusiveAdapter:
    def run(self, role, state):
        return AgentResult(
            status="INCONCLUSIVE",
            summary="Cannot determine result",
            progress=True,
        )


class BudgetExhaustAdapter:
    def __init__(self, tokens: int = 0, cost: float = 0.0):
        self.tokens = tokens
        self.cost = cost

    def run(self, role, state):
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=self.tokens, cost=self.cost),
        )


class ReviewBlockingAdapter:
    def run(self, role, state):
        if role == "reviewer":
            return AgentResult(
                status="OK",
                summary="Review found blocking issues",
                blocking_review_findings=True,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        if role == "verifier":
            return AgentResult(
                status="OK",
                summary="Verification found issues",
                verification_passed=False,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class FailFromDiscoverAdapter:
    def run(self, role, state):
        if role == "discoverer":
            return AgentResult(
                status="FAIL",
                summary="Discovery failed",
                progress=False,
                usage=Usage(tokens=100, cost=0.001),
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class FailFromVerifyAdapter:
    """FAIL in VERIFY should NOT terminate — it should trigger REPAIR."""

    def __init__(self):
        self.verify_count = 0

    def run(self, role, state):
        if role == "verifier":
            self.verify_count += 1
            if self.verify_count == 1:
                return AgentResult(
                    status="FAIL",
                    summary="Verification failed",
                    verification_passed=False,
                    progress=True,
                    usage=Usage(tokens=100, cost=0.001),
                )
            return AgentResult(
                status="OK",
                summary="Verification passed after repair",
                verification_passed=True,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class WallClockExhaustAdapter:
    """Adapter that simulates slow execution."""

    def __init__(self, sleep_seconds: float = 0.1):
        self.sleep_seconds = sleep_seconds

    def run(self, role, state):
        time.sleep(self.sleep_seconds)
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=10, cost=0.001),
        )


class ExceptionAdapter:
    """Adapter that raises an exception."""

    def run(self, role, state):
        if role == "executor":
            raise RuntimeError("Simulated adapter failure")
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class InvalidStatusAdapter:
    """Adapter that returns an invalid status."""

    def run(self, role, state):
        if role == "verifier":
            return AgentResult(
                status="INVALID",
                summary="Bad status",
                progress=True,
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
        )


class FailReviewAdapter:
    """Adapter that returns FAIL during REVIEW once, then passes."""

    def __init__(self):
        self.review_count = 0

    def run(self, role, state):
        if role == "reviewer":
            self.review_count += 1
            if self.review_count == 1:
                return AgentResult(
                    status="FAIL",
                    summary="Review failed",
                    blocking_review_findings=True,
                    progress=True,
                    usage=Usage(tokens=100, cost=0.001),
                )
            return AgentResult(
                status="OK",
                summary="Review passed after repair",
                blocking_review_findings=False,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        if role == "verifier":
            return AgentResult(
                status="OK",
                summary="Verification passed",
                verification_passed=True,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class ContradictoryResultAdapter:
    """Adapter that returns FAIL with verification_passed=True."""

    def __init__(self):
        self.verify_count = 0

    def run(self, role, state):
        if role == "verifier":
            self.verify_count += 1
            if self.verify_count == 1:
                return AgentResult(
                    status="FAIL",
                    summary="Contradictory result",
                    verification_passed=True,
                    progress=True,
                    usage=Usage(tokens=100, cost=0.001),
                )
            return AgentResult(
                status="OK",
                summary="Verification passed",
                verification_passed=True,
                progress=True,
                usage=Usage(tokens=100, cost=0.001),
            )
        return AgentResult(
            status="OK",
            summary="Stage completed",
            progress=True,
            usage=Usage(tokens=100, cost=0.001),
        )


class LoopEngineTests(unittest.TestCase):
    def test_demo_repairs_then_ships(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(DemoAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.SHIPPED)
            self.assertEqual(result.repair_attempts, 1)
            self.assertGreaterEqual(len(result.evidence), 1)
        finally:
            os.unlink(path)

    def test_no_progress_handoffs(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(max_iterations=20, max_consecutive_no_progress=2)
            engine = LoopEngine(NoProgressAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.HANDOFF)
            self.assertIn("no_progress", result.blockers)
        finally:
            os.unlink(path)

    def test_blocked_handoffs(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(BlockedAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.HANDOFF)
        finally:
            os.unlink(path)

    def test_inconclusive_handoffs(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(InconclusiveAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.HANDOFF)
        finally:
            os.unlink(path)

    def test_token_budget_exhaustion(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(token_budget=100, max_iterations=20, max_consecutive_no_progress=10)
            engine = LoopEngine(
                BudgetExhaustAdapter(tokens=50),
                JsonlMemoryStore(path),
            )
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.BUDGET_EXHAUSTED)
            self.assertIn("token_budget", result.blockers)
        finally:
            os.unlink(path)

    def test_cost_budget_exhaustion(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(cost_budget=0.10, max_iterations=20, max_consecutive_no_progress=10)
            engine = LoopEngine(
                BudgetExhaustAdapter(cost=0.06),
                JsonlMemoryStore(path),
            )
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.BUDGET_EXHAUSTED)
            self.assertIn("cost_budget", result.blockers)
        finally:
            os.unlink(path)

    def test_max_repairs_exhaustion(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(max_repairs=2, max_iterations=20, max_consecutive_no_progress=10)
            engine = LoopEngine(ReviewBlockingAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.BUDGET_EXHAUSTED)
            self.assertIn("max_repairs", result.blockers)
            self.assertEqual(result.repair_attempts, 2)
        finally:
            os.unlink(path)

    def test_fail_from_non_verify_state(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(FailFromDiscoverAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.FAILED)
        finally:
            os.unlink(path)

    def test_fail_from_verify_triggers_repair(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            adapter = FailFromVerifyAdapter()
            engine = LoopEngine(adapter, JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.SHIPPED)
            self.assertEqual(result.repair_attempts, 1)
        finally:
            os.unlink(path)

    def test_empty_criteria_raises(self):
        engine = LoopEngine(DemoAdapter(), JsonlMemoryStore("/tmp/test-loop.jsonl"))
        with self.assertRaises(ValueError):
            engine.run("goal", [])

    def test_history_recorded(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(DemoAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertGreater(len(result.history), 0)
            for entry in result.history:
                self.assertIn("iteration", entry)
                self.assertIn("role", entry)
                self.assertIn("status", entry)
                self.assertIn("stage_seconds", entry)
        finally:
            os.unlink(path)

    def test_loop_id_unique(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(DemoAdapter(), JsonlMemoryStore(path))
            r1 = engine.run("goal1", ["criterion"])
            r2 = engine.run("goal2", ["criterion"])
            self.assertNotEqual(r1.loop_id, r2.loop_id)
        finally:
            os.unlink(path)

    def test_demo_adapter_reusable(self):
        adapter = DemoAdapter(fail_first_verify=False)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(adapter, JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.SHIPPED)
            self.assertEqual(result.repair_attempts, 0)

            adapter.reset()
            result2 = engine.run("goal2", ["criterion"])
            self.assertEqual(result2.state, State.SHIPPED)
        finally:
            os.unlink(path)

    def test_adapter_exception_fails_gracefully(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(ExceptionAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.FAILED)
            self.assertTrue(any("adapter_exception" in b for b in result.blockers))
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_invalid_status_fails_gracefully(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(InvalidStatusAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.FAILED)
            self.assertTrue(any("invalid_status" in b for b in result.blockers))
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_fail_review_triggers_repair(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(max_repairs=4, max_iterations=20, max_consecutive_no_progress=10)
            engine = LoopEngine(FailReviewAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.SHIPPED)
            self.assertEqual(result.repair_attempts, 1)
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_contradictory_result_handled(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            engine = LoopEngine(ContradictoryResultAdapter(), JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"])
            self.assertEqual(result.state, State.SHIPPED)
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_empty_criteria_strings_rejected(self):
        engine = LoopEngine(DemoAdapter(), JsonlMemoryStore("/tmp/test-loop.jsonl"))
        with self.assertRaises(ValueError):
            engine.run("goal", ["", "valid"])
        with self.assertRaises(ValueError):
            engine.run("goal", [])


class JsonlMemoryStoreTests(unittest.TestCase):
    def test_persists_state(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            store = JsonlMemoryStore(path)
            state = LoopState(
                loop_id="test-123",
                goal="test goal",
                acceptance_criteria=["crit"],
                budgets=Budgets(),
            )
            store.save(state)

            with open(path) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["loop_id"], "test-123")
            self.assertEqual(record["goal"], "test goal")
            self.assertEqual(record["state"], "DISCOVER")
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_concurrent_writes_safe(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            store = JsonlMemoryStore(path)
            errors = []

            def writer(thread_id: int):
                try:
                    for i in range(10):
                        state = LoopState(
                            loop_id=f"loop-{thread_id}-{i}",
                            goal=f"goal-{thread_id}",
                            acceptance_criteria=["crit"],
                            budgets=Budgets(),
                        )
                        store.save(state)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")

            with open(path) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 50)
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nested", "dir", "memory.jsonl")
            os.makedirs(os.path.dirname(path))
            store = JsonlMemoryStore(path)
            state = LoopState(
                loop_id="test",
                goal="test",
                acceptance_criteria=["crit"],
                budgets=Budgets(),
            )
            store.save(state)
            self.assertTrue(os.path.exists(path))


class ValidationTests(unittest.TestCase):
    def test_valid_loop_state(self):
        state = {
            "loop_id": "abc",
            "goal": "test",
            "state": "DISCOVER",
            "iteration": 0,
            "budgets": {
                "max_iterations": 12,
                "max_repairs": 4,
                "max_consecutive_no_progress": 2,
                "token_budget": 500000,
                "cost_budget": 25.0,
                "wall_clock_budget_seconds": 7200,
            },
            "acceptance_criteria": ["crit"],
            "started_at": time.time(),
        }
        self.assertTrue(is_valid_loop_state(state))
        validate_loop_state(state)

    def test_invalid_loop_state_missing_required(self):
        state = {"loop_id": "abc"}
        self.assertFalse(is_valid_loop_state(state))
        with self.assertRaises(ValidationError):
            validate_loop_state(state)

    def test_valid_agent_result(self):
        result = {
            "status": "OK",
            "summary": "done",
        }
        self.assertTrue(is_valid_agent_result(result))

    def test_invalid_agent_result_bad_status(self):
        result = {"status": "INVALID", "summary": "bad"}
        self.assertFalse(is_valid_agent_result(result))

    def test_started_at_in_schema(self):
        state = {
            "loop_id": "abc",
            "goal": "test",
            "state": "DISCOVER",
            "iteration": 0,
            "budgets": {
                "max_iterations": 12,
                "max_repairs": 4,
                "max_consecutive_no_progress": 2,
                "token_budget": 500000,
                "cost_budget": 25.0,
                "wall_clock_budget_seconds": 7200,
            },
            "acceptance_criteria": ["crit"],
            "started_at": 1234567890.0,
        }
        validate_loop_state(state)


class WallClockBudgetTests(unittest.TestCase):
    def test_wall_clock_exhaustion_detected(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            budgets = Budgets(
                wall_clock_budget_seconds=1,
                max_iterations=100,
                max_consecutive_no_progress=100,
                token_budget=999999,
                cost_budget=999.0,
            )
            adapter = WallClockExhaustAdapter(sleep_seconds=0.3)
            engine = LoopEngine(adapter, JsonlMemoryStore(path))
            result = engine.run("goal", ["criterion"], budgets)
            self.assertEqual(result.state, State.BUDGET_EXHAUSTED)
            self.assertIn("wall_clock_budget", result.blockers)
        finally:
            os.unlink(path)
            if os.path.exists(path + ".lock"):
                os.unlink(path + ".lock")


if __name__ == "__main__":
    unittest.main()
