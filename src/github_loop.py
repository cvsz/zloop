from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .runtime_contracts import Permission, PermissionGate


@dataclass(frozen=True)
class PullRequestSnapshot:
    number: int
    head_sha: str
    base_branch: str
    required_checks: Sequence[str]


class GitHubAdapter(Protocol):
    def get_pull_request(self, number: int) -> PullRequestSnapshot: ...
    def push_branch(self, branch: str, expected_head_sha: str) -> str: ...
    def merge_pull_request(self, number: int, expected_head_sha: str) -> str: ...


class SafeGitHubLoop:
    def __init__(self, adapter: GitHubAdapter, permissions: PermissionGate) -> None:
        self.adapter = adapter
        self.permissions = permissions

    def assert_fresh(self, number: int, expected_head_sha: str) -> PullRequestSnapshot:
        snapshot = self.adapter.get_pull_request(number)
        if snapshot.head_sha != expected_head_sha:
            raise RuntimeError("stale pull request head SHA")
        return snapshot

    def merge(self, number: int, expected_head_sha: str, checks_passed: bool, approved: bool) -> str:
        self.permissions.require(Permission.HIGH_IMPACT)
        self.assert_fresh(number, expected_head_sha)
        if not checks_passed or not approved:
            raise RuntimeError("merge gate not satisfied")
        return self.adapter.merge_pull_request(number, expected_head_sha)
