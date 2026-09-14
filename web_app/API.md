# API and External Integrations

## 1. Scope

Website v1 does not expose a public Omnix backend API.

Its primary external data dependency is GitHub release/repository metadata.

## 2. GitHub Release Integration

### Purpose
Resolve:
- latest stable version;
- tag;
- publish date;
- release URL;
- downloadable assets;
- prerelease status.

### Source
GitHub Releases API for the official Omnix CLI repository.

### Rules
- fetch server-side/build-time where possible;
- never depend on a browser GitHub token;
- validate the response;
- cache;
- fail safely.

### No release case
Current state may contain no GitHub Release.

Expected normalized state:

```ts
type ReleaseState =
  | { kind: "stable"; release: ReleaseInfo }
  | { kind: "prerelease"; release: ReleaseInfo }
  | { kind: "none" }
  | { kind: "unavailable" }
```

The UI must explicitly support `none`.

## 3. Installation Metadata

Do not infer an install command from a package name unless distribution has been verified.

Installation data should be manually versioned or generated from the release pipeline.

Example:

```ts
type InstallMethod = {
  id: "pipx" | "uv" | "pip" | "binary" | "source"
  label: string
  command: string
  platforms?: string[]
  minimumPython?: string
  stable: boolean
}
```

## 4. Repository Links

Centralize:
- repository URL;
- issues URL;
- releases URL;
- docs URL if created.

Never scatter hard-coded GitHub URLs across components.

## 5. Analytics

No analytics API is required for v1.

If analytics are later introduced:
- prefer privacy-conscious collection;
- document every event;
- avoid sending CLI commands, repository names, terminal input, or other potentially sensitive developer content;
- update privacy/security docs before release.

## 6. Contact / Feedback

Do not add a form backend in v1 unless there is a clear owner for submissions and privacy handling.

Prefer GitHub Issues/Discussions for early-stage product feedback.

## 7. API Acceptance Criteria

- no secret keys in browser;
- release fetch failure does not break page rendering;
- external responses validated;
- links use HTTPS;
- no unsupported release is labelled stable;
- platform asset mapping has tests before enabling direct downloads.

## 8. Phase 1 release boundary

Repository: `Bibek200619/Omnix-CLI`. The public Releases API returned `[]` on 2026-09-14; snapshot state is `none`. Package version `0.1.0` is not a release version claim.

The helper normalizes only published, non-draft records, prefers a stable release over a prerelease, and selects the newest publish date within that channel. Malformed responses, HTTP failures, timeouts, or untrusted URLs produce `unavailable`, distinct from an empty release list. Release and asset URLs must belong to the official GitHub repository. Unverified assets and install commands are never promoted to download actions. Source navigation remains available in every state.

The foundation page is static and independent of this fetch. A future InstallPanel must additionally require manually verified distribution metadata before showing any stable-download CTA, even if a stable GitHub tag exists.
