from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from agent_memory.enums import MemoryType, Scope, SourceType
from agent_memory.retention import RetentionEngine
from agent_memory.schemas import DurableMemory, Provenance


def make_memory(*, stored_at: datetime, ttl: timedelta | None) -> DurableMemory:
    return DurableMemory(
        memory_id='memory-1',
        candidate_id='candidate-1',
        stored_at=stored_at,
        entity='agent',
        slot='status',
        value='active',
        raw_text='agent status active',
        memory_type=MemoryType.GOAL_STATE,
        confidence=0.7,
        salience=0.8,
        scope=Scope.TASK,
        ttl=ttl,
        source=Provenance(source_type=SourceType.SYSTEM, source_id='sys-1'),
        valid_from=stored_at,
    )


class RetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RetentionEngine()
        self.now = datetime(2026, 1, 15, tzinfo=timezone.utc)

    def test_ttl_expiration(self) -> None:
        memory = make_memory(stored_at=self.now - timedelta(days=10), ttl=timedelta(days=7))
        self.assertTrue(self.engine.is_expired(memory, self.now))

    def test_non_expiring_memory_stays_active(self) -> None:
        memory = make_memory(stored_at=self.now - timedelta(days=365), ttl=None)
        self.assertFalse(self.engine.is_expired(memory, self.now))
        self.assertGreaterEqual(self.engine.decay_score(memory, self.now), 0.25)

    def test_ttl_backed_memory_decays_to_floor(self) -> None:
        memory = make_memory(stored_at=self.now - timedelta(days=365), ttl=timedelta(days=30))
        self.assertEqual(self.engine.decay_score(memory, self.now), 0.05)


if __name__ == '__main__':
    unittest.main()
