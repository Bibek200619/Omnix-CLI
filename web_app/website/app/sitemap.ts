import type { MetadataRoute } from "next";
import { resolveSiteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = resolveSiteUrl(process.env.SITE_URL);
  return siteUrl ? [{ url: siteUrl.href }] : [];
}
