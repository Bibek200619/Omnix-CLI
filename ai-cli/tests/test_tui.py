"""Behavioral coverage for the interactive shell and its existing-command bridge."""

from __future__ import annotations

import asyncio
import signal
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.output.base import Size
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from omnix_cli.cli.main import app
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.memory import ConversationEntry, ConversationRole, ProjectGoal
from omnix_cli.tui.app import TerminalApp, _fit_line
from omnix_cli.tui.catalog import command_path, commands_for, matches
from omnix_cli.tui.presentation import (
    PIXEL_MARK,
    Entry,
    Patch,
    artifact_changes,
    artifact_snapshot,
    clean,
    logo,
    project_context,
    theme_style,
)
from omnix_cli.tui.runner import CommandRunner, invocation, needs_terminal


def group() -> TyperGroup:
    command = get_command(app)
    assert isinstance(command, TyperGroup)
    return command


class SizedOutput(DummyOutput):
    def __init__(self, columns: int = 120, rows: int = 36) -> None:
        self.columns = columns
        self.rows = rows

    def get_size(self) -> Size:
        return Size(self.rows, self.columns)


async def eventually(predicate: Callable[[], bool]) -> None:
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(0.02)


def test_catalog_contains_real_workflows_and_separate_ui_actions() -> None:
    commands = commands_for(group())
    source = {c.name for c in commands if not c.local}
    assert len(source) == 33
    assert {"architect", "build", "repair", "sessions work", "sessions history"} <= source
    assert "tui" not in source
    assert {c.name for c in commands if c.local} == {
        "help",
        "context",
        "changes",
        "theme",
        "new",
        "resume",
        "exit",
    }
    assert matches(commands, "/arch")[0].name == "architect"
    assert matches(commands, "/workspace")
    assert matches(commands, "/does-not-exist") == []
    assert command_path(commands, "sessions history --json").name == "sessions history"
    assert command_path(commands, "architectural") is None
    ui = TerminalApp(group(), Path.cwd(), output=SizedOutput())
    ui.composer.text = "/"
    assert len(ui.suggestions()) == 40
    assert {"new", "resume"} <= {command.name for command in ui.suggestions()}
    ui.composer.text = "/context"
    assert [command.name for command in ui.suggestions()] == ["context"]


def test_logo_is_terminal_text_with_ascii_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    assert len(PIXEL_MARK) == 11
    assert {len(row) for row in PIXEL_MARK} == {28}
    assert "█" in "".join(t for _, t in logo())
    monkeypatch.setenv("OMNIX_ASCII", "1")
    rendered = "".join(t for _, t in logo())
    assert "#" in rendered and "█" not in rendered


def test_empty_welcome_explains_account_and_provider_setup_separately(tmp_path: Path) -> None:
    ui = TerminalApp(group(), tmp_path, output=SizedOutput())
    assert ui.account_status == "disconnected"
    assert "/init to begin" in ui._account_message()
    ui.project = "Atlas"
    (tmp_path / ".project").mkdir()
    (tmp_path / ".project" / "project.blueprint.json").touch()
    assert "/login to sign in" in ui._account_message()


def test_no_color_has_no_color_styles_and_terminal_theme_inherits_background() -> None:
    assert all("#" not in style for _, style in theme_style("slate", True).style_rules)
    assert all("bg:" not in style for _, style in theme_style("terminal").style_rules)
    assert any("#eef2f7" in style for _, style in theme_style("light").style_rules)
    assert any(
        name == "base" and "#182333" in style
        for name, style in theme_style("slate").style_rules
    )


def test_status_path_is_middle_truncated_to_terminal_width() -> None:
    path = "/a/very/long/project/path/that/should/not/overflow/the/status/bar"
    fitted = _fit_line(f"Atlas  {path}", 24)
    assert fitted.startswith("Atlas  /") and fitted.endswith("status/bar")
    assert len(fitted) == 24
    assert _fit_line("short", 3) == "..."


def test_patch_has_accurate_counts_line_numbers_and_no_false_applied_claim() -> None:
    patch = Patch(".project/artifacts/a.json", "old\nkeep\n", "new\nextra\nkeep\n")
    text = "\n".join(patch.lines())
    assert "(+2 -1)" in text
    assert "+         1  new" in text
    assert "-    1        old" in text
    assert "application source was not applied" in text
    patch.expanded = False
    assert len(patch.lines()) == 1
    assert "collapsed" in patch.lines()[0]
    assert "old" not in patch.lines()[0]


def test_large_patch_is_bounded_but_totals_are_exact() -> None:
    patch = Patch("large", "", "\n".join(f"line {i}" for i in range(500)))
    lines = patch.lines()
    assert "(+500 -0)" in lines[0]
    assert len(lines) < 210
    assert any("limited" in x for x in lines)


