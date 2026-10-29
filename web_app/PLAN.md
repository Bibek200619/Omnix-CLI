# Execution Plan

Vercel path preparation (2026-10-30): the owner confirmed `omni-x.co.in/cli`.
The optional build-time `/cli` prefix, scoped metadata/assets/native links, and
separate 20-test deployment rehearsal are complete. The existing Vercel apex-to-www
redirect is preserved. Project creation currently requires authenticated write
access; `DEPLOYMENT.md` records the exact routing/build contract and pending live
acceptance. Do not mark the public website launched from local test results.

Current-source reconciliation (2026-10-30): the website phases below are implemented
and the reviewed work is merged through PR #61. Newer CLI integrations on main
required a follow-up command-index correction: all 33 executable entries, including
offline session history, are now represented, with optional account/server gates.
The website and current Python package checks pass; current release instructions
follow the actual artifact workflow. Remaining launch work is the human/device,
real HTTPS deployment, indexing, and public distribution acceptance in `LAUNCH.md`
and `RELEASE.md`, not additional homepage sections.

## Working Model

The implementation agent does not redesign the product while coding.

For each milestone:

1. Read relevant specification.
2. Write a micro-plan.
3. Implement the smallest coherent slice.
4. Run static checks and targeted tests.
5. Fix failures.
6. Run integration/E2E relevant to the slice.
7. Perform visual review.
8. Commit only when green.
9. Update `CHANGELOG.md` when behavior/spec changes.
10. Move to the next milestone.

If a test fails, create a small repair plan and loop until green. Do not stack unrelated fixes.

---

## Phase 0 — Repository and release discovery

### Goal
Establish the website against the real CLI.

Tasks:
- confirm canonical repository;
- confirm CLI version;
- confirm Python requirement;
- confirm actual commands;
- confirm current agent/capability status;
- confirm provider status;
- inspect release/distribution state;
- decide source/install strategy for preview launch.

Exit criteria:
- no marketing claim is unsupported;
- download state is explicitly defined.

---

## Phase 1 — Website scaffold

Tasks:
- open `website/`;
- configure Next.js + TypeScript;
- strict lint/type rules;
- test runner;
- Playwright;
- base metadata;
- CSS token foundation;
- CI commands.

Do not build marketing sections yet.

Exit:
- blank shell builds and tests green.

---

## Phase 2 — Design-system primitives

Build:
- Container
- Section
- Button
- Link
- Badge
- Code/CodeBlock
- CopyButton
- Tabs/Disclosure if required

Exit:
- primitives documented;
- keyboard/focus states complete;
- no arbitrary styling patterns.

---

## Phase 3 — Header + hero

Build:
- responsive header;
- primary CTA;
- GitHub CTA;
- hero copy;
- real terminal demonstration.

Terminal content should use a real Omnix flow, for example:
`omnix init` → configure → `omnix chat` → `omnix architect` → `omnix blueprint`.

Do not imply code generation from Architect if current product does not do it.

Exit:
- strong first viewport at mobile and desktop;
- reduced-motion state works;
- no generic AI hero patterns.

---

## Phase 4 — Signature orchestration journey

Build:
- goal node;
- Master Agent;
- project state/context;
- Architect Agent;
- confirmed roadmap capabilities (currently additional live provider adapters);
- responsive vertical alternative;
- accessible semantic equivalent.

This is the section that should give the site its recognizable identity.

Exit:
- story understandable without animation;
- available vs roadmap unmistakable;
- 60fps-like smoothness on reasonable hardware without excessive JS.

Implementation: `OrchestrationJourney` and `JourneyExplorer` provide user-controlled progression with static semantic content. Wide screens use a connected horizontal route and shared explanation; vertical layouts place detail beneath the selected stage. `#how-it-works` is a valid header target. Phase 5 and later sections remain deferred.

---

## Phase 5 — Product proof

Build:
- Memory/context section;
- Provider section;
- Command explorer;
- Architect flow.

Use real content.

Exit:
- every command/capability verified against source;
- copy controls work;
- mobile layouts complete.

Implementation: four server-rendered product-proof sections cover local project memory, provider implementation status, all 26 registered commands, and the Architect pipeline. Native disclosure keeps the 16 orchestration commands compact, while shared copy controls provide exact command copying. Durable anchors now exist for `#memory`, `#cli`, and `#architect`.

---

## Phase 6 — Roadmap

Build a restrained phase timeline.

Current:
- foundation;
- provider layer;
- Master Agent;
- Architect Agent;
- Planner and worker artifact generation;
- integration, QA reports, repair artifacts;
- dependency-aware execution and build orchestration (source preview).

Future:
- live Anthropic, Google, OpenRouter, and DeepSeek adapters.

Discovery corrected the former phase-3-only capability list; see `PRODUCT.md`. Available source workflows are not a stable release or proof of runnable generated applications. No additional roadmap agent roles are confirmed.

Exit:
- no future feature appears shipped.

