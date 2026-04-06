from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from agent_memory.adapters.memvid_store import InMemoryMemoryStore
from agent_memory.belief_store import BeliefStore
from agent_memory.clock import Clock
from agent_memory.enums import MemoryType, QueryIntent, Scope, SourceType
from agent_memory.memory_retriever import MemoryRetriever
from agent_memory.ranker import MemoryRanker
from agent_memory.schemas import DurableMemory, Provenance, RetrievalQuery


class FixedClock(Clock):
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


class TemporalRecallTests(unittest.TestCase):
    def test_historical_fact_respects_as_of_filter(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store = InMemoryMemoryStore()
        old_memory = DurableMemory(
            memory_id='memory-1',
            candidate_id='candidate-1',
            stored_at=base,
            entity='project',
            slot='status',
            value='planning',
            raw_text='project status planning',
            memory_type=MemoryType.FACT,
            confidence=0.8,
            salience=0.7,
            scope=Scope.PROJECT,
            ttl=None,
            source=Provenance(source_type=SourceType.FILE, source_id='file-1'),
            valid_from=base,
            valid_to=base + timedelta(days=3),
            event_time=base,
        )
        new_memory = DurableMemory(
            memory_id='memory-2',
            candidate_id='candidate-2',
            stored_at=base + timedelta(days=3),
            entity='project',
            slot='status',
            value='shipped',
            raw_text='project status shipped',
            memory_type=MemoryType.FACT,
            confidence=0.9,
            salience=0.8,
            scope=Scope.PROJECT,
            ttl=None,
            source=Provenance(source_type=SourceType.FILE, source_id='file-2'),
            valid_from=base + timedelta(days=3),
            event_time=base + timedelta(days=3),
        )
        store.put_memory(old_memory)
        store.put_memory(new_memory)
        retriever = MemoryRetriever(store, BeliefStore(store, FixedClock(base + timedelta(days=10))), MemoryRanker(), FixedClock(base + timedelta(days=10)))

        hits = retriever.retrieve(
            RetrievalQuery(
                query_text='What was the project status historically?',
                intent=QueryIntent.HISTORICAL_FACT,
                entity='project',
                slot='status',
                as_of=base + timedelta(days=2),
            )
        )

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].value, 'planning')


if __name__ == '__main__':
    unittest.main()
