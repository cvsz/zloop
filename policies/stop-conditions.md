# Stop Conditions

A loop MUST stop on success, human handoff, budget exhaustion, policy violation, or terminal failure.

## Success
All mandatory acceptance criteria pass independent verification and required review has no blocking findings.

## Handoff
Escalate when approval/credentials/input are required, verification remains inconclusive, repeated failure reaches the no-progress limit, proposed work exceeds scope, or destructive/irreversible work lacks explicit authority.

## Budget exhaustion
Terminate when any hard token, monetary, wall-clock, iteration, or repair limit is reached.

A loop MUST NOT weaken or redefine success criteria merely to terminate successfully.
