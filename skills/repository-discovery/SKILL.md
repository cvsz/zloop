---
name: repository-discovery
description: Use when starting work in a repository and needing targeted context on instructions, source, tests, dependencies, CI, or failures
---

# Repository Discovery

## Purpose
Build the minimum repository context needed to make a correct plan during the DISCOVER stage of a zLoop.

## When to use
- First stage of any zLoop run (DISCOVER state)
- When entering an unfamiliar codebase
- After a HANDOFF when resuming work

## Procedure

1. **Load project instructions first**
   - Read `AGENTS.md`, `README.md`, architecture/roadmap/planning docs
   - Identify coding conventions, testing patterns, and build system

2. **Targeted source inspection**
   - Use grep/glob to find relevant modules — avoid whole-repository dumps
   - Map entry points, public APIs, and data flow
   - Identify existing test coverage and CI configuration

3. **Dependency analysis**
   - Parse dependency manifests (requirements.txt, package.json, etc.)
   - Check for known vulnerabilities or outdated packages
   - Identify internal vs external dependencies

4. **Failure evidence collection**
   - Review recent CI failures, error logs, issue trackers
   - Look for patterns in previous attempts (check `.zloop/memory.jsonl` if present)

## Required outputs
- Relevant file map with paths and purposes
- Constraints and invariants discovered
- Existing gates (tests, lint, security scans)
- Known failures and their signatures
- Unknowns requiring further investigation
- Dependency graph summary

## Integration with zLoop

```python
# In your AgentAdapter.run() when role == "discoverer":
def run(self, role: str, state: LoopState) -> AgentResult:
    if role == "discoverer":
        # Perform discovery, return evidence
        return AgentResult(
            status="OK",
            summary="Discovery complete: identified 3 relevant modules, 2 test files",
            evidence=[
                "src/module_a.py: primary implementation",
                "tests/test_module_a.py: existing coverage 78%",
                "ci.yml: runs pytest + ruff",
            ],
            risks=["legacy module_b has no type hints"],
        )
```

## Safety / quality gates
- Operate within declared scope — do not read unrelated directories
- Produce evidence for every material claim (file paths, line numbers)
- Never bypass stop conditions or permission boundaries
- Update persistent loop memory after meaningful progress
