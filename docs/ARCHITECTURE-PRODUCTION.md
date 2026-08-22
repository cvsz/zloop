# ZLoop Production Architecture

## Control plane
Mission API -> Orchestrator -> Policy Engine + Budget Governor + Model Router.

## Data plane
Isolated Executors -> Connector Adapters -> Independent Verifiers -> Repair Planner.

## Persistence
PostgreSQL for canonical loop/checkpoint/idempotency/approval state; durable queue for worker leases/retries/cancellation; object storage for artifacts; append-only audit store for mutation events.

## Security invariants
- deny mutation by default;
- tenant/actor/action/target binding on approvals;
- no client-side provider secrets;
- executor cannot directly mark `SHIPPED`;
- stale revision/SHA blocks mutation;
- credentials are scoped per adapter and never persisted in loop memory;
- external side effects require durable idempotency keys;
- `INCONCLUSIVE` is never success.

## Fleet constraints
Children receive strict subsets of parent scope and remaining budget. Depth, fan-out and concurrency caps are mandatory. Mutating children use isolated workspaces. Final acceptance belongs to an independent verifier.
