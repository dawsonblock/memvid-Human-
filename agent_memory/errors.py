class MemoryError(Exception):
    pass


class PolicyViolation(MemoryError):
    pass


class InvalidCandidate(MemoryError):
    pass


class BeliefUpdateError(MemoryError):
    pass
