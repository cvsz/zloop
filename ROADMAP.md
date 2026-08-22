# ZLoop Roadmap

ZLoop is a bounded, verifiable loop-engineering runtime for agentic work. The roadmap prioritizes closed-loop reliability, independent verification, durable state, cost control, and auditable execution before broader autonomy.

## Phase 0 — Repository and CI baseline

- [x] Core loop engine and tests
- [x] Agent role contracts
- [x] Reusable skill contracts
- [x] Loop state / verification schemas
- [x] GitHub Actions CI
- [x] Dependabot
- [x] Dependency Review
- [x] CodeQL
- [x] Upgrade checkout to v7
- [x] Upgrade setup-python to v6
- [x] Upgrade CodeQL Action to v4
- [x] Add workflow concurrency cancellation and timeouts

## Phase 1 — Durable runtime

- [ ] Replace JSONL-only persistence with a durable state-store interface
- [ ] Add SQLite reference backend
- [ ] Add PostgreSQL production backend
- [ ] Add resumable runs and checkpoint recovery
- [ ] Add cancellation and deadlines
- [ ] Add durable idempotency records for side effects
- [ ] Add retry backoff and failure classification
- [ ] Add deterministic state-machine transition tests

## Phase 2 — Model and context routing

- [ ] Provider-neutral model adapter interface
- [ ] Cheap-model-first routing policy
- [ ] Fallback chains and provider health scoring
- [ ] Per-stage model profiles
- [ ] Token and cost forecasting
- [ ] Context compaction and duplicate-read detection
- [ ] Structured-output validation and repair

## Phase 3 — Execution isolation and connectors

- [ ] Git worktree manager
- [ ] Sandbox execution boundary
- [ ] GitHub connector adapter
- [ ] CI/check adapter
- [ ] Issue/ticket adapter boundary
- [ ] Database/staging API adapter boundary
- [ ] Capability-based permissions
- [ ] Human approval gate for remote/high-impact mutations

## Phase 4 — Verification and repair

- [ ] Acceptance-criteria compiler
- [ ] Deterministic verification matrix
- [ ] Independent verifier enforcement
- [ ] Security/static-analysis gate adapters
- [ ] Reviewer severity model
- [ ] Failure-signature catalog
- [ ] No-progress detection using evidence fingerprints
- [ ] Bounded repair planner
- [ ] Regression verification before ship

## Phase 5 — Fleet orchestration

- [ ] Specialist/subagent registry
- [ ] Scoped subgoals and per-agent budgets
- [ ] Parallel worktree execution
- [ ] Cross-agent conflict detection
- [ ] Fleet-level cost governor
- [ ] Quorum verification for critical operations
- [ ] Dynamic delegation with hard fan-out limits

## Phase 6 — Production operations

- [ ] Structured audit event schema
- [ ] OpenTelemetry traces
- [ ] Metrics and SLOs
- [ ] Cost ledger and budget dashboards
- [ ] RBAC / tenant boundaries
- [ ] Secret isolation
- [ ] SBOM and provenance
- [ ] Artifact attestation/signing
- [ ] OpenSSF Scorecard
- [ ] Container vulnerability scanning where applicable

## Release gates

A phase is complete only when its implementation has tests, documentation, failure-path coverage, security review, and observable evidence. ZLoop must never redefine acceptance criteria or bypass verification merely to reach a successful terminal state.
