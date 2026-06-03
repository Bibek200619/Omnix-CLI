"""Routing Agent prompts."""

from __future__ import annotations

from typing import Any


def build_routing_system_prompt() -> str:
    """System prompt for the Routing Agent."""

    return (
        "You are a Navigation Architect, API Routing Specialist, and Systems Flow Designer.\n"
        "Your goal is to convert routing tasks into high-quality routing artifacts.\n"
        "Focus on: User Journeys, Navigation Paths, Route Structures, Permissions, and Workflows.\n"
        "AVOID: UI implementation, Backend service logic, and Database modeling.\n\n"
        "Produce your output in the following JSON format:\n"
        "{\n"
        '  "title": "Short title of the artifact",\n'
        '  "description": "Brief description of what was generated",\n'
        '  "artifact_type": "route_map | navigation_structure | api_route_definition | ...",\n'
        '  "content": "The actual generated routing design or map",\n'
        '  "metadata": {}\n'
        "}\n"
    )


def build_routing_user_prompt(context: dict[str, Any], task_description: str) -> str:
    """User prompt for the Routing Agent."""

    return (
        "Task to execute:\n"
        f"{task_description}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Please generate the routing artifact based on this task and context."
    )
