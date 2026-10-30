# Vercel subpath deployment

Requested launch URL: `https://omni-x.co.in/cli`.

The existing Vercel project `omnix` owns the domain. Its current domain settings
redirect `omni-x.co.in` to `www.omni-x.co.in`, so preserve that policy: the final
CLI canonical destination is `https://www.omni-x.co.in/cli`. GoDaddy registration
does not require a DNS change to add a path. Do not attach or transfer the apex
domain to the CLI website project.

## Verified protected preview — 2026-10-30

After the owner authenticated the Vercel CLI, the isolated `omnix-cli-website`
project was created in the same team as the domain-owning `omnix` project.

- Project ID: `prj_jRQnikTyD9xWPyqtVuUdRagaaocM`; Node 24; root `web_app/website`.
- [Preview at /cli](https://omnix-cli-website-l8b7ovo1z-crazy764gaming-4092s-projects.vercel.app/cli).
- Deployment: `dpl_E18qAKpicXYDPqxoCfmu2s3oN2TN`, READY, API target `staging`.
- Source: exact tested commit `312fc0f9db74fdc08cd1ceaed2ed505414909865`.
- Build environment: `/cli` prefix, canonical `https://www.omni-x.co.in/cli`,
  indexing disabled. Preview feedback/toolbar disabled for this project to retain
  the site's existing CSP without an injected external-script violation.
- Hosted Chromium review passed at 390 and 1440 px: HTTP 200, 30 successful asset
  responses, zero browser console errors, logo/fonts, metadata, menu/Escape,
  installation anchor, social image, and 404 recovery. CSP, noindex, and Vercel's
  HTTPS/HSTS response headers were verified. This is not a field-performance or
  human screen-reader certification.

Vercel Authentication remains enabled. Review through the normal Vercel sign-in;
the short-lived link used for isolated automated QA was revoked and its local
access files removed. The first implicit production-target build was canceled
before completion; subsequent builds used the explicit staging target.

The connector cannot yet access this new project; authenticated CLI operations
were used. The existing domain's project, DNS, and public `/cli` routing have not
been changed. The preview is ready for review, not a public-domain launch.

## CLI project

- Source repository: `Bibek200619/Omnix-CLI`.
- Root directory: `web_app/website`.
- Framework: Next.js; Node 24; install: `npm ci`; build: `npm run build`.
- Build environment: `SITE_URL=https://www.omni-x.co.in`,
  `NEXT_PUBLIC_BASE_PATH=/cli`, `SITE_INDEXABLE=false`.
- Start with an isolated Vercel preview; verify it at `/cli`, including its
  assets and metadata. The prefix is compiled into the build: rebuild after
  changing it. No CLI/provider credentials or database are needed.
- Keep `SITE_INDEXABLE=false` until the human/device and live acceptance checks
  in `LAUNCH.md` pass.

## Existing domain-owning project

After the website PR is reviewed/merged and the CLI deployment has a verified,
stable production project origin, add these two
rewrites to the existing frontend's reviewed configuration, before its fallback
routes. Replace `CLI_ORIGIN` with that actual HTTPS origin, with no trailing slash:

```text
/cli          -> CLI_ORIGIN/cli
/cli/:path*   -> CLI_ORIGIN/cli/:path*
```

Preserve `/cli` in upstream paths. That catch-all includes `/cli/_next/*`,
`/cli/brand/*`, `/cli/social-preview`, `/cli/sitemap.xml`, and review/404 routes.
Do not forward the parent app's `/_next/*` to the CLI project. Preserve query
parameters, content types, caching, response status, and security headers. If
parent authentication middleware runs on all paths, exclude the public `/cli`
zone from login redirection without weakening authentication elsewhere.

The domain-level `/robots.txt` must be reviewed in the parent app. During preview
it must not contradict noindex metadata/headers; before indexing, it must allow
`/cli` while excluding `/cli/design-system` and reference the CLI sitemap. Do not
replace the parent's rules or sitemap with this application's scoped metadata.

## Verification

`npm run check` verifies root development plus an isolated `/cli` production
build/browser rehearsal. `npm run test:subpath` runs just the latter; it rebuilds
`.next` with the deployment prefix and keeps indexing off. Rebuild normally before
returning to root-mode development.

Before routing the public path, verify the actual preview's HTML, canonical and
social URLs, logo/font/CSS/JS requests, image optimizer, keyboard/menu behavior,
anchors, 404 recovery, and security headers. Then verify the same requests through
the public domain and its apex-to-www redirect, as well as the unchanged parent
homepage/sign-in flows. A Cloudflare/protection response is not launch acceptance.

Rollback consists of restoring only the parent app's prior `/cli` routing and
retaining its previous deployment; keep the CLI app noindex. Publication of a
stable CLI installer is a separate decision governed by `RELEASE.md`.
