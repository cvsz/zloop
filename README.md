# ZLoop

ZLoop is a vendor-neutral, production-oriented framework for building AI agent systems that improve their own work through bounded feedback loops.

## Core lifecycle

`DISCOVER → PLAN → EXECUTE → VERIFY → REVIEW → REPAIR → VERIFY → SHIP`

Every run is constrained by explicit budgets, stop conditions, permission boundaries, independent verification, persistent memory, and human handoff.

## Principles

- Closed loops first.
- Maker/checker separation.
- No unbounded retries.
- Persist state outside model context.
- Mutations require authorization and idempotency.
- Verification decides completion, not the executor.
- Cost/context are first-class resources.
- Parallel agents use isolated worktrees.
- Every material action is auditable.

## Components

- Orchestrator, Discoverer, Planner, Executor, Verifier, Reviewer, Repairer
- Memory Manager and Cost/Context Governor
- reusable skills under `skills/`
- JSON contracts under `schemas/`
- policy-as-code documentation under `policies/`
- provider-neutral Python reference runtime under `src/`
- coding, research, content and fleet examples

## Quick start

```bash
python -m unittest discover -s src -p 'test_*.py' -v
python src/loop_engine.py
```

Replace the demo adapter with adapters for your preferred LLM/model gateway, GitHub/CI, issue tracker, database, staging API, or other connector.

## Acceptance rule

ZLoop may ship only when all mandatory acceptance criteria pass independent verification and required review has no blocking finding. `INCONCLUSIVE` is never treated as success.
