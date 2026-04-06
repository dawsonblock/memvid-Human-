from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_memory.adapters.memvid_store import InMemoryMemoryStore
from agent_memory.belief_store import BeliefStore
from agent_memory.belief_updater import BeliefUpdater
from agent_memory.clock import Clock
from agent_memory.enums import MemoryType, QueryIntent, Scope, SourceType
from agent_memory.memory_retriever import MemoryRetriever
from agent_memory.ranker import MemoryRanker
from agent_memory.schemas import DurableMemory, Provenance, RetrievalQuery
from agent_memory.source_trust import SourceTrust


class FixedClock(Clock):
    def __init__(self) -> None:
        self.current = datetime(2026, 1, 5, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current


def make_memory(*, memory_id: str, memory_type: MemoryType, slot: str, value: str, raw_text: str) -> DurableMemory:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return DurableMemory(
        memory_id=memory_id,
        candidate_id=f'candidate-{memory_id}',
        stored_at=now,
        entity='sam',
        slot=slot,
        value=value,
        raw_text=raw_text,
        memory_type=memory_type,
        confidence=0.8,
        salience=0.8,
        scope=Scope.PRIVATE,
        ttl=None,
        source=Provenance(source_type=SourceType.FILE, source_id=f'file-{memory_id}'),
        valid_from=now,
        event_time=now,
    )


class RetrievalPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FixedClock()
        self.store = InMemoryMemoryStore()
        belief_store = BeliefStore(self.store, self.clock)
        updater = BeliefUpdater(belief_store, SourceTrust())
        fact = make_memory(
            memory_id='fact-1',
            memory_type=MemoryType.FACT,
            slot='favorite_editor',
            value='helix',
            raw_text='Sam favorite_editor helix',
        )
        pref = make_memory(
            memory_id='pref-1',
            memory_type=MemoryType.PREFERENCE,
            slot='style',
            value='concise',
            raw_text='Sam prefers concise answers',
        )
        goal = make_memory(
            memory_id='goal-1',
            memory_type=MemoryType.GOAL_STATE,
            slot='current_task',
            value='ship release',
            raw_text='Current task is ship release',
        )
        for memory in [fact, pref, goal]:
            self.store.put_memory(memory)
            updater.apply(memory)
        self.retriever = MemoryRetriever(self.store, belief_store, MemoryRanker(), self.clock)

    def test_current_fact_prefers_active_belief(self) -> None:
        hits = self.retriever.retrieve(
            RetrievalQuery(
                query_text="What is Sam's current favorite editor?",
                intent=QueryIntent.CURRENT_FACT,
                entity='sam',
                slot='favorite_editor',
            )
        )

        self.assertEqual(hits[0].reason, 'active_belief')
        self.assertEqual(hits[0].value, 'helix')

    def test_preference_lookup_prefers_preference_memory(self) -> None:
        hits = self.retriever.retrieve(
            RetrievalQuery(
                query_text='What style does Sam prefer?',
                intent=QueryIntent.PREFERENCE_LOOKUP,
                entity='sam',
                slot='style',
            )
        )

        self.assertEqual(hits[0].value, 'concise')
        self.assertEqual(hits[0].memory_type, MemoryType.PREFERENCE)

    def test_task_state_prefers_goal_state(self) -> None:
        hits = self.retriever.retrieve(
            RetrievalQuery(
                query_text='What is the current task status?',
                intent=QueryIntent.TASK_STATE,
                entity='sam',
                slot='current_task',
            )
        )

        self.assertEqual(hits[0].value, 'ship release')
        self.assertEqual(hits[0].memory_type, MemoryType.GOAL_STATE)


if __name__ == '__main__':
    unittest.main()
