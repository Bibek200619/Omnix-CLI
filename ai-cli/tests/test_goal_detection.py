from __future__ import annotations

from aicli.agents.master.memory_manager import detect_goal


def test_detect_goal_from_direct_build_request() -> None:
    assert detect_goal("Build a CRM platform") == "Build a CRM platform"


def test_detect_goal_from_intent_phrase() -> None:
    assert (
        detect_goal("I want to create a hotel booking application.")
        == "Create a hotel booking application"
    )


def test_detect_goal_ignores_project_questions() -> None:
    assert detect_goal("What are we building?") is None
