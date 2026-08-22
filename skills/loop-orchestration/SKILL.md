# Loop Orchestration

## Purpose
Run a bounded Discover → Plan → Execute → Verify → Review/Repair feedback cycle.

## Procedure
1. Load goal, durable state, permissions and budgets.
2. Validate configuration.
3. Run discovery.
4. Require a finite plan and acceptance criteria.
5. Execute approved actions.
6. Run independent verification and review.
7. Invoke bounded repair for blocking failures.
8. Detect repeated/no-progress cycles.
9. Ship only after required gates pass; otherwise hand off or terminate.

## Required outputs
Loop state, transition decision, evidence references, and terminal reason.
