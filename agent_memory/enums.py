from __future__ import annotations

from enum import Enum


class MemoryType(str, Enum):
    TRACE = 'trace'
    EPISODE = 'episode'
    FACT = 'fact'
    PREFERENCE = 'preference'
    GOAL_STATE = 'goal_state'


class BeliefStatus(str, Enum):
    ACTIVE = 'active'
    DISPUTED = 'disputed'
    STALE = 'stale'
    RETRACTED = 'retracted'


class QueryIntent(str, Enum):
    CURRENT_FACT = 'current_fact'
    HISTORICAL_FACT = 'historical_fact'
    PREFERENCE_LOOKUP = 'preference_lookup'
    TASK_STATE = 'task_state'
    EPISODIC_RECALL = 'episodic_recall'
    SEMANTIC_BACKGROUND = 'semantic_background'


class SourceType(str, Enum):
    CHAT = 'chat'
    FILE = 'file'
    TOOL = 'tool'
    SYSTEM = 'system'
    EXTERNAL = 'external'


class Scope(str, Enum):
    PRIVATE = 'private'
    TASK = 'task'
    PROJECT = 'project'
    SHARED = 'shared'


class PromotionDecision(str, Enum):
    REJECT = 'reject'
    STORE_TRACE = 'store_trace'
    PROMOTE = 'promote'


class BeliefAction(str, Enum):
    REINFORCE = 'reinforce'
    UPDATE = 'update'
    DISPUTE = 'dispute'
    RETRACT = 'retract'
