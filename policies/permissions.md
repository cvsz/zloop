# Permission Policy

Permission classes: `READ_ONLY`, `LOCAL_MUTATION`, `REMOTE_MUTATION`, `HIGH_IMPACT`.

Default deny for mutations. Each mutating action records actor, target, action, scope, approval source, idempotency key, timestamp, and result. Production deployment, destructive operations, and credential/security changes are high-impact and require explicit authority.
