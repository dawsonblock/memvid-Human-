from __future__ import annotations

from datetime import timedelta
from typing import Any

from .audit import AuditLogger
from .belief_updater import BeliefUpdater
from .enums import MemoryType, PromotionDecision, Scope
from .memory_classifier import MemoryClassifier
from .memory_intake import MemoryIntake
from .memory_promoter import MemoryPromoter
from .memory_retriever import MemoryRetriever
from .schemas import CandidateMemory, PromotionResult, Provenance, RetrievalHit, RetrievalQuery
from .adapters.memvid_store import MemoryStore


BELIEF_BACKED_TYPES = {MemoryType.FACT, MemoryType.PREFERENCE, MemoryType.GOAL_STATE}


class MemoryController:
    def __init__(
        self,
        *,
        store: MemoryStore,
        intake: MemoryIntake,
        classifier: MemoryClassifier,
        promoter: MemoryPromoter,
        belief_updater: BeliefUpdater,
        retriever: MemoryRetriever,
        audit: AuditLogger,
    ) -> None:
        self.store = store
        self.intake = intake
        self.classifier = classifier
        self.promoter = promoter
        self.belief_updater = belief_updater
        self.retriever = retriever
        self.audit = audit

    def ingest_text(
        self,
        *,
        raw_text: str,
        source: Provenance,
        actor: str = 'system',
        entity: str | None = None,
        slot: str | None = None,
        value: str | None = None,
        memory_type: MemoryType = MemoryType.TRACE,
        confidence: float = 0.40,
        salience: float = 0.30,
        scope: Scope = Scope.PRIVATE,
        ttl: timedelta | None = None,
        extra: dict[str, Any] | None = None,
    ) -> PromotionResult:
        candidate = self.intake.from_text(
            raw_text=raw_text,
            source=source,
            entity=entity,
            slot=slot,
            value=value,
            memory_type=memory_type,
            confidence=confidence,
            salience=salience,
            scope=scope,
            ttl=ttl,
            extra=extra,
        )
        return self.ingest_candidate(candidate, actor=actor)

    def ingest_candidate(self, candidate: CandidateMemory, actor: str = 'system') -> PromotionResult:
        classified = self.classifier.classify(candidate)

        self.audit.log(
            event_type='candidate_classified',
            actor=actor,
            target_id=classified.candidate_id,
            payload={
                'memory_type': classified.memory_type.value,
                'entity': classified.entity,
                'slot': classified.slot,
                'confidence': classified.confidence,
                'salience': classified.salience,
            },
        )

        result = self.promoter.decide(classified)

        if result.decision == PromotionDecision.STORE_TRACE:
            trace_id = self.store.put_trace(classified.raw_text, {'candidate_id': classified.candidate_id})
            self.audit.log(
                event_type='trace_stored',
                actor=actor,
                target_id=trace_id,
                payload={'candidate_id': classified.candidate_id},
            )
            return result

        if result.decision == PromotionDecision.REJECT:
            self.audit.log(
                event_type='candidate_rejected',
                actor=actor,
                target_id=classified.candidate_id,
                payload={'reasons': result.reasons},
            )
            return result

        durable = result.durable_memory
        if durable is None:
            raise ValueError(
                f'Promotion decision {result.decision.value} requires durable_memory, '
                f'but none was provided for candidate {classified.candidate_id}'
            )
        self.store.put_memory(durable)

        self.audit.log(
            event_type='memory_promoted',
            actor=actor,
            target_id=durable.memory_id,
            payload={
                'candidate_id': classified.candidate_id,
                'memory_type': durable.memory_type.value,
                'entity': durable.entity,
                'slot': durable.slot,
                'value': durable.value,
            },
        )

        if durable.entity and durable.slot and durable.memory_type in BELIEF_BACKED_TYPES:
            action, belief = self.belief_updater.apply(durable)
            self.audit.log(
                event_type='belief_updated',
                actor=actor,
                target_id=belief.belief_id,
                payload={
                    'action': action.value,
                    'entity': belief.entity,
                    'slot': belief.slot,
                    'current_value': belief.current_value,
                    'status': belief.status.value,
                },
            )

        return result

    def retrieve(self, query: RetrievalQuery, actor: str = 'system') -> list[RetrievalHit]:
        hits = self.retriever.retrieve(query)
        self.audit.log(
            event_type='retrieval_performed',
            actor=actor,
            target_id=None,
            payload={
                'query_text': query.query_text,
                'intent': query.intent.value,
                'entity': query.entity,
                'slot': query.slot,
                'result_count': len(hits),
            },
        )
        return hits
