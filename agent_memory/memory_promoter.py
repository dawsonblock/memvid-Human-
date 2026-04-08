from __future__ import annotations

import uuid

from .clock import Clock
from .enums import MemoryType, PromotionDecision
from .errors import InvalidCandidate
from .policy import MemoryPolicy
from .schemas import CandidateMemory, DurableMemory, PromotionResult


class MemoryPromoter:
    def __init__(self, policy: MemoryPolicy, clock: Clock) -> None:
        self.policy = policy
        self.clock = clock

    def decide(self, candidate: CandidateMemory) -> PromotionResult:
        self._validate(candidate)
        reasons: list[str] = []

        if candidate.memory_type == MemoryType.TRACE:
            reasons.append('trace_memory_is_not_promoted')
            return PromotionResult(decision=PromotionDecision.STORE_TRACE, reasons=reasons)

        if self.policy.should_require_confirmation(candidate) and not candidate.extra.get('confirmed', False):
            reasons.append('confirmation_required')
            return PromotionResult(decision=PromotionDecision.REJECT, reasons=reasons)

        threshold = self.policy.promotion_threshold_for(candidate)
        score = (candidate.confidence * 0.55) + (candidate.salience * 0.45)

        if score < threshold:
            reasons.append(f'score_below_threshold:{score:.3f}<{threshold:.3f}')
            return PromotionResult(decision=PromotionDecision.REJECT, reasons=reasons)

        durable = DurableMemory(
            memory_id=str(uuid.uuid4()),
            candidate_id=candidate.candidate_id,
            stored_at=self.clock.now(),
            entity=candidate.entity,
            slot=candidate.slot,
            value=candidate.value,
            raw_text=candidate.raw_text,
            memory_type=candidate.memory_type,
            confidence=candidate.confidence,
            salience=candidate.salience,
            scope=candidate.scope,
            ttl=self.policy.effective_ttl(candidate),
            source=candidate.source,
            event_time=candidate.event_time,
            valid_from=candidate.valid_at or candidate.observed_at,
            tags=list(candidate.tags),
            extra=dict(candidate.extra),
        )
        reasons.append('candidate_promoted')
        return PromotionResult(
            decision=PromotionDecision.PROMOTE,
            reasons=reasons,
            durable_memory=durable,
        )

    def _validate(self, candidate: CandidateMemory) -> None:
        if not candidate.raw_text.strip():
            raise InvalidCandidate('Candidate raw_text cannot be empty')
        if not 0.0 <= candidate.confidence <= 1.0:
            raise InvalidCandidate('Candidate confidence must be between 0.0 and 1.0')
        if not 0.0 <= candidate.salience <= 1.0:
            raise InvalidCandidate('Candidate salience must be between 0.0 and 1.0')
