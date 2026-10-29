import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from omnix_cli.core.state_manager import StateManager
from omnix_cli.integrations import omnix_sessions
from omnix_cli.integrations.omnix_auth import OmnixAuthError
from omnix_cli.integrations.omnix_sessions import _validate_request
from omnix_cli.schemas.artifacts import Artifact, ArtifactType
from omnix_cli.schemas.build import BuildOutcome
from omnix_cli.schemas.repair import RepairArtifact


def _request(**overrides):
    value = {
        "protocol_version": 1,
        "session_id": "13caad67-3758-445e-81c8-a98165e955d7",
        "linked_project_id": "project-1",
        "capability": "build",
        "capability_version": 1,
        "idempotency_key": "6e822aae-62ea-4d73-bd7a-f437b3a82c25",
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        "input": {"kind": "build", "goal": "Add coverage"},
    }
    value.update(overrides)
    return value


def test_accepts_only_typed_build_for_current_link():
    assert _validate_request(_request(), {"linked_project_id": "project-1"}) == (
        "13caad67-3758-445e-81c8-a98165e955d7",
        "build",
        _request()["input"],
    )


@pytest.mark.parametrize(
    "capability,capability_input",
    [
        ("plan", {"kind": "plan", "goal": "Plan the API"}),
        ("qa", {"kind": "qa", "local_run_id": "build_0001", "profile": "default"}),
        (
            "repair",
            {"kind": "repair", "local_run_id": "build_0001", "finding_ids": ["QA-1"]},
        ),
    ],
)
def test_accepts_only_typed_v1_capabilities(capability, capability_input):
    request = _request(capability=capability, input=capability_input)
    assert _validate_request(request, {"linked_project_id": "project-1"}) == (
        request["session_id"],
        capability,
        capability_input,
    )


@pytest.mark.parametrize(
    "payload,link",
    [
        (_request(capability="repair"), {"linked_project_id": "project-1"}),
        (_request(capability_version=2), {"linked_project_id": "project-1"}),
        (_request(shell="echo unsafe"), {"linked_project_id": "project-1"}),
        (_request(linked_project_id="project-2"), {"linked_project_id": "project-1"}),
        (
            _request(input={"kind": "build", "goal": "Build", "shell": "echo unsafe"}),
            {"linked_project_id": "project-1"},
        ),
        (_request(expires_at="2020-01-01T00:00:00+00:00"), {"linked_project_id": "project-1"}),
    ],
)
def test_rejects_unsupported_or_unsafe_request(payload, link):
    with pytest.raises(OmnixAuthError):
        _validate_request(payload, link)


class FakeApi:
    def __init__(self):
        self.events = []
        self.delivery = {
            "request": {
                "protocol_version": 1,
                "session_id": "13caad67-3758-445e-81c8-a98165e955d7",
                "linked_project_id": "project-1",
                "capability": "build",
                "capability_version": 1,
                "idempotency_key": "6e822aae-62ea-4d73-bd7a-f437b3a82c25",
                "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
                "input": {"kind": "build", "goal": "Add coverage"},
            },
            "cancel_requested": False,
        }

    def request(self, method, path, payload=None):
        if path == "/status":
            return {"linked": True, "linked_project_id": "project-1"}
        if path == "/capabilities":
            return {
                "capabilities": [
                    {"name": name, "version": 1} for name in ("plan", "build", "qa", "repair")
                ]
            }
        if path == "/sessions/poll":
            return {"deliveries": [self.delivery]}
        if path.endswith("/control"):
            return {"cancel_requested": False}
        if path.endswith("/events"):
            self.events.append(payload)
            return {"accepted": True}
        raise AssertionError(f"unexpected API request {method} {path}")


