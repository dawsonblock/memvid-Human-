from __future__ import annotations

from dataclasses import replace

from .enums import MemoryType
from .schemas import CandidateMemory


class MemoryClassifier:
    def classify(self, candidate: CandidateMemory) -> CandidateMemory:
        text = candidate.raw_text.lower()

        if candidate.memory_type != MemoryType.TRACE:
            return candidate

        if (
            candidate.entity is not None
            and candidate.slot is not None
            and candidate.value is not None
        ):
            if candidate.slot in {'preference', 'style', 'likes', 'dislikes'}:
                return replace(
                    candidate,
                    memory_type=MemoryType.PREFERENCE,
                    salience=max(candidate.salience, 0.75),
                    confidence=max(candidate.confidence, 0.75),
                )

            if candidate.slot in {'goal', 'task', 'status', 'current_task', 'blocker'}:
                return replace(
                    candidate,
                    memory_type=MemoryType.GOAL_STATE,
                    salience=max(candidate.salience, 0.70),
                )

            return replace(
                candidate,
                memory_type=MemoryType.FACT,
                salience=max(candidate.salience, 0.60),
            )

        if any(tok in text for tok in ['failed', 'ran', 'asked', 'created', 'updated', 'retrieved']):
            return replace(
                candidate,
                memory_type=MemoryType.EPISODE,
                salience=max(candidate.salience, 0.45),
            )

        return candidate
