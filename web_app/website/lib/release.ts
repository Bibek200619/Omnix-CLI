import { links } from "@/lib/constants";

export type ReleaseAsset = { name: string; url: string; size: number };
export type ReleaseInfo = {
  tag: string;
  publishedAt: string;
  url: string;
  assets: ReleaseAsset[];
};
export type ReleaseState =
  | { kind: "stable"; release: ReleaseInfo }
  | { kind: "prerelease"; release: ReleaseInfo }
  | { kind: "none" }
  | { kind: "unavailable" };

export const releaseSnapshot = {
  state: { kind: "none" } satisfies ReleaseState,
  checkedAt: "2026-09-14",
  source: `${links.releases}`,
} as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function trustedUrl(value: unknown, prefix: string): value is string {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      !url.username &&
      !url.password &&
      !url.search &&
      !url.hash &&
      url.href.startsWith(prefix) &&
      url.href.length > prefix.length
    );
  } catch {
    return false;
  }
}

/** A release record proves publication only, never installability or artifact integrity. */
export function normalizeReleases(payload: unknown): ReleaseState {
  if (!Array.isArray(payload)) return { kind: "unavailable" };
  const candidates: { prerelease: boolean; release: ReleaseInfo }[] = [];
  for (const item of payload) {
    if (!isRecord(item) || typeof item.draft !== "boolean")
      return { kind: "unavailable" };
    if (item.draft) continue;
    if (
      typeof item.prerelease !== "boolean" ||
      typeof item.tag_name !== "string" ||
      !item.tag_name.trim() ||
      typeof item.published_at !== "string" ||
      !Number.isFinite(Date.parse(item.published_at)) ||
      !trustedUrl(item.html_url, `${links.releases}/tag/`) ||
      !Array.isArray(item.assets)
    )
      return { kind: "unavailable" };

    const assets: ReleaseAsset[] = [];
    for (const asset of item.assets) {
      if (
        !isRecord(asset) ||
        typeof asset.name !== "string" ||
        !asset.name.trim() ||
        typeof asset.size !== "number" ||
        !Number.isSafeInteger(asset.size) ||
        asset.size < 0 ||
        !trustedUrl(asset.browser_download_url, `${links.releases}/download/`)
      )
        return { kind: "unavailable" };
      assets.push({
        name: asset.name,
        url: asset.browser_download_url,
        size: asset.size,
      });
    }
    candidates.push({
      prerelease: item.prerelease,
      release: {
        tag: item.tag_name,
        publishedAt: item.published_at,
        url: item.html_url,
        assets,
      },
    });
  }
  candidates.sort(
    (a, b) =>
      Number(a.prerelease) - Number(b.prerelease) ||
      Date.parse(b.release.publishedAt) - Date.parse(a.release.publishedAt),
  );
  const latest = candidates[0];
  return latest
    ? {
        kind: latest.prerelease ? "prerelease" : "stable",
        release: latest.release,
      }
    : { kind: "none" };
}
