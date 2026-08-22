import tempfile
import unittest
from pathlib import Path

from src.execution import CommandRunner
from src.github_loop import PullRequestSnapshot, SafeGitHubLoop
from src.loop_engine import Budgets, LoopState, State
from src.observability import Metrics
from src.recovery import assert_legal_transition, restore_state, serialize_state
from src.runtime_contracts import (
    BudgetLedger, FleetGovernor, ModelProfile, ModelRouter, Permission,
    PermissionGate, VerificationCheck, VerifierRegistry, Verdict,
    evidence_fingerprint, redact_secrets, validate_structured_output,
)


class Provider:
    def __init__(self): self.calls = []
    def invoke(self, model, payload):
        self.calls.append(model)
        if model == "cheap": raise RuntimeError("temporary failure")
        return {"ok": True, "usage": {"tokens": 10, "cost": 0.1}}


class GitHubFake:
    def __init__(self): self.snapshot = PullRequestSnapshot(1, "abc", "main", ["ci"])
    def get_pull_request(self, number): return self.snapshot
    def push_branch(self, branch, expected_head_sha): return expected_head_sha
    def merge_pull_request(self, number, expected_head_sha): return "merged"


class RuntimeContractTests(unittest.TestCase):
    def test_router_fallback_and_budget(self):
        ledger = BudgetLedger(100, 1.0); provider = Provider()
        self.assertTrue(ModelRouter(provider, ledger).run(ModelProfile("executor", "cheap", ["strong"]), {})["ok"])
        self.assertEqual(provider.calls, ["cheap", "strong"])
        self.assertEqual(ledger.tokens_used, 10)

    def test_budget_fails_closed(self):
        with self.assertRaises(RuntimeError): BudgetLedger(5, 1.0).charge(tokens=6, cost=0.0)

    def test_permissions_default_deny(self):
        gate = PermissionGate([Permission.READ_ONLY])
        with self.assertRaises(PermissionError): gate.require(Permission.REMOTE_MUTATION)

    def test_verifier_missing_is_inconclusive(self):
        registry = VerifierRegistry(); registry.register(VerificationCheck("tests", lambda: Verdict.PASS))
        result = registry.evaluate(["tests", "security"])
        self.assertEqual(result["security"], Verdict.INCONCLUSIVE)

    def test_fingerprint_is_order_independent(self):
        self.assertEqual(evidence_fingerprint(["a", "b"]), evidence_fingerprint(["b", "a", "a"]))

    def test_fleet_limits(self):
        with self.assertRaises(RuntimeError): FleetGovernor(max_fanout=2).validate_spawn(depth=0, children=3)

    def test_structured_output_and_redaction(self):
        validate_structured_output({"status": "ok"}, ["status"])
        with self.assertRaises(ValueError): validate_structured_output({}, ["status"])
        self.assertEqual(redact_secrets("token=abc", ["abc"]), "token=[REDACTED]")

    def test_checkpoint_round_trip_and_transition(self):
        state = LoopState("id", "goal", ["criterion"], Budgets(), state=State.PLAN)
        self.assertEqual(restore_state(serialize_state(state)).state, State.PLAN)
        assert_legal_transition(State.DISCOVER, State.PLAN)
        with self.assertRaises(ValueError): assert_legal_transition(State.DISCOVER, State.SHIPPED)

    def test_command_runner_is_permission_bound(self):
        with tempfile.TemporaryDirectory() as d:
            denied = CommandRunner(d, PermissionGate([Permission.READ_ONLY]))
            with self.assertRaises(PermissionError): denied.run(["python", "-c", "print(1)"])
            allowed = CommandRunner(d, PermissionGate([Permission.LOCAL_MUTATION]))
            self.assertEqual(allowed.run(["python", "-c", "print(1)"]).returncode, 0)

    def test_github_merge_requires_fresh_sha_checks_and_approval(self):
        loop = SafeGitHubLoop(GitHubFake(), PermissionGate([Permission.HIGH_IMPACT]))
        with self.assertRaises(RuntimeError): loop.merge(1, "stale", True, True)
        with self.assertRaises(RuntimeError): loop.merge(1, "abc", False, True)
        self.assertEqual(loop.merge(1, "abc", True, True), "merged")

    def test_metrics_records_success_and_failure(self):
        metrics = Metrics()
        with metrics.span("ok"): pass
        self.assertTrue(metrics.timings[-1].success)


if __name__ == "__main__": unittest.main()
