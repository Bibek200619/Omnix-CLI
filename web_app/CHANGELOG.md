# Changelog

All meaningful changes to the Omnix CLI website specification and implementation should be recorded here.

Use a lightweight Keep-a-Changelog style.

## [Unreleased]

### Vercel subpath launch preparation — 2026-10-30
- Created a protected Vercel preview from the exact tested commit after owner authentication; verified hosted assets, headers, metadata, mobile navigation, and recovery. Recorded deployment evidence and pending public-domain routing in `DEPLOYMENT.md`.
- Added a build-time path prefix for the requested `/cli` destination, shared by navigation, public assets, metadata, sitemap, and recovery links.
- Added an isolated production subpath browser rehearsal alongside root-mode checks, preserving default noindex behavior.
- Corrected canonical URL serialization and Safari pointer-open menu focus so Escape dismissal works consistently under the deployed path.
- Documented the Vercel multi-project routing contract and existing apex-to-www redirect without transferring the parent domain or changing DNS.

### Current CLI reconciliation — 2026-10-30
- Rechecked main after account-linking and remote-session integration; added the missing offline session-history command and corrected session option syntax.
- Derived the command count from product data and extended source-registration checks to every registered subcommand, closing a test gap that missed session history.
- Documented optional account/server requirements and reconciled release instructions with the actual `vVERSION` artifact/attestation workflow. Source preview and public indexing gates remain unchanged.

### Final quality and launch readiness — 2026-10-24
- Completed full-page responsive, keyboard, reduced-motion, high-contrast, accessibility-tree, and cross-browser review; included WCAG 2.1/2.2 A tags and fixed visible-label naming on roadmap links.
- Patched Next.js/config and Vitest plus compatible transitive dependencies; audit now reports zero vulnerabilities. Added production CSP resource restrictions with a documented static-rendering exception.
- Added an intentional 404, a generated social preview using the official logo, footer recovery links, and a deliberate public-indexing gate requiring an HTTPS origin.
- Added bounded build/credential review and read-only pinned-action GitHub PR CI; CI logo verification no longer depends on uncommitted reference assets.
- Recorded independent visual/spec review, local Lighthouse measurements, configuration rehearsal, and remaining human/deployment/publication gates in `QUALITY_REPORT.md` and `LAUNCH.md`.

### Phase 7 — 2026-10-24
- Added a source-preview installation panel with real setup commands, requirements, copy recovery, and troubleshooting.
- Connected the server-side release resolver to the homepage with hourly revalidation and explicit stable/prerelease/none/unavailable states; publication alone does not enable unverified downloads.
- Directed preview actions to the new setup section and added repeatable package verification and a tagged release runbook.

### Phase 6 — 2026-10-24
- Added a source-preview capability timeline and a separate branch for the four confirmed roadmap provider adapters.
- Added implementation links and durable Roadmap navigation, preserving artifact/report and release boundaries.
- Kept the section server rendered with existing primitives and tokens, without new dependencies or animation.

### Phase 5 — 2026-10-05
- Added source-backed project memory, provider, CLI command, and Architect proof sections with durable anchors.
- Added a complete 26-command index with exact CopyButton controls and a native disclosure for the 16 preview-orchestration commands.
- Added explicit OpenAI Available and four provider Roadmap states, plus local-memory and runtime-validation boundaries.
- Moved the hero walkthrough to `#hero-cli` so navigation reaches the complete `#cli` explorer, and widened the desktop-header breakpoint for the expanded valid navigation.
- Added component and browser coverage for command completeness/copying, provider status, Architect claims, accessibility, navigation, and responsive overflow.
- Separated blueprint and memory file ownership, clarified command argument placeholders, and synchronized mobile navigation focus handling with the 75rem desktop breakpoint.

### Phase 4 — 2026-09-16
- Added the signature journey at `#how-it-works`: a connected, selectable goal → Master → context → explicit Architect → blueprint narrative, with a vertical alternative and server-rendered semantic content.
- Kept source-preview build workflows distinct from the four roadmap provider adapters. Rechecked the CLI source and empty GitHub release list; no automatic chat dispatch or runtime validation is implied.
- Added keyboard stage selection, desktop Previous/Next/restart, inline mobile explanations, no-JavaScript rendering, and immediate full-contrast updates without animation dependencies.
- Added the valid navigation target and fixed the existing mobile header resize handler so it only restores focus when navigation owned it.
- Added journey coverage in Chromium, mobile emulation, Firefox, and WebKit; isolated Firefox app data for macOS test launches. The logo smoke check now waits for image decoding.
- Reviewed screenshot/video references, preserved the official logo, and kept subsequent product-proof sections out of scope.

### Phase 3 — 2026-09-15
- Replaced the preview placeholder with a production header and hero, preserving the official logo and source-preview distribution boundary.
- Added accessible mobile navigation and a static five-command walkthrough with explicit configuration, website narration, and copy recovery.
- Rechecked CLI behavior and the empty public release list; no download command or generated output is invented.
- Kept later homepage sections out of scope and retained noindex until launch review.

### Phase 2 — 2026-09-15
- Added native Container, Section, Button, Link, Badge, Code, CodeBlock, and CopyButton primitives with shared semantic styling.
- Added a noindex component review route and documented primitive props, state, keyboard and clipboard fallback contracts.
- Reused primitives in the existing preview shell. Deferred optional Tabs/Disclosure and all marketing sections.
- Added component and browser coverage for controls, status labels, copy recovery, code overflow, and accessibility.

### Phase 0 and Phase 1 — 2026-09-14
- Inspected Python CLI source and separated its preview capabilities from the Node MVP.
- Corrected stale roadmap labels: Planner, workers, Integration, QA, Repair, execution coordination, and build orchestration already exist in source. Documented artifact/report limitations and the lack of Master chat dispatch.
- Confirmed Python >=3.12, package 0.1.0, 26 registered commands, one live provider adapter, four placeholders, and no public GitHub releases.
- Reviewed all useful local reference assets and preserved the official logo.
- Established a static Next.js foundation, semantic design tokens, structured product data, release state helpers, and automated quality commands under `website/`.
- Reserved subsequent UI work for Phase 2 onward; no final homepage or install CTA.

### Added
- Initial product specification.
- Website requirements.
- Information architecture.
- User-flow definitions.
- Design system.
- Component contracts.
- Frontend architecture.
- GitHub release/API integration contract.
- No-database decision for v1.
- Security requirements.
- Accessibility requirements.
- Testing strategy.
- Phased execution plan.
- Reference and originality rules.

### Decisions
- `web_app/*.md` is the canonical documentation source.
- `web_app/documents/*.md`, when present, is a secondary mirror only.
- Website v1 is static-first and does not require a database.
- Production download CTA depends on a verified CLI release/distribution path.
- Current and roadmap agent capabilities must be visually and semantically distinct.
- The “Angry Birds” influence is limited to progression/journey structure, not visual copying.

## Change Entry Template

```md
## [YYYY-MM-DD]

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Removed
- ...

### Decision
- ...
```
