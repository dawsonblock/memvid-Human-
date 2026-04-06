from __future__ import annotations

from datetime import datetime

from .enums import MemoryType, QueryIntent
from .schemas import RetrievalHit


TYPE_BONUS = {
    MemoryType.PREFERENCE: 0.20,
    MemoryType.GOAL_STATE: 0.18,
    MemoryType.FACT: 0.16,
    MemoryType.EPISODE: 0.10,
    MemoryType.TRACE: 0.02,
}


class MemoryRanker:
    def score(self, hit: RetrievalHit, intent: QueryIntent, now: datetime) -> float:
        score = hit.score
        score += TYPE_BONUS.get(hit.memory_type, 0.0)

        if hit.event_time:
            age_days = max(0.0, (now - hit.event_time).total_seconds() / 86400.0)
            if intent in {QueryIntent.TASK_STATE, QueryIntent.EPISODIC_RECALL}:
                score += max(0.0, 0.20 - (age_days * 0.01))

        if intent == QueryIntent.PREFERENCE_LOOKUP and hit.memory_type == MemoryType.PREFERENCE:
            score += 0.25

        if intent == QueryIntent.CURRENT_FACT and hit.memory_type == MemoryType.FACT:
            score += 0.20

        if intent == QueryIntent.HISTORICAL_FACT and hit.event_time is not None:
            score += 0.15

        return score

    def rerank(self, hits: list[RetrievalHit], intent: QueryIntent, now: datetime) -> list[RetrievalHit]:
        return sorted(hits, key=lambda hit: self.score(hit, intent, now), reverse=True)
