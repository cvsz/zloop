from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
import os
import subprocess

from .runtime_contracts import Permission, PermissionGate


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    def __init__(self, workspace: str, permission_gate: PermissionGate, timeout_seconds: int = 120) -> None:
        self.workspace = Path(workspace).resolve()
        self.permission_gate = permission_gate
        self.timeout_seconds = timeout_seconds

    def run(self, command: Sequence[str], *, env: Mapping[str, str] | None = None) -> CommandResult:
        self.permission_gate.require(Permission.LOCAL_MUTATION)
        if not self.workspace.exists() or not self.workspace.is_dir():
            raise ValueError("workspace must exist")
        safe_env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"}
        if env:
            safe_env.update(env)
        completed = subprocess.run(
            list(command), cwd=self.workspace, env=safe_env,
            text=True, capture_output=True, timeout=self.timeout_seconds, check=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
