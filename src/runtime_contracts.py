from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, Mapping, Protocol, Sequence
import hashlib
import json
import time


class Permission(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOCAL_MUTATION = "LOCAL_MUTATION"
    REMOTE_MUTATION = "REMOTE_MUTATION"
    HIGH_IMPACT = "HIGH_IMPACT"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class ModelProfile:
    role: str
    primary: str
    fallbacks: Sequence[str] = ()
    max_tokens: int = 32_000
    max_cost: float = 1.0


@dataclass
class BudgetLedger:
    token_limit: int
    cost_limit: float
    tokens_used: int = 0
    cost_used: float = 0.0

    def charge(self, *, tokens: int, cost: float) -> None:
        if tokens < 0 or cost < 0:
            raise ValueError("usage cannot be negative")
        if self.tokens_used + tokens > self.token_limit:
            raise RuntimeError("token budget exceeded")
        if self.cost_used + cost > self.cost_limit:
            raise RuntimeError("cost budget exceeded")
        self.tokens_used += tokens
        self.cost_used += cost


class ModelProvider(Protocol):
    def invoke(self, model: str, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class ModelRouter:
    def __init__(self, provider: ModelProvider, ledger: BudgetLedger) -> None:
        self.provider = provider
        self.ledger = ledger

    def run(self, profile: ModelProfile, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        last_error: Exception | None = None
        for model in (profile.primary, *profile.fallbacks):
            try:
                result = self.provider.invoke(model, payload)
                usage = result.get("usage", {})
                self.ledger.charge(tokens=int(usage.get("tokens", 0)), cost=float(usage.get("cost", 0.0)))
                return result
            except Exception as exc:
                last_error = exc
        raise RuntimeError("all model routes failed") from last_error


def validate_structured_output(value: Mapping[str, Any], required: Iterable[str]) -> None:
    missing = [key for key in required if key not in value]
    if missing:
        raise ValueError(f"missing structured-output fields: {', '.join(missing)}")


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    target: str
    permission: Permission
    result: str
    idempotency_key: str | None = None
    tenant_id: str | None = None
    created_at: float = field(default_factory=time.time)


class PermissionGate:
    def __init__(self, allowed: Iterable[Permission]) -> None:
        self.allowed = set(allowed)

    def require(self, permission: Permission) -> None:
        if permission not in self.allowed:
            raise PermissionError(f"permission denied: {permission.value}")


def evidence_fingerprint(items: Iterable[str]) -> str:
    canonical = json.dumps(sorted(set(items)), separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    run: Callable[[], Verdict]


class VerifierRegistry:
    def __init__(self) -> None:
        self._checks: Dict[str, VerificationCheck] = {}

    def register(self, check: VerificationCheck) -> None:
        if check.name in self._checks:
            raise ValueError(f"duplicate verifier: {check.name}")
        self._checks[check.name] = check

    def evaluate(self, required: Sequence[str]) -> Dict[str, Verdict]:
        results: Dict[str, Verdict] = {}
        for name in required:
            results[name] = Verdict.INCONCLUSIVE if name not in self._checks else self._checks[name].run()
        return results


class FleetGovernor:
    def __init__(self, *, max_depth: int = 2, max_fanout: int = 4) -> None:
        self.max_depth = max_depth
        self.max_fanout = max_fanout

    def validate_spawn(self, *, depth: int, children: int) -> None:
        if depth >= self.max_depth:
            raise RuntimeError("fleet max depth reached")
        if children > self.max_fanout:
            raise RuntimeError("fleet max fanout exceeded")


def redact_secrets(text: str, secrets: Iterable[str]) -> str:
    output = text
    for secret in secrets:
        if secret:
            output = output.replace(secret, "[REDACTED]")
    return output
