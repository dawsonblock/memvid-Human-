from __future__ import annotations

import uuid

from .clock import Clock
from .enums import BeliefStatus
from .schemas import BeliefRecord, DurableMemory
from .adapters.memvid_store import MemoryStore


class BeliefStore:
    def __init__(self, store: MemoryStore, clock: Clock) -> None:
        self.store = store
        self.clock = clock

    def get(self, entity: str, slot: str) -> BeliefRecord | None:
        return self.store.get_active_belief(entity, slot)

    def create_from_memory(self, memory: DurableMemory, source_weight: float) -> BeliefRecord:
        now = self.clock.now()
        belief = BeliefRecord(
            belief_id=str(uuid.uuid4()),
            entity=memory.entity or '',
            slot=memory.slot or '',
            current_value=memory.value,
            status=BeliefStatus.ACTIVE,
            confidence=memory.confidence,
            valid_from=memory.valid_from or now,
            valid_to=None,
            last_reviewed_at=now,
            supporting_memory_ids=[memory.memory_id],
            source_weights={memory.source.source_id: source_weight},
        )
        self.store.update_belief(belief)
        return belief

    def save(self, belief: BeliefRecord) -> None:
        belief.last_reviewed_at = self.clock.now()
        self.store.update_belief(belief)
