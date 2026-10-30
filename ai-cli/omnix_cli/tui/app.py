"""Conversation-first terminal with native editing, command discovery and real output."""

from __future__ import annotations

import asyncio
import os
import shlex
import sys
from pathlib import Path

import typer
from prompt_toolkit.application import Application, run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import Input
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import (
    ConditionalContainer,
    Dimension,
    DynamicContainer,
    HSplit,
    Layout,
    VSplit,
    Window,
)
from prompt_toolkit.layout.containers import Container, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.styles import DynamicStyle
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.widgets import TextArea
from typer.core import TyperGroup

from omnix_cli import __version__
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.tui.catalog import Command, command_path, commands_for, matches
from omnix_cli.tui.presentation import (
    THEMES,
    Entry,
    Patch,
    TranscriptLexer,
    artifact_changes,
    artifact_snapshot,
    clean,
    logo,
    project_context,
    theme_style,
)
from omnix_cli.tui.runner import CommandRunner, needs_terminal, run_terminal_command

HELP = (
    "Enter Send / Run     Ctrl+J Newline     / Commands\n"
    "Up/Down Select command     Enter/Tab Insert (Enter again to run)\n"
    "Escape Restore draft / Close context     Tab/Shift+Tab Focus\n"
    "PageUp/PageDown Scroll transcript     Space Toggle patch when transcript focused\n"
    "Ctrl+C Interrupt; twice at idle to exit     Ctrl+D Exit with an empty draft\n\n"
    "Plain messages go to Master. Specialists run only when invoked.\n"
    "Generated artifacts are not applied application source or executed tests.\n"
    "Use // at the start to send an absolute path as a message.\n"
    "/theme slate|light|terminal|mono changes this session's theme."
)


def _fit_line(text: str, width: int) -> str:
    """Keep status-bar labels readable without letting paths resize the layout."""
    if width <= 0:
        return ""
    if get_cwidth(text) <= width:
        return text
    if width <= 3:
        return "." * width
    left = (width - 1) // 2
    right = width - left - 1
    return text[:left] + "…" + text[-right:]


