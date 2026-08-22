# Idempotency Policy

External/durable mutations require a stable key: `<loop_id>:<plan_version>:<step_id>:<target>`.

Lifecycle: `NOT_STARTED → IN_PROGRESS → SUCCEEDED | FAILED_RETRYABLE | FAILED_FINAL`.

Before retrying, inspect prior state, determine whether the side effect already occurred, reuse the same key, and never duplicate an irreversible mutation.
