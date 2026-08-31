# Cost & Context Governor Agent

## Purpose
Prevent runaway token, latency, tool, and monetary consumption. Track budgets and trigger escalation before exhaustion.

## Implementation
The governor is built into `LoopEngine._budget_reason()` and enforced at every iteration. It checks all six budget dimensions before AND after each adapter call.

## Role name
The governor is not a separate role — it's an integral part of the orchestrator.

## Budget dimensions
| Budget | Field | Default | Terminal on exhaustion |
|--------|-------|---------|----------------------|
| Iteration cap | `max_iterations` | 12 | `BUDGET_EXHAUSTED` |
| Repair cap | `max_repairs` | 4 | `BUDGET_EXHAUSTED` |
| No-progress cap | `max_consecutive_no_progress` | 2 | `HANDOFF` |
| Token budget | `token_budget` | 500,000 | `BUDGET_EXHAUSTED` |
| Cost budget | `cost_budget` | $25.00 | `BUDGET_EXHAUSTED` |
| Wall-clock budget | `wall_clock_budget_seconds` | 7200 | `BUDGET_EXHAUSTED` |

## Enforcement behavior
```python
# Engine checks budgets BEFORE adapter call
reason = self._budget_reason(s)
if reason:
    s.state = State.HANDOFF if reason == "no_progress" else State.BUDGET_EXHAUSTED
    break

# ... adapter runs ...

# Engine checks budgets AFTER adapter call
reason = self._budget_reason(s)
if reason:
    s.state = State.HANDOFF if reason == "no_progress" else State.BUDGET_EXHAUSTED
    break
```

## Actions
| Action | Trigger | Result |
|--------|---------|--------|
| Approve next stage | All budgets OK | Continue loop |
| Require compression | Context > threshold | Summarize completed stages |
| Block redundant work | No progress detected | Increment counter |
| Trigger handoff | `no_progress >= max` | → HANDOFF |
| Terminate exhausted | Any hard budget hit | → BUDGET_EXHAUSTED |

## Context compaction guidelines
Replace completed stage transcripts with concise summaries:

```python
# BAD: returning full file contents in evidence
evidence=["Full file contents: ..."]

# GOOD: concise summary with reference
evidence=["src/handler.py:42 — added Pydantic validation (16 lines added)"]
```

## Budget presets
```python
from zloop import Budgets

# Quick tasks — fast, cheap
QUICK = Budgets(
    max_iterations=5,
    max_repairs=2,
    max_consecutive_no_progress=1,
    token_budget=50_000,
    cost_budget=5.0,
    wall_clock_budget_seconds=600,
)

# Standard tasks
STANDARD = Budgets()  # defaults

# Complex tasks — more room
COMPLEX = Budgets(
    max_iterations=20,
    max_repairs=6,
    max_consecutive_no_progress=3,
    token_budget=1_000_000,
    cost_budget=50.0,
    wall_clock_budget_seconds=14400,
)
```

## Escalation triggers
Escalate when:
- Budget < 20% remaining with low completion probability
- Same failure repeats without measurable progress
- Verification is ambiguous (INCONCLUSIVE)
- Destructive action requested without explicit authority
- `consecutive_no_progress >= max_consecutive_no_progress - 1`

## Output example
```python
# Adapter signals budget awareness
return AgentResult(
    status="OK",
    summary="Stage complete — 45% token budget remaining",
    evidence=["tokens_used: 5000", "budget_remaining: 495000"],
    usage=Usage(tokens=5000, cost=0.05),
)
```

## Forbidden behavior
- Do not exceed budgets silently
- Do not ignore no-progress patterns
- Do not disable budget checks
- Do not reset counters without cause
