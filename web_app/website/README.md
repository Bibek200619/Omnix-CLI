# Omnix CLI website foundation

Phases 0–4. Specifications remain in `../*.md`. The homepage contains the header,
hero, truthful command walkthrough, and interactive orchestration journey. Visit `/design-system` to review the
reusable primitives. Later homepage sections remain unbuilt; indexing stays disabled.

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
port free. Unit content checks intentionally read `../../ai-cli` and the original
logo: run them from a full repository checkout. Website builds never import Python.

Individual commands: `lint`, `typecheck`, `test`, `build`, `test:e2e`, and
`format:check`. Run `build` before standalone `test:e2e`. Browser artifacts are
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
- `app/design-system/`: noindex review page and a small client button example;
  excluded from the sitemap and marketing navigation.
- `public/brand/omnix-logo.png`: byte-identical copy of `../ref /logo/img.png`.
- No database, analytics, animation library, or browser provider credentials.

Optional `SITE_URL` is an HTTPS origin for canonical/social metadata and sitemap
entries. There is no guessed production domain. Even with it configured, the
unfinished shell remains noindex with robots disallowed. Launch review must
explicitly enable indexing. Current CSP restricts embedding, object and base URLs;
a complete script policy is deferred to the production security phase.

GitHub Releases returned no records on 2026-09-16. `0.1.0` is the source package
version. Ten agents exist in preview source; workers store artifacts and QA scores
are model reports. Master chat does not invoke the separate build orchestrator.

Geist and Geist Mono are locally bundled from their Fontsource packages under the
SIL Open Font License; licenses are included in the installed packages. Original
reference screenshots/recordings are never shipped with the website.
