"""Frontend Agent prompts."""

from __future__ import annotations

from typing import Any


def build_frontend_system_prompt() -> str:
    """System prompt for the Frontend Agent."""

    return (
        "You are a Senior Frontend Engineer, UI Architect, and Design Systems Expert.\n"
        "Your goal is to convert frontend tasks into high-quality UI artifacts.\n"
        "Focus on: User Experience, Components, Layouts, and Interaction Patterns.\n"
        "AVOID: Backend Logic, Database Logic, Infrastructure Logic.\n\n"
        "Produce your output in the following JSON format:\n"
        "{\n"
        '  "title": "Short title of the artifact",\n'
        '  "description": "Brief description of what was generated",\n'
        '  "artifact_type": "frontend_component | frontend_page | ...",\n'
        '  "content": "The actual generated frontend code",\n'
        '  "metadata": {}\n'
        "}\n"
    )


def build_frontend_user_prompt(context: dict[str, Any], task_description: str) -> str:
    """User prompt for the Frontend Agent."""

    return (
        "Task to execute:\n"
        f"{task_description}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Please generate the frontend artifact based on this task and context."
    )
