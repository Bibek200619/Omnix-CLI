# Omnix integration v1: CLI implementation notes

**Status:** Device sign-in and project linking are implemented in Omnix #219 and Omnix-CLI #47. Remote execution supports typed `plan`, `build`, `qa`, and `repair` capability v1 requests through durable Omnix sessions. Local task and local plan references that cannot be mapped safely are rejected.

The canonical ownership model and protocol contract live in the [Omnix + Omnix CLI Integration RFC v1](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/omnix-cli-integration-rfc-v1.md), tracked by [Omnix #218](https://github.com/Bibek200619/Omnix/issues/218) and [Omnix-CLI #46](https://github.com/Bibek200619/Omnix-CLI/issues/46). The canonical [session request schema](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/v1/session-request.schema.json) and [run event schema](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/v1/run-event.schema.json) are maintained in Omnix to avoid two sources of truth. This note records how that contract applies to the Python CLI in `ai-cli/`.

## CLI-owned state

- `StateManager` remains the owner of the local `.project/` directory and all detailed project, plan, execution, build, QA, repair, and artifact state.
- Local project files, source, provider configuration/credentials, full prompts/logs, and full artifact contents remain on the device by default.
- Local CLI workflows remain available without login, a linked project, or Omnix connectivity.
- V1 must add a stable local project ID without breaking existing `.project/` files; local run IDs already belong to CLI execution records. Omnix-issued linked-project/session IDs are stored as opaque correlation IDs and do not grant access by themselves.

## Device sign-in and project linking

- Run `omnix login` from an initialized project. The CLI opens the Omnix device approval page and polls until approval or the 10-minute device code expires.
- Approval is tied to the signed-in Omnix user. The CLI then receives a 15-minute opaque access token and a rotating 30-day refresh token. The database stores only SHA-256 hashes; tokens are stored on the client only in the operating-system credential store. If no supported secure keyring is available, login fails without writing credentials to `.project`, `.env`, or another plaintext file.
- Run `omnix link` to choose a workspace or pass `--workspace-id`. Linking rechecks current workspace access in Omnix. `omnix status` shows the link; `omnix unlink` removes it; `omnix logout` revokes the device and removes its local credential.
- Omnix Settings → CLI Devices lists approved devices and lets the account owner revoke them. Each protected CLI integration request rechecks the device token, expiry, current workspace membership, and allowed scope. The initial scopes are `workspace:read` and `project:link`; neither scope authorizes command execution.
- The local project UUID is stored in `.project/omnix_project.json` and contains no credential. Existing `.project/` files remain readable without migration. Set `OMNIX_API_URL` only when using a trusted development endpoint; non-local endpoints must use HTTPS.
- `omnix login`, `link`, `unlink`, `status`, and `logout` are optional. All other local CLI workflows continue to work offline without an Omnix account.

## Remote request handling

- The CLI initiates outbound HTTPS polls; v1 does not open a local network listener. Run `omnix sessions work` to poll once. Each delivered build asks for local confirmation; `--yes` is available for explicitly unattended operation.
- The CLI advertises protocol and capability versions. It accepts only the negotiated `plan`, `build`, `qa`, and `repair` v1 capabilities and rejects unknown versions, unknown fields, and unresolved local references.
- Raw shell strings, arbitrary executable names, arbitrary filesystem paths, environment values, and provider keys are not valid request fields.
- Before execution, the CLI checks credential validity, link identity, request expiry, capability/schema compatibility, replay/idempotency state, and existing local approval requirements.
- Each accepted build request maps to the existing `AutonomousOrchestrator` workflow. The CLI keeps a mode-0600 `.project/omnix_remote_sessions.json` resume cursor with event outbox data; Omnix stores the durable session projection and append-only event ledger.
- If Omnix is unavailable, local-only workflows continue. Remote requests are not inferred from cached browser state; local sync events use a bounded outbox and may later be rejected on expiry/revocation.

## Data sent to Omnix

Only the fields allowed by the canonical RFC and the negotiated v1 schema may be sent: protocol/capability versions, opaque identifiers, lifecycle events, bounded progress, user-requested goal text, selected summaries, provenance references, and artifact manifests. Do not add source upload, provider secrets, environment files, raw logs, prompt transcripts, local paths, or artifact bytes without a separately approved contract.

## Implementation gates

1. Complete the shared contract and schema examples before adding remote behavior. (Complete.)
2. Implement secure device login, credential storage, link/unlink, and revocation before polling for work. (Complete; session/capability APIs remain a later gate.)
3. The capability bridge supports `plan`, `build`, `qa`, and `repair` v1 and requires the explicit `sessions:execute` device scope shown on the browser approval screen. Previously approved devices retain their existing narrower scopes.
4. Add sync/outbox and user-facing status/approval commands without changing standalone command behavior.
5. Run the cross-repository compatibility and security matrix before enabling a beta release.

Related paired workstreams: [Omnix-CLI #47](https://github.com/Bibek200619/Omnix-CLI/issues/47), [#48](https://github.com/Bibek200619/Omnix-CLI/issues/48), [#49](https://github.com/Bibek200619/Omnix-CLI/issues/49), [#50](https://github.com/Bibek200619/Omnix-CLI/issues/50), [#51](https://github.com/Bibek200619/Omnix-CLI/issues/51), [Omnix #219](https://github.com/Bibek200619/Omnix/issues/219), [#220](https://github.com/Bibek200619/Omnix/issues/220), [#221](https://github.com/Bibek200619/Omnix/issues/221), [#222](https://github.com/Bibek200619/Omnix/issues/222), and [#223](https://github.com/Bibek200619/Omnix/issues/223).
