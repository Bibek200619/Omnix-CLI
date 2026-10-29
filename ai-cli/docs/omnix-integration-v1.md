# Omnix integration v1: CLI implementation notes

**Status:** Proposed; no Omnix link or remote execution behavior is implemented yet.

The canonical ownership model and protocol contract live in the [Omnix + Omnix CLI Integration RFC v1](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/omnix-cli-integration-rfc-v1.md), tracked by [Omnix #218](https://github.com/Bibek200619/Omnix/issues/218) and [Omnix-CLI #46](https://github.com/Bibek200619/Omnix-CLI/issues/46). The canonical [session request schema](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/v1/session-request.schema.json) and [run event schema](https://github.com/Bibek200619/Omnix/blob/main/docs/integrations/v1/run-event.schema.json) are maintained in Omnix to avoid two sources of truth. This note records how that contract applies to the Python CLI in `ai-cli/`.

## CLI-owned state

- `StateManager` remains the owner of the local `.project/` directory and all detailed project, plan, execution, build, QA, repair, and artifact state.
- Local project files, source, provider configuration/credentials, full prompts/logs, and full artifact contents remain on the device by default.
- Local CLI workflows remain available without login, a linked project, or Omnix connectivity.
- V1 must add a stable local project ID without breaking existing `.project/` files; local run IDs already belong to CLI execution records. Omnix-issued linked-project/session IDs are stored as opaque correlation IDs and do not grant access by themselves.

## Remote request handling

- The CLI initiates outbound HTTPS polls; v1 does not open a local network listener.
- The CLI advertises protocol and capability versions. It accepts only a negotiated `plan`, `build`, `qa`, or `repair` request with a validated typed input targeting the currently linked project.
- Raw shell strings, arbitrary executable names, arbitrary filesystem paths, environment values, and provider keys are not valid request fields.
- Before execution, the CLI checks credential validity, link identity, request expiry, capability/schema compatibility, replay/idempotency state, and existing local approval requirements.
- Each accepted request is mapped to the corresponding local workflow and local run record. Status/progress events are sequenced and idempotent; detailed history remains in `.project/`.
- If Omnix is unavailable, local-only workflows continue. Remote requests are not inferred from cached browser state; local sync events use a bounded outbox and may later be rejected on expiry/revocation.

## Data sent to Omnix

Only the fields allowed by the canonical RFC and the negotiated v1 schema may be sent: protocol/capability versions, opaque identifiers, lifecycle events, bounded progress, user-requested goal text, selected summaries, provenance references, and artifact manifests. Do not add source upload, provider secrets, environment files, raw logs, prompt transcripts, local paths, or artifact bytes without a separately approved contract.

## Implementation gates

1. Complete the shared contract and schema examples before adding remote behavior.
2. Implement secure device login, credential storage, link/unlink, and revocation before polling for work.
3. Add the capability bridge only after server-side session authorization and replay/idempotency semantics exist.
4. Add sync/outbox and user-facing status/approval commands without changing standalone command behavior.
5. Run the cross-repository compatibility and security matrix before enabling a beta release.

Related paired workstreams: [Omnix-CLI #47](https://github.com/Bibek200619/Omnix-CLI/issues/47), [#48](https://github.com/Bibek200619/Omnix-CLI/issues/48), [#49](https://github.com/Bibek200619/Omnix-CLI/issues/49), [#50](https://github.com/Bibek200619/Omnix-CLI/issues/50), [#51](https://github.com/Bibek200619/Omnix-CLI/issues/51), [Omnix #219](https://github.com/Bibek200619/Omnix/issues/219), [#220](https://github.com/Bibek200619/Omnix/issues/220), [#221](https://github.com/Bibek200619/Omnix/issues/221), [#222](https://github.com/Bibek200619/Omnix/issues/222), and [#223](https://github.com/Bibek200619/Omnix/issues/223).
