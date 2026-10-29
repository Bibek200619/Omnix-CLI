"""Omnix account, device, and project-link commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer

from omnix_cli.core.exceptions import OmnixError
from omnix_cli.integrations.omnix_auth import (
    CredentialStore,
    OmnixApi,
    OmnixAuthError,
    project_id_for,
)
from omnix_cli.integrations.omnix_sessions import session_protocol_status


def _report_error(error: Exception) -> None:
    message = str(error) if isinstance(error, OmnixAuthError) else "Omnix CLI request failed."
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(1) from error


def login_command(
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Sign in to Omnix using browser-approved device authorization."""
    api: OmnixApi | None = None
    try:
        state_manager, project_id = project_id_for(workspace)
        store = CredentialStore()
        if store.read(project_id):
            raise OmnixAuthError(
                "This local project is already logged in. Run `omnix logout` first."
            )
        api = OmnixApi(project_id, store=store)
        api.login(state_manager)
        typer.secho(
            "Signed in to Omnix. Run `omnix link` to choose a workspace for this local project.",
            fg=typer.colors.GREEN,
        )
    except (OmnixAuthError, OmnixError) as exc:
        _report_error(exc)
    finally:
        if api is not None:
            api.close()


def logout_command(
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Revoke this CLI device and remove its OS credential."""
    api: OmnixApi | None = None
    try:
        _, project_id = project_id_for(workspace)
        store = CredentialStore()
        if store.read(project_id) is None:
            typer.echo("This local project is not logged in.")
            return
        api = OmnixApi(project_id, store=store)
        try:
            api.request("DELETE", "/session")
            typer.echo("CLI device revoked in Omnix.")
        except OmnixAuthError as exc:
            typer.secho(
                f"Could not confirm remote revocation ({exc}). Remove the device from "
                "Omnix Settings → CLI Devices.",
                fg=typer.colors.YELLOW,
                err=True,
            )
        store.delete(project_id)
        typer.echo("Local Omnix credentials removed from the OS credential store.")
    except (OmnixAuthError, OmnixError) as exc:
        _report_error(exc)
    finally:
        if api is not None:
            api.close()


def link_command(
    workspace_id: Annotated[
        str | None, typer.Option("--workspace-id", help="Authorized Omnix workspace ID.")
    ] = None,
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Link this local project to a workspace the signed-in user can access."""
    api: OmnixApi | None = None
    try:
        _, project_id = project_id_for(workspace)
        api = OmnixApi(project_id)
        if workspace_id is None:
            workspaces = api.request("GET", "/workspaces")
            if not workspaces:
                raise OmnixAuthError("Your Omnix account has no authorized workspaces to link.")
            typer.echo("Choose an Omnix workspace:")
            for index, item in enumerate(workspaces, start=1):
                role = item.get("current_user_role") or "member"
                typer.echo(f"  {index}. {item.get('name') or 'Workspace'} ({role})")
            choice = typer.prompt("Workspace number", type=int)
            if choice < 1 or choice > len(workspaces):
                raise OmnixAuthError("Workspace selection is out of range.")
            selected = workspaces[choice - 1]
            workspace_id = str(selected["id"])
            workspace_name = str(selected.get("name") or "Workspace")
        else:
            workspace_name = workspace_id
        result = api.request("POST", "/link", {"workspace_id": workspace_id})
        typer.secho(
            f"Linked {result.get('project_name') or 'local project'} to {workspace_name}.",
            fg=typer.colors.GREEN,
        )
    except (OmnixAuthError, OmnixError) as exc:
        _report_error(exc)
    finally:
        if api is not None:
            api.close()


def unlink_command(
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Remove this device's workspace and project link in Omnix."""
    api: OmnixApi | None = None
    try:
        _, project_id = project_id_for(workspace)
        api = OmnixApi(project_id)
        api.request("DELETE", "/link")
        typer.echo("Local project unlinked from Omnix. The CLI remains available offline.")
    except (OmnixAuthError, OmnixError) as exc:
        _report_error(exc)
    finally:
        if api is not None:
            api.close()


def omnix_status_command(
    workspace: Annotated[
        Path,
        typer.Option(
            "--workspace",
            "-w",
            help="Project root containing the .project directory.",
            file_okay=False,
        ),
    ] = Path("."),
) -> None:
    """Show the current Omnix account and local-project link status."""
    api: OmnixApi | None = None
    try:
        _, project_id = project_id_for(workspace)
        store = CredentialStore()
        if store.read(project_id) is None:
            typer.echo(
                "Not logged in. Local CLI commands remain available. "
                "Run `omnix login` to connect Omnix."
            )
            return
        api = OmnixApi(project_id, store=store)
        result: dict[str, Any] = api.request("GET", "/status")
        typer.echo("Omnix CLI device: connected")
        typer.echo(f"Project: {result.get('project_name') or 'local project'}")
        if result.get("linked"):
            typer.echo(f"Workspace ID: {result.get('workspace_id')}")
            typer.echo(f"Omnix project ID: {result.get('linked_project_id')}")
            if "sessions:execute" not in result.get("scopes", []):
                typer.echo("Remote sessions: not enabled for this CLI device")
            else:
                try:
                    capabilities = api.request("GET", "/capabilities")
                except OmnixAuthError:
                    typer.echo("Remote sessions: compatibility check unavailable")
                else:
                    compatibility = session_protocol_status(capabilities)
                    if compatibility == "compatible":
                        typer.echo("Remote sessions: compatible (protocol v1 capabilities)")
                    else:
                        typer.echo("Remote sessions: incompatible; update Omnix CLI before polling")
        else:
            typer.echo("Workspace: not linked")
    except (OmnixAuthError, OmnixError) as exc:
        _report_error(exc)
    finally:
        if api is not None:
            api.close()
