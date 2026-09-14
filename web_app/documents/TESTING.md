<!-- MIRROR FILE: canonical source is ../TESTING.md. Do not edit independently. -->

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
- future roles = roadmap;
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