class TerminalApp:
    def __init__(
        self,
        group: TyperGroup,
        workspace: Path,
        theme: str = "slate",
        *,
        input: Input | None = None,
        output: Output | None = None,
    ) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.output = output or create_output()
        self.commands = commands_for(group)
        self.theme = theme
        self.no_color = "NO_COLOR" in os.environ
        self.runner = CommandRunner()
        self.entries: list[Entry] = []
        self.welcome = True
        self.busy = False
        self.exit_armed = False
        self.context_open = False
        self.palette_open = False
        self.selection = 0
        self.previous_text = ""
        self.restore_draft = ""
        self.inserting = False
        self.hint = "Type a goal, or / for commands. Start with /init for a new project."
        self.last_patches: list[Patch] = []
        self.patch_index = 0
        self.project, self.model, details = project_context(self.workspace)
        self.transcript = TextArea(
            read_only=True,
            scrollbar=False,
            wrap_lines=True,
            lexer=TranscriptLexer(),
            name="transcript",
        )
        self.context = TextArea(
            text=details,
            read_only=True,
            wrap_lines=True,
            style="class:context",
            name="project-context",
        )
        self.context_window = Window(
            content=self.context.control,
            width=35,
            wrap_lines=True,
            style="class:context",
        )
        self.composer = TextArea(
            height=lambda: min(5, max(2, self.composer.text.count("\n") + 1)),
            prompt="> ",
            history=InMemoryHistory(),
            multiline=True,
            wrap_lines=True,
            style="class:input",
            name="composer",
        )
        self.composer.buffer.on_text_changed += self._edited
        self._load_conversation()
        palette = ConditionalContainer(
            Window(
                FormattedTextControl(self._catalog),
                height=self._palette_height,
                style="class:context",
                wrap_lines=False,
            ),
            Condition(lambda: self.palette_open),
        )
        header = Window(FormattedTextControl(self._header), height=2)
        footer = Window(FormattedTextControl(self._footer), height=2, wrap_lines=True)
        root = HSplit(
            [header, DynamicContainer(self._body), palette, self.composer, footer],
            style="class:base",
            window_too_small=Window(
                FormattedTextControl("Terminal too small. Enlarge it or use omnix tui --plain."),
                wrap_lines=True,
            ),
        )
        self.app: Application[None] = Application(
            layout=Layout(root, focused_element=self.composer),
            key_bindings=self._bindings(),
            full_screen=True,
            style=DynamicStyle(lambda: theme_style(self.theme, self.no_color)),
            color_depth=ColorDepth.DEPTH_1_BIT if self.no_color else None,
            input=input,
            output=self.output,
            min_redraw_interval=0.05,
            mouse_support=False,
        )
        self.app.ttimeoutlen = 0.1

    def _load_conversation(self) -> None:
        state = StateManager(self.workspace)
        if not state.project_dir.exists():
            return
        try:
            memory = state.load_memory()
            for item in memory.conversations[-40:]:
                self.entries.append(Entry("You" if item.role == "user" else "Master", item.content))
            self.welcome = not self.entries
        except (OmnixError, OSError, ValueError) as exc:
            self.entries.append(Entry("Failed to load project state", str(exc)))
            self.welcome = False
        self._refresh_transcript()

    def _body(self) -> Container:
        if self.context_open:
            if self.output.get_size().columns < 110:
                return self.context.__pt_container__()
            return VSplit(
                [
                    self.transcript,
                    Window(width=2),
                    self.context_window,
                ],
                width=Dimension(min=1),
            )
        if self.welcome:
            small = self.output.get_size().rows < 24
            return HSplit(
                [
                    Window(),
                    Window(
                        FormattedTextControl("Omnix CLI" if small else logo),
                        height=1 if small else 11,
                        align=WindowAlign.CENTER,
                    ),
                    Window(
                        FormattedTextControl("One conversation. Your project."),
                        height=2,
                        align=WindowAlign.CENTER,
                        style="class:muted",
                    ),
                    Window(),
                ]
            )
        return self.transcript.__pt_container__()

    def _header(self) -> StyleAndTextTuples:
        available = self.output.get_size().columns
        workspace = _fit_line(
            f"{self.project}  {clean(str(self.workspace))}",
            available,
        )
        return [
            ("class:heading", f"Omnix CLI {__version__} / source preview\n"),
            ("class:muted", workspace),
        ]

    def _footer(self) -> StyleAndTextTuples:
        if self.output.get_size().columns < 80:
            keys = "Enter Send  / Commands  Esc Back  Ctrl+C Stop"
        else:
            keys = "Enter Send  Ctrl+J Newline  / Commands  Tab Focus  PgUp/PgDn Scroll"
        status = "Running" if self.busy else "Ready"
        if self.exit_armed:
            return [("class:muted", keys + "\n"), ("class:warning", self.hint)]
        return [
            ("class:muted", keys + "\n"),
            ("class:accent", f"Master / {self.model} / {status} / "),
            ("class:warning" if self.exit_armed else "class:muted", clean(self.hint)),
        ]

    def _palette_height(self) -> int:
        return min(11, max(3, self.output.get_size().rows // 2))

    def suggestions(self) -> list[Command]:
        return matches(self.commands, self.composer.text)

    def _catalog(self) -> StyleAndTextTuples:
        choices = self.suggestions()
        if not choices:
            return [
                ("class:muted", "No matching commands. Backspace to filter; Esc restores draft.")
            ]
        self.selection = min(self.selection, len(choices) - 1)
        count = max(1, self._palette_height() - 2)
        offset = max(0, self.selection - count + 1)
        width = self.output.get_size().columns
        result: StyleAndTextTuples = [
            (
                "class:muted",
                f"Commands {offset + 1}-{min(offset + count, len(choices))} of {len(choices)}\n",
            )
        ]
        for i, command in enumerate(choices[offset : offset + count], start=offset):
            label = " [UI]" if command.local else ""
            prefix = "> " if i == self.selection else "  "
            description = f"  {command.description}{label}" if width >= 60 else label
            row = f"{prefix}/{command.name:<18}{description}"
            row += " " * max(0, width - get_cwidth(row))
            result.append(("class:selected" if i == self.selection else "", row + "\n"))
        result.append(("class:muted", "Up/Down Select  Enter/Tab Insert  Esc Close"))
        return result

    def _edited(self, buffer: Buffer) -> None:
        text = buffer.text
        if text:
            self.welcome = False
        self.exit_armed = False
        if not self.inserting:
            path = command_path(self.commands, text.removeprefix("/").strip())
            has_arguments = path is not None and text.startswith("/" + path.name + " ")
            eligible = text.startswith("/") and not text.startswith("//") and "\n" not in text
            if eligible and not has_arguments:
                if not self.palette_open and not self.previous_text.startswith("/"):
                    self.restore_draft = self.previous_text
                self.palette_open = True
                self.selection = 0
            else:
                self.palette_open = False
        self.previous_text = text

    def insert_command(self) -> None:
        choices = self.suggestions()
        if not choices:
            return
        command = choices[min(self.selection, len(choices) - 1)]
        self.inserting = True
        self.composer.buffer.document = Document(f"/{command.name} ", len(command.name) + 2)
        self.inserting = False
        self.palette_open = False
        self.hint = "Command inserted. Review arguments, then Enter to run."

    def _refresh_transcript(self) -> None:
        focused = hasattr(self, "app") and self.app.layout.has_focus(self.transcript)
        old_cursor = self.transcript.buffer.cursor_position
        while len(self.entries) > 80:
            self.entries.pop(0)
        text = "\n\n".join(entry.render() for entry in self.entries)
        if len(text) > 262_144:
            text = (
                "[Older output omitted; use project commands to inspect stored state.]\n"
                + text[-262_144:]
            )
        self.transcript.buffer.set_document(
            Document(text, min(old_cursor, len(text)) if focused else len(text)),
            bypass_readonly=True,
        )
        if hasattr(self, "app"):
            self.app.invalidate()

    def _bindings(self) -> KeyBindings:
        keys = KeyBindings()
        palette = Condition(lambda: self.palette_open) & has_focus(self.composer)

        @keys.add("enter", filter=has_focus(self.composer))
        def send(event: KeyPressEvent) -> None:
            if self.palette_open and self.suggestions():
                self.insert_command()
            elif not self.busy:
                text = self.composer.text.strip()
                if text:
                    self.composer.buffer.append_to_history()
                    self.composer.text = ""
                    self.palette_open = False
                    self.app.create_background_task(self.submit(text))
            else:
                self.hint = "Work is running. Ctrl+C interrupts; your draft is retained."

        @keys.add("c-j", filter=has_focus(self.composer))
        def newline(event: KeyPressEvent) -> None:
            self.composer.buffer.insert_text("\n")

        @keys.add("up", filter=palette)
        @keys.add("down", filter=palette)
        def select(event: KeyPressEvent) -> None:
            delta = -1 if event.key_sequence[-1].key == "up" else 1
            self.selection = max(0, min(len(self.suggestions()) - 1, self.selection + delta))

        @keys.add("tab")
        @keys.add("s-tab")
        def focus(event: KeyPressEvent) -> None:
            if self.palette_open and self.suggestions():
                self.insert_command()
            elif event.key_sequence[-1].key == "s-tab":
                self.app.layout.focus_previous()
            else:
                self.app.layout.focus_next()

        @keys.add("escape")
        def escape(event: KeyPressEvent) -> None:
            if self.palette_open:
                self.inserting = True
                self.composer.text = self.restore_draft
                self.composer.buffer.cursor_position = len(self.restore_draft)
                self.inserting = False
            self.palette_open = False
            self.context_open = False
            self.app.layout.focus(self.composer)

        @keys.add("pageup")
        @keys.add("pagedown")
        def scroll(event: KeyPressEvent) -> None:
            self.welcome = False
            self.app.layout.focus(self.transcript)
            amount = max(1, self.output.get_size().rows - 8)
            if event.key_sequence[-1].key == "pageup":
                self.transcript.buffer.cursor_up(amount)
            else:
                self.transcript.buffer.cursor_down(amount)

        @keys.add(" ", filter=has_focus(self.transcript))
        def expand(event: KeyPressEvent) -> None:
            self.toggle_patch()

        @keys.add("c-c")
        def interrupt(event: KeyPressEvent) -> None:
            if self.busy:
                self.runner.interrupt()
                self.hint = "Interrupt requested. Waiting for the command to stop."
            elif self.exit_armed:
                self.app.exit()
            else:
                self.exit_armed = True
                self.welcome = False
                self.hint = "Press Ctrl+C again to exit. Your project files will be retained."

        @keys.add("c-d", filter=has_focus(self.composer))
        def eof(event: KeyPressEvent) -> None:
            if not self.composer.text and not self.busy:
                self.app.exit()
            else:
                self.composer.buffer.delete()

        return keys

    def toggle_patch(self) -> None:
        if self.last_patches:
            patch = self.last_patches[self.patch_index]
            patch.expanded = not patch.expanded
            self._refresh_transcript()

    def local_command(self, command: Command, args: list[str]) -> None:
        if command.name == "exit":
            self.app.exit()
        elif command.name == "context":
            self.context_open = not self.context_open
            if self.context_open:
                target = (
                    self.context_window
                    if self.output.get_size().columns >= 110
                    else self.context
                )
                self.app.layout.focus(target)
            else:
                self.app.layout.focus(self.composer)
        elif command.name == "theme":
            if len(args) != 1 or args[0] not in THEMES:
                self.entries.append(Entry("Theme", "Use /theme slate|light|terminal|mono."))
            else:
                self.theme = args[0]
                self.hint = f"Theme: {self.theme} (this session)."
        elif command.name == "changes":
            if not self.last_patches:
                self.entries.append(Entry("Changes", "No saved artifact changes in this session."))
            elif args and (
                not args[0].isdigit() or not 1 <= int(args[0]) <= len(self.last_patches)
            ):
                self.hint = f"Choose a patch number from 1 to {len(self.last_patches)}."
            else:
                self.patch_index = int(args[0]) - 1 if args else self.patch_index
                self.toggle_patch()
                self.context_open = False
                self.app.layout.focus(self.transcript)
        else:
            listing = "\n".join(f"/{c.name:<18} {c.description}" for c in self.commands)
            self.entries.append(Entry("Keyboard and command help", HELP + "\n\n" + listing))
            self.context_open = False

    async def submit(self, text: str) -> None:
        if self.busy:
            return
        self.welcome = False
        try:
            if text.startswith("/") and not text.startswith("//"):
                args = shlex.split(text[1:])
                command = command_path(self.commands, text[1:].strip())
                if command is None:
                    self.entries.append(
                        Entry("Failed: unknown command", "Use / to find an action.")
                    )
                    self._refresh_transcript()
                    return
                if command.local:
                    self.local_command(command, args[len(command.name.split()) :])
                    self._refresh_transcript()
                    return
                if args == ["chat"]:
                    self.hint = "Type a message to talk with Master."
                    return
            else:
                args = ["chat", "--", text[1:] if text.startswith("//") else text]
        except ValueError as exc:
            self.entries.append(Entry("Failed to parse command", str(exc)))
            self._refresh_transcript()
            return
        self.entries.append(Entry("You", text))
        if self.output.get_size().columns < 110:
            self.context_open = False
        label = (
            "Master"
            if args[0] == "chat"
            else "/" + " ".join(args[:2] if args[0] == "sessions" else args[:1])
        )
        entry = Entry("Running " + label)
        self.entries.append(entry)
        self.busy = True
        self.hint = "Ctrl+C interrupts. Draft input stays editable."
        self._refresh_transcript()
        before = artifact_snapshot(self.workspace)
        try:
            if needs_terminal(args):
                code = await run_in_terminal(
                    lambda: run_terminal_command(args, self.workspace),
                    in_executor=True,
                )
                entry.text = "Returned from the native interactive command."
            else:

                def output(chunk: str) -> None:
                    entry.text += chunk
                    self._refresh_transcript()

                code = await self.runner.run(args, self.workspace, output)
            entry.heading = label if code == 0 else f"Failed {label} (exit {code})"
            if code < 0 or code == 130:
                entry.heading = f"Interrupted {label}; inspect stored state before retrying."
        except (OSError, ValueError) as exc:
            entry.heading, entry.text = "Failed " + label, str(exc)
        finally:
            entry.patches = artifact_changes(before, artifact_snapshot(self.workspace))
            self.last_patches = entry.patches
            self.patch_index = 0
            self.busy = False
            self.project, self.model, details = project_context(self.workspace)
            self.context.text = details
            self.hint = "/help for keyboard guidance. /changes toggles the latest patch."
            self._refresh_transcript()

    def run(self) -> None:
        self.app.run()


def run_plain(group: TyperGroup, workspace: Path) -> None:
    """Linear output uses the same handlers with no redraw, logo or injected ANSI."""
    commands = commands_for(group)
    last_patches: list[Patch] = []
    typer.echo("Omnix CLI / linear mode. /help for commands; /exit to leave.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo()
            return
        if not text:
            continue
        command = command_path(commands, text[1:]) if text.startswith("/") else None
        if command and command.local:
            if command.name == "exit":
                return
            if command.name == "context":
                typer.echo(project_context(workspace)[2])
            elif command.name == "changes":
                if not last_patches:
                    typer.echo("No saved artifact changes in this session.")
                for patch in last_patches:
                    typer.echo("\n".join(patch.lines()))
            elif command.name == "theme":
                typer.echo("Linear mode uses your terminal defaults without added colors.")
            else:
                typer.echo(
                    "Enter sends one line. /context shows project state; /changes shows the latest "
                    "artifact changes. /exit or Ctrl+D exits. Ctrl+C interrupts.\n\n"
                    + "\n".join(f"/{c.name} {c.description}" for c in commands)
                )
            continue
        if text.startswith("/") and not text.startswith("//") and command is None:
            typer.echo("Unknown command. Use /help.")
            continue
        try:
            args = (
                shlex.split(text[1:])
                if command
                else ["chat", "--", text[1:] if text.startswith("//") else text]
            )
            if args == ["chat"]:
                continue
            before = artifact_snapshot(workspace)
            if needs_terminal(args):
                run_terminal_command(args, workspace)
            else:
                runner = CommandRunner()
                asyncio.run(
                    runner.run(args, workspace, lambda part: typer.echo(clean(part), nl=False))
                )
            last_patches = artifact_changes(before, artifact_snapshot(workspace))
            for patch in last_patches:
                typer.echo("\n".join(patch.lines()))
        except (ValueError, OSError) as exc:
            typer.echo(f"Failed: {clean(str(exc))}")
        except KeyboardInterrupt:
            typer.echo("Interrupted. Inspect project state before retrying.")


def launch(group: TyperGroup, workspace: Path, theme: str = "slate", plain: bool = False) -> None:
    workspace = workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise typer.BadParameter(
            "Workspace must be an existing directory.", param_hint="--workspace"
        )
    if (
        plain
        or os.environ.get("TERM") == "dumb"
        or not sys.stdin.isatty()
        or not sys.stdout.isatty()
    ):
        run_plain(group, workspace)
    else:
        TerminalApp(group, workspace, theme).run()
