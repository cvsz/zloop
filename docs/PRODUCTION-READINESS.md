# ZLoop Production Readiness

ZLoop is considered **production-grade-ready** only when every gate below has implementation evidence, automated tests, and operational ownership. This document distinguishes implemented foundations from deployment-dependent controls.

## Implemented foundation

- bounded loop lifecycle and terminal states;
- independent verifier/reviewer contracts;
- durable SQLite checkpoint and idempotency ledger;
- durable SQLite reference queue with leases, lease-expiry reclaim, retry, cancellation and deadlines;
- checkpoint serialization/restoration helpers;
- legal state-transition validation;
- provider-neutral model routing contract and bounded fallback;
- hard global and per-profile token/cost limits with fail-closed behavior;
- structured-output validation;
- deny-by-default permission gate;
- verifier registry with fail-closed `INCONCLUSIVE` behavior;
- evidence fingerprints for repeat/no-progress detection;
- bounded fleet depth/fan-out governor;
- permission-bound command runner with timeout and reduced environment;
- GitHub PR safety boundary with stale-SHA, approval and check gates;
- audit event contract with tenant field;
- metrics/tracing-compatible span primitives;
- secret-redaction helper;
- CI, CodeQL, Dependency Review, Dependabot, concurrency and timeouts.

## Mandatory deployment gates before production mutation

1. PostgreSQL durable state/idempotency implementation and migration tests.
2. Production queue/worker backend with distributed leases and crash-recovery integration tests; SQLite is the local/reference backend only.
3. OS/container sandbox with CPU, memory, process and network limits; the reference command runner is not a security sandbox.
4. Capability-scoped real connector adapters with tenant/actor/action/target binding.
5. External approval authority for `REMOTE_MUTATION` and `HIGH_IMPACT` operations.
6. Durable append-only audit sink and retention policy.
7. OpenTelemetry exporter configuration, SLO dashboards and alerting.
8. Secrets-manager integration and production redaction tests.
9. Branch protection with required CI/security/review checks.
10. SBOM, provenance/attestation, signed release process and rollback runbook.
11. PostgreSQL backups, restore drills, RPO/RTO and disaster-recovery ownership.
12. Load, concurrency and chaos tests against the actual deployment topology.

## Release criteria

No production release may be marked ready unless all required checks have explicit passing evidence, no blocking review finding remains, mutating connectors are approval-bound, idempotency survives restarts, state recovery is crash-tested, budgets fail closed, `INCONCLUSIVE` never ships, secrets are absent from artifacts/logs, and rollback/handoff procedures are tested.
