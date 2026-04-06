from __future__ import annotations

from typing import Any, Protocol
import uuid

from .clock import Clock
from .schemas import AuditEvent


class AuditSink(Protocol):
    def append(self, event: AuditEvent) -> None: ...


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)


class AuditLogger:
    def __init__(self, sink: AuditSink, clock: Clock) -> None:
        self.sink = sink
        self.clock = clock

    def log(
        self,
        event_type: str,
        actor: str,
        target_id: str | None,
        payload: dict[str, Any],
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            occurred_at=self.clock.now(),
            actor=actor,
            target_id=target_id,
            payload=payload,
        )
        self.sink.append(event)
        return event
