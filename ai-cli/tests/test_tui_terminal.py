"""Render the actual installed command in a POSIX pseudo-terminal, not a fake UI."""

from __future__ import annotations

import codecs
import os
import select
import struct
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pyte
import pytest

from omnix_cli.core.state_manager import StateManager
from omnix_cli.tui.runner import command_environment

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX PTY integration coverage")


class Terminal:
    def __init__(self, workspace: Path, columns: int, rows: int, theme: str = "slate") -> None:
        import fcntl
        import pty
        import termios

        self.master, self.slave = pty.openpty()
        self.original_mode = termios.tcgetattr(self.slave)
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
        self.screen = pyte.Screen(columns, rows)
        self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        env = {**command_environment(), "TERM": "xterm-256color", "PROMPT_TOOLKIT_NO_CPR": "1"}
        env.pop("NO_COLOR", None)
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "omnix_cli.cli.main",
                "--workspace",
                str(workspace),
                "--theme",
                theme,
            ],
            stdin=self.slave,
            stdout=self.slave,
            stderr=self.slave,
            cwd=workspace,
            env=env,
            start_new_session=True,
        )

    @property
    def text(self) -> str:
        return "\n".join(self.screen.display)

    def send(self, value: bytes) -> None:
        os.write(self.master, value)

    def wait(self, predicate: Callable[[], bool], timeout: float = 8) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if select.select([self.master], [], [], 0.05)[0]:
                data = os.read(self.master, 65536)
                self.stream.feed(self.decoder.decode(data))
            if predicate():
                self.drain()
                return
            if self.process.poll() is not None:
                break
        raise AssertionError(f"Terminal condition not reached:\n{self.text}")

    def drain(self) -> None:
        # A real terminal consumes the complete frame continuously, including SGR.
        # Do not resize our emulator halfway through an unread escape sequence.
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline and select.select([self.master], [], [], 0.06)[0]:
            self.stream.feed(self.decoder.decode(os.read(self.master, 65536)))

    def resize(self, columns: int, rows: int) -> None:
        import fcntl
        import signal
        import termios

        self.drain()
        self.screen.resize(rows, columns)
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
        self.process.send_signal(signal.SIGWINCH)

    def wait_for_exit(self) -> int:
        # Keep consuming the final redraw/terminal restoration; PTY buffers are small.
        self.wait(lambda: self.process.poll() is not None, timeout=5)
        return self.process.wait(1)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(3)
        os.close(self.master)
        os.close(self.slave)


@contextmanager
def terminal(workspace: Path, columns: int, rows: int, theme: str = "slate") -> Iterator[Terminal]:
    ui = Terminal(workspace, columns, rows, theme)
    try:
        yield ui
    finally:
        ui.close()


@pytest.mark.parametrize("columns,rows", [(120, 36), (80, 24), (60, 20), (40, 16)])
def test_real_terminal_welcome_catalog_resize_and_clean_exit(
    tmp_path: Path,
    columns: int,
    rows: int,
) -> None:
    import termios

    with terminal(tmp_path, columns, rows) as ui:
        ui.wait(lambda: "source preview" in ui.text)
        assert "Window too small" not in ui.text
        assert "One conversation. Your project." in ui.text
        assert "Type a goal or / to begin." in ui.text
        assert "Describe what you want to work on" in ui.text
        assert "Master / Unconfigured / Local" in ui.text
        assert ui.screen.display[0].startswith("  Omnix CLI")
        assert ui.screen.buffer[0][0].bg == "182333"
        assert any(
            cell.bg == "223246"
            for row in ui.screen.buffer.values()
            for cell in row.values()
        )
        if rows >= 24:
            ui.wait(lambda: "█" in ui.text)
        ui.send(b"/")
        ui.wait(lambda: "Commands 1-" in ui.text)
        assert any(
            cell.bg == "304c75"
            for row in ui.screen.buffer.values()
            for cell in row.values()
        )
        if columns - 4 >= 60:
            assert "Catalog / 33 source-backed actions" in ui.text
        else:
            assert "Catalog / 33 actions" in ui.text
        assert "█" not in ui.text
        ui.send(b"\x1b[B" * 32)
        ui.wait(lambda: "/sessions history" in ui.text)
        assert "/exit" not in ui.text
        ui.send(b"\x1b")
        ui.wait(lambda: "Commands 1-" not in ui.text and "/exit" not in ui.text)
        ui.send(b"/exit")
        ui.wait(lambda: "/exit" in ui.text)
        ui.send(b"\x1b")
        ui.wait(lambda: "Commands 1-" not in ui.text)
        ui.resize(60, 20)
        ui.wait(lambda: len(ui.screen.display) == 20 and "source preview" in ui.text)
        ui.send(b"\x03")
        ui.wait(lambda: "again to exit" in ui.text)
        ui.send(b"\x03")
        assert ui.wait_for_exit() == 0
        restored = termios.tcgetattr(ui.slave)
        # Darwin's volatile PENDIN bit can change when canonical input resumes.
        restored[3] &= ~getattr(termios, "PENDIN", 0)
        ui.original_mode[3] &= ~getattr(termios, "PENDIN", 0)
        assert restored == ui.original_mode


def test_real_terminal_runs_commands_and_recovers_from_error(tmp_path: Path) -> None:
    with terminal(tmp_path, 120, 36) as ui:
        ui.wait(lambda: "█" in ui.text)
        ui.send(b'/init --project-name "Atlas"\r')
        ui.wait(
            lambda: "Initialized Omnix CLI" in ui.text
            and "Master / Local / Atlas / Local" in ui.text
        )
        assert StateManager(tmp_path).load_blueprint().project_name == "Atlas"
        ui.send(b"/artifact missing\r")
        ui.wait(
            lambda: "not found" in ui.text and "Master / Local / Atlas / Local" in ui.text
        )
        ui.send(b"Remember this project decision: use SQLite.\r")
        ui.wait(
            lambda: "Master Agent recorded" in ui.text
            and "Master / Local / Atlas / Local" in ui.text
        )
        memory = StateManager(tmp_path).load_memory()
        assert memory.conversations[-2].content == "Remember this project decision: use SQLite."
        assert "█" not in ui.text
        ui.send(b"\x04")
        assert ui.wait_for_exit() == 0


@pytest.mark.parametrize("theme", ["light", "terminal", "mono"])
def test_real_terminal_themes_render_without_traceback(tmp_path: Path, theme: str) -> None:
    with terminal(tmp_path, 80, 24, theme) as ui:
        ui.wait(lambda: "█" in ui.text)
        assert "Traceback" not in ui.text
        if theme == "light":
            assert ui.screen.buffer[0][0].bg == "eef2f7"
        ui.send(b"\x04")
        assert ui.wait_for_exit() == 0
