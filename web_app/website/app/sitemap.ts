import type { MetadataRoute } from "next";
import { resolveIndexing, resolveSiteUrl } from "@/lib/site";
import { appPath } from "@/lib/paths";

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = resolveSiteUrl(process.env.SITE_URL);
  return siteUrl && resolveIndexing(siteUrl, process.env.SITE_INDEXABLE)
    ? [{ url: new URL(appPath("/"), siteUrl).href }]
    : [];
}
