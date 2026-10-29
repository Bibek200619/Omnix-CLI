"""Device authorization and scoped Omnix CLI credentials."""

from __future__ import annotations

import json
import os
import platform
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import keyring
import typer

from omnix_cli.core.state_manager import StateManager

SERVICE_NAME = "omnix-cli"
DEFAULT_API_URL = "https://api.omni-x.co.in"
API_PREFIX = "/integrations/cli/v1"
SAFE_KEYRING_MODULES = (
    "keyring.backends.macOS",
    "keyring.backends.Windows",
    "keyring.backends.SecretService",
    "keyring.backends.kwallet",
)


class OmnixAuthError(RuntimeError):
    """Safe-to-display authentication or integration error."""


def _backend_is_secure(backend: Any) -> bool:
    if getattr(backend, "priority", 0) <= 0:
        return False
    module = type(backend).__module__
    if module.startswith(SAFE_KEYRING_MODULES):
        return True
    chained = getattr(backend, "backends", None)
    return bool(chained) and all(_backend_is_secure(item) for item in chained)


class CredentialStore:
    """Store credentials only in a supported operating-system secret store."""

    def __init__(self) -> None:
        try:
            backend = keyring.get_keyring()
        except Exception as exc:
            raise OmnixAuthError(
                "No secure OS credential store is available; CLI login was not saved."
            ) from exc
        if not _backend_is_secure(backend):
            raise OmnixAuthError(
                "No secure OS credential store is available. Configure macOS Keychain, "
                "Windows Credential Locker, or a Linux Secret Service before logging in."
            )

    def read(self, project_id: str) -> dict[str, Any] | None:
        try:
            value = keyring.get_password(SERVICE_NAME, project_id)
        except Exception as exc:
            raise OmnixAuthError(
                "Could not read Omnix credentials from the OS credential store."
            ) from exc
        if value is None:
            return None
        try:
            payload = json.loads(value)
            if not isinstance(payload, dict) or not all(
                isinstance(payload.get(field), str)
                for field in ("device_id", "access_token", "refresh_token")
            ):
                raise ValueError("invalid credential record")
            return payload
        except (ValueError, TypeError) as exc:
            raise OmnixAuthError(
                "The saved Omnix credential record is invalid; run `omnix logout` and log in again."
            ) from exc

    def write(self, project_id: str, credentials: dict[str, Any]) -> None:
        try:
            keyring.set_password(
                SERVICE_NAME, project_id, json.dumps(credentials, separators=(",", ":"))
            )
        except Exception as exc:
            raise OmnixAuthError(
                "Could not save Omnix credentials to the OS credential store."
            ) from exc

    def delete(self, project_id: str) -> None:
        try:
            keyring.delete_password(SERVICE_NAME, project_id)
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception as exc:
            raise OmnixAuthError(
                "Could not remove Omnix credentials from the OS credential store."
            ) from exc


def api_base_url() -> str:
    raw = os.environ.get("OMNIX_API_URL", DEFAULT_API_URL).strip()
    parsed = urlsplit(raw)
    allowed_local = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not allowed_local:
        raise OmnixAuthError("OMNIX_API_URL must use HTTPS (HTTP is allowed only for localhost).")
    if not parsed.netloc or parsed.username or parsed.password:
        raise OmnixAuthError("OMNIX_API_URL must be a valid URL without embedded credentials.")
    return raw.rstrip("/")


