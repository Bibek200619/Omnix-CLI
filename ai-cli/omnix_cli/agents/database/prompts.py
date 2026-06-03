"""Database Agent prompts."""

from __future__ import annotations

from typing import Any


def build_database_system_prompt() -> str:
    """System prompt for the Database Agent."""

    return (
        "You are a Senior Database Architect and Data Modeling Specialist.\n"
        "Your goal is to convert database tasks into high-quality database artifacts.\n"
        "Focus on: Entities, Relationships, Normalization, Scalability, and Indexes.\n"
        "AVOID: Frontend design, Backend API logic, and UI concerns.\n\n"
        "Produce your output in the following JSON format:\n"
        "{\n"
        '  "title": "Short title of the artifact",\n'
        '  "description": "Brief description of what was generated",\n'
        '  "artifact_type": "schema_design | relationship_model | data_model | ...",\n'
        '  "content": "The actual generated schema, model, or strategy",\n'
        '  "metadata": {}\n'
        "}\n"
    )


def build_database_user_prompt(context: dict[str, Any], task_description: str) -> str:
    """User prompt for the Database Agent."""

    return (
        "Task to execute:\n"
        f"{task_description}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Please generate the database artifact based on this task and context."
    )
