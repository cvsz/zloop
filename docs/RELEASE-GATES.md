# Release Gates

## Automated
- unit tests
- compile/static syntax checks
- CodeQL/security analysis
- dependency review
- secret-pattern scan
- package/build validation
- persistence migration tests when schemas change

## Engineering
- maker/checker separation
- blocking findings resolved
- acceptance criteria mapped to evidence
- backward compatibility assessed
- rollback path documented
- mutations covered by permission + idempotency tests

## Production-only
- required branch checks configured
- release provenance verified
- secrets-manager integration verified
- audit retention configured
- dashboards/alerts enabled
- backup restore drill passed
- capacity/load test passed
- operator runbook reviewed

No missing or `INCONCLUSIVE` mandatory gate may be treated as PASS.