class OmnixApi:
    def __init__(
        self, project_id: str, *, store: CredentialStore | None = None, api_url: str | None = None
    ) -> None:
        self.project_id = project_id
        self.store = store or CredentialStore()
        self.base_url = (api_url or api_base_url()).rstrip("/") + API_PREFIX
        self.client = httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0), follow_redirects=False)

    def close(self) -> None:
        self.client.close()

    def _raw(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = self.client.request(
                method,
                f"{self.base_url}{path}",
                json=payload,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise OmnixAuthError(
                "Omnix could not be reached. Check your connection and try again."
            ) from exc
        if response.is_redirect:
            raise OmnixAuthError("Omnix returned an unexpected redirect; the request was stopped.")
        try:
            result = response.json()
        except ValueError:
            result = {}
        if not response.is_success:
            detail = result.get("detail") if isinstance(result, dict) else None
            safe_details = {
                "authorization_pending": "Waiting for approval in the browser.",
                "slow_down": "Approval polling was rate limited.",
            }
            message = safe_details.get(
                detail, f"Omnix rejected the request (HTTP {response.status_code})."
            )
            if response.status_code == 428:
                raise ApprovalPending(message)
            raise OmnixAuthError(message)
        if not isinstance(result, (dict, list)):
            raise OmnixAuthError("Omnix returned an invalid response.")
        return result

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        credentials = self.store.read(self.project_id)
        if credentials is None:
            raise OmnixAuthError("Not logged in. Run `omnix login` first.")
        if float(credentials.get("access_expires_at", 0)) <= time.time() + 20:
            credentials = self._refresh(credentials)
        try:
            return self._raw(method, path, payload, credentials["access_token"])
        except OmnixAuthError as exc:
            if "HTTP 401" not in str(exc):
                raise
            credentials = self._refresh(credentials)
            return self._raw(method, path, payload, credentials["access_token"])

    def _refresh(self, credentials: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._raw(
                "POST",
                "/token",
                {"grant_type": "refresh_token", "refresh_token": credentials["refresh_token"]},
            )
        except OmnixAuthError as exc:
            raise OmnixAuthError(
                "Omnix login expired or was revoked. Run `omnix login` again."
            ) from exc
        next_credentials = self._token_record(response)
        self.store.write(self.project_id, next_credentials)
        return next_credentials

    @staticmethod
    def _token_record(response: dict[str, Any]) -> dict[str, Any]:
        return {
            "device_id": str(response["device_id"]),
            "access_token": str(response["access_token"]),
            "refresh_token": str(response["refresh_token"]),
            "access_expires_at": time.time() + int(response["expires_in"]),
            "refresh_expires_at": time.time() + int(response["refresh_expires_in"]),
            "scopes": list(response.get("scopes") or []),
        }

    def login(self, state_manager: StateManager, *, timeout_seconds: int = 600) -> dict[str, Any]:
        blueprint = state_manager.load_blueprint()
        project_id = state_manager.ensure_project_id()
        response = self._raw(
            "POST",
            "/device/code",
            {
                "local_project_id": project_id,
                "project_name": blueprint.project_name or state_manager.workspace.name,
                "device_name": f"Omnix CLI ({platform.system()})",
                "scopes": ["workspace:read", "project:link", "sessions:execute"],
            },
        )
        url = response["verification_uri"]
        typer.echo("Approve this Omnix CLI sign-in in your browser:")
        typer.echo(f"  {url}")
        if not webbrowser.open(url):
            typer.echo("Open the URL above manually to continue.")
        typer.echo(f"Device code: {response['user_code']}")
        typer.echo("Waiting for browser approval…")
        deadline = time.monotonic() + min(timeout_seconds, int(response["expires_in"]))
        interval = max(2, int(response.get("interval", 3)))
        while time.monotonic() < deadline:
            try:
                token_response = self._raw(
                    "POST",
                    "/token",
                    {"grant_type": "device_code", "device_code": response["device_code"]},
                )
                credentials = self._token_record(token_response)
                try:
                    self.store.write(project_id, credentials)
                except OmnixAuthError:
                    try:
                        self._raw("DELETE", "/session", token=credentials["access_token"])
                    finally:
                        raise
                return {"project_id": project_id, "credentials": credentials}
            except ApprovalPending:
                time.sleep(interval)
        raise OmnixAuthError("The device code expired. Run `omnix login` to start a new request.")


class ApprovalPending(OmnixAuthError):
    """Expected polling state before the user approves the browser prompt."""


def project_id_for(workspace: Path) -> tuple[StateManager, str]:
    manager = StateManager(workspace)
    return manager, manager.ensure_project_id()
