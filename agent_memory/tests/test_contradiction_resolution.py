from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_memory.adapters.memvid_store import InMemoryMemoryStore
from agent_memory.belief_store import BeliefStore
from agent_memory.belief_updater import BeliefUpdater
from agent_memory.clock import Clock
from agent_memory.enums import BeliefAction, BeliefStatus, MemoryType, Scope, SourceType
from agent_memory.schemas import DurableMemory, Provenance
from agent_memory.source_trust import SourceTrust


class FixedClock(Clock):
    def __init__(self) -> None:
        self.current = datetime(2026, 2, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current


def make_memory(*, memory_id: str, value: str, source_type: SourceType, confidence: float) -> DurableMemory:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    return DurableMemory(
        memory_id=memory_id,
        candidate_id=f'candidate-{memory_id}',
        stored_at=now,
        entity='workspace',
        slot='owner',
        value=value,
        raw_text=f'workspace owner {value}',
        memory_type=MemoryType.FACT,
        confidence=confidence,
        salience=0.7,
        scope=Scope.SHARED,
        ttl=None,
        source=Provenance(source_type=source_type, source_id=f'{source_type.value}-{memory_id}'),
        valid_from=now,
    )


class ContradictionResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        clock = FixedClock()
        store = InMemoryMemoryStore()
        self.updater = BeliefUpdater(BeliefStore(store, clock), SourceTrust())

    def test_high_trust_source_supersedes_old_value(self) -> None:
        self.updater.apply(make_memory(memory_id='m1', value='alice', source_type=SourceType.CHAT, confidence=0.70))
        action, belief = self.updater.apply(
            make_memory(memory_id='m2', value='bob', source_type=SourceType.SYSTEM, confidence=0.90)
        )

        self.assertEqual(action, BeliefAction.UPDATE)
        self.assertEqual(belief.current_value, 'bob')
        self.assertEqual(belief.status, BeliefStatus.ACTIVE)

    def test_low_trust_source_marks_belief_disputed(self) -> None:
        self.updater.apply(make_memory(memory_id='m1', value='alice', source_type=SourceType.SYSTEM, confidence=0.90))
        action, belief = self.updater.apply(
            make_memory(memory_id='m2', value='mallory', source_type=SourceType.EXTERNAL, confidence=0.70)
        )

        self.assertEqual(action, BeliefAction.DISPUTE)
        self.assertEqual(belief.status, BeliefStatus.DISPUTED)
        self.assertIn('m2', belief.opposing_memory_ids)


if __name__ == '__main__':
    unittest.main()
