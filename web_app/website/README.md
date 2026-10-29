# Omnix CLI website

Phases 0–7 implementation, with local quality review for Phases 8–11.
Specifications remain in `../*.md`. The homepage contains the header,
hero, truthful command walkthrough, interactive orchestration journey, and four
source-backed product-proof sections, the source-preview roadmap, and verified
source setup. Visit `/design-system` to review the reusable primitives. Final local
quality reviews are recorded in `../QUALITY_REPORT.md`. Human/deployment acceptance
steps remain in `../LAUNCH.md`; indexing defaults to disabled.

## Development

Node >=22.12 and npm are required.

```sh
npm ci
npm run dev
```

## Verification

```sh
npx playwright install chromium firefox webkit
npm run check
```

`check` runs formatting, lint, strict typecheck, Vitest/Testing Library, a production
build, and Playwright against its own production server on port 3100. Keep that
port free. Unit content checks intentionally read `../../ai-cli`: run them from a
full repository checkout. Logo integrity uses the verified official checksum and
also compares the local reference when present. Website builds never import Python.

Individual commands: `lint`, `typecheck`, `test`, `build`, `test:e2e`, and
`format:check`. `review:build` scans built browser assets for credential patterns
and reports all-route JavaScript sizes. Run `build` before standalone `test:e2e`. Browser artifacts are
ignored under `test-results/` and `playwright-report/`.

## Boundaries

- `app/`: Server Components, local variable fonts, token CSS, metadata routes.
- `content/`: source-backed commands, agents, provider boundaries, roadmap.
- `lib/`: centralized identity/URLs, validated deployment origin, pure release
  normalization and server-only GitHub fetch. No install commands are inferred.
- `components/ui/`: native, token-driven primitives. Contracts and usage are in
  `../COMPONENTS.md`. CopyButton owns the clipboard interaction boundary.
- `components/orchestration/`: server-rendered narrative plus user-controlled
  stage selection. The journey has no autoplay, scroll interception, or CLI execution.
- `components/marketing/product-proof-sections.tsx`: memory, provider, complete
  command-index, and Architect evidence sections. Only shared copy controls hydrate.
- `components/marketing/roadmap-section.tsx`: server-rendered capability progression
  and a separate branch for confirmed future provider adapters.
- `components/marketing/install-section.tsx`: verified source setup and explicit
  release/failure states. The async route resolves public GitHub metadata server-side;
  the home route revalidates hourly and preserves setup if GitHub is unavailable.
- `app/design-system/`: noindex review page and a small client button example;
  excluded from the sitemap and marketing navigation.
- `public/brand/omnix-logo.png`: byte-identical copy of `../ref /logo/img.png`.
- No database, analytics, animation library, or browser provider credentials.

Optional `SITE_URL` is an HTTPS origin for canonical/social metadata and sitemap
entries. There is no guessed production domain. Indexing remains disabled until
`SITE_INDEXABLE=true` is deliberately set after the launch checklist. It requires
an HTTPS origin and consistently controls page metadata, response headers, robots,
and sitemap. Review fixtures/404 stay noindex. The production CSP restricts
resources and connections; inline framework bootstrap/styles remain an explicit
static-rendering exception. See `../SECURITY.md` for the tradeoff and host HSTS gate.

The repository's read-only GitHub workflow runs audit and these checks on PRs.
No build secrets, browser provider keys, or release-publish credentials are needed.

GitHub Releases returned no records on 2026-10-30. `0.1.0` is the source package
version. Ten agents exist in preview source; workers store artifacts and QA scores
are model reports. Master chat does not invoke the separate build orchestrator.

Current main exposes 33 executable command entries, including optional Omnix
account linking and `sessions work` / `sessions history`. Remote work requires an
authorized link and compatible server with sessions enabled; history is readable
offline. The website documents these commands but does not execute them or store
account credentials. Content tests compare top-level and grouped registrations
against the Python source so omitted subcommands fail CI.

The source-install commands were verified with Python 3.12.13. See
`../RELEASE.md` for the candidate verification script and tagged-release process.
No candidate has been published and no registry distribution is claimed.

Geist and Geist Mono are locally bundled from their Fontsource packages under the
SIL Open Font License; licenses are included in the installed packages. Original
reference screenshots/recordings are never shipped with the website.