def test_external_control_sequences_are_not_sent_to_the_terminal() -> None:
    text = "safe\x1b[31mred\x1b[0m\x1b]52;c;clipboard\x07\x00text\nnext"
    assert clean(text) == "saferedtext\nnext"
    assert "\x1b" not in Entry("Heading", text).render()


def test_artifact_diffs_compare_saved_content_and_ignore_symlinks(tmp_path: Path) -> None:
    state = StateManager(tmp_path)
    state.init_project()
    artifact = Artifact(
        id="test",
        task_id="task",
        agent="frontend",
        title="Greeting",
        artifact_type=ArtifactType.FRONTEND_COMPONENT,
        content="hello\n",
    )
    before = artifact_snapshot(tmp_path)
    state.save_artifact(artifact)
    first = artifact_snapshot(tmp_path)
    assert len(artifact_changes(before, first)) == 1
    assert artifact_changes(first, first) == []
    state.save_artifact(artifact.model_copy(update={"content": "goodbye\n", "version": 2}))
    changes = artifact_changes(first, artifact_snapshot(tmp_path))
    assert len(changes) == 1
    assert changes[0].before == "hello\n" and changes[0].after == "goodbye\n"
    (state.artifacts_dir / "alias.json").symlink_to(next(state.artifacts_dir.glob("*.json")))
    assert len(artifact_snapshot(tmp_path)) == 1


def test_context_is_local_and_does_not_create_state(tmp_path: Path) -> None:
    _, model, details = project_context(tmp_path)
    assert "unconfigured" in model.casefold() and "/init" in details
    assert not (tmp_path / ".project").exists()
    StateManager(tmp_path).init_project(project_name="Atlas")
    name, model, details = project_context(tmp_path)
    assert name == "Atlas" and model == "Local"
    assert "Configuration is not a live connection check" in details
    assert not (tmp_path / ".project" / "omnix_project.json").exists()


def test_runner_preserves_message_arguments_and_existing_workspace(tmp_path: Path) -> None:
    args = invocation(["chat", "--", "--workspace"], tmp_path)
    assert args[-2:] == ["--", "--workspace"]
    assert args[-4:-2] == ["--workspace", str(tmp_path)]
    args = invocation(["memory", "-w", "/somewhere"], tmp_path)
    assert str(tmp_path) not in args
    assert str(tmp_path) not in invocation(["memory", "-w/somewhere"], tmp_path)
    assert needs_terminal(["link"])
    assert not needs_terminal(["link", "--workspace-id=chosen"])
    assert needs_terminal(["sessions", "work"])
    assert not needs_terminal(["sessions", "work", "--help"])


def test_runner_streams_real_commands_and_validation_failures(tmp_path: Path) -> None:
    async def scenario() -> None:
        runner = CommandRunner()
        output: list[str] = []
        code = await runner.run(["init", "--project-name", "Atlas"], tmp_path, output.append)
        assert code == 0 and "Initialized Omnix CLI" in "".join(output)
        output.clear()
        assert await runner.run(["chat", "--", "--workspace"], tmp_path, output.append) == 0
        assert StateManager(tmp_path).load_memory().conversations[0].content == "--workspace"
        output.clear()
        assert await runner.run(["artifact", "missing"], tmp_path, output.append) == 1
        assert "not found" in "".join(output)
        assert runner.process is None

    asyncio.run(scenario())


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process-group signal test")
def test_interrupt_stops_a_real_child_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from omnix_cli.tui import runner as module

    monkeypatch.setattr(
        module,
        "invocation",
        lambda args, workspace: [
            sys.executable,
            "-u",
            "-c",
            "import time; print('started', flush=True); time.sleep(60)",
        ],
    )

    async def scenario() -> None:
        runner = CommandRunner()
        output: list[str] = []
        task = asyncio.create_task(runner.run([], tmp_path, output.append))
        await eventually(lambda: "started" in "".join(output))
        runner.interrupt()
        assert await asyncio.wait_for(task, 6) in {-signal.SIGINT, 130}
        assert runner.process is None

    asyncio.run(scenario())