Implementation: a static seven-stage source-preview timeline, a separate provider-derived future branch, implementation links, and valid Roadmap navigation. Verification on 2026-10-24 passed source evidence/status checks, keyboard focus, narrow/zoom reflow, reduced motion, no-JavaScript rendering, and desktop/mobile screenshot review. Phase 6 is complete; Phase 7 remains next.

---

## Phase 7 — Release pipeline / download experience

Implementation: verified source setup and Python packaging in isolation; added a repeatable candidate-verification script and a tagged release runbook without publishing a release. The server release resolver now feeds a source-preview installation panel with all four metadata states. Preview navigation, copying, failure recovery, reflow, no-JavaScript, and keyboard behavior passed verification on 2026-10-24. The current preview path is complete; public tagged distribution requires the maintainer steps in `RELEASE.md` before a stable installer can be enabled. Phase 8 remains next.

### Track A — CLI repository
Create or finalize:
- tagged release process;
- build/package verification;
- checksums/signing when applicable;
- release notes;
- optional package registry publish.

### Track B — Website
Build:
- release resolver;
- stable/prerelease/no-release states;
- install tabs;
- copy command;
- GitHub Releases fallback.

Exit:
- CTA downloads/installs a verified artifact or accurately says Preview.

---

## Phase 8 — Responsive and accessibility pass

Review plan: inspect all sections together at the specified widths, enlarged text, keyboard navigation, no JavaScript, reduced motion, forced colors, and browser accessibility trees. Extend cross-browser coverage to the final page and repair only observed issues.

Result (2026-10-24): complete-page checks pass in Chromium/mobile, Firefox, and WebKit, including enlarged text and all WCAG A/AA axe tag groups. Native Chrome keyboard/accessibility-tree review passes. Roadmap link names now include their visible labels. A human VoiceOver/NVDA listening pass remains an acceptance gate in `LAUNCH.md`; automated tree inspection is not reported as speech certification.

Review every section:
- 320 px;
- 375/390 px;
- tablet;
- 1280 px;
- 1440+ px;
- 200% zoom;
- keyboard;
- screen reader smoke test;
- reduced motion.

No new features.

---

## Phase 9 — Performance and security

Review plan: audit and patch dependencies, measure the production page with Lighthouse, inspect compressed browser assets and resource requests, tighten compatible security headers, and scan source/generated browser assets for credential patterns. Retain static rendering and document CSP exceptions.

Result (2026-10-24): patched dependencies, npm audit reports zero vulnerabilities, resource-restricting CSP passes browser tests, and the bounded build scan finds no credential patterns. Local Lighthouse reports Performance 98 in preview and 100 in the configured launch rehearsal. Read-only, pinned-action PR CI now runs audit, the full check, and build review. See `QUALITY_REPORT.md` for measurements and limits.

- bundle review;
- image/font optimization;
- headers/CSP;
- dependency audit;
- remove unused JS;
- verify external URLs;
- verify generated bundle contains no secrets.

---

## Phase 10 — AI-smell review

Result (2026-10-24): independent standards and spec/visual reviewers inspected the final desktop/mobile output. Standards findings: none. One social-image logo rendering defect was fixed and independently rechecked; no additional generic AI-pattern flags remain. The final brand-image test protects its dimensions and visible logo, alongside the official PNG checksum.

A separate reviewer should flag:
- generic three-card layouts;
- excessive gradients/glow;
- repetitive rounded boxes;
- filler copy;
- fake metrics/social proof;
- generic headings;
- meaningless animation;
- duplicated Tailwind strings;
- inconsistent spacing;
- decorative visuals unrelated to Omnix.

Every flag must be either fixed or justified.

---

## Phase 11 — Launch review

Review plan: add an intentional 404/recovery path, verify metadata and the official social image/logo, and provide an explicit indexing gate tied to a configured HTTPS production origin. Keep review fixtures noindex even when marketing indexing is enabled. Record external launch gates without inventing a domain or a stable CLI release.

Result (2026-10-24): local mechanical review passes, including 404, social image, all 12 outbound links, and indexing/canonical/robots/sitemap rehearsal with a synthetic HTTPS origin. Source-preview implementation is ready for final acceptance. Actual HTTPS deployment verification, human screen-reader/real-device acceptance, deliberate indexing enablement, and stable CLI publication remain external gates documented in `LAUNCH.md` and `RELEASE.md`; the site is not declared publicly launched.

Checklist:
- product truth verified;
- version/install verified;
- links verified;
- metadata/social previews;
- favicon;
- sitemap/robots;
- accessibility;
- E2E;
- performance;
- error/fallback states;
- 404 if needed;
- final production preview.

---

## Definition of Done

A section is done only when:
- content is final enough to ship;
- responsive;
- keyboard accessible;
- reduced-motion compatible;
- uses design tokens;
- tested where behavior exists;
- visually reviewed;
- truthful to current CLI.

The website is done only when the install/download journey works end-to-end.
