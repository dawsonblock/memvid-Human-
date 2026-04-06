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
        self.current = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current


def make_memory(*, memory_id: str, value: str, source_type: SourceType, confidence: float, extra=None) -> DurableMemory:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return DurableMemory(
        memory_id=memory_id,
        candidate_id=f'candidate-{memory_id}',
        stored_at=now,
        entity='user',
        slot='favorite_editor',
        value=value,
        raw_text=f'user favorite_editor is {value}',
        memory_type=MemoryType.FACT,
        confidence=confidence,
        salience=0.8,
        scope=Scope.PRIVATE,
        ttl=None,
        source=Provenance(source_type=source_type, source_id=f'{source_type.value}-{memory_id}'),
        valid_from=now,
        extra=extra or {},
    )


class BeliefUpdaterTests(unittest.TestCase):
    def setUp(self) -> None:
        clock = FixedClock()
        store = InMemoryMemoryStore()
        belief_store = BeliefStore(store, clock)
        self.updater = BeliefUpdater(belief_store, SourceTrust())
        self.store = store

    def test_reinforces_matching_value(self) -> None:
        initial = make_memory(memory_id='m1', value='vim', source_type=SourceType.CHAT, confidence=0.8)
        self.updater.apply(initial)

        action, belief = self.updater.apply(
            make_memory(memory_id='m2', value='vim', source_type=SourceType.FILE, confidence=0.85)
        )

        self.assertEqual(action, BeliefAction.REINFORCE)
        self.assertEqual(belief.status, BeliefStatus.ACTIVE)
        self.assertEqual(len(belief.supporting_memory_ids), 2)
        self.assertGreaterEqual(belief.confidence, 0.85)

    def test_high_trust_conflict_updates_belief(self) -> None:
        self.updater.apply(make_memory(memory_id='m1', value='vim', source_type=SourceType.CHAT, confidence=0.70))

        action, belief = self.updater.apply(
            make_memory(memory_id='m2', value='helix', source_type=SourceType.FILE, confidence=0.85)
        )

        self.assertEqual(action, BeliefAction.UPDATE)
        self.assertEqual(belief.current_value, 'helix')
        self.assertEqual(belief.status, BeliefStatus.ACTIVE)

    def test_lower_trust_conflict_disputes_belief(self) -> None:
        self.updater.apply(make_memory(memory_id='m1', value='vim', source_type=SourceType.FILE, confidence=0.85))

        action, belief = self.updater.apply(
            make_memory(memory_id='m2', value='nano', source_type=SourceType.EXTERNAL, confidence=0.60)
        )

        self.assertEqual(action, BeliefAction.DISPUTE)
        self.assertEqual(belief.status, BeliefStatus.DISPUTED)
        self.assertIn('m2', belief.opposing_memory_ids)

    def test_retracts_belief_when_memory_requests_it(self) -> None:
        self.updater.apply(make_memory(memory_id='m1', value='vim', source_type=SourceType.FILE, confidence=0.85))

        action, belief = self.updater.apply(
            make_memory(
                memory_id='m2',
                value='vim',
                source_type=SourceType.SYSTEM,
                confidence=0.95,
                extra={'retracts': True},
            )
        )

        self.assertEqual(action, BeliefAction.RETRACT)
        self.assertEqual(belief.status, BeliefStatus.RETRACTED)
        self.assertIsNone(belief.current_value)


if __name__ == '__main__':
    unittest.main()
