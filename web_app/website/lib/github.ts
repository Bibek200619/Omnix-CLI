import "server-only";
import { repository } from "@/lib/constants";
import { normalizeReleases, type ReleaseState } from "@/lib/release";

/** Server-side public metadata only. No browser token and no build-time dependency. */
export async function fetchReleaseState(
  fetcher: typeof fetch = fetch,
): Promise<ReleaseState> {
  try {
    const response = await fetcher(
      `https://api.github.com/repos/${repository.owner}/${repository.name}/releases?per_page=100`,
      {
        headers: {
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(5000),
      },
    );
    if (!response.ok) return { kind: "unavailable" };
    const payload: unknown = await response.json();
    return normalizeReleases(payload);
  } catch {
    return { kind: "unavailable" };
  }
}
