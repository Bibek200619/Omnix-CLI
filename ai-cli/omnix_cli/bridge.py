"""Versioned JSON Lines bridge for native terminal frontends."""

from __future__ import annotations

import asyncio
import codecs
import difflib
import json
import os
import shlex
import signal
import sys
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from typer.main import get_command

from omnix_cli.cli.main import app
from omnix_cli.core.exceptions import OmnixError
from omnix_cli.core.state_manager import StateManager
from omnix_cli.integrations.omnix_auth import CredentialStore, OmnixAuthError
from omnix_cli.schemas.memory import ConversationEntry
from omnix_cli.tui.catalog import Command, command_path, commands_for
from omnix_cli.tui.presentation import artifact_snapshot, project_context
from omnix_cli.tui.runner import command_environment, invocation, needs_terminal

PROTOCOL_VERSION = 1
MAX_OUTPUT_CHARS = 524_288
MAX_DIFF_ROWS = 400


def _catalog() -> list[Command]:
    command = get_command(app)
    return commands_for(command)


class Bridge:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.commands = _catalog()
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def emit(self, event: dict[str, Any]) -> None:
        print(json.dumps({"version": PROTOCOL_VERSION, **event}, ensure_ascii=False), flush=True)

    def start(self) -> None:
        project, model, context = project_context(self.workspace)
        conversation: list[dict[str, str]] = []
        state = StateManager(self.workspace)
        account_status = self._account_status(state)
        if state.project_dir.exists():
            try:
                memory = state.load_memory()
                self._active_session_id(state, memory.conversations)
                conversation = [
                    {
                        "role": "user" if item.role == "user" else "master",
                        "text": item.content,
                    }
                    for item in memory.conversations[-40:]
                ]
            except (OmnixError, OSError, ValueError):
                conversation = []
        self.emit(
            {
                "event": "ready",
                "workspace": str(self.workspace),
                "project": project,
                "model": model,
                "account_status": account_status,
                "context": context,
                "conversation": conversation,
                "commands": [
                    {"name": command.name, "description": command.description}
                    for command in self.commands
                    if not command.local
                ],
            }
        )

    @staticmethod
    def _account_status(state: StateManager) -> str:
        """Read local credential presence without making an account request."""
        if not state.omnix_project_path.exists():
            return "disconnected"
        try:
            project = json.loads(state.omnix_project_path.read_text(encoding="utf-8"))
            project_id = project.get("project_id")
            if not isinstance(project_id, str):
                return "unknown"
            return "connected" if CredentialStore().read(project_id) else "disconnected"
        except (OSError, ValueError, AttributeError, OmnixAuthError):
            return "unknown"

    async def serve(self) -> None:
        self.start()
        while line := await asyncio.to_thread(sys.stdin.readline):
            try:
                request = json.loads(line)
                if request.get("version") != PROTOCOL_VERSION:
                    self.emit({"event": "error", "message": "Unsupported protocol version."})
                elif request.get("type") == "run":
                    self._run(request)
                elif request.get("type") == "cancel":
                    self._cancel(str(request.get("id", "")))
                elif request.get("type") in {"session_new", "session_resume"}:
                    self._handle_session(request)
                elif request.get("type") == "shutdown":
                    break
                else:
                    self.emit({"event": "error", "message": "Unknown bridge request."})
            except (json.JSONDecodeError, AttributeError, TypeError) as exc:
                self.emit({"event": "error", "message": f"Invalid bridge request: {exc}"})
        await self._stop_all()

    def _run(self, request: dict[str, Any]) -> None:
        request_id = str(request.get("id", ""))
        if not request_id or request_id in self.tasks:
            self.emit({"event": "error", "id": request_id, "message": "Invalid request id."})
            return
        if self.tasks:
            self.emit(
                {"event": "error", "id": request_id, "message": "Another command is running."}
            )
            return
        text = request.get("input")
        if not isinstance(text, str) or not text.strip():
            self.emit({"event": "error", "id": request_id, "message": "Input is empty."})
            return
        self.tasks[request_id] = asyncio.create_task(self._execute(request_id, text.strip()))

    def _command_args(self, text: str) -> list[str]:
        if text.startswith("//"):
            return ["chat", "--", text[1:]]
        if not text.startswith("/"):
            return ["chat", text]
        command_text = text[1:].strip()
        command = command_path(self.commands, command_text)
        if command is None:
            raise ValueError("Unknown command. Type / to see registered commands.")
        remainder = command_text[len(command.name) :].strip()
        args = shlex.split(remainder)
        return [*command.name.split(), *args]

    def _handle_session(self, request: dict[str, Any]) -> None:
        request_id = str(request.get("id", ""))
        action = request.get("type")
        try:
            state = StateManager(self.workspace)
            memory = state.load_memory()
            session_dir = state.project_dir / "tui_sessions"
            active_path = session_dir / "active.json"
            active_id = self._active_session_id(state, memory.conversations)

            if memory.conversations:
                self._save_session(session_dir, active_id, memory.conversations)

            if action == "session_new":
                memory.conversations = []
                state.save_memory(memory)
                next_id = str(uuid4())
                self._write_json(active_path, {"id": next_id})
                self.emit(
                    {
                        "event": "session",
                        "id": request_id,
                        "action": "new",
                        "message": "New conversation started. The previous conversation is saved.",
                        "conversation": [],
                    }
                )
                return

            sessions = []
            if session_dir.exists():
                for path in session_dir.glob("*.json"):
                    if path == active_path:
                        continue
                    try:
                        session = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        continue
                    if session.get("id") != active_id and isinstance(
                        session.get("conversations"), list
                    ):
                        sessions.append(session)
            sessions.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
            if not sessions:
                self.emit(
                    {
                        "event": "error",
                        "id": request_id,
                        "message": "No previous conversation is available to resume.",
                    }
                )
                return

            session = sessions[0]
            restored = [
                ConversationEntry.model_validate(entry)
                for entry in session["conversations"]
            ]
            memory.conversations = restored
            state.save_memory(memory)
            self._write_json(active_path, {"id": session["id"]})
            self.emit(
                {
                    "event": "session",
                    "id": request_id,
                    "action": "resume",
                    "message": (
                        "Resumed conversation: "
                        f"{session.get('title') or 'Untitled conversation'}"
                    ),
                    "conversation": [
                        {
                            "role": "user" if entry.role.value == "user" else "master",
                            "text": entry.content,
                        }
                        for entry in restored[-40:]
                    ],
                }
            )
        except (OSError, ValueError, TypeError, OmnixError) as exc:
            self.emit(
                {
                    "event": "error",
                    "id": request_id,
                    "message": f"Could not update conversation history: {exc}",
                }
            )

    def _active_session_id(
        self, state: StateManager, conversations: list[ConversationEntry]
    ) -> str:
        """Migrate pre-session conversation memory without discarding it."""
        session_dir = state.project_dir / "tui_sessions"
        active_path = session_dir / "active.json"
        try:
            active_id = json.loads(active_path.read_text(encoding="utf-8")).get("id")
        except (OSError, ValueError, AttributeError):
            active_id = None

        archives = [path for path in session_dir.glob("*.json") if path != active_path]
        if conversations and not archives:
            self._save_session(session_dir, f"legacy-{uuid4()}", conversations)
        if not isinstance(active_id, str):
            active_id = str(uuid4())
            self._write_json(active_path, {"id": active_id})
        return active_id

    @staticmethod
    def _save_session(
        session_dir: Path, session_id: str, conversations: list[ConversationEntry]
    ) -> None:
        first_user = next(
            (entry.content for entry in conversations if entry.role.value == "user"),
            "",
        )
        title = first_user.splitlines()[0][:72] if first_user else "Untitled conversation"
        Bridge._write_json(
            session_dir / f"{session_id}.json",
            {
                "id": session_id,
                "title": title,
                "updated_at": datetime.now(UTC).isoformat(),
                "conversations": [entry.model_dump(mode="json") for entry in conversations],
            },
        )

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    async def _execute(self, request_id: str, text: str) -> None:
        emitted = 0
        output_limited = False
        try:
            args = self._command_args(text)
            argv = invocation(args, self.workspace)
            if needs_terminal(args):
                self.emit({"event": "handoff", "id": request_id, "argv": argv})
                return
            before = artifact_snapshot(self.workspace)
            self.emit({"event": "started", "id": request_id, "command": " ".join(args[:2])})
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=self.workspace,
                env={**command_environment(), "TERM": "dumb", "PYTHONUNBUFFERED": "1"},
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=os.name != "nt",
            )
            self.processes[request_id] = process
            assert process.stdout is not None
            decoder = codecs.getincrementaldecoder("utf-8")("replace")
            while chunk := await process.stdout.read(4096):
                decoded = decoder.decode(chunk)
                remaining = MAX_OUTPUT_CHARS - emitted
                if remaining > 0:
                    content = decoded[:remaining]
                    if content:
                        self.emit({"event": "output", "id": request_id, "text": content})
                        emitted += len(content)
                if emitted >= MAX_OUTPUT_CHARS and not output_limited:
                    self.emit(
                        {
                            "event": "output",
                            "id": request_id,
                            "text": (
                                "\n[Output display limited; inspect saved project reports "
                                "for more.]\n"
                            ),
                        }
                    )
                    output_limited = True
            tail = decoder.decode(b"", final=True)
            if tail and emitted < MAX_OUTPUT_CHARS:
                self.emit({"event": "output", "id": request_id, "text": tail})
            if process.returncode is None:
                await process.wait()
            after = artifact_snapshot(self.workspace)
            for path in sorted(before.keys() | after.keys()):
                old = before.get(path, "")
                new = after.get(path, "")
                if old != new:
                    patch_lines, added, removed = _diff_rows(old, new)
                    rows_truncated = len(patch_lines) > MAX_DIFF_ROWS
                    self.emit(
                        {
                            "event": "patch",
                            "id": request_id,
                            "path": path,
                            "status": "saved",
                            "added": added,
                            "removed": removed,
                            "lines": patch_lines[:MAX_DIFF_ROWS],
                            "rows_truncated": rows_truncated,
                            "text": "\n".join(
                                difflib.unified_diff(
                                    old.splitlines(), new.splitlines(), lineterm=""
                                )
                            ),
                        }
                    )
            project, model, context = project_context(self.workspace)
            self.emit(
                {
                    "event": "context",
                    "id": request_id,
                    "project": project,
                    "model": model,
                    "context": context,
                }
            )
            self.emit(
                {"event": "complete", "id": request_id, "exit_code": process.returncode or 0}
            )
        except (OSError, ValueError) as exc:
            self.emit({"event": "error", "id": request_id, "message": str(exc)})
        finally:
            self.processes.pop(request_id, None)
            self.tasks.pop(request_id, None)

    def _cancel(self, request_id: str) -> None:
        process = self.processes.get(request_id)
        if process is None or process.returncode is not None:
            self.emit({"event": "error", "id": request_id, "message": "No active command."})
            return
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        asyncio.create_task(self._stop_after_grace(process))
        self.emit({"event": "cancelled", "id": request_id})

    async def _stop_all(self) -> None:
        await asyncio.gather(
            *(self._stop_after_grace(process) for process in self.processes.values()),
            return_exceptions=True,
        )
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)

    async def _stop_after_grace(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        try:
            await asyncio.wait_for(process.wait(), 3)
            return
        except TimeoutError:
            pass
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            await asyncio.wait_for(process.wait(), 2)
            return
        except (ProcessLookupError, TimeoutError):
            pass
        if os.name == "nt":
            process.kill()
        else:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        await process.wait()


def _diff_rows(before: str, after: str) -> tuple[list[dict[str, Any]], int, int]:
    """Turn a unified diff into line-numbered rows without reading source files."""
    unified = difflib.unified_diff(before.splitlines(), after.splitlines(), n=3)
    rows: list[dict[str, Any]] = []
    old_line = new_line = 0
    added = removed = 0
    for line in unified:
        if line.startswith("@@"):
            import re

            match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                old_line, new_line = map(int, match.groups())
                rows.append({"kind": "hunk", "text": line})
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+"):
            rows.append({"kind": "added", "new_line": new_line, "text": line[1:]})
            added += 1
            new_line += 1
        elif line.startswith("-"):
            rows.append({"kind": "removed", "old_line": old_line, "text": line[1:]})
            removed += 1
            old_line += 1
        elif line.startswith(" "):
            rows.append(
                {
                    "kind": "context",
                    "old_line": old_line,
                    "new_line": new_line,
                    "text": line[1:],
                }
            )
            old_line += 1
            new_line += 1
    return rows, added, removed


async def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Omnix local frontend bridge")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args()
    await Bridge(args.workspace).serve()


if __name__ == "__main__":
    asyncio.run(_main())
