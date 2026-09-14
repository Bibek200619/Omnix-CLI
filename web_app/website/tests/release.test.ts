import { describe, expect, it, vi } from "vitest";
import { fetchReleaseState } from "@/lib/github";
import { links } from "@/lib/constants";
import { normalizeReleases } from "@/lib/release";

const published = {
  tag_name: "test-stable",
  draft: false,
  prerelease: false,
  published_at: "2026-01-01T00:00:00Z",
  html_url: `${links.releases}/tag/test-stable`,
  assets: [],
};

describe("release normalization (synthetic fixtures, not actual releases)", () => {
  it("distinguishes no published releases from unavailable data", () => {
    expect(normalizeReleases([])).toEqual({ kind: "none" });
    expect(normalizeReleases([{ draft: true }])).toEqual({ kind: "none" });
    expect(normalizeReleases({ message: "rate limited" })).toEqual({
      kind: "unavailable",
    });
  });

  it("prefers stable over a newer prerelease and picks newest stable by date", () => {
    const result = normalizeReleases([
      {
        ...published,
        tag_name: "test-preview",
        prerelease: true,
        published_at: "2026-03-01T00:00:00Z",
      },
      published,
      {
        ...published,
        tag_name: "test-newer",
        published_at: "2026-02-01T00:00:00Z",
      },
    ]);
    expect(result.kind).toBe("stable");
    if (result.kind === "stable") expect(result.release.tag).toBe("test-newer");
  });

  it("supports a prerelease-only repository without inventing an install command", () => {
    const result = normalizeReleases([{ ...published, prerelease: true }]);
    expect(result.kind).toBe("prerelease");
    expect(result).not.toHaveProperty("installCommand");
  });

  it.each([
    { published_at: null },
    { published_at: "not a date" },
    { tag_name: " " },
    { prerelease: "false" },
    { assets: {} },
    { html_url: "https://github.com/attacker/repo/releases/tag/v1" },
    {
      html_url:
        "https://github.com.evil.test/Bibek200619/Omnix-CLI/releases/tag/v1",
    },
    { html_url: `${links.releases}/tag/../../../../attacker` },
    { html_url: "javascript:alert(1)" },
  ])("rejects malformed or untrusted metadata: %j", (patch) => {
    expect(normalizeReleases([{ ...published, ...patch }])).toEqual({
      kind: "unavailable",
    });
  });

  it("validates assets without exposing a verified download action", () => {
    const asset = {
      name: "fixture.whl",
      size: 100,
      browser_download_url: `${links.releases}/download/test-stable/fixture.whl`,
    };
    const result = normalizeReleases([{ ...published, assets: [asset] }]);
    expect(result.kind).toBe("stable");
    if (result.kind === "stable")
      expect(result.release.assets[0]?.url).toBe(asset.browser_download_url);
    expect(
      normalizeReleases([
        {
          ...published,
          assets: [
            { ...asset, browser_download_url: "https://evil.test/fixture.whl" },
          ],
        },
      ]),
    ).toEqual({ kind: "unavailable" });
    expect(
      normalizeReleases([{ ...published, assets: [{ ...asset, size: -1 }] }]),
    ).toEqual({ kind: "unavailable" });
  });
});

describe("server GitHub boundary", () => {
  it.each([403, 404, 429, 500])(
    "returns unavailable for HTTP %i",
    async (status) => {
      const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response("{}", { status }));
      expect(await fetchReleaseState(fetcher)).toEqual({ kind: "unavailable" });
    },
  );

  it("returns unavailable for network/timeout and malformed JSON failures", async () => {
    const offline = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new Error("offline"));
    const invalid = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("not JSON"));
    expect(await fetchReleaseState(offline)).toEqual({ kind: "unavailable" });
    expect(await fetchReleaseState(invalid)).toEqual({ kind: "unavailable" });
  });

  it("normalizes a public response and sets a cache and timeout", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response("[]"));
    expect(await fetchReleaseState(fetcher)).toEqual({ kind: "none" });
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining(
        "api.github.com/repos/Bibek200619/Omnix-CLI/releases",
      ),
      expect.objectContaining({
        next: { revalidate: 3600 },
        signal: expect.any(AbortSignal),
      }),
    );
  });
});
