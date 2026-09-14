import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  // This foundation is not the public launch. Change deliberately at launch review.
  return { rules: { userAgent: "*", disallow: "/" } };
}