def test_worker_runs_typed_build_once_and_keeps_replay_cursor_private(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    api = FakeApi()
    state = StateManager(tmp_path)
    calls = []
    run_ids = []

    class FakeOrchestrator:
        def __init__(self, _state, *, config):
            self.state = _state
            self.progress_callback = None

        async def build(self, goal, *, run_id=None):
            calls.append(goal)
            run_ids.append(run_id)
            self.progress_callback("Build accepted locally")
            self.state.save_artifact(
                Artifact(
                    id="artifact-1",
                    task_id="task-1",
                    agent="builder",
                    title="Session result",
                    description="Bounded result summary",
                    artifact_type=ArtifactType.FRONTEND_COMPONENT,
                    content="private source content",
                )
            )
            return SimpleNamespace(
                run_id=run_id,
                outcome=BuildOutcome.SUCCESS,
                task_count=4,
                artifacts_generated=1,
                final_quality_score=92,
                blueprint_summary=SimpleNamespace(
                    feature_count=3,
                    entity_count=2,
                    module_count=1,
                    page_count=4,
                    api_count=5,
                    architecture_note_count=2,
                ),
            )

    monkeypatch.setattr(omnix_sessions, "AutonomousOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(omnix_sessions.typer, "confirm", lambda *args, **kwargs: True)

    assert omnix_sessions.work_once(state, api) == 1
    assert omnix_sessions.work_once(state, api) == 1
    assert calls == ["Add coverage"]
    assert run_ids == [f"remote_{api.delivery['request']['session_id'][:32]}"]
    assert api.events[0]["payload"]["local_run_id"] == run_ids[0]
    assert [event["event_type"] for event in api.events] == [
        "run.accepted",
        "phase.started",
        "phase.progress",
        "phase.completed",
        "artifact.manifest",
        "run.succeeded",
    ]
    manifest = next(
        event["payload"] for event in api.events if event["event_type"] == "artifact.manifest"
    )
    phase_summary = next(
        event["payload"]["summary"]
        for event in api.events
        if event["event_type"] == "phase.completed"
    )
    assert "4 tasks, 1 artifact; quality score 92" in phase_summary
    assert "3 features, 2 entities, 1 module, 4 pages, 5 APIs" in phase_summary
    assert manifest["items"] == [
        {
            "local_artifact_id": "build:artifact-1",
            "artifact_type": "frontend_component",
            "display_name": "Session result",
            "summary": "Generated frontend component artifact",
            "sha256": "a27abace604556434dab994b534102e36d720b28214e3b8fba4e39fa80cf5537",
            "size_bytes": len("private source content"),
            "provenance_refs": ["task-1"],
        }
    ]
    assert "content" not in str(manifest)
    assert "path" not in str(manifest).lower()
    history_path = tmp_path / ".project" / "omnix_remote_sessions.json"
    assert stat.S_IMODE(history_path.stat().st_mode) == 0o600
    history = json.loads(history_path.read_text(encoding="utf-8"))
    assert history["sessions"][api.delivery["request"]["session_id"]]["terminal"] is True


def test_worker_records_local_decline_without_running_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    api = FakeApi()
    monkeypatch.setattr(omnix_sessions.typer, "confirm", lambda *args, **kwargs: False)
    assert omnix_sessions.work_once(StateManager(tmp_path), api) == 1
    assert [event["event_type"] for event in api.events] == ["run.cancelled"]


def test_revoked_device_stops_remote_build_and_preserves_cancelled_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    stopped = []

    class RevokedApi(FakeApi):
        def request(self, method, path, payload=None):
            if path.endswith("/control"):
                raise OmnixAuthError("Omnix login expired or was revoked.", status_code=401)
            if path.endswith("/events") and payload.get("event_type") not in {
                "run.accepted",
                "phase.started",
            }:
                raise OmnixAuthError("Omnix login expired or was revoked.", status_code=401)
            return super().request(method, path, payload)

    class FakeOrchestrator:
        def __init__(self, _state, *, config):
            self.progress_callback = None
            self.stop_requested = False

        def request_stop(self):
            self.stop_requested = True
            stopped.append(True)

        async def build(self, goal, *, run_id=None):
            self.progress_callback("Working on a local task")
            return SimpleNamespace(outcome=BuildOutcome.CANCELLED)

    revoked_api = RevokedApi()
    monkeypatch.setattr(omnix_sessions, "AutonomousOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(omnix_sessions.typer, "confirm", lambda *args, **kwargs: True)

    with pytest.raises(OmnixAuthError, match="Remote sync is partial"):
        omnix_sessions.work_once(StateManager(tmp_path), revoked_api)

    assert stopped == [True]
    session_id = revoked_api.delivery["request"]["session_id"]
    history = json.loads(
        (tmp_path / ".project" / "omnix_remote_sessions.json").read_text(encoding="utf-8")
    )
    session = history["sessions"][session_id]
    assert session["sync_state"] == "partial"
    assert session["local_result"]["events"][-1] == {
        "event_type": "run.cancelled",
        "payload": {"kind": "run.cancelled", "initiated_by": "policy"},
    }


def test_session_history_is_offline_readable_and_excludes_private_inputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    state = StateManager(tmp_path)
    omnix_sessions._write_history(
        state,
        {
            "sessions": {
                "session-safe-id": {
                    "capability": "build",
                    "remote_status": "running",
                    "sync_state": "partial",
                    "goal": "private task text",
                    "token": "must-not-display",
                }
            }
        },
    )

    omnix_sessions.history_sessions_command(workspace=tmp_path)

    output = capsys.readouterr().out
    assert "session-safe-id  build  running  sync: partial" in output
    assert "available offline" in output
    assert "private task text" not in output
    assert "must-not-display" not in output
    assert "omnix sessions work" in output


@pytest.mark.parametrize(
    "capabilities,expected",
    [
        (
            {
                "protocol_version": 1,
                "capabilities": [
                    {"name": name, "version": 1} for name in ("plan", "build", "qa", "repair")
                ],
            },
            "compatible",
        ),
        ({"protocol_version": 2, "capabilities": []}, "incompatible"),
        (
            {"protocol_version": 1, "capabilities": [{"name": "build", "version": 1}]},
            "incompatible",
        ),
    ],
)
def test_session_protocol_status(capabilities, expected):
    assert omnix_sessions.session_protocol_status(capabilities) == expected


def test_worker_persists_local_result_when_event_upload_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    api = FakeApi()
    state = StateManager(tmp_path)

    class OfflineApi(FakeApi):
        def request(self, method, path, payload=None):
            if path.endswith("/events") and payload.get("event_type") == "phase.progress":
                raise OmnixAuthError("Omnix could not be reached.")
            return super().request(method, path, payload)

    class FakeOrchestrator:
        def __init__(self, _state, *, config):
            self.progress_callback = None

        async def build(self, goal, *, run_id=None):
            self.progress_callback("Local build completed")
            return SimpleNamespace(outcome=BuildOutcome.SUCCESS)

    monkeypatch.setattr(omnix_sessions, "AutonomousOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(omnix_sessions.typer, "confirm", lambda *args, **kwargs: True)
    offline = OfflineApi()
    with pytest.raises(OmnixAuthError):
        omnix_sessions.work_once(state, offline)

    record = json.loads((tmp_path / ".project" / "omnix_remote_sessions.json").read_text())
    session_id = offline.delivery["request"]["session_id"]
    assert (
        record["sessions"][session_id]["local_result"]["events"][-1]["event_type"]
        == "run.succeeded"
    )
    assert record["sessions"][session_id]["sync_state"] == "partial"
    assert record["sessions"][session_id]["pending_event"]["event_type"] == "phase.progress"

    omnix_sessions.work_once(state, api)
    assert [event["event_type"] for event in offline.events + api.events] == [
        "run.accepted",
        "phase.started",
        "phase.progress",
        "phase.completed",
        "run.succeeded",
    ]
    recovered = json.loads((tmp_path / ".project" / "omnix_remote_sessions.json").read_text())
    assert "sync_state" not in recovered["sessions"][session_id]


def test_conflicted_event_is_recorded_and_recoverable(tmp_path: Path):
    state = StateManager(tmp_path)

    class ConflictApi(FakeApi):
        conflict = True

        def request(self, method, path, payload=None):
            if self.conflict and path.endswith("/events"):
                raise OmnixAuthError("Omnix rejected the request (HTTP 409).")
            return super().request(method, path, payload)

    api = ConflictApi()
    session_id = api.delivery["request"]["session_id"]
    payload = {"kind": "run.accepted", "local_run_id": "remote-run-1"}
    with pytest.raises(OmnixAuthError):
        omnix_sessions._emit(api, state, session_id, "run.accepted", payload)

    history_path = tmp_path / ".project" / "omnix_remote_sessions.json"
    conflicted = json.loads(history_path.read_text())["sessions"][session_id]
    assert conflicted["sync_state"] == "conflicted"
    assert conflicted["pending_event"]["payload"] == payload

    api.conflict = False
    omnix_sessions._emit(api, state, session_id, "run.accepted", payload)
    recovered = json.loads(history_path.read_text())["sessions"][session_id]
    assert recovered["sequence"] == 1
    assert "sync_state" not in recovered


def test_artifact_manifest_is_bounded_and_omits_paths_and_descriptions(tmp_path: Path):
    unsafe_artifact = Artifact(
        id="/Users/private/artifact.json",
        task_id="/Users/private/task.json",
        agent="builder",
        title="/Users/private/result.ts",
        description="Do not publish this detailed description.",
        artifact_type=ArtifactType.FRONTEND_COMPONENT,
        content="private source content",
    )
    state = SimpleNamespace(
        list_artifacts=lambda: [unsafe_artifact],
        list_repair_artifacts=lambda: [],
    )
    manifest, omitted = omnix_sessions._artifact_manifest(state, {})
    assert omitted == 0
    assert len(manifest) == 1
    assert "/Users/private" not in str(manifest)
    assert "private" not in str(manifest)
    assert "Do not publish" not in str(manifest)
    assert "private source content" not in str(manifest)

    state = StateManager(tmp_path)
    for index in range(102):
        state.save_artifact(
            Artifact(
                id=f"artifact-{index}",
                task_id=f"task-{index}",
                agent="builder",
                title=f"Artifact {index}",
                artifact_type=ArtifactType.FRONTEND_COMPONENT,
                content="x",
            )
        )
    manifest, omitted = omnix_sessions._artifact_manifest(state, {})
    assert 0 < len(manifest) < 100
    assert len(manifest) + omitted == 102


def test_repair_artifacts_sync_digest_and_provenance_only(tmp_path: Path):
    state = StateManager(tmp_path)
    state.save_repair_artifact(
        RepairArtifact(
            id="repair_artifact_1",
            repair_plan_id="plan_item_1",
            qa_finding_id="finding_1",
            target_agent="frontend",
            title="Repair result",
            description="Private repair details stay local.",
            content="private repaired source",
            cycle=1,
        )
    )

    manifest, omitted = omnix_sessions._artifact_manifest(state, {})
    assert omitted == 0
    assert manifest[0]["artifact_type"] == "repair_artifact"
    assert manifest[0]["provenance_refs"] == ["plan_item_1", "finding_1"]
    assert manifest[0]["sha256"]
    assert "Private repair details" not in str(manifest)
    assert "private repaired source" not in str(manifest)
