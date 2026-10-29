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
from omnix_cli.schemas.build import BuildOutcome


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

    class FakeOrchestrator:
        def __init__(self, _state, *, config):
            self.progress_callback = None

        async def build(self, goal):
            calls.append(goal)
            self.progress_callback("Build accepted locally")
            return SimpleNamespace(outcome=BuildOutcome.SUCCESS)

    monkeypatch.setattr(omnix_sessions, "AutonomousOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(omnix_sessions.typer, "confirm", lambda *args, **kwargs: True)

    assert omnix_sessions.work_once(state, api) == 1
    assert omnix_sessions.work_once(state, api) == 1
    assert calls == ["Add coverage"]
    assert [event["event_type"] for event in api.events] == [
        "run.accepted",
        "phase.started",
        "phase.progress",
        "phase.completed",
        "run.succeeded",
    ]
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

        async def build(self, goal):
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

    omnix_sessions.work_once(state, api)
    assert [event["event_type"] for event in offline.events + api.events] == [
        "run.accepted",
        "phase.started",
        "phase.progress",
        "phase.completed",
        "run.succeeded",
    ]
