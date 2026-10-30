"""Discover registered Typer commands instead of maintaining a second product catalog."""

from __future__ import annotations

from dataclasses import dataclass

from typer.core import TyperGroup


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    local: bool = False


LOCAL_COMMANDS = (
    Command("help", "Keyboard help and all available commands", True),
    Command("context", "Show or hide local project context", True),
    Command("changes", "Expand saved artifact changes; optional patch number", True),
    Command("theme", "Choose black, blue, white, terminal or mono", True),
    Command("new", "Start a new conversation and save the current one", True),
    Command("resume", "Resume the most recent previous conversation", True),
    Command("exit", "Close the terminal interface", True),
)


def commands_for(group: TyperGroup) -> list[Command]:
    """Flatten supported command paths, retaining the original help descriptions."""
    result: list[Command] = []

    def visit(parent: TyperGroup, prefix: str = "") -> None:
        for name, command in parent.commands.items():
            if name == "tui" or command.hidden:
                continue
            path = f"{prefix}{name}"
            if isinstance(command, TyperGroup):
                visit(command, f"{path} ")
            else:
                result.append(Command(path, command.get_short_help_str(90)))

    visit(group)
    return result + list(LOCAL_COMMANDS)


def matches(commands: list[Command], query: str) -> list[Command]:
    """Rank names before description matches; every action remains reachable."""
    query = query.removeprefix("/").strip().casefold()
    return sorted(
        (c for c in commands if query in f"{c.name} {c.description}".casefold()),
        key=lambda c: (not c.name.casefold().startswith(query), commands.index(c)),
    )


def command_path(commands: list[Command], text: str) -> Command | None:
    """Resolve the longest command path without interpreting shell operators."""
    return next(
        (
            command
            for command in sorted(commands, key=lambda c: len(c.name), reverse=True)
            if text == command.name or text.startswith(command.name + " ")
        ),
        None,
    )
