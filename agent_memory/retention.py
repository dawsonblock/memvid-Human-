from __future__ import annotations

from datetime import datetime

from .schemas import DurableMemory


class RetentionEngine:
    def is_expired(self, memory: DurableMemory, now: datetime) -> bool:
        if memory.ttl is None:
            return False
        return memory.stored_at + memory.ttl < now

    def decay_score(self, memory: DurableMemory, now: datetime) -> float:
        age_days = max(0.0, (now - memory.stored_at).total_seconds() / 86400.0)
        base = memory.salience
        if age_days <= 0:
            return base
        if memory.ttl is None:
            return max(0.25, base - (age_days * 0.002))
        return max(0.05, base - (age_days * 0.01))
