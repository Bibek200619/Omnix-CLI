import { afterEach, expect, it, vi } from "vitest";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { resolveIndexing, resolveSiteUrl } from "@/lib/site";

afterEach(() => vi.unstubAllEnvs());

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
