from __future__ import annotations

from .clock import Clock
from .retention import RetentionEngine
from .schemas import DurableMemory
from .adapters.memvid_store import MemoryStore


class MemoryDecayJob:
    def __init__(self, store: MemoryStore, retention: RetentionEngine, clock: Clock) -> None:
        self.store = store
        self.retention = retention
        self.clock = clock

    def run(self, memories: list[DurableMemory]) -> list[str]:
        expired: list[str] = []
        now = self.clock.now()
        for memory in memories:
            if self.retention.is_expired(memory, now):
                self.store.expire_memory(memory.memory_id)
                expired.append(memory.memory_id)
        return expired
