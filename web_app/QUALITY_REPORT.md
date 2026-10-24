# Website quality review — 2026-10-24

Scope: the Next.js website, its product-data/release boundaries, production browser
assets, and the local candidate-verification script. No CLI source or unrelated
local memory/reference files were changed.

## Security findings

| Dependency audit severity | Earlier lockfile | After repair |
|---|---:|---:|
| Critical | 1 | 0 |
| High | 6 | 0 |
| Moderate | 2 | 0 |
| Low / informational | 0 | 0 |
| Total affected packages | 9 | 0 |

High confidence: the old pinned Next.js and several tooling/transitive packages
matched npm advisories. The authorized quality repair pins Next.js and
eslint-config-next 16.4.3, Vitest 5.0.5, and refreshes compatible transitive fixes.
No force upgrade or new runtime dependency was used. Exploitability depends on
the relevant framework features and host; this report does not claim the website
was exploited. Primary Next.js advisories:
[image optimization](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw),
[cached typed arrays](https://github.com/vercel/next.js/security/advisories/GHSA-673q-mjm6-r5xr).

Pinned-action, read-only PR CI runs lockfile installation, browser setup, audit,
the full check, and build review. Official logo integrity uses its verified
checksum even when local reference files are absent from the checkout.

Application data-flow review found no additional actionable vulnerability: the
only external data fetch targets the fixed official GitHub repository, validated
release URLs feed escaped React text/links, no untrusted HTML is rendered, and
there are no user accounts, forms, database queries, provider keys, or executable
browser commands. The release verifier uses argument-vector subprocesses, a
resolved tracked commit, safe archive extraction, and temporary environments.

Production CSP restricts sources, connections, embedding, and form actions. Inline
framework scripts/styles are a documented static/ISR exception, so this is not a
strict nonce policy or a substitute for safe rendering. Production disallows eval;
development alone permits Next tooling's eval/WebSockets. HSTS requires the real
HTTPS host. See `SECURITY.md`.

`npm run review:build` scans first-party source and all generated browser text
assets for high-confidence credential patterns, printing paths/counts only. It
found no matching credentials. This bounded scan is not a guarantee against every
possible secret or runtime vulnerability.

## Responsive and accessibility review

The complete page was checked at 320/375/390/768/1024/1280/1440px, with desktop
200% text enlargement and narrow reflow, keyboard operation, reduced motion,
forced colors, no JavaScript, and browser accessibility-tree output. Header links
can wrap when text grows. Manual Chrome keyboard/native-accessibility inspection
confirmed setup destination focus and expanded help/recovery content.

Lighthouse found a visible-label/accessibility-name mismatch in roadmap source
links that the earlier axe tag subset omitted. Labels now include the visible
"View implementation" text, and the complete-page axe check includes WCAG 2.1 A
and 2.2 A tags alongside AA. No speech-output or human screen-reader certification
is claimed. That acceptance pass remains in `LAUNCH.md`.

## Independent design review

Standards reviewer: no actionable standards/maintainability finding. Spec/visual
reviewer: one P2 finding, now closed. The initial social PNG silently dropped its
logo; numeric image dimensions and explicit sizing fixed it. A browser regression
check now verifies dimensions and blue brand pixels as well as PNG validity.

Both reviewers inspected full desktop/mobile screenshots and found no additional
generic AI-pattern flags. The ledger, provider table, command index, Architect
pipeline, and roadmap use different structures to explain real content. The
palette, restrained accent, official logo, and connected journey follow the
documented Omnix direction. No copied brand composition, glow/blob decoration,
fake dashboard, invented metric, testimonial, or future-agent promise was added.

## Performance lab evidence

Lighthouse 13.5.0, isolated Chrome for Testing, mobile simulated throttling, local
production build:

| Run | Performance | Accessibility | Best Practices | SEO |
|---|---:|---:|---:|---:|
| Preview before final label fix | 98 | 100 | 100 | 66 |
| Configured indexing rehearsal after fixes | 100 | 100 | 100 | 100 |

The configured run used the synthetic example.com origin locally, not a live
deployment. LCP 1.9s, TBT 20ms, CLS 0. It transferred about 246KB in 13 requests,
including about 150KB of scripts and 54KB of local fonts; no third-party requests
were made. All-route compressed JavaScript is about 191KB, which is not the same
as a single page's transferred payload. Preview SEO is intentionally reduced by
noindex. Lighthouse scores and these timings are lab observations, not field
performance, INP, or accessibility certification.

## Publication boundary

Mechanical configuration checks passed for canonical/social URLs, robots,
sitemap, design-system noindex, and 404 recovery. All 12 unique outbound links
returned successful HTTP statuses. The actual HTTPS deployment, human listening
pass, real-device acceptance, and deliberate indexing enablement remain launch
gates. A stable CLI distribution remains a separate maintainer publication gate;
the verified source-preview installation path works today.
