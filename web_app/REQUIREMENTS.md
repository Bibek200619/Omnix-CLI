# Requirements

## 1. Functional Requirements

### FR-001 — Hero
The home page must contain:
- Omnix CLI identity;
- concise value proposition;
- one primary install/download CTA;
- one secondary GitHub CTA;
- a terminal demonstration using real Omnix commands.

### FR-002 — Product explanation
The site must explain:
- Master Agent;
- persistent project context;
- Architect Agent;
- provider abstraction;
- current preview capabilities versus confirmed roadmap capabilities.

### FR-003 — Interactive orchestration journey
The main product narrative should use a scroll-driven or step-driven visual progression inspired by a game-level journey:
- visitor starts at a project goal;
- goal reaches Master Agent;
- project context connects to specialist commands and the separate build orchestrator; do not imply Master chat dispatches specialists;
- implemented roles appear active;
- confirmed roadmap capabilities appear visually distinct and clearly labeled; no extra future agent roles are currently confirmed.

The experience must remain understandable when animation is disabled.

### FR-004 — CLI demo
The terminal demo must:
- use real commands;
- have deterministic scripted output;
- never pretend to execute code in the visitor’s machine;
- support pause/replay when motion is substantial;
- remain readable without JavaScript animation.

### FR-005 — Command explorer
Provide a compact command section for at least:
- `omnix init`
- `omnix config`
- `omnix models`
- `omnix ping`
- `omnix chat`
- `omnix architect`
- `omnix blueprint`
- `omnix memory`
- `omnix goals`
- `omnix decisions`

### FR-006 — Download / install
The site must expose:
- current stable version;
- Python requirement;
- install command or release artifact;
- platform-specific notes where required;
- checksum/signing information when the release process supports it;
- GitHub Releases fallback.

Until a proper release exists, the UI must say **Preview / source install** rather than pretending a production binary is available.

### FR-007 — GitHub
GitHub source access must be available in the navigation and footer.

### FR-008 — Roadmap
The website must distinguish:
- Available now;
- In progress, if explicitly known;
- Planned.

### FR-009 — Responsive behavior
Support:
- 320 px small mobile;
- modern mobile widths;
- tablet;
- 1280–1440 px desktop;
- large desktop without uncontrolled line length.

### FR-010 — SEO/social metadata
Provide:
- descriptive title;
- description;
- canonical URL;
- Open Graph metadata;
- Twitter/X card metadata;
- favicon/app icons;
- structured data where useful and truthful.

## 2. Non-Functional Requirements

### NFR-001 — Performance
Target:
- Lighthouse Performance ≥ 95 on production build where practical;
- LCP < 2.5 s at p75 target;
- CLS < 0.1;
- INP < 200 ms target;
- no autoplay video required for comprehension.

### NFR-002 — Accessibility
Target WCAG 2.2 AA.

### NFR-003 — Type safety
All website application code should use strict TypeScript.

### NFR-004 — Dependency restraint
Do not add a dependency for behavior that can be implemented clearly with platform/browser features or the existing stack.

### NFR-005 — Motion restraint
Animations must use transform/opacity where possible and respect `prefers-reduced-motion`.

### NFR-006 — Content truth
No fake:
- user counts;
- download counts;
- testimonials;
- logos;
- performance claims;
- company adoption;
- benchmark results.

### NFR-007 — Maintainability
Product capability data, commands, roadmap status and release metadata should be represented as structured data rather than duplicated throughout components.

### NFR-008 — Security
No secrets in client code. External URLs must be allow-listed where practical. See `SECURITY.md`.

## 3. Design Requirements

The site must avoid default AI-landing-page patterns:
- purple/blue gradient blob hero;
- glassmorphism everywhere;
- repeated three-card feature grids;
- random `rounded-3xl` containers;
- glowing borders with no meaning;
- giant empty hero space;
- meaningless floating code particles;
- fake dashboards;
- copied Linear/Vercel visual identity.

The design should feel:
- technical;
- editorial;
- deliberate;
- terminal-native;
- high-contrast;
- precise.

## 4. Content Requirements

Every major marketing statement must be traceable to:
- current repository behavior;
- an explicitly documented roadmap item; or
- a clearly subjective design/value statement.

## 5. Release Dependency

A production download CTA is blocked until the CLI has a reliable distribution channel.

Preferred order:
1. publish a signed/tagged GitHub Release;
2. optionally publish to PyPI if intended;
3. produce platform binaries only if the CLI packaging strategy supports them;
4. have the website consume the release metadata.

The site must fail gracefully if release metadata cannot be fetched.
