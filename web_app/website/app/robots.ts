import type { MetadataRoute } from "next";
import { resolveIndexing, resolveSiteUrl } from "@/lib/site";
import { appPath, basePath } from "@/lib/paths";

export default function robots(): MetadataRoute.Robots {
  const origin = resolveSiteUrl(process.env.SITE_URL);
  const indexable = resolveIndexing(origin, process.env.SITE_INDEXABLE);
  const scope = basePath ? [`${basePath}$`, `${basePath}/`] : "/";
  return indexable && origin
    ? {
        rules: {
          userAgent: "*",
          allow: scope,
          disallow: appPath("/design-system"),
        },
        sitemap: new URL(appPath("/sitemap.xml"), origin).href,
      }
    : { rules: { userAgent: "*", disallow: scope } };
}
