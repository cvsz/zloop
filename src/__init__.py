"""zLoop Engineering Kit — bounded autonomous feedback loops."""

from .zloop_engine import (
    State,
    TERMINAL,
    Budgets,
    Usage,
    AgentResult,
    LoopState,
    AgentAdapter,
    MemoryStore,
    JsonlMemoryStore,
    LoopEngine,
    DemoAdapter,
)

__version__ = "1.0.0"
__all__ = [
    "State",
    "TERMINAL",
    "Budgets",
    "Usage",
    "AgentResult",
    "LoopState",
    "AgentAdapter",
    "MemoryStore",
    "JsonlMemoryStore",
    "LoopEngine",
    "DemoAdapter",
]
