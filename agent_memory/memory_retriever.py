from __future__ import annotations

from .belief_store import BeliefStore
from .clock import Clock
from .enums import MemoryType, QueryIntent, SourceType
from .ranker import MemoryRanker
from .schemas import BeliefRecord, Provenance, RetrievalHit, RetrievalQuery
from .adapters.memvid_store import MemoryStore


BELIEF_MEMORY_TYPES = {
    QueryIntent.CURRENT_FACT: MemoryType.FACT,
    QueryIntent.PREFERENCE_LOOKUP: MemoryType.PREFERENCE,
    QueryIntent.TASK_STATE: MemoryType.GOAL_STATE,
}


class MemoryRetriever:
    def __init__(
        self,
        store: MemoryStore,
        belief_store: BeliefStore,
        ranker: MemoryRanker,
        clock: Clock,
    ) -> None:
        self.store = store
        self.belief_store = belief_store
        self.ranker = ranker
        self.clock = clock

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalHit]:
        hits: list[RetrievalHit] = []

        if query.as_of is None and query.intent in BELIEF_MEMORY_TYPES and query.entity and query.slot:
            belief = self.belief_store.get(query.entity, query.slot)
            if belief and belief.current_value is not None:
                hits.append(self._belief_to_hit(belief, query.intent))

        hits.extend(self.store.search(query))
        deduped = self._dedupe_hits(hits)
        reranked = self.ranker.rerank(deduped, query.intent, self.clock.now())
        return reranked[: query.top_k]

    def _belief_to_hit(self, belief: BeliefRecord, intent: QueryIntent) -> RetrievalHit:
        return RetrievalHit(
            memory_id=belief.belief_id,
            score=1.0,
            reason='active_belief',
            memory_type=BELIEF_MEMORY_TYPES[intent],
            entity=belief.entity,
            slot=belief.slot,
            value=belief.current_value,
            raw_text=f'{belief.entity}.{belief.slot} = {belief.current_value}',
            source=Provenance(source_type=SourceType.SYSTEM, source_id='belief_store'),
            event_time=belief.valid_from,
            extra={'belief_status': belief.status.value},
        )

    def _dedupe_hits(self, hits: list[RetrievalHit]) -> list[RetrievalHit]:
        by_memory_id: dict[str, RetrievalHit] = {}
        for hit in hits:
            incumbent = by_memory_id.get(hit.memory_id)
            if incumbent is None or hit.score > incumbent.score:
                by_memory_id[hit.memory_id] = hit
        return list(by_memory_id.values())
