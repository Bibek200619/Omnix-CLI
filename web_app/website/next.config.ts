import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";
import { resolveIndexing, resolveSiteUrl } from "./lib/site";

const indexable = resolveIndexing(
  resolveSiteUrl(process.env.SITE_URL),
  process.env.SITE_INDEXABLE,
);
const development = process.env.NODE_ENV === "development";
// ISR needs Next's inline bootstrap. No eval or external resources in production.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${development ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  `connect-src 'self'${development ? " ws: wss:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "form-action 'none'",
].join("; ");

const nextConfig: NextConfig = {
  turbopack: { root: fileURLToPath(new URL(".", import.meta.url)) },
  outputFileTracingRoot: fileURLToPath(new URL(".", import.meta.url)),
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value: csp,
          },
          {
            key: "X-Robots-Tag",
            value: indexable ? "index, follow" : "noindex, nofollow",
          },
        ],
      },
      {
        source: "/design-system/:path*",
        headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }],
      },
    ];
  },
};

export default nextConfig;
