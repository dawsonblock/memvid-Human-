from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
import re
import uuid

from ..enums import BeliefStatus, MemoryType, QueryIntent, Scope, SourceType
from ..schemas import BeliefRecord, DurableMemory, Provenance, RetrievalHit, RetrievalQuery


class MemoryStore(Protocol):
    def put_trace(self, raw_text: str, metadata: dict[str, Any]) -> str: ...
    def put_memory(self, memory: DurableMemory) -> str: ...
    def update_belief(self, belief: BeliefRecord) -> None: ...
    def get_active_belief(self, entity: str, slot: str) -> BeliefRecord | None: ...
    def search(self, query: RetrievalQuery) -> list[RetrievalHit]: ...
    def list_memories_for_belief(self, entity: str, slot: str) -> list[DurableMemory]: ...
    def expire_memory(self, memory_id: str) -> None: ...


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self.traces: dict[str, dict[str, Any]] = {}
        self.memories: dict[str, DurableMemory] = {}
        self.beliefs: dict[str, BeliefRecord] = {}
        self.active_beliefs: dict[tuple[str, str], str] = {}
        self.expired_memory_ids: set[str] = set()

    def put_trace(self, raw_text: str, metadata: dict[str, Any]) -> str:
        trace_id = str(uuid.uuid4())
        self.traces[trace_id] = {'raw_text': raw_text, 'metadata': dict(metadata)}
        return trace_id

    def put_memory(self, memory: DurableMemory) -> str:
        self.memories[memory.memory_id] = memory
        return memory.memory_id

    def update_belief(self, belief: BeliefRecord) -> None:
        self.beliefs[belief.belief_id] = belief
        key = (belief.entity, belief.slot)
        if belief.status in {BeliefStatus.ACTIVE, BeliefStatus.DISPUTED}:
            self.active_beliefs[key] = belief.belief_id
        elif self.active_beliefs.get(key) == belief.belief_id:
            self.active_beliefs.pop(key, None)

    def get_active_belief(self, entity: str, slot: str) -> BeliefRecord | None:
        belief_id = self.active_beliefs.get((entity, slot))
        if belief_id is None:
            return None
        return self.beliefs.get(belief_id)

    def search(self, query: RetrievalQuery) -> list[RetrievalHit]:
        hits: list[RetrievalHit] = []
        for memory in self.memories.values():
            if memory.memory_id in self.expired_memory_ids:
                continue
            if not self._matches_query(memory, query):
                continue
            score = self._score_memory(memory, query)
            if score <= 0 and not self._has_structured_match(memory, query):
                continue
            hits.append(
                RetrievalHit(
                    memory_id=memory.memory_id,
                    score=max(score, 0.01),
                    reason='search_match',
                    memory_type=memory.memory_type,
                    entity=memory.entity,
                    slot=memory.slot,
                    value=memory.value,
                    raw_text=memory.raw_text,
                    source=memory.source,
                    event_time=memory.event_time or memory.valid_from,
                    extra=dict(memory.extra),
                )
            )
        return sorted(hits, key=lambda hit: hit.score, reverse=True)

    def list_memories_for_belief(self, entity: str, slot: str) -> list[DurableMemory]:
        return sorted(
            [
                memory
                for memory in self.memories.values()
                if memory.entity == entity
                and memory.slot == slot
                and memory.memory_id not in self.expired_memory_ids
            ],
            key=lambda memory: memory.stored_at,
        )

    def expire_memory(self, memory_id: str) -> None:
        self.expired_memory_ids.add(memory_id)

    def _matches_query(self, memory: DurableMemory, query: RetrievalQuery) -> bool:
        if query.scope is not None and memory.scope != query.scope:
            return False
        if query.entity is not None and memory.entity != query.entity:
            return False
        if query.slot is not None and memory.slot != query.slot:
            return False
        if query.tags and not set(query.tags).issubset(set(memory.tags)):
            return False
        if query.intent not in self._allowed_intents(memory.memory_type):
            return False
        if query.as_of is not None and not self._matches_as_of(memory, query.as_of):
            return False
        return True

    def _allowed_intents(self, memory_type: MemoryType) -> set[QueryIntent]:
        mapping = {
            MemoryType.FACT: {QueryIntent.CURRENT_FACT, QueryIntent.HISTORICAL_FACT, QueryIntent.SEMANTIC_BACKGROUND},
            MemoryType.PREFERENCE: {QueryIntent.PREFERENCE_LOOKUP, QueryIntent.SEMANTIC_BACKGROUND},
            MemoryType.GOAL_STATE: {QueryIntent.TASK_STATE, QueryIntent.SEMANTIC_BACKGROUND},
            MemoryType.EPISODE: {QueryIntent.EPISODIC_RECALL, QueryIntent.SEMANTIC_BACKGROUND},
            MemoryType.TRACE: {QueryIntent.EPISODIC_RECALL, QueryIntent.SEMANTIC_BACKGROUND},
        }
        return mapping.get(memory_type, {QueryIntent.SEMANTIC_BACKGROUND})

    def _matches_as_of(self, memory: DurableMemory, as_of: datetime) -> bool:
        start = memory.valid_from or memory.event_time or memory.stored_at
        end = memory.valid_to
        if end is not None:
            return start <= as_of <= end
        return start <= as_of

    def _has_structured_match(self, memory: DurableMemory, query: RetrievalQuery) -> bool:
        return (
            (query.entity is not None and memory.entity == query.entity)
            or (query.slot is not None and memory.slot == query.slot)
            or (bool(query.tags) and set(query.tags).issubset(set(memory.tags)))
        )

    def _score_memory(self, memory: DurableMemory, query: RetrievalQuery) -> float:
        haystack_tokens = set(self._tokenize(self._memory_text(memory)))
        query_tokens = set(self._tokenize(query.query_text))
        score = 0.0
        if query_tokens:
            score += len(query_tokens & haystack_tokens) / len(query_tokens)
        if query.entity is not None and memory.entity == query.entity:
            score += 0.25
        if query.slot is not None and memory.slot == query.slot:
            score += 0.20
        if query.scope is not None and memory.scope == query.scope:
            score += 0.05
        if query.tags:
            score += min(0.15, 0.05 * len(set(query.tags) & set(memory.tags)))
        return score

    def _memory_text(self, memory: DurableMemory) -> str:
        parts = [memory.raw_text]
        if memory.entity:
            parts.append(memory.entity)
        if memory.slot:
            parts.append(memory.slot)
        if memory.value:
            parts.append(memory.value)
        parts.extend(memory.tags)
        return ' '.join(parts).lower()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'[a-z0-9_]+', text.lower())
