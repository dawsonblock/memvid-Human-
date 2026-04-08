from __future__ import annotations

from .enums import SourceType
from .schemas import Provenance


DEFAULT_SOURCE_WEIGHTS: dict[SourceType, float] = {
    SourceType.SYSTEM: 0.95,
    SourceType.FILE: 0.85,
    SourceType.CHAT: 0.80,
    SourceType.TOOL: 0.75,
    SourceType.EXTERNAL: 0.60,
}


class SourceTrust:
    def __init__(self, weights: dict[SourceType, float] | None = None) -> None:
        self.weights = (
            DEFAULT_SOURCE_WEIGHTS.copy() if weights is None else weights.copy()
        )

    def weight_for(self, source: Provenance) -> float:
        return self.weights.get(source.source_type, 0.50)
