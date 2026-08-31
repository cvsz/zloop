---
name: cost-governance
description: Use when an agent loop, long-running task, or multi-agent workflow needs explicit budget, context, retry, or escalation control
---

# Cost Governance

## Purpose
Keep agent loops affordable and predictable using zLoop's six-dimensional budget system.

## Budget dimensions
| Budget | Default | Description |
|--------|---------|-------------|
| `max_iterations` | 12 | Total loop iterations (all stages) |
| `max_repairs` | 4 | Maximum repair attempts |
| `max_consecutive_no_progress` | 2 | Handoff after N consecutive no-progress iterations |
| `token_budget` | 500,000 | Cumulative token limit |
| `cost_budget` | $25.00 | Cumulative monetary limit |
| `wall_clock_budget_seconds` | 7200 | Wall-clock time limit (2 hours) |

## Enforcement behavior
- Checked **before** each adapter call (pre-stage)
- Checked **after** each adapter call (post-stage)
- `max_iterations`, `max_repairs`, `token_budget`, `cost_budget`, `wall_clock_budget` → `BUDGET_EXHAUSTED`
- `max_consecutive_no_progress` → `HANDOFF` (not exhausted)

```python
from zloop import Budgets

# Small task: fast, cheap
small = Budgets(
    max_iterations=5,
    max_repairs=2,
    max_consecutive_no_progress=1,
    token_budget=50_000,
    cost_budget=5.0,
    wall_clock_budget_seconds=600,
)

# Large task: more room
large = Budgets(
    max_iterations=20,
    max_repairs=6,
    max_consecutive_no_progress=3,
    token_budget=1_000_000,
    cost_budget=50.0,
    wall_clock_budget_seconds=14400,
)
```

## Context compaction
Replace completed stage transcripts with concise summaries:
```python
# In your AgentAdapter.run():
return AgentResult(
    status="OK",
    summary="Discovery: 3 modules, 2 tests, 1 CI config found",
    # Only include essential evidence, not full transcripts
    evidence=["src/a.py: primary", "tests/test_a.py: 78% coverage"],
)
```

## Required outputs
| Output | Description |
|--------|-------------|
| Budget ledger | Cumulative tokens/cost per stage |
| Remaining allowance | `budget - used` for each dimension |
| Governance decision | Continue / HANDOFF / BUDGET_EXHAUSTED |
| Escalation action | Triggered when budget < 20% remaining |

## Escalation triggers
Escalate when:
- Budget < 20% remaining with low completion probability
- Same failure repeats without measurable progress
- Verification is ambiguous (INCONCLUSIVE)
- Destructive action requested without explicit authority

## Safety / quality gates
- Budgets are hard limits — never exceeded silently
- Track consumption at every iteration
- Deduplicate context to reduce token usage
- Block repeated identical attempts (no-progress detection)
- Escalate before hard budget exhaustion
