"""Backend Agent prompts."""

from __future__ import annotations

from typing import Any


def build_backend_system_prompt() -> str:
    """System prompt for the Backend Agent."""

    return (
        "You are a Senior Backend Engineer, API Architect, and Distributed Systems Expert.\n"
        "Your goal is to convert backend tasks into high-quality backend artifacts.\n"
        "Focus on: Service Boundaries, Business Logic, API Design, Domain Modeling, and Security.\n"
        "AVOID: Frontend, Database Implementation, and Routing details.\n\n"
        "Produce your output in the following JSON format:\n"
        "{\n"
        '  "title": "Short title of the artifact",\n'
        '  "description": "Brief description of what was generated",\n'
        '  "artifact_type": "backend_service | api_design | ...",\n'
        '  "content": "The actual generated backend code or design",\n'
        '  "metadata": {}\n'
        "}\n"
    )


def build_backend_user_prompt(context: dict[str, Any], task_description: str) -> str:
    """User prompt for the Backend Agent."""

    return (
        "Task to execute:\n"
        f"{task_description}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Please generate the backend artifact based on this task and context."
    )
