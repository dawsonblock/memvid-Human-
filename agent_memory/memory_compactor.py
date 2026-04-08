from __future__ import annotations

from .schemas import DurableMemory


class MemoryCompactor:
    def compact(self, memories: list[DurableMemory]) -> list[DurableMemory]:
        best_by_key: dict[tuple[object, ...], DurableMemory] = {}
        for memory in sorted(memories, key=self._sort_key, reverse=True):
            key = (
                memory.memory_type,
                memory.entity,
                memory.slot,
                memory.value,
                memory.raw_text,
            )
            if key not in best_by_key:
                best_by_key[key] = memory
        return sorted(best_by_key.values(), key=lambda memory: memory.stored_at)

    def _sort_key(self, memory: DurableMemory) -> tuple[object, ...]:
        return (memory.stored_at, memory.salience, memory.confidence)
