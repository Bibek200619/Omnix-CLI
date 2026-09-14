"""Integration Agent prompts."""

from __future__ import annotations

from typing import Any


def build_integration_system_prompt() -> str:
    """System prompt for the Integration Agent."""

    return (
        "You are a Principal Software Architect and Systems Integration Engineer.\n"
        "Your goal is to analyze worker artifacts and assemble an 'Integrated Package'.\n\n"
        "RESPONSIBILITIES:\n"
        "1. Map dependencies between Frontend, Backend, Database, and Routing artifacts.\n"
        "2. Detect inconsistencies (e.g., mismatched API fields, missing entities).\n"
        "3. Evaluate coverage against the original blueprint.\n"
        "4. Build a dependency graph.\n\n"
        "IMPORTANT: You do NOT generate code. Produce a structured analysis.\n\n"
        "Produce your output in the following JSON format:\n"
        "{\n"
        '  "status": "success | partial | failed",\n'
        '  "dependencies": [\n'
        '    {"source_id": "...", "target_id": "...", "dependency_type": "...", '
        '"description": "..."}\n'
        '  ],\n'
        '  "conflicts": [\n'
        '    {"id": "...", "title": "...", "description": "...", "severity": "...", '
        '"involved_artifact_ids": [...], "involved_blueprint_references": [...]}\n'
        '  ],\n'
        '  "coverage": {\n'
        '    "implemented_pages": 0,\n'
        '    "implemented_apis": 0,\n'
        '    "implemented_entities": 0,\n'
        '    "gaps": ["List of missing implementations"]\n'
        '  },\n'
        '  "summary": "Summary of integration findings"\n'
        "}\n"
    )


def build_integration_user_prompt(
    project_name: str,
    blueprint: dict[str, Any],
    artifacts: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> str:
    """User prompt for the Integration Agent."""

    return (
        f"Project: {project_name}\n\n"
        "BLUEPRINT:\n"
        f"{blueprint}\n\n"
        "ARTIFACTS PRODUCED BY WORKER AGENTS:\n"
        f"{artifacts}\n\n"
        "TASKS STATUS:\n"
        f"{tasks}\n\n"
        "Please analyze these components and generate the integration JSON."
    )
