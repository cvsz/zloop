from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterator
import time


@dataclass(frozen=True)
class SpanRecord:
    name: str
    duration_seconds: float
    success: bool


class Metrics:
    def __init__(self) -> None:
        self.counters: Dict[str, int] = defaultdict(int)
        self.timings: list[SpanRecord] = []

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        success = False
        try:
            yield
            success = True
        finally:
            self.timings.append(SpanRecord(name, time.perf_counter() - started, success))
