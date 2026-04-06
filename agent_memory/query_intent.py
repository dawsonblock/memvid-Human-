from __future__ import annotations

from .enums import QueryIntent


class QueryIntentDetector:
    def detect(self, query_text: str) -> QueryIntent:
        q = query_text.lower()

        if any(tok in q for tok in ['prefer', 'preference', 'likes', 'dislikes', 'style']):
            return QueryIntent.PREFERENCE_LOOKUP

        if any(tok in q for tok in ['currently', 'current', 'now', 'latest truth']):
            return QueryIntent.CURRENT_FACT

        if any(tok in q for tok in ['as of', 'at that time', 'historically', 'back then']):
            return QueryIntent.HISTORICAL_FACT

        if any(tok in q for tok in ['task', 'status', 'open blocker', 'current goal']):
            return QueryIntent.TASK_STATE

        if any(tok in q for tok in ['what happened', 'timeline', 'sequence', 'episode']):
            return QueryIntent.EPISODIC_RECALL

        return QueryIntent.SEMANTIC_BACKGROUND
