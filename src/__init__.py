"""zLoop Engineering Kit — bounded autonomous feedback loops."""

from .zloop_engine import (
    TERMINAL,
    AgentAdapter,
    AgentResult,
    Budgets,
    DemoAdapter,
    JsonlMemoryStore,
    LoopEngine,
    LoopState,
    MemoryStore,
    State,
    Usage,
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
