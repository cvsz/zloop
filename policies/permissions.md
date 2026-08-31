# Permission Policy

Permission classes:

- `READ_ONLY`: inspect files, logs, metadata, public/authorized resources.
- `LOCAL_MUTATION`: edit isolated local/worktree content.
- `REMOTE_MUTATION`: push branch, update issue/ticket, write database/staging API.
- `HIGH_IMPACT`: production deployment, destructive operation, credential/security changes.

Default deny for mutations.

Every mutating action records:
- actor
- target
- action
- scope
- approval source
- idempotency key
- timestamp
- result
