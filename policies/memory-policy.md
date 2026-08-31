# Memory Policy

## Durable loop memory format
Store:
- goal and normalized acceptance criteria;
- current state;
- current plan version;
- stage summaries;
- attempt/repair counters;
- evidence references;
- blockers;
- remaining work;
- budget ledger.

## Context compaction
Completed stage transcripts should be replaced by concise factual summaries and evidence pointers.

## Forbidden memory
Do not store credentials, tokens, unnecessary personal data, hidden reasoning, or unredacted secrets.
