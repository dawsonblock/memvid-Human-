from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .enums import (
    BeliefStatus,
    MemoryType,
    PromotionDecision,
    QueryIntent,
    Scope,
    SourceType,
)


@dataclass(slots=True)
class Provenance:
    source_type: SourceType
    source_id: str
    author: str | None = None
    uri: str | None = None
    tool_name: str | None = None
    snippet: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CandidateMemory:
    candidate_id: str
    observed_at: datetime
    entity: str | None
    slot: str | None
    value: str | None
    raw_text: str
    source: Provenance
    memory_type: MemoryType
    confidence: float
    salience: float
    scope: Scope
    ttl: timedelta | None
    tags: list[str] = field(default_factory=list)
    event_time: datetime | None = None
    valid_at: datetime | None = None
    embedding_ref: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DurableMemory:
    memory_id: str
    candidate_id: str
    stored_at: datetime
    entity: str | None
    slot: str | None
    value: str | None
    raw_text: str
    memory_type: MemoryType
    confidence: float
    salience: float
    scope: Scope
    ttl: timedelta | None
    source: Provenance
    event_time: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BeliefRecord:
    belief_id: str
    entity: str
    slot: str
    current_value: str | None
    status: BeliefStatus
    confidence: float
    valid_from: datetime
    valid_to: datetime | None
    last_reviewed_at: datetime
    supporting_memory_ids: list[str] = field(default_factory=list)
    opposing_memory_ids: list[str] = field(default_factory=list)
    source_weights: dict[str, float] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetentionRule:
    memory_type: MemoryType
    default_ttl: timedelta | None
    promotion_threshold: float
    decay_floor: float
    requires_confirmation: bool
    retrieval_priority: float


@dataclass(slots=True)
class RetrievalQuery:
    query_text: str
    intent: QueryIntent
    entity: str | None = None
    slot: str | None = None
    as_of: datetime | None = None
    scope: Scope | None = None
    top_k: int = 8
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalHit:
    memory_id: str
    score: float
    reason: str
    memory_type: MemoryType
    entity: str | None
    slot: str | None
    value: str | None
    raw_text: str
    source: Provenance
    event_time: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PromotionResult:
    decision: PromotionDecision
    reasons: list[str]
    durable_memory: DurableMemory | None = None


@dataclass(slots=True)
class AuditEvent:
    event_id: str
    event_type: str
    occurred_at: datetime
    actor: str
    target_id: str | None
    payload: dict[str, Any]
