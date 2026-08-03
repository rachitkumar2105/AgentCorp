"""Unit tests for the Memory Engine."""

import pytest

from app.memory.extractor import MemoryExtractor


@pytest.fixture
def extractor() -> MemoryExtractor:
    """Create a MemoryExtractor instance."""
    return MemoryExtractor()


def test_memory_extractor_extracts_single_preference(extractor: MemoryExtractor) -> None:
    """Should extract one user preference."""

    history = "I prefer using dark mode in all applications."

    memories = extractor.extract_memories(history)

    assert len(memories) == 1
    assert memories[0]["title"] == "User preference"


def test_memory_extractor_returns_empty_for_non_preferences(
    extractor: MemoryExtractor,
) -> None:
    """Should not extract memories from unrelated text."""

    history = "Just chatting about the weather today."

    memories = extractor.extract_memories(history)

    assert memories == []


def test_memory_extractor_handles_empty_string(
    extractor: MemoryExtractor,
) -> None:
    """Should safely handle empty input."""

    memories = extractor.extract_memories("")

    assert memories == []


def test_memory_extractor_extracts_multiple_preferences(
    extractor: MemoryExtractor,
) -> None:
    """Should extract multiple preferences if supported."""

    history = (
        "I prefer dark mode. "
        "I prefer PostgreSQL over MySQL."
    )

    memories = extractor.extract_memories(history)

    assert len(memories) >= 2


def test_memory_extractor_is_case_insensitive(
    extractor: MemoryExtractor,
) -> None:
    """Preference detection should ignore case."""

    history = "I PREFER DARK MODE."

    memories = extractor.extract_memories(history)

    assert len(memories) == 1


def test_memory_extractor_handles_whitespace(
    extractor: MemoryExtractor,
) -> None:
    """Should ignore surrounding whitespace."""

    history = "     I prefer dark mode.      "

    memories = extractor.extract_memories(history)

    assert len(memories) == 1


def test_memory_extractor_rejects_random_text(
    extractor: MemoryExtractor,
) -> None:
    """Random text should not generate memories."""

    history = (
        "Lorem ipsum dolor sit amet, "
        "consectetur adipiscing elit."
    )

    memories = extractor.extract_memories(history)

    assert memories == []


@pytest.mark.parametrize(
    "history",
    [
        "I prefer Python.",
        "I prefer Linux.",
        "I prefer tea over coffee.",
    ],
)
def test_memory_extractor_parametrized_preferences(
    extractor: MemoryExtractor,
    history: str,
) -> None:
    """Different preference statements should all be detected."""

    memories = extractor.extract_memories(history)

    assert len(memories) == 1
