"""Opt-in worker for the explicit Omnix build v1 capability."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

import typer

from omnix_cli.agents.planner import PlannerAgent
from omnix_cli.agents.qa.agent import QAAgent
from omnix_cli.agents.repair.agent import RepairAgent
from omnix_cli.agents.repair.context_builder import RepairContextBuilder
from omnix_cli.core.state_manager import StateManager
from omnix_cli.integrations.omnix_auth import OmnixApi, OmnixAuthError
from omnix_cli.memory.memory_manager import MemoryManager
from omnix_cli.orchestrator import AutonomousOrchestrator
from omnix_cli.schemas.build import BuildConfig, BuildOutcome

SUPPORTED_CAPABILITIES = {("plan", 1), ("build", 1), ("qa", 1), ("repair", 1)}
REMOTE_HISTORY_FILE = "omnix_remote_sessions.json"


class _SelectedRepairContextBuilder:
    def __init__(self, state: StateManager, finding_ids: set[str]) -> None:
        self._base = RepairContextBuilder(state)
        self._finding_ids = finding_ids

    def build_context(self) -> dict[str, Any]:
        context = self._base.build_context()
        quality = context.get("quality_report", {})
        findings = quality.get("findings", [])
        available = {item.get("id") for item in findings if isinstance(item, dict)}
        if not self._finding_ids <= available:
            raise OmnixAuthError(
                "One or more repair findings are no longer available in the local QA report."
            )
        quality["findings"] = [
            item
            for item in findings
            if isinstance(item, dict) and item.get("id") in self._finding_ids
        ]
        context["quality_report"] = quality
        return context


def _require_local_run(state: StateManager, run_id: str) -> None:
    try:
        history = state.load_build_history()
    except Exception as exc:
        raise OmnixAuthError(
            "The referenced local build is not available in this project."
        ) from exc
    if not any(run.run_id == run_id for run in history.runs):
        raise OmnixAuthError("The referenced local build does not belong to this project.")


def _artifact_manifest(
    state: StateManager, before_digests: dict[str, str]
) -> tuple[list[dict[str, Any]], int]:
    """Return bounded metadata for artifacts created during this local session."""
    items: list[dict[str, Any]] = []

    def opaque_reference(value: str) -> str:
        if re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value) and ".." not in value:
            return value
        return f"opaque_{hashlib.sha256(value.encode('utf-8')).hexdigest()}"

    artifacts: list[tuple[str, str, str, str, str, list[str]]] = []
    for artifact in state.list_artifacts():
        artifacts.append(
            (
                f"build:{artifact.id}",
                artifact.id,
                str(artifact.artifact_type),
                artifact.title,
                artifact.content,
                [artifact.task_id],
            )
        )
    for artifact in state.list_repair_artifacts():
        artifacts.append(
            (
                f"repair:{artifact.id}",
                artifact.id,
                "repair_artifact",
                artifact.title,
                artifact.content,
                [artifact.repair_plan_id, artifact.qa_finding_id],
            )
        )
    changed_artifacts = []
    for artifact_key, _artifact_id, artifact_type, title, content_value, provenance in artifacts:
        content = content_value.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        if before_digests.get(artifact_key) == digest:
            continue
        changed_artifacts.append(
            (artifact_key, artifact_type, title, provenance, digest, len(content))
        )
    for artifact_key, artifact_type, title, provenance, digest, size_bytes in changed_artifacts:
        artifact_type = artifact_type[:64]
        if "/" in title or "\\" in title:
            display_name = "Generated artifact"
        else:
            display_name = re.sub(r"[^A-Za-z0-9 _()-]", "", title).strip()[:256]
        item = {
            "local_artifact_id": opaque_reference(artifact_key),
            "artifact_type": artifact_type,
            "display_name": display_name or "Generated artifact",
            "summary": f"Generated {artifact_type.replace('_', ' ')} artifact",
            "sha256": digest,
            "size_bytes": size_bytes,
            "provenance_refs": [opaque_reference(ref) for ref in provenance],
        }
        candidate = [*items, item]
        payload_size = len(str({"kind": "artifact.manifest", "items": candidate}).encode("utf-8"))
        if len(candidate) > 100 or payload_size > 12000:
            break
        items.append(item)
    return items, len(changed_artifacts) - len(items)


def _artifact_snapshot(state: StateManager) -> dict[str, str]:
    return {
        **{
            f"build:{item.id}": hashlib.sha256(item.content.encode("utf-8")).hexdigest()
            for item in state.list_artifacts()
        },
        **{
            f"repair:{item.id}": hashlib.sha256(item.content.encode("utf-8")).hexdigest()
            for item in state.list_repair_artifacts()
        },
    }


async def _run_capability(
    state: StateManager,
    capability: str,
    capability_input: dict[str, Any],
    progress_callback,
    local_run_id: str | None = None,
):
    if capability == "build":
        orchestrator = AutonomousOrchestrator(state, config=BuildConfig())

        def on_progress(message: str) -> None:
            if progress_callback(message):
                orchestrator.request_stop()

        orchestrator.progress_callback = on_progress
        report = await orchestrator.build(capability_input["goal"], run_id=local_run_id)
        blueprint = getattr(report, "blueprint_summary", None)
        blueprint_counts = ""
        if blueprint is not None:
            blueprint_counts = (
                "; blueprint: "
                f"{blueprint.feature_count} features, {blueprint.entity_count} entities, "
                f"{blueprint.module_count} "
                f"{'module' if blueprint.module_count == 1 else 'modules'}, "
                f"{blueprint.page_count} pages, "
                f"{blueprint.api_count} APIs, "
                f"{blueprint.architecture_note_count} architecture notes"
            )
        quality = getattr(report, "final_quality_score", None)
        quality_summary = f"; quality score {quality}" if quality is not None else ""
        task_count = getattr(report, "task_count", 0)
        artifact_count = getattr(report, "artifacts_generated", 0)
        summary = (
            f"Build {report.outcome.value}; {task_count} "
            f"{'task' if task_count == 1 else 'tasks'}, {artifact_count} "
            f"{'artifact' if artifact_count == 1 else 'artifacts'}"
            f"{quality_summary}{blueprint_counts}"
        )
        return summary[:4096], report.outcome == BuildOutcome.SUCCESS
    if capability == "plan":
        MemoryManager(state).add_goal(capability_input["goal"])
        result = await PlannerAgent(state).run()
        return (
            f"Planner generated {result.new_task_count} new tasks and updated "
            f"{result.updated_task_count} existing tasks.",
            True,
        )
    _require_local_run(state, capability_input["local_run_id"])
    if capability == "qa":
        result = await QAAgent(state).evaluate()
        summary = result.summary
        return (
            f"QA completed with quality score {summary.quality_score} and "
            f"{summary.critical_issues} critical findings.",
            summary.status.value not in {"FAILED", "REVIEW_REQUIRED"},
        )
    finding_ids = set(capability_input["finding_ids"])
    result = await RepairAgent(
        state,
        context_builder=_SelectedRepairContextBuilder(state, finding_ids),
    ).repair()
    return (
        f"Repair processed {result.repair_report.issues_processed} requested findings "
        f"and generated {result.repair_report.artifacts_generated} artifacts.",
        True,
    )


def _history_path(state: StateManager) -> Path:
    return state.project_dir / REMOTE_HISTORY_FILE


def _read_history(state: StateManager) -> dict[str, Any]:
    path = _history_path(state)
    if not path.exists():
        return {"sessions": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OmnixAuthError(
            "Local remote-session history is unreadable; it was left unchanged."
        ) from exc
    if not isinstance(value, dict) or not isinstance(value.get("sessions"), dict):
        raise OmnixAuthError("Local remote-session history has an unsupported format.")
    return value


def _write_history(state: StateManager, history: dict[str, Any]) -> None:
    path = _history_path(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(prefix=".omnix-remote-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(history, stream, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except Exception:
        with suppress(OSError):
            os.unlink(temp_path)
        raise


def _emit(
    api: OmnixApi, state: StateManager, session_id: str, event_type: str, payload: dict[str, Any]
) -> None:
    history = _read_history(state)
    record = history["sessions"].setdefault(session_id, {"sequence": 0, "terminal": False})
    if record.get("terminal"):
        return
    pending = record.get("pending_event")
    if pending is not None and (
        pending.get("event_type") != event_type or pending.get("payload") != payload
    ):
        _submit_pending_event(api, state, session_id, history, record, pending)
        if record["terminal"]:
            return
        return _emit(api, state, session_id, event_type, payload)
    if pending is None:
        pending = {
            "protocol_version": 1,
            "session_id": session_id,
            "sequence": int(record["sequence"]) + 1,
            "event_idempotency_key": str(uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.now(UTC).isoformat(),
            "payload": payload,
        }
        record["pending_event"] = pending
        _write_history(state, history)
    _submit_pending_event(api, state, session_id, history, record, pending)


def _submit_pending_event(
    api: OmnixApi,
    state: StateManager,
    session_id: str,
    history: dict[str, Any],
    record: dict[str, Any],
    pending: dict[str, Any],
) -> None:
    try:
        api.request("POST", f"/sessions/{session_id}/events", pending)
    except OmnixAuthError as exc:
        message = str(exc)
        record["sync_state"] = (
            "conflicted" if "HTTP 409" in message or "HTTP 422" in message else "partial"
        )
        record["sync_error"] = message[:256]
        _write_history(state, history)
        if record["sync_state"] == "conflicted":
            raise OmnixAuthError(
                "Remote sync conflict (HTTP 409/422). The pending event and local result "
                "were preserved. Resolve the session conflict, then rerun `omnix sessions work` "
                "to retry the same idempotent event."
            ) from exc
        raise OmnixAuthError(
            "Remote sync is partial. The pending event and local result were preserved; "
            "check the connection or device authorization, then rerun `omnix sessions work`."
        ) from exc
    record["sequence"] = pending["sequence"]
    record["terminal"] = pending["event_type"] in {
        "run.succeeded",
        "run.failed",
        "run.cancelled",
    }
    record.pop("pending_event", None)
    record.pop("sync_state", None)
    record.pop("sync_error", None)
    _write_history(state, history)


def _store_local_result(
    state: StateManager,
    session_id: str,
    events: list[dict[str, Any]],
) -> None:
    history = _read_history(state)
    record = history["sessions"].setdefault(session_id, {"sequence": 0, "terminal": False})
    record["local_result"] = {"events": events}
    _write_history(state, history)


def _sync_local_result(api: OmnixApi, state: StateManager, session_id: str) -> None:
    history = _read_history(state)
    result = history["sessions"].get(session_id, {}).get("local_result")
    if not isinstance(result, dict):
        return
    while result.get("events"):
        next_event = result["events"][0]
        _emit(
            api,
            state,
            session_id,
            next_event["event_type"],
            next_event["payload"],
        )
        history = _read_history(state)
        result = history["sessions"][session_id]["local_result"]
        result["events"].pop(0)
        _write_history(state, history)
    record = history["sessions"][session_id]
    record["terminal"] = True
    record.pop("local_result", None)
    _write_history(state, history)


def _validate_request(request: Any, link: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    if not isinstance(request, dict) or request.get("protocol_version") != 1:
        raise OmnixAuthError("Omnix sent an unsupported session protocol version.")
    if set(request) != {
        "protocol_version",
        "session_id",
        "linked_project_id",
        "capability",
        "capability_version",
        "idempotency_key",
        "expires_at",
        "input",
    }:
        raise OmnixAuthError("Omnix sent unsupported session fields.")
    if (request.get("capability"), request.get("capability_version")) not in SUPPORTED_CAPABILITIES:
        raise OmnixAuthError("Omnix sent a capability this CLI does not support.")
    if request.get("linked_project_id") != link.get("linked_project_id"):
        raise OmnixAuthError("The session targets a different linked project; it was not run.")
    expires = request.get("expires_at")
    try:
        expiry = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
    except ValueError as exc:
        raise OmnixAuthError("Omnix sent an invalid session expiry; it was not run.") from exc
    if expiry.tzinfo is None or expiry <= datetime.now(UTC):
        raise OmnixAuthError("The Omnix session expired; it was not run.")
    session_id = request.get("session_id")
    request_input = request.get("input")
    if (
        not isinstance(session_id, str)
        or len(session_id) > 64
        or not isinstance(request_input, dict)
    ):
        raise OmnixAuthError("Omnix sent a malformed session request.")
    try:
        UUID(session_id)
        UUID(str(request.get("idempotency_key")))
    except ValueError as exc:
        raise OmnixAuthError("Omnix sent invalid session identifiers.") from exc
    capability = request["capability"]
    if request_input.get("kind") != capability:
        raise OmnixAuthError("Omnix sent mismatched capability input; it was not run.")
    if capability in {"plan", "build"}:
        allowed = {"kind", "goal"} | ({"task_ref"} if capability == "plan" else {"local_plan_id"})
        goal = request_input.get("goal")
        if set(request_input) - allowed or not isinstance(goal, str) or not 1 <= len(goal) <= 10000:
            raise OmnixAuthError(f"Omnix sent invalid {capability} input; it was not run.")
        if capability == "plan" and "task_ref" in request_input:
            raise OmnixAuthError(
                "This CLI cannot map a workspace task reference to a local task yet."
            )
        if capability == "build" and "local_plan_id" in request_input:
            raise OmnixAuthError("This CLI cannot map a local plan ID to a build input yet.")
    elif capability == "qa":
        if set(request_input) - {"kind", "local_run_id", "profile"}:
            raise OmnixAuthError("Omnix sent unsupported QA input fields.")
        if (
            not isinstance(request_input.get("local_run_id"), str)
            or not 1 <= len(request_input["local_run_id"]) <= 128
        ):
            raise OmnixAuthError("Omnix sent an invalid QA run reference.")
        if request_input.get("profile", "default") != "default":
            raise OmnixAuthError("This CLI supports only the default QA profile.")
    else:
        if set(request_input) != {"kind", "local_run_id", "finding_ids"}:
            raise OmnixAuthError("Omnix sent unsupported repair input fields.")
        if (
            not isinstance(request_input.get("local_run_id"), str)
            or not 1 <= len(request_input["local_run_id"]) <= 128
        ):
            raise OmnixAuthError("Omnix sent an invalid repair run reference.")
        finding_ids = request_input.get("finding_ids")
        if (
            not isinstance(finding_ids, list)
            or not 1 <= len(finding_ids) <= 100
            or len(set(finding_ids)) != len(finding_ids)
            or any(not isinstance(item, str) or not 1 <= len(item) <= 128 for item in finding_ids)
        ):
            raise OmnixAuthError("Omnix sent invalid repair finding IDs.")
    return session_id, capability, request_input


def work_once(state: StateManager, api: OmnixApi, *, confirm: bool = True) -> int:
    state.project_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state.project_dir / ".omnix_remote_sessions.lock"
    for _ in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            try:
                owner_pid = int(lock_path.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                owner_pid = -1
            if owner_pid <= 0:
                with suppress(OSError):
                    lock_path.unlink()
                continue
            try:
                os.kill(owner_pid, 0)
            except ProcessLookupError:
                with suppress(OSError):
                    lock_path.unlink()
                continue
            except PermissionError:
                raise OmnixAuthError(
                    "Another Omnix session worker is already active for this project."
                ) from None
            raise OmnixAuthError(
                "Another Omnix session worker is already active for this project."
            ) from None
        else:
            with os.fdopen(descriptor, "w", encoding="ascii") as stream:
                stream.write(str(os.getpid()))
                stream.flush()
                os.fsync(stream.fileno())
            break
    else:
        raise OmnixAuthError("Could not acquire the local Omnix session-worker lock.")
    try:
        return _work_once_locked(state, api, confirm=confirm)
    finally:
        with suppress(FileNotFoundError):
            lock_path.unlink()


def _work_once_locked(state: StateManager, api: OmnixApi, *, confirm: bool) -> int:
    link = api.request("GET", "/status")
    if not isinstance(link, dict) or not link.get("linked"):
        raise OmnixAuthError("Link this local project before polling for Omnix sessions.")
    capabilities = api.request("GET", "/capabilities")
    advertised = {
        (item.get("name"), item.get("version"))
        for item in capabilities.get("capabilities", [])
        if isinstance(item, dict)
    }
    if not advertised >= SUPPORTED_CAPABILITIES:
        raise OmnixAuthError(
            "The linked Omnix server does not advertise all supported v1 capabilities."
        )
    result = api.request("POST", "/sessions/poll", {})
    deliveries = result.get("deliveries", []) if isinstance(result, dict) else []
    if not deliveries:
        typer.echo("No queued Omnix sessions.")
        return 0
    for delivery in deliveries:
        request = delivery.get("request") if isinstance(delivery, dict) else None
        session_id, capability, capability_input = _validate_request(request, link)
        history = _read_history(state)
        existing = history["sessions"].get(session_id, {})
        if existing.get("terminal"):
            typer.echo(
                f"Session {session_id} was already completed locally; skipping duplicate delivery."
            )
            continue
        if existing.get("blocked"):
            typer.echo(f"Session {session_id} needs local recovery; it was not run again.")
            continue
        if existing.get("local_result"):
            _sync_local_result(api, state, session_id)
            continue
        if existing.get("started"):
            _emit(
                api,
                state,
                session_id,
                "run.disconnected",
                {
                    "kind": "run.disconnected",
                    "reason": (
                        "The CLI restarted during a local build; inspect the local build "
                        "report before retrying."
                    ),
                },
            )
            history = _read_history(state)
            history["sessions"].setdefault(session_id, {})["blocked"] = True
            _write_history(state, history)
            typer.echo(f"Session {session_id} was interrupted locally; it was not run again.")
            continue
        if delivery.get("cancel_requested"):
            _emit(
                api,
                state,
                session_id,
                "run.cancelled",
                {"kind": "run.cancelled", "initiated_by": "omnix_user"},
            )
            continue
        local_run_id = existing.get("local_run_id")
        if not isinstance(local_run_id, str):
            local_run_id = f"remote_{session_id[:32]}"
            history = _read_history(state)
            history["sessions"].setdefault(session_id, {"sequence": 0, "terminal": False})[
                "local_run_id"
            ] = local_run_id
            _write_history(state, history)
        if confirm and not typer.confirm(
            f"Run approved Omnix {capability} session {session_id}?", default=False
        ):
            _emit(
                api,
                state,
                session_id,
                "run.cancelled",
                {"kind": "run.cancelled", "initiated_by": "cli_user"},
            )
            continue
        if not existing.get("accepted"):
            _emit(
                api,
                state,
                session_id,
                "run.accepted",
                {"kind": "run.accepted", "local_run_id": local_run_id},
            )
            history = _read_history(state)
            history["sessions"].setdefault(session_id, {})["accepted"] = True
            _write_history(state, history)
        progress: list[str] = []

        def report_progress(
            message: str,
            _session_id: str = session_id,
            _progress: list[str] = progress,
        ) -> bool:
            cancel = False
            try:
                control = api.request("GET", f"/sessions/{_session_id}/control")
                cancel = bool(control.get("cancel_requested"))
            except OmnixAuthError:
                # A lost Omnix connection must not turn a local build into a false failure.
                pass
            if len(_progress) < 20:
                _progress.append(str(message)[:1024])
            return cancel

        _emit(
            api,
            state,
            session_id,
            "phase.started",
            {"kind": "phase.started", "phase": capability},
        )
        history = _read_history(state)
        history["sessions"].setdefault(session_id, {})["started"] = True
        _write_history(state, history)
        before_artifact_digests = _artifact_snapshot(state)
        try:
            summary, success = asyncio.run(
                _run_capability(state, capability, capability_input, report_progress, local_run_id)
            )
        except Exception:
            _emit(
                api,
                state,
                session_id,
                "run.failed",
                {
                    "kind": "run.failed",
                    "error_code": "local_build_failed",
                    "summary": (
                        "The local build failed. See the CLI's local build report for details."
                    ),
                },
            )
            continue
        if capability == "build" and summary == BuildOutcome.CANCELLED.value:
            terminal_event_type = "run.cancelled"
            terminal_payload = {"kind": terminal_event_type, "initiated_by": "omnix_user"}
        elif success:
            terminal_event_type = "run.succeeded"
        else:
            terminal_event_type = "run.failed"
            terminal_payload = {
                "kind": terminal_event_type,
                "error_code": f"{capability}_not_successful",
                "summary": summary[:4096],
            }
        if terminal_event_type == "run.succeeded":
            terminal_payload = {"kind": terminal_event_type, "summary": summary[:4096]}
        result_events = [
            {
                "event_type": "phase.progress",
                "payload": {"kind": "phase.progress", "phase": capability, "message": message},
            }
            for message in progress
        ]
        result_events.extend(
            [
                {
                    "event_type": "phase.completed",
                    "payload": {
                        "kind": "phase.completed",
                        "phase": capability,
                        "summary": summary[:4096],
                    },
                },
                {"event_type": terminal_event_type, "payload": terminal_payload},
            ]
        )
        manifest_items, omitted_artifacts = _artifact_manifest(state, before_artifact_digests)
        if manifest_items:
            if omitted_artifacts:
                phase_summary = next(
                    event["payload"]
                    for event in reversed(result_events)
                    if event["event_type"] == "phase.completed"
                )
                phase_summary["summary"] = phase_summary["summary"][:3900] + (
                    f" (manifest lists {len(manifest_items)} of "
                    f"{len(manifest_items) + omitted_artifacts} artifacts)"
                )
            result_events.insert(
                -1,
                {
                    "event_type": "artifact.manifest",
                    "payload": {"kind": "artifact.manifest", "items": manifest_items},
                },
            )
        _store_local_result(state, session_id, result_events)
        _sync_local_result(api, state, session_id)
        typer.echo(f"Completed Omnix {capability} session {session_id}: {summary}")
    return len(deliveries)


def work_sessions_command(
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Skip the local confirmation prompt for each approved session."),
    ] = False,
) -> None:
    """Poll once and run queued, typed build sessions for this linked project."""
    manager = StateManager(workspace)
    project_id = manager.ensure_project_id()
    api = OmnixApi(project_id)
    try:
        work_once(manager, api, confirm=not yes)
    except OmnixAuthError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    finally:
        api.close()
