from __future__ import annotations

from datetime import timedelta

from .enums import MemoryType
from .schemas import CandidateMemory, RetentionRule


DEFAULT_RETENTION_RULES: dict[MemoryType, RetentionRule] = {
    MemoryType.TRACE: RetentionRule(
        memory_type=MemoryType.TRACE,
        default_ttl=timedelta(days=7),
        promotion_threshold=1.0,
        decay_floor=0.05,
        requires_confirmation=False,
        retrieval_priority=0.2,
    ),
    MemoryType.EPISODE: RetentionRule(
        memory_type=MemoryType.EPISODE,
        default_ttl=timedelta(days=180),
        promotion_threshold=0.45,
        decay_floor=0.15,
        requires_confirmation=False,
        retrieval_priority=0.6,
    ),
    MemoryType.FACT: RetentionRule(
        memory_type=MemoryType.FACT,
        default_ttl=None,
        promotion_threshold=0.70,
        decay_floor=0.35,
        requires_confirmation=True,
        retrieval_priority=0.9,
    ),
    MemoryType.PREFERENCE: RetentionRule(
        memory_type=MemoryType.PREFERENCE,
        default_ttl=None,
        promotion_threshold=0.65,
        decay_floor=0.45,
        requires_confirmation=True,
        retrieval_priority=1.0,
    ),
    MemoryType.GOAL_STATE: RetentionRule(
        memory_type=MemoryType.GOAL_STATE,
        default_ttl=timedelta(days=30),
        promotion_threshold=0.55,
        decay_floor=0.25,
        requires_confirmation=False,
        retrieval_priority=0.95,
    ),
}


class MemoryPolicy:
    def __init__(self, retention_rules: dict[MemoryType, RetentionRule] | None = None) -> None:
        self.retention_rules = retention_rules or DEFAULT_RETENTION_RULES

    def retention_rule_for(self, memory_type: MemoryType) -> RetentionRule:
        return self.retention_rules[memory_type]

    def promotion_threshold_for(self, candidate: CandidateMemory) -> float:
        rule = self.retention_rule_for(candidate.memory_type)
        return rule.promotion_threshold

    def should_require_confirmation(self, candidate: CandidateMemory) -> bool:
        return self.retention_rule_for(candidate.memory_type).requires_confirmation

    def effective_ttl(self, candidate: CandidateMemory) -> timedelta | None:
        return candidate.ttl or self.retention_rule_for(candidate.memory_type).default_ttl
