from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_memory.clock import Clock
from agent_memory.enums import MemoryType, Scope, SourceType
from agent_memory.memory_classifier import MemoryClassifier
from agent_memory.memory_intake import MemoryIntake
from agent_memory.schemas import Provenance


class FixedClock(Clock):
    def __init__(self) -> None:
        self.current = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current


class MemoryClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = MemoryIntake(FixedClock())
        self.classifier = MemoryClassifier()
        self.source = Provenance(source_type=SourceType.CHAT, source_id='chat-1')

    def test_classifies_preferences_from_structured_slot(self) -> None:
        candidate = self.intake.from_text(
            raw_text='Pat prefers concise answers.',
            source=self.source,
            entity='pat',
            slot='preference',
            value='concise answers',
            memory_type=MemoryType.TRACE,
            scope=Scope.PRIVATE,
        )

        classified = self.classifier.classify(candidate)

        self.assertEqual(classified.memory_type, MemoryType.PREFERENCE)
        self.assertGreaterEqual(classified.confidence, 0.75)
        self.assertGreaterEqual(classified.salience, 0.75)

    def test_classifies_goal_state_from_structured_slot(self) -> None:
        candidate = self.intake.from_text(
            raw_text='Current task is shipping the release.',
            source=self.source,
            entity='agent',
            slot='current_task',
            value='shipping the release',
        )

        classified = self.classifier.classify(candidate)

        self.assertEqual(classified.memory_type, MemoryType.GOAL_STATE)
        self.assertGreaterEqual(classified.salience, 0.70)

    def test_classifies_episode_from_action_language(self) -> None:
        candidate = self.intake.from_text(
            raw_text='The agent updated the deployment checklist after it failed.',
            source=self.source,
        )

        classified = self.classifier.classify(candidate)

        self.assertEqual(classified.memory_type, MemoryType.EPISODE)
        self.assertGreaterEqual(classified.salience, 0.45)


if __name__ == '__main__':
    unittest.main()
