from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_memory.adapters.memvid_store import InMemoryMemoryStore
from agent_memory.audit import AuditLogger, InMemoryAuditSink
from agent_memory.belief_store import BeliefStore
from agent_memory.belief_updater import BeliefUpdater
from agent_memory.clock import Clock
from agent_memory.enums import MemoryType, PromotionDecision, QueryIntent, Scope, SourceType
from agent_memory.memory_classifier import MemoryClassifier
from agent_memory.memory_controller import MemoryController
from agent_memory.memory_intake import MemoryIntake
from agent_memory.memory_promoter import MemoryPromoter
from agent_memory.memory_retriever import MemoryRetriever
from agent_memory.policy import MemoryPolicy
from agent_memory.ranker import MemoryRanker
from agent_memory.schemas import Provenance, RetrievalQuery
from agent_memory.source_trust import SourceTrust


class FixedClock(Clock):
    def __init__(self) -> None:
        self.current = datetime(2026, 3, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current


class ControllerEndToEndTests(unittest.TestCase):
    def test_controller_governs_ingest_and_retrieval(self) -> None:
        clock = FixedClock()
        store = InMemoryMemoryStore()
        audit_sink = InMemoryAuditSink()
        belief_store = BeliefStore(store, clock)
        controller = MemoryController(
            store=store,
            intake=MemoryIntake(clock),
            classifier=MemoryClassifier(),
            promoter=MemoryPromoter(MemoryPolicy(), clock),
            belief_updater=BeliefUpdater(belief_store, SourceTrust()),
            retriever=MemoryRetriever(store, belief_store, MemoryRanker(), clock),
            audit=AuditLogger(audit_sink, clock),
        )
        source = Provenance(source_type=SourceType.FILE, source_id='file-1')

        trace_result = controller.ingest_text(
            raw_text='Nightly backup note.',
            source=source,
            actor='tester',
        )
        fact_result = controller.ingest_text(
            raw_text='User favorite_editor is helix.',
            source=source,
            actor='tester',
            entity='user',
            slot='favorite_editor',
            value='helix',
            memory_type=MemoryType.TRACE,
            confidence=0.85,
            salience=0.90,
            scope=Scope.PRIVATE,
            extra={'confirmed': True},
        )

        hits = controller.retrieve(
            RetrievalQuery(
                query_text='What is the current favorite editor?',
                intent=QueryIntent.CURRENT_FACT,
                entity='user',
                slot='favorite_editor',
            ),
            actor='tester',
        )

        self.assertEqual(trace_result.decision, PromotionDecision.STORE_TRACE)
        self.assertEqual(fact_result.decision, PromotionDecision.PROMOTE)
        self.assertEqual(hits[0].value, 'helix')
        self.assertEqual(hits[0].reason, 'active_belief')
        self.assertEqual([event.event_type for event in audit_sink.events], [
            'candidate_classified',
            'trace_stored',
            'candidate_classified',
            'memory_promoted',
            'belief_updated',
            'retrieval_performed',
        ])


if __name__ == '__main__':
    unittest.main()
