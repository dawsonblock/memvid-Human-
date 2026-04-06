from __future__ import annotations

from dataclasses import replace
from typing import Any
import uuid

from .clock import Clock
from .enums import MemoryType, Scope
from .schemas import CandidateMemory, Provenance


class MemoryIntake:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def from_text(
        self,
        *,
        raw_text: str,
        source: Provenance,
        entity: str | None = None,
        slot: str | None = None,
        value: str | None = None,
        memory_type: MemoryType = MemoryType.TRACE,
        confidence: float = 0.40,
        salience: float = 0.30,
        scope: Scope = Scope.PRIVATE,
        extra: dict[str, Any] | None = None,
    ) -> CandidateMemory:
        return CandidateMemory(
            candidate_id=str(uuid.uuid4()),
            observed_at=self.clock.now(),
            entity=entity,
            slot=slot,
            value=value,
            raw_text=raw_text,
            source=source,
            memory_type=memory_type,
            confidence=confidence,
            salience=salience,
            scope=scope,
            ttl=None,
            extra=extra or {},
        )

    def enrich(
        self,
        candidate: CandidateMemory,
        *,
        entity: str | None = None,
        slot: str | None = None,
        value: str | None = None,
        memory_type: MemoryType | None = None,
        confidence: float | None = None,
        salience: float | None = None,
    ) -> CandidateMemory:
        return replace(
            candidate,
            entity=entity if entity is not None else candidate.entity,
            slot=slot if slot is not None else candidate.slot,
            value=value if value is not None else candidate.value,
            memory_type=memory_type if memory_type is not None else candidate.memory_type,
            confidence=confidence if confidence is not None else candidate.confidence,
            salience=salience if salience is not None else candidate.salience,
        )
