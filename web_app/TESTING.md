# Testing Strategy

## 1. Philosophy

The website is small enough that quality should be high.

Testing should protect:
- product truth;
- release/download behavior;
- accessibility;
- responsive navigation;
- interactive storytelling;
- performance.

## 2. Static Checks

Every PR:
- TypeScript strict check;
- lint;
- formatting check;
- production build;
- dead-link check where practical.

## 3. Unit / Component Tests

Prioritize behavior, not implementation details.

Test:
- CopyButton success/failure;
- InstallPanel states;
- release normalization;
- navigation disclosure;
- tabs/disclosures;
- roadmap status rendering;
- reduced-motion branches where feasible;
- platform asset mapping if direct downloads exist.

## 4. Integration Tests

Test the page with realistic structured content.

Scenarios:
- stable release available;
- prerelease only;
- no release;
- GitHub API unavailable.

The home page must render in all four.

## 5. End-to-End

Playwright scenarios:

### E2E-001 — Main journey
- load home;
- click navigation anchors;
- inspect CLI section;
- reach Download;
- copy install command.

### E2E-002 — Mobile
- open mobile viewport;
- open/close navigation;
- navigate to Download;
- verify no page-level horizontal overflow.

### E2E-003 — Keyboard
- Tab through interactive controls;
- verify visible focus;
- operate mobile menu/tabs/disclosures.

### E2E-004 — Reduced motion
- emulate reduced motion;
- verify full content remains present.

### E2E-005 — Release fallback
- mock failed release request;
- ensure page still offers GitHub/source fallback.

## 6. Visual Regression

Useful for:
- hero;
- orchestration journey;
- terminal;
- download section.

Do not make pixel snapshots so brittle that every copy change is painful.

Test representative:
- mobile;
- desktop;
- reduced motion/static state.

## 7. Accessibility

Automated axe on:
- home;
- open mobile nav;
- command explorer states;
- install tabs.

Manual accessibility remains required.

## 8. Performance

Run Lighthouse against production build.

Watch:
- LCP;
- CLS;
- INP;
- JavaScript payload;
- font loading;
- third-party scripts.

A decorative animation is not allowed to cost a meaningful performance regression.

## 9. Content Truth Tests

Where product data is structured, add assertions:
- Architect status = available;
- implemented source agents = available with preview scope;
- unimplemented provider generation adapters = roadmap;
- required Python version = documented value;
- current commands list includes only actual CLI commands;
- no “stable download” state when there is no release.

## 10. Browser Matrix

Minimum:
- latest Chrome;
- latest Firefox;
- latest Safari;
- Chromium mobile emulation;
- real iOS/Android smoke test before major public launch if available.

## 11. Release Gate

Production is blocked if:
- build fails;
- TypeScript/lint fails;
- critical/serious axe violations exist;
- main E2E fails;
- download URL is unverified;
- current/roadmap product status is incorrect;
- mobile horizontal overflow exists;
- Lighthouse reveals a major regression without explicit review.

## 12. Phase 1 verification scope

Run from `website/`: `npm run check` (format, lint, strict typecheck, unit/component tests, build, production Playwright). Install the Chromium test browser first with `npx playwright install chromium`. No root CI workflow is added in this workspace-only phase; these commands are ready for subsequent CI wiring.

Release normalization and mocked fetch tests cover stable, prerelease, none, unavailable, draft records, malformed data, and untrusted links. The static foundation has no InstallPanel and is independent of release fetches; full install-state page integration tests belong to Phase 7.

Product tests compare content against actual Python command registrations and implementation files. Playwright checks desktop/mobile, 320 px reflow with enlarged text, keyboard skip/focus, reduced motion, forced colors, JavaScript-disabled rendering, assets/fonts, metadata, and axe. Full cross-browser and human screen-reader acceptance remain launch gates, not claims made by an automated Chromium smoke test.

## 13. Phase 2 verification scope

Component tests protect native button semantics, loading/disabled behavior, safe links, explicit status labels, labelled sections/code, exact clipboard output, denied/missing clipboard fallback, and retry behavior. Browser tests exercise the component review page with keyboard activation, horizontal code scrolling, mobile reflow, reduced motion, forced colors, axe, and no-JavaScript readable code. Screenshot inspection verifies default and interaction states against the tokens. Keep the Phase 1 checks as regression coverage.

## 14. Phase 3 verification scope

Component tests cover hero product truth, valid anchor destinations, mobile disclosure state, Escape/focus restoration, destination focus, the complete command data set, and the absence of fabricated terminal output. Browser tests cover 320/375/390/768/1024/1280/1440 px layouts, desktop/mobile navigation, breakpoint reset, keyboard focus, outside tabbing, reduced motion, exact workflow copying, no stable download CTA, no-JavaScript navigation, forced colors, axe, and screenshot review. At Phase 3 completion, the production check ran 54 Vitest tests and 50 Playwright tests across Chromium and mobile Chromium emulation.

## 15. Phase 4 verification scope

Journey tests cover the complete semantic route, selected-stage detail, Previous/Next/restart, source-backed claims, and explicit provider roadmap boundaries. Browser checks cover seven widths (320–1440 px), keyboard operation, focus preservation on resize, enlarged text, no JavaScript, reduced motion, forced colors, valid navigation targets, and axe. The journey suite also runs in Firefox and WebKit; install all three browser engines with `npx playwright install chromium firefox webkit`. Existing Chromium/mobile regressions remain in the default check. Browser engines and accessibility-tree checks do not replace real-device or human screen-reader acceptance before launch.

On macOS, Playwright setup uses a disposable Firefox app-data directory and removes it after the suite. This avoids the macOS 27 direct-launch/profile failure tracked in [Mozilla bug 2060476](https://bugzilla.mozilla.org/show_bug.cgi?id=2060476) without accessing personal browser data or changing OS permissions. Test browser profiles remain isolated in all engines.

Phase 4 verification (2026-09-16): formatting, lint, strict typecheck, all 58 Vitest tests, production build, and all 102 Playwright tests passed. Screenshot review covered the seven specified widths and keyboard/selected states. A local production Lighthouse run scored Performance 98, Accessibility 100, and Best Practices 100 (LCP 2.4 s, CLS 0, TBT 30 ms). These are lab measurements, not field performance guarantees.
