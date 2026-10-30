"""Stream existing CLI commands without global stdout redirection or shell execution."""

from __future__ import annotations

import asyncio
import codecs
import os
import signal
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


def invocation(args: list[str], workspace: Path) -> list[str]:
    marker = args.index("--") if "--" in args else len(args)
    options = args[:marker]
    if not any(x == "--workspace" or x.startswith(("-w", "--workspace=")) for x in options):
        args = [*args[:marker], "--workspace", str(workspace), *args[marker:]]
    return [sys.executable, "-m", "omnix_cli.cli.main", *args]


def command_environment() -> dict[str, str]:
    env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb", "PYTHONUNBUFFERED": "1"}
    root = str(Path(__file__).resolve().parents[2])
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [root, env.get("PYTHONPATH", "")]))
    return env


def needs_terminal(args: list[str]) -> bool:
    """Keep native workspace selection and explicit remote approval fully interactive."""
    if "--help" in args:
        return False
    return (args[:1] == ["link"] and not any(x.startswith("--workspace-id") for x in args)) or args[
        :2
    ] == ["sessions", "work"]


class CommandRunner:
    def __init__(self) -> None:
        self.process: asyncio.subprocess.Process | None = None
        self.stop_task: asyncio.Task[None] | None = None

    async def run(self, args: list[str], workspace: Path, on_output: Callable[[str], None]) -> int:
        self.process = await asyncio.create_subprocess_exec(
            *invocation(args, workspace),
            cwd=workspace,
            env=command_environment(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )
        process = self.process
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        size = 0
        limited = False
        try:
            assert process.stdout is not None
            while chunk := await process.stdout.read(4096):
                text = decoder.decode(chunk)
                if size < 524_288:
                    on_output(text[: 524_288 - size])
                elif not limited:
                    on_output(
                        "\n[Output display limited; inspect stored project reports for more.]\n"
                    )
                    limited = True
                size += len(text)
            tail = decoder.decode(b"", final=True)
            if tail and size < 524_288:
                on_output(tail)
            return await process.wait()
        finally:
            if process.returncode is None:
                self.interrupt()
                try:
                    await asyncio.wait_for(process.wait(), 3)
                except TimeoutError:
                    self._signal(signal.SIGTERM)
                    try:
                        await asyncio.wait_for(process.wait(), 2)
                    except TimeoutError:
                        self._signal(signal.SIGKILL)
                        await process.wait()
            if self.stop_task is not None:
                self.stop_task.cancel()
                self.stop_task = None
            self.process = None

    def interrupt(self) -> None:
        self._signal(signal.SIGINT)
        if self.process is not None and self.stop_task is None:
            self.stop_task = asyncio.create_task(self._stop_after_grace(self.process))

    async def _stop_after_grace(self, process: asyncio.subprocess.Process) -> None:
        try:
            await asyncio.wait_for(process.wait(), 3)
        except TimeoutError:
            self._signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), 2)
            except TimeoutError:
                self._signal(signal.SIGKILL)

    def _signal(self, sig: signal.Signals) -> None:
        process = self.process
        if process is None or process.returncode is not None:
            return
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass


def run_terminal_command(args: list[str], workspace: Path) -> int:
    return subprocess.call(invocation(args, workspace), cwd=workspace, env=command_environment())
