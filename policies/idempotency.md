# Idempotency Policy

External and durable mutations require a stable idempotency key:

`<loop_id>:<plan_version>:<step_id>:<target>`

Lifecycle:

`NOT_STARTED → IN_PROGRESS → SUCCEEDED | FAILED_RETRYABLE | FAILED_FINAL`

Before retrying:
1. inspect prior result;
2. determine whether the side effect already occurred;
3. reuse the same key;
4. never duplicate irreversible mutations.

Local pure computations do not require mutation idempotency, but their results should still be cached when expensive.
