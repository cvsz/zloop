# Fleet Loop Example

```text
                   Orchestrator
           ┌──────────┼──────────┐
           ↓          ↓          ↓
      Research     Engineer       QA
           ↓          ↓          ↓
      evidence    worktree     verifier
                      ↓
                   reviewer
                      ↓
                    repair
```

Orchestrator owns the global budget. Specialists receive scoped subgoals and smaller budgets. Mutating specialists use isolated worktrees. Durable shared memory is authoritative. QA is independent from implementation. Parallelism is capped.
