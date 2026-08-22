import tempfile
import unittest

from src.loop_engine import AgentResult, Budgets, DemoAdapter, JsonlMemoryStore, LoopEngine, State, Usage


class NoProgressAdapter:
    def run(self, role, state):
        return AgentResult("OK", "no progress", progress=False, usage=Usage(tokens=1))


class BlockedAdapter:
    def run(self, role, state):
        return AgentResult("BLOCKED", "approval required", progress=False)


class LoopEngineTests(unittest.TestCase):
    def test_demo_repairs_then_ships(self):
        with tempfile.NamedTemporaryFile() as f:
            result = LoopEngine(DemoAdapter(), JsonlMemoryStore(f.name)).run("goal", ["criterion"])
            self.assertEqual(result.state, State.SHIPPED)
            self.assertEqual(result.repair_attempts, 1)

    def test_no_progress_handoffs(self):
        with tempfile.NamedTemporaryFile() as f:
            result = LoopEngine(NoProgressAdapter(), JsonlMemoryStore(f.name)).run(
                "goal", ["criterion"], Budgets(max_iterations=20, max_consecutive_no_progress=2)
            )
            self.assertEqual(result.state, State.HANDOFF)
            self.assertIn("no_progress", result.blockers)

    def test_blocked_handoffs(self):
        with tempfile.NamedTemporaryFile() as f:
            result = LoopEngine(BlockedAdapter(), JsonlMemoryStore(f.name)).run("goal", ["criterion"])
            self.assertEqual(result.state, State.HANDOFF)


if __name__ == "__main__":
    unittest.main()
