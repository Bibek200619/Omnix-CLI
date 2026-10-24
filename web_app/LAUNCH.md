# Launch readiness

The implementation supports a truthful source-preview launch. Public release and
deployment acceptance remain deliberate actions; no production domain or stable
CLI distribution is invented.

## Verified locally — 2026-10-24

- Source-backed product copy, commands, agents, provider states, and source setup.
- Responsive layouts, enlarged text, reduced motion, forced colors, keyboard
  navigation, clipboard recovery, and no-JavaScript content.
- Chromium/mobile, Firefox, and WebKit end-to-end and accessibility-tree checks.
- Independent visual/specification review; official logo preserved and visible in
  the generated social image.
- Production build, security headers, dependency audit, browser asset review,
  first-party credential-pattern scan, and Lighthouse lab review.
- All 12 unique outbound anchor destinations respond successfully.
- Intentional 404 with keyboard recovery and noindex.
- Explicit indexing rehearsal with a synthetic `https://example.com` origin.
  Canonical/social URLs, robots, sitemap, and review-fixture noindex passed. This
  was a local configuration test, not a deployment to that domain.

See `QUALITY_REPORT.md` and `TESTING.md` for evidence and limits.

## Before enabling public indexing

1. Merge the reviewed feature PRs in dependency order. Never push directly to main.
2. Complete a human VoiceOver or NVDA listening pass, including menu dismissal,
   journey selection, provider table, command disclosure, copy feedback/manual
   fallback, and source-setup help. Browser accessibility trees are useful evidence
   but do not certify the spoken experience. Check a real mobile device too.
3. Configure the actual verified HTTPS origin as `SITE_URL`. Confirm the deployed
   host's TLS, redirects, HSTS, security headers, release fallback, and source links.
4. Check the deployed canonical URL, `/social-preview` image, favicon, 404,
   `/robots.txt`, and `/sitemap.xml`. Measure the deployed page's performance.
5. Set `SITE_INDEXABLE=true` only after those checks pass, rebuild/redeploy, and
   confirm the live page is indexable. With the flag absent or false, metadata,
   headers, robots, and sitemap remain in preview mode. The design-system route
   always keeps noindex; 404 pages keep noindex metadata.

The flag fails validation without an HTTPS `SITE_URL`. No analytics, forms,
accounts, provider credentials, or database are required for this website.

## CLI distribution

Source setup is verified. A stable package-registry or direct-download installer
remains gated on the maintainer's tagged publication and artifact verification
in `RELEASE.md`. The website continues to say Preview and does not infer a package
registry command from the project name.

## Recovery

If the deployed review reveals a regression, keep `SITE_INDEXABLE=false`, retain
the previous known-good deployment, and fix through a branch/PR. Recheck relevant
tests and the complete install journey before enabling indexing again. GitHub
metadata failure must retain the source-preview setup and release-page links.
