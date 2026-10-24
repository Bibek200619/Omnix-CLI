import type { MetadataRoute } from "next";
import { resolveIndexing, resolveSiteUrl } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  const origin = resolveSiteUrl(process.env.SITE_URL);
  const indexable = resolveIndexing(origin, process.env.SITE_INDEXABLE);
  return indexable && origin
    ? {
        rules: { userAgent: "*", allow: "/", disallow: "/design-system" },
        sitemap: new URL("/sitemap.xml", origin).href,
      }
    : { rules: { userAgent: "*", disallow: "/" } };
}
