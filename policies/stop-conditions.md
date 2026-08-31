# Stop Conditions

A loop MUST stop when any of the following is true:

## Success
All mandatory acceptance criteria pass independent verification and required review has no blocking findings.

## Handoff
- approval/credential/input required from a human;
- verifier result remains inconclusive after allowed discovery;
- repeated failure signature reaches `max_consecutive_no_progress`;
- proposed action exceeds authorized scope;
- destructive/irreversible action lacks explicit approval.

## Budget exhaustion
Any hard token, monetary, wall-clock, iteration, or repair limit is reached.

## Policy violation
Security, privacy, permission, or safety invariant is violated.

A loop MUST NOT redefine success criteria merely to terminate successfully.
