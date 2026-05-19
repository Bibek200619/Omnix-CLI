from __future__ import annotations

from aicli.agents.master.memory_manager import detect_decisions


def test_detect_decision_from_will_use_phrase() -> None:
    assert detect_decisions("We will use FastAPI.") == ["Use FastAPI"]


def test_detect_decision_from_lets_use_phrase() -> None:
    assert detect_decisions("Let's use PostgreSQL for persistence") == [
        "Use PostgreSQL for persistence"
    ]


def test_detect_decision_deduplicates_matches() -> None:
    decisions = detect_decisions("We will use React. We will use React.")

    assert decisions == ["Use React"]
