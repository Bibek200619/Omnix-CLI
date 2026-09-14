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
