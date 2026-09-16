# Execution Plan

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

---

## Phase 7 — Release pipeline / download experience

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

- bundle review;
- image/font optimization;
- headers/CSP;
- dependency audit;
- remove unused JS;
- verify external URLs;
- verify generated bundle contains no secrets.

---

## Phase 10 — AI-smell review

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
