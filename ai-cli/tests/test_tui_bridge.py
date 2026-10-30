"""Conversation controls delegated from the Rust terminal frontend."""

from __future__ import annotations

from pathlib import Path

import pytest

import omnix_cli.bridge as bridge_module
from omnix_cli.bridge import Bridge
from omnix_cli.core.state_manager import StateManager
from omnix_cli.schemas.memory import ConversationEntry, ConversationRole


def test_bridge_new_and_resume_preserve_account_identity_and_model_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StateManager(tmp_path)
    state.init_project(project_name="Atlas")
    state.ensure_project_id()
    memory = state.load_memory()
    memory.conversations = [
        ConversationEntry(role=ConversationRole.USER, content="First conversation"),
        ConversationEntry(role=ConversationRole.ASSISTANT, content="First answer"),
    ]
    state.save_memory(memory)
    identity_before = state.omnix_project_path.read_bytes()
    models_before = state.models_path.read_bytes()

    bridge = Bridge(tmp_path)
    def unexpected_credential_access() -> None:
        raise AssertionError("conversation controls must not read or revoke account credentials")

    monkeypatch.setattr(bridge_module, "CredentialStore", unexpected_credential_access)
    events: list[dict[str, object]] = []
    monkeypatch.setattr(bridge, "emit", events.append)
    bridge._handle_session({"id": "new-request", "type": "session_new"})

    assert events[-1]["event"] == "session"
    assert state.load_memory().conversations == []
    assert state.omnix_project_path.read_bytes() == identity_before
    assert state.models_path.read_bytes() == models_before

    memory = state.load_memory()
    memory.conversations = [
        ConversationEntry(role=ConversationRole.USER, content="Second conversation"),
    ]
    state.save_memory(memory)
    bridge._handle_session({"id": "resume-request", "type": "session_resume"})

    assert events[-1]["action"] == "resume"
    assert [item.content for item in state.load_memory().conversations] == [
        "First conversation",
        "First answer",
    ]
    assert state.omnix_project_path.read_bytes() == identity_before
    assert state.models_path.read_bytes() == models_before
