from __future__ import annotations

from pathlib import Path

import pytest

from omnix_cli.cli.commands import omnix_account


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
            "Remote sessions: compatible (protocol v1 capabilities)",
        ),
        (
            {"protocol_version": 2, "capabilities": []},
            "Remote sessions: incompatible; update Omnix CLI before polling",
        ),
    ],
)
def test_status_displays_protocol_compatibility(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    capabilities: dict,
    expected: str,
) -> None:
    class Store:
        def read(self, project_id: str):
            assert project_id == "local-project-1"
            return {"access_token": "opaque", "refresh_token": "opaque"}

    class Api:
        def __init__(self, project_id: str, *, store=None):
            assert project_id == "local-project-1"
            assert store is not None

        def request(self, method: str, path: str):
            assert method == "GET"
            if path == "/status":
                return {
                    "linked": True,
                    "workspace_id": "workspace-1",
                    "linked_project_id": "linked-project-1",
                    "project_name": "Example",
                    "scopes": ["sessions:execute"],
                }
            if path == "/capabilities":
                return capabilities
            raise AssertionError(f"unexpected request: {path}")

        def close(self) -> None:
            pass

    monkeypatch.setattr(
        omnix_account, "project_id_for", lambda _workspace: (None, "local-project-1")
    )
    monkeypatch.setattr(omnix_account, "CredentialStore", Store)
    monkeypatch.setattr(omnix_account, "OmnixApi", Api)

    omnix_account.omnix_status_command(workspace=tmp_path)

    output = capsys.readouterr().out
    assert "Omnix CLI device: connected" in output
    assert expected in output


def test_status_explains_when_remote_sessions_are_not_authorized(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Store:
        def read(self, _project_id: str):
            return {"access_token": "opaque", "refresh_token": "opaque"}

    class Api:
        def __init__(self, _project_id: str, *, store=None):
            pass

        def request(self, _method: str, path: str):
            assert path == "/status"
            return {"linked": True, "workspace_id": "workspace-1", "scopes": []}

        def close(self) -> None:
            pass

    monkeypatch.setattr(
        omnix_account, "project_id_for", lambda _workspace: (None, "local-project-1")
    )
    monkeypatch.setattr(omnix_account, "CredentialStore", Store)
    monkeypatch.setattr(omnix_account, "OmnixApi", Api)

    omnix_account.omnix_status_command(workspace=tmp_path)

    assert "Remote sessions: not enabled for this CLI device" in capsys.readouterr().out
