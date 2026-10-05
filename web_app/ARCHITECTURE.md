# Website Architecture

## 1. Recommended Stack

- Next.js with App Router
- React
- TypeScript with strict mode
- Tailwind CSS or CSS Modules with semantic design tokens
- lightweight motion library only where it provides clear value
- Vitest/Jest + Testing Library for component behavior
- Playwright for end-to-end
- axe integration for automated accessibility checks

If the repository already chooses a different frontend stack before implementation, update this document before coding.

## 2. Architecture Goals

- static-first;
- minimal client JavaScript;
- excellent SEO;
- release information can update without rewriting product content;
- product truth represented as data;
- animations isolated from core content;
- no database requirement for v1.

## 3. Suggested Directory

```text
website/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── sitemap.ts
│   └── robots.ts
├── components/
│   ├── ui/
│   ├── marketing/
│   ├── terminal/
│   └── orchestration/
├── content/
│   ├── agents.ts
│   ├── commands.ts
│   ├── providers.ts
│   └── roadmap.ts
├── lib/
│   ├── github.ts
│   ├── release.ts
│   └── constants.ts
├── public/
├── tests/
└── package.json
```

## 4. Rendering Strategy

Default to Server Components/static rendering.

Use Client Components only for:
- navigation disclosure;
- copy-to-clipboard;
- terminal playback controls;
- scroll-aware journey activation;
- interactive tabs/disclosures.

Do not make the entire page client-rendered to enable animation.

## 5. Release Data

Preferred model:
- server-side/build-time fetch from GitHub Releases;
- validate response;
- normalize into internal `ReleaseInfo`;
- cache reasonably;
- static fallback if GitHub is unavailable.

Example internal shape:

```ts
type ReleaseInfo = {
  version: string
  tag: string
  publishedAt: string
  prerelease: boolean
  url: string
  assets: ReleaseAsset[]
}
```

## 6. Content Architecture

Product data must live outside presentational components.

Example:
```ts
type CapabilityStatus = "available" | "roadmap"

type Agent = {
  id: string
  name: string
  status: CapabilityStatus
  summary: string
}
```

This is especially important so future agents cannot accidentally appear as shipped.

## 7. Animation Architecture

The semantic layout exists first.

Animation layer:
- observes scroll/intersection;
- changes visual state only;
- does not insert/remove essential content;
- disables or simplifies under reduced motion.

Do not use animation as a navigation dependency.

## 8. Error Handling

External release failure:
- log server-side where available;
- render preview/fallback state;
- keep GitHub source link usable.

Clipboard failure:
- make text selectable;
- provide manual-copy feedback.

Image/asset failure:
- never hide essential explanatory text behind visuals.

## 9. Build Boundaries

The website must not import Omnix CLI Python runtime code.

Integration occurs through:
- documented commands/capabilities;
- release metadata;
- links.

This keeps website deployment independent of CLI execution.

## 10. Deployment

Recommended:
- Vercel or equivalent static/serverless host;
- preview deployments for PRs;
- production deploy only after CI gates.

No deployment secrets may be exposed to browser bundles.

## 11. Performance Strategy

- optimize/subset fonts;
- avoid large video hero;
- prefer SVG/CSS for diagrams;
- lazy-load below-fold nonessential media;
- keep third-party scripts near zero;
- do not ship animation libraries to sections that do not animate.

## 12. Observability

v1:
- deployment/build errors;
- Core Web Vitals where privacy policy allows;
- no invasive session replay by default.

Any analytics addition requires updating `DATABASE.md`, `SECURITY.md`, and privacy documentation.

## 13. Phase 1 decisions

- Application and dependency files live only in `web_app/website/`.
- Next.js App Router, React, strict TypeScript, Tailwind v4, ESLint, Prettier, Vitest/Testing Library, Playwright and axe. No animation runtime, database, analytics, or provider SDK.
- Page and layout remain Server Components. Domain directories are reserved with `.gitkeep`; reusable primitives begin in Phase 2.
- Pure release normalization is separate from a `server-only` GitHub fetch helper. It supports stable, prerelease, none, and unavailable, validates repository URLs, and never invents an install method. Phase 1 does not fetch releases during page rendering.
- `SITE_URL` is optional and must be a valid HTTPS deployment origin. Canonical/social URLs and sitemap entries are emitted only when configured. The unfinished foundation is always noindex and robots-disallowed; launch must deliberately change this. No fictional production domain.
- `npm run check` supplies CI-ready formatting, lint, typecheck, unit/component, build, and production Playwright checks. Root GitHub workflow wiring is deferred; this phase does not modify paths outside the website workspace.

## 14. Phase 2 decisions

- Eight native-element primitives under `components/ui/`, with token-driven CSS Modules. No new runtime dependencies.
- CopyButton isolates Clipboard API state and manual fallback. Server-rendered code stays selectable without JavaScript.
- `/design-system` is an unlinked, noindex review fixture. Its small action demonstration is a Client Component; the route stays a Server Component.
- The existing homepage adopts Container, Link and Code to exercise composition while retaining its Phase 1 scope.
- Optional Tabs/Disclosure await a real consuming section. No marketing section or CLI change belongs to Phase 2.

## 15. Phase 3 decisions

- The home route remains a Server Component composition. SiteHeader, HeroSection, and HeroTerminal render their essential content on the server; only MobileNav and CopyButton hydrate for user interaction.
- MobileNav is an in-flow disclosure with native button semantics, focus restoration, Escape handling, breakpoint reset, and a no-JavaScript link fallback. It has no modal focus trap or scroll listener.
- The hero uses a static, source-backed five-command walkthrough. It presents commands and website notes as separate text; there is no fake output, autoplay timer, live region, provider request, or animation dependency.
- Because the verified release state is `none`, both hero actions point to the source preview/repository. A stable install CTA remains blocked until release metadata and distribution are verified.

## 16. Phase 4 decisions

- The home route adds only the orchestration journey at `#how-it-works`. Header data gains the valid destination; later proof, roadmap timeline, and download sections remain deferred.
- `OrchestrationJourney` renders content on the server and passes stage bodies as React nodes into `JourneyExplorer`. The client boundary owns user-controlled selection and its explanatory annotation. A media-query subscription places the single annotation near its node on vertical layouts or in a shared panel on wide layouts; no timers, scroll listeners, provider calls, canvas, or new dependencies.
- Five ordered stages distinguish Master memory from explicit Architect invocation. A separate build continuation describes source-preview artifacts/reports; a dashed branch shows only the four confirmed roadmap provider adapters.
- The full route is the accessible semantic equivalent of the diagram. Hydration enables controls without hiding the story. Reduced motion and no-JavaScript rendering remain complete.

## 17. Phase 5 decisions

- Four Server Components add the product-proof sections. Structured content lives in `content/product-proof.ts` and reuses the canonical command and provider modules; only the existing CopyButton hydrates.
- The hero terminal keeps `#hero-cli`, while the complete command index owns the durable `#cli` navigation target. Memory and Architect gain the documented `#memory` and `#architect` targets. The desktop header breakpoint moves to 75 rem to preserve navigation spacing after those targets become valid.
- The command index renders all 26 registered commands. Ten core commands remain open; the remaining 16 use native `details`, preserving keyboard and no-JavaScript operation without a new disclosure component.
- Provider status is a semantic table with explicit Available/Roadmap badges. The Architect pipeline is an ordered list of public implementation stages; it does not expose or simulate chain-of-thought.
