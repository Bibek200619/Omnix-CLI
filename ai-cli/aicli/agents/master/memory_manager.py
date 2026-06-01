"""Master Agent memory extraction helpers."""

from __future__ import annotations

import re

from aicli.agents.master.models import DetectedMemoryUpdates

_GOAL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^build\s+(?P<title>.+)$", re.IGNORECASE), "Build"),
    (re.compile(r"^create\s+(?P<title>.+)$", re.IGNORECASE), "Create"),
    (re.compile(r"^make\s+(?P<title>.+)$", re.IGNORECASE), "Make"),
    (re.compile(r"^develop\s+(?P<title>.+)$", re.IGNORECASE), "Develop"),
    (re.compile(r"^i want to build\s+(?P<title>.+)$", re.IGNORECASE), "Build"),
    (re.compile(r"^i want to create\s+(?P<title>.+)$", re.IGNORECASE), "Create"),
    (re.compile(r"^we need to build\s+(?P<title>.+)$", re.IGNORECASE), "Build"),
    (re.compile(r"^help me build\s+(?P<title>.+)$", re.IGNORECASE), "Build"),
    (re.compile(r"^(?:let's|lets) build\s+(?P<title>.+)$", re.IGNORECASE), "Build"),
)

_DECISION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwe will use\s+(?P<choice>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\bi will use\s+(?P<choice>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\bwe should use\s+(?P<choice>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\b(?:let's|lets) use\s+(?P<choice>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\bwe decided to use\s+(?P<choice>[^.?!]+)", re.IGNORECASE),
)


def detect_memory_updates(message: str) -> DetectedMemoryUpdates:
    """Detect simple, deterministic memory updates from a user message."""

    return DetectedMemoryUpdates(
        goal=detect_goal(message),
        decisions=detect_decisions(message),
    )


def detect_goal(message: str) -> str | None:
    """Detect a project goal from common goal-setting phrasing."""

    normalized_message = _clean_fragment(message)
    if not normalized_message:
        return None

    for pattern, verb in _GOAL_PATTERNS:
        match = pattern.match(normalized_message)
        if match is None:
            continue

        title = _clean_fragment(match.group("title"))
        if not title:
            return None
        return f"{verb} {title}"

    return None


def detect_decisions(message: str) -> list[str]:
    """Detect simple technology or project decisions from a user message."""

    decisions: list[str] = []
    seen: set[str] = set()
    for pattern in _DECISION_PATTERNS:
        for match in pattern.finditer(message):
            choice = _clean_fragment(match.group("choice"))
            if not choice:
                continue
            decision = f"Use {choice}"
            lookup_key = " ".join(decision.casefold().split())
            if lookup_key in seen:
                continue
            seen.add(lookup_key)
            decisions.append(decision)
    return decisions


def _clean_fragment(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    return cleaned.strip(" .?!")
