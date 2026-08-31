from setuptools import setup, find_packages

setup(
    name="zloop",
    version="1.0.0",
    description="Vendor-neutral framework for bounded autonomous engineering feedback loops",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "jsonschema>=4.0",
    ],
    entry_points={
        "console_scripts": [
            "zloop=zloop_engine:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["schemas/*.json"],
    },
    data_files=[
        ("zloop_config", ["config/loop.example.yaml"]),
        ("zloop_schemas", [
            "schemas/loop-state.schema.json",
            "schemas/agent-result.schema.json",
            "schemas/verification-result.schema.json",
        ]),
        ("zloop_agents", [
            "agents/orchestrator.md",
            "agents/discoverer.md",
            "agents/planner.md",
            "agents/executor.md",
            "agents/verifier.md",
            "agents/reviewer.md",
            "agents/repairer.md",
            "agents/memory-manager.md",
            "agents/cost-context-governor.md",
        ]),
        ("zloop_policies", [
            "policies/stop-conditions.md",
            "policies/permissions.md",
            "policies/idempotency.md",
            "policies/memory-policy.md",
        ]),
            ("zloop_skills", [
            "skills/loop-orchestration/SKILL.md",
            "skills/repository-discovery/SKILL.md",
            "skills/execution-planning/SKILL.md",
            "skills/bounded-execution/SKILL.md",
            "skills/independent-verification/SKILL.md",
            "skills/repair-loop/SKILL.md",
            "skills/persistent-memory/SKILL.md",
            "skills/worktree-isolation/SKILL.md",
            "skills/cost-governance/SKILL.md",
        ]),
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
