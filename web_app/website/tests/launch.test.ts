import { afterEach, expect, it, vi } from "vitest";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { resolveIndexing, resolveSiteUrl } from "@/lib/site";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

it("keeps preview indexing disabled even with a configured origin", () => {
  const origin = resolveSiteUrl("https://example.com");
  expect(resolveIndexing(origin, undefined)).toBe(false);
  expect(resolveIndexing(origin, "false")).toBe(false);
  vi.stubEnv("SITE_URL", "https://example.com");
  vi.stubEnv("SITE_INDEXABLE", "false");
  expect(robots()).toEqual({ rules: { userAgent: "*", disallow: "/" } });
  expect(sitemap()).toEqual([]);
});

it("requires an explicit launch flag and HTTPS origin for indexing", () => {
  expect(() => resolveIndexing(undefined, "true")).toThrow(/requires/);
  expect(() => resolveIndexing(undefined, "yes")).toThrow(/true or false/);
  vi.stubEnv("SITE_URL", "https://example.com");
  vi.stubEnv("SITE_INDEXABLE", "true");
  expect(robots()).toEqual({
    rules: { userAgent: "*", allow: "/", disallow: "/design-system" },
    sitemap: "https://example.com/sitemap.xml",
  });
  expect(sitemap()).toEqual([{ url: "https://example.com/" }]);
});

it.each(["false", "true"])(
  "scopes subpath robots and sitemap when indexing is %s",
  async (indexing) => {
    vi.stubEnv("SITE_URL", "https://www.omni-x.co.in");
    vi.stubEnv("NEXT_PUBLIC_BASE_PATH", "/cli");
    vi.stubEnv("SITE_INDEXABLE", indexing);
    vi.resetModules();
    const { default: scopedRobots } = await import("@/app/robots");
    const { default: scopedSitemap } = await import("@/app/sitemap");
    if (indexing === "false") {
      expect(scopedRobots()).toEqual({
        rules: { userAgent: "*", disallow: ["/cli$", "/cli/"] },
      });
      expect(scopedSitemap()).toEqual([]);
    } else {
      expect(scopedRobots()).toEqual({
        rules: {
          userAgent: "*",
          allow: ["/cli$", "/cli/"],
          disallow: "/cli/design-system",
        },
        sitemap: "https://www.omni-x.co.in/cli/sitemap.xml",
      });
      expect(scopedSitemap()).toEqual([
        { url: "https://www.omni-x.co.in/cli" },
      ]);
    }
  },
);
