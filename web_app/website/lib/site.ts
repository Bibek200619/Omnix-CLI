export function resolveSiteUrl(value: string | undefined): URL | undefined {
  if (!value?.trim()) return undefined;
  const url = new URL(value);
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      "SITE_URL must be an HTTPS origin without credentials, a path, query, or fragment.",
    );
  }
  return url;
}

export function resolveIndexing(
  siteUrl: URL | undefined,
  value: string | undefined,
): boolean {
  if (!value || value === "false") return false;
  if (value !== "true")
    throw new Error("SITE_INDEXABLE must be true or false.");
  if (!siteUrl)
    throw new Error("SITE_INDEXABLE=true requires a verified HTTPS SITE_URL.");
  return true;
}
