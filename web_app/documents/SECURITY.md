<!-- MIRROR FILE: canonical source is ../SECURITY.md. Do not edit independently. -->

# Security

## 1. Security Goals

The public website must:
- not expose credentials;
- not execute arbitrary user code;
- not execute visitor terminal commands;
- not distribute unverified artifacts;
- resist common browser/web attacks;
- make the download chain auditable.

## 2. Secrets

Never place in client code:
- GitHub tokens;
- provider API keys;
- deployment credentials;
- signing keys.

Use deployment/server secrets only where required.

## 3. Download Integrity

The download CTA is security-sensitive.

Before enabling direct binary downloads:
- releases must come from the official repository;
- asset naming must be deterministic;
- platform mapping must be validated;
- checksums should be published;
- signing should be added where feasible;
- the website must never construct arbitrary download hosts from untrusted data.

Until then, prefer official GitHub Release links.

## 4. Supply Chain

- pin lockfiles;
- use automated dependency alerts;
- minimize dependencies;
- review install scripts;
- run CI on pull requests;
- avoid untrusted postinstall behavior;
- keep framework/runtime patched.

## 5. Browser Security

Recommended production headers:
- `Content-Security-Policy`
- `Referrer-Policy`
- `Permissions-Policy`
- `X-Content-Type-Options: nosniff`
- frame restrictions via CSP `frame-ancestors`

Set HSTS at the hosting/domain layer once HTTPS is stable.

CSP should be designed around actual dependencies rather than disabled to satisfy third-party scripts.

## 6. External Links

- use HTTPS;
- use `rel="noopener noreferrer"` when appropriate;
- distinguish external navigation;
- centralize trusted domains.

## 7. XSS

Marketing copy and command data should be source-controlled.

Do not render external Markdown/HTML with unsafe `dangerouslySetInnerHTML`.

If markdown rendering is later introduced:
- sanitize;
- restrict allowed HTML;
- test malicious input.

## 8. GitHub API

Public read requests should not require a client token.

If authenticated server-side requests become necessary for rate limits:
- token stays server-side;
- use minimal read-only permissions;
- rotate and audit credentials.

## 9. Analytics and Privacy

Never collect:
- command contents typed by visitors;
- local repository names;
- file paths;
- API keys;
- clipboard contents.

Avoid session replay by default.

## 10. Security Testing Gate

Before production:
- dependency audit passes;
- no secrets in generated JS;
- headers verified;
- CSP tested;
- external links reviewed;
- release URL logic tested;
- direct download assets verified against expected repository/release.