def test_palette_keyboard_inserts_without_running_and_reaches_last_action(tmp_path: Path) -> None:
    async def scenario() -> None:
        with create_pipe_input() as pipe:
            ui = TerminalApp(group(), tmp_path, input=pipe, output=SizedOutput())
            task = asyncio.create_task(ui.app.run_async())
            try:
                await asyncio.sleep(0.05)
                assert ui.welcome
                pipe.send_text("/")
                await eventually(lambda: ui.palette_open)
                assert not ui.welcome
                command_count = len(ui.suggestions())
                pipe.send_bytes(b"\x1b[B" * (command_count - 1))
                await eventually(lambda: ui.selection == command_count - 1)
                assert "/exit" in "".join(t for _, t in ui._catalog())
                pipe.send_bytes(b"\x7f")
                await eventually(lambda: not ui.palette_open)
                assert ui.composer.text == "" and ui.welcome
                pipe.send_text("/ini")
                await eventually(lambda: ui.composer.text == "/ini")
                pipe.send_bytes(b"\r")
                await eventually(lambda: ui.composer.text == "/init ")
                assert not (tmp_path / ".project").exists()
                pipe.send_bytes(b"\r")
                await eventually(lambda: (tmp_path / ".project").exists())
                await eventually(lambda: not ui.busy)
                assert "Initialized Omnix CLI" in ui.transcript.text
                pipe.send_bytes(b"\x04")
                await asyncio.wait_for(task, 3)
            finally:
                if not task.done():
                    ui.app.exit()
                    await task

    asyncio.run(scenario())


def test_new_archives_conversation_and_resume_restores_it(tmp_path: Path) -> None:
    state = StateManager(tmp_path)
    state.init_project(project_name="Atlas")
    state.ensure_project_id()
    model_settings_before = state.models_path.read_bytes()
    project_identity_before = state.omnix_project_path.read_bytes()
    memory = state.load_memory()
    memory.goals.append(ProjectGoal(id="goal-1", title="Keep project context"))
    memory.conversations = [
        ConversationEntry(role=ConversationRole.USER, content="Design authentication"),
        ConversationEntry(role=ConversationRole.ASSISTANT, content="Use a session boundary."),
    ]
    state.save_memory(memory)

    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        asyncio.run(ui.submit("/new"))
        assert "previous conversation is saved" in ui.hint
        assert ui.welcome and not ui.entries
    assert state.load_memory().conversations == []
    assert state.load_memory().goals[0].title == "Keep project context"
    assert state.models_path.read_bytes() == model_settings_before
    assert state.omnix_project_path.read_bytes() == project_identity_before

    next_memory = state.load_memory()
    next_memory.conversations = [
        ConversationEntry(role=ConversationRole.USER, content="A later chat"),
    ]
    state.save_memory(next_memory)
    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        asyncio.run(ui.submit("/resume"))
        assert ui.hint == "Resumed conversation: Design authentication"
        assert [entry.text for entry in ui.entries] == [
            "Design authentication",
            "Use a session boundary.",
        ]
    assert state.load_memory().goals[0].title == "Keep project context"


def test_resume_migrates_existing_unsegmented_conversation_history(
    tmp_path: Path,
) -> None:
    state = StateManager(tmp_path)
    state.init_project(project_name="Atlas")
    memory = state.load_memory()
    memory.conversations = [
        ConversationEntry(role=ConversationRole.USER, content="Current chat"),
    ]
    state.save_memory(memory)
    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        asyncio.run(ui.submit("/resume"))
        assert not ui.welcome
        assert "You\nCurrent chat" in ui.transcript.text
        assert ui.hint == "Resumed conversation: Current chat"


def test_empty_composer_arrows_scroll_transcript_instead_of_recalling_history(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with create_pipe_input() as pipe:
            ui = TerminalApp(group(), tmp_path, input=pipe, output=SizedOutput())
            ui.entries = [Entry("Output", "\n".join(f"line {i}" for i in range(30)))]
            ui.welcome = False
            ui._refresh_transcript()
            initial_cursor = ui.transcript.buffer.cursor_position
            task = asyncio.create_task(ui.app.run_async())
            try:
                pipe.send_bytes(b"\x1b[A")
                await eventually(lambda: ui.app.layout.has_focus(ui.transcript))
                assert ui.transcript.buffer.cursor_position < initial_cursor
                assert ui.composer.text == ""
                assert not ui.palette_open
                ui.app.exit()
                await asyncio.wait_for(task, 3)
            finally:
                if not task.done():
                    ui.app.exit()
                    await task

    asyncio.run(scenario())


def test_shift_return_inserts_a_newline_in_the_composer(tmp_path: Path) -> None:
    async def scenario() -> None:
        with create_pipe_input() as pipe:
            ui = TerminalApp(group(), tmp_path, input=pipe, output=SizedOutput())
            task = asyncio.create_task(ui.app.run_async())
            try:
                pipe.send_bytes(b"\x1b[13;2u")
                await eventually(lambda: ui.composer.text == "\n")
                assert not ui.busy
                ui.app.exit()
                await asyncio.wait_for(task, 3)
            finally:
                if not task.done():
                    ui.app.exit()
                    await task

    asyncio.run(scenario())


@pytest.mark.parametrize("width,rows", [(120, 36), (80, 24), (60, 20), (40, 16)])
def test_compact_context_focus_theme_and_diff_toggle(tmp_path: Path, width: int, rows: int) -> None:
    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=SizedOutput(width, rows))
        asyncio.run(ui.submit("/context"))
        focus_target = ui.context_window if width >= 110 else ui.context
        assert ui.context_open and ui.app.layout.has_focus(focus_target)
        asyncio.run(ui.submit("/theme light"))
        assert ui.theme == "light"
        patch = Patch("test", "old", "new")
        ui.entries.append(Entry("Artifact output", patches=[patch]))
        ui.last_patches = [patch]
        asyncio.run(ui.submit("/changes"))
        assert not patch.expanded and ui.app.layout.has_focus(ui.transcript)
        assert "collapsed" in ui.transcript.text


