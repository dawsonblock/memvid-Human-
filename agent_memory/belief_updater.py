from __future__ import annotations

from .belief_store import BeliefStore
from .enums import BeliefAction, BeliefStatus
from .errors import BeliefUpdateError
from .schemas import BeliefRecord, DurableMemory
from .source_trust import SourceTrust


class BeliefUpdater:
    def __init__(self, belief_store: BeliefStore, source_trust: SourceTrust) -> None:
        self.belief_store = belief_store
        self.source_trust = source_trust

    def apply(self, memory: DurableMemory) -> tuple[BeliefAction, BeliefRecord]:
        if not memory.entity or not memory.slot:
            raise BeliefUpdateError('Belief updates require entity and slot')

        source_weight = self.source_trust.weight_for(memory.source)
        current = self.belief_store.get(memory.entity, memory.slot)

        if current is None:
            belief = self.belief_store.create_from_memory(memory, source_weight)
            return BeliefAction.UPDATE, belief

        current.source_weights[memory.source.source_id] = source_weight

        if memory.extra.get('retracts') is True:
            current.status = BeliefStatus.RETRACTED
            current.current_value = None
            current.valid_to = memory.valid_from or memory.stored_at
            current.opposing_memory_ids.append(memory.memory_id)
            self.belief_store.save(current)
            return BeliefAction.RETRACT, current

        if current.current_value == memory.value:
            current.status = BeliefStatus.ACTIVE
            current.supporting_memory_ids.append(memory.memory_id)
            current.confidence = min(1.0, current.confidence + 0.05)
            self.belief_store.save(current)
            return BeliefAction.REINFORCE, current

        if source_weight >= 0.85 and memory.confidence >= current.confidence:
            current.status = BeliefStatus.STALE
            current.valid_to = memory.valid_from or memory.stored_at
            self.belief_store.save(current)
            belief = self.belief_store.create_from_memory(memory, source_weight)
            return BeliefAction.UPDATE, belief

        current.status = BeliefStatus.DISPUTED
        current.opposing_memory_ids.append(memory.memory_id)
        self.belief_store.save(current)
        return BeliefAction.DISPUTE, current
