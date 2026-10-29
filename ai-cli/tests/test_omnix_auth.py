from __future__ import annotations

import json
from pathlib import Path

import httpx
import keyring
import pytest

from omnix_cli.core.state_manager import StateManager
from omnix_cli.integrations.omnix_auth import (
    CredentialStore,
    OmnixApi,
    OmnixAuthError,
)


def test_project_identity_is_stable_and_contains_no_credentials(tmp_path: Path) -> None:
    manager = StateManager(tmp_path)
    manager.init_project(project_name="Local project")

    first = manager.ensure_project_id()
    second = manager.ensure_project_id()

    assert first == second
    identity_path = manager.project_dir / "omnix_project.json"
    assert json.loads(identity_path.read_text(encoding="utf-8")) == {"project_id": first}
    assert identity_path.stat().st_mode & 0o777 == 0o600


def test_credential_store_refuses_unencrypted_file_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    PlaintextBackend = type(
        "PlaintextBackend",
        (),
        {"__module__": "keyring.backends.file", "priority": 1},
    )
    monkeypatch.setattr(keyring, "get_keyring", lambda: PlaintextBackend())

    with pytest.raises(OmnixAuthError, match="No secure OS credential store"):
        CredentialStore()


def test_cli_api_rotates_expired_access_credentials_before_request() -> None:
    class Store:
        def __init__(self) -> None:
            self.value = {
                "device_id": "device-1",
                "access_token": "old-access",
                "refresh_token": "old-refresh",
                "access_expires_at": 0,
            }

        def read(self, project_id: str):
            assert project_id == "project-1"
            return dict(self.value)

        def write(self, project_id: str, value):
            assert project_id == "project-1"
            self.value = dict(value)

    store = Store()
    requests: list[tuple[str, str | None]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"{}")
        requests.append((request.url.path, request.headers.get("Authorization")))
        if request.url.path.endswith("/token"):
            assert body["grant_type"] == "refresh_token"
            assert body["refresh_token"] == "old-refresh"
            return httpx.Response(
                200,
                json={
                    "device_id": "device-1",
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 900,
                    "refresh_expires_in": 3600,
                    "scopes": ["workspace:read"],
                },
            )
        assert request.headers.get("Authorization") == "Bearer new-access"
        return httpx.Response(200, json={"linked": False})

    api = OmnixApi("project-1", store=store, api_url="https://omnix.test")
    api.client.close()
    api.client = httpx.Client(transport=httpx.MockTransport(handle))
    try:
        assert api.request("GET", "/status") == {"linked": False}
    finally:
        api.close()

    assert [path.rsplit("/", 1)[-1] for path, _ in requests] == ["token", "status"]
    assert store.value["access_token"] == "new-access"
    assert store.value["refresh_token"] == "new-refresh"


def test_revoked_api_response_preserves_http_status_for_safe_work_stopping() -> None:
    class Store:
        def read(self, _project_id: str):
            return {
                "device_id": "device-1",
                "access_token": "opaque-access",
                "refresh_token": "opaque-refresh",
                "access_expires_at": 9999999999,
            }

    api = OmnixApi("project-1", store=Store(), api_url="https://omnix.test")
    api.client.close()
    api.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(401, json={"detail": "unauthorized"})
        )
    )
    try:
        with pytest.raises(OmnixAuthError) as raised:
            api.request("GET", "/sessions/session-1/control")
    finally:
        api.close()

    assert raised.value.status_code == 401
    assert "opaque-access" not in str(raised.value)