def test_existing_conversation_skips_the_welcome_mark(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(app, ["init", "-w", str(tmp_path)])
    runner.invoke(app, ["chat", "-w", str(tmp_path), "Hello"])
    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        assert not ui.welcome
        assert "You\nHello" in ui.transcript.text
        assert "Master" in ui.transcript.text


def test_plain_mode_uses_real_handlers_without_ansi_or_logo(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["tui", "--plain", "-w", str(tmp_path)],
        input='/init --project-name "Atlas"\nHello\n/memory\n/changes\n/theme slate\n/exit\n',
    )
    assert result.exit_code == 0, result.output
    assert "Initialized Omnix CLI" in result.output
    assert "Master Agent recorded" in result.output
    assert "No saved artifact changes" in result.output
    assert "terminal defaults" in result.output
    assert "Phase 2" not in result.output
    assert "\x1b" not in result.output and "█" not in result.output
    assert StateManager(tmp_path).load_memory().project_name == "Atlas"


def test_no_arguments_in_a_pipe_shows_help_without_starting_tui() -> None:
    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    assert "Commands" in result.output and "tui" in result.output


def test_command_completion_renders_real_saved_artifact_diff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StateManager(tmp_path)
    state.init_project()
    artifact = Artifact(
        id="greeting",
        task_id="task",
        agent="frontend",
        title="Greeting",
        artifact_type=ArtifactType.FRONTEND_COMPONENT,
        content="old\n",
    )
    state.save_artifact(artifact)
    source = tmp_path / "source.ts"
    source.write_text("untouched\n")

    async def run(args: list[str], workspace: Path, output: Callable[[str], None]) -> int:
        state.save_artifact(artifact.model_copy(update={"content": "new\nextra\n", "version": 2}))
        output("Generated artifact saved.\n")
        return 0

    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        monkeypatch.setattr(ui.runner, "run", run)
        asyncio.run(ui.submit("/execute task"))
        assert len(ui.last_patches) == 1
        assert "Saved artifact .project/artifacts/greeting.json (+2 -1)" in ui.transcript.text
        assert "application source was not applied" in ui.transcript.text
        assert source.read_text() == "untouched\n"
        assert not ui.busy


def test_invalid_commands_and_corrupt_state_are_recoverable_without_reset(tmp_path: Path) -> None:
    state = StateManager(tmp_path)
    state.init_project()
    state.memory_path.write_text("invalid JSON")
    with create_pipe_input() as pipe:
        ui = TerminalApp(group(), tmp_path, input=pipe, output=DummyOutput())
        assert not ui.welcome and "Failed to load project state" in ui.transcript.text
        asyncio.run(ui.submit("/not-a-command"))
        assert "unknown command" in ui.transcript.text
        asyncio.run(ui.submit('/init "unterminated'))
        assert "Failed to parse command" in ui.transcript.text
        assert state.memory_path.read_text() == "invalid JSON"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal escalation test")
def test_interrupt_escalates_when_child_ignores_sigint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from omnix_cli.tui import runner as module

    monkeypatch.setattr(
        module,
        "invocation",
        lambda args, workspace: [
            sys.executable,
            "-u",
            "-c",
            "import signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); "
            "print('started',flush=True); time.sleep(60)",
        ],
    )

    async def scenario() -> None:
        runner = CommandRunner()
        output: list[str] = []
        task = asyncio.create_task(runner.run([], tmp_path, output.append))
        await eventually(lambda: "started" in "".join(output))
        runner.interrupt()
        assert await asyncio.wait_for(task, 6) == -signal.SIGTERM
        assert runner.process is None

    asyncio.run(scenario())
