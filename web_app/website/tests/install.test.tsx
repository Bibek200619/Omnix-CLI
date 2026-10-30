import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Home from "@/app/page";
import { InstallSection } from "@/components/marketing/install-section";
import { sourceSetup } from "@/content/install";
import { fetchReleaseState } from "@/lib/github";
import { links } from "@/lib/constants";
import type { ReleaseState } from "@/lib/release";

vi.mock("@/lib/github", () => ({ fetchReleaseState: vi.fn() }));

// Synthetic publication fixtures prove UI states, not actual Omnix releases.
const release = {
  tag: "fixture-v1",
  url: `${links.releases}/tag/fixture-v1`,
  publishedAt: "2026-01-01T00:00:00Z",
  assets: [],
};
const states: { state: ReleaseState; heading: string }[] = [
  { state: { kind: "none" }, heading: "No published release is listed." },
  {
    state: { kind: "unavailable" },
    heading: "Release information is unavailable.",
  },
  {
    state: { kind: "stable", release },
    heading: "Stable release published fixture-v1",
  },
  {
    state: { kind: "prerelease", release },
    heading: "Prerelease published fixture-v1",
  },
];

beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

it.each(states)(
  "renders server release state $state.kind while keeping verified setup",
  async ({ state, heading }) => {
    vi.mocked(fetchReleaseState).mockResolvedValue(state);
    render(await Home());
    expect(fetchReleaseState).toHaveBeenCalledOnce();
    const section = screen.getByRole("region", {
      name: "Start with the source.",
    });
    expect(
      within(section).getByRole("heading", { name: heading }),
    ).toBeVisible();
    expect(
      within(section).getByRole("figure", { name: sourceSetup.label }),
    ).toHaveTextContent("uv sync --frozen");
    expect(within(section).getByText(/does not add a global/)).toBeVisible();
    expect(
      within(section).queryByRole("link", {
        name: /^(install|download) omnix$/i,
      }),
    ).not.toBeInTheDocument();
    if (state.kind === "stable" || state.kind === "prerelease") {
      expect(
        within(section).getByRole("link", { name: "Review release" }),
      ).toHaveAttribute("href", release.url);
      expect(within(section).getByText(/has not been verified/)).toBeVisible();
    } else
      expect(
        within(section).getByRole("link", { name: "Check GitHub Releases" }),
      ).toHaveAttribute("href", links.releases);
  },
);

it("copies only the verified source setup commands", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText },
  });
  render(<InstallSection releaseState={{ kind: "none" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Copy setup commands" }));
  expect(await screen.findByRole("status")).toHaveTextContent(
    "Copied to clipboard.",
  );
  expect(writeText).toHaveBeenCalledWith(sourceSetup.command);
  expect(sourceSetup.command).not.toMatch(/pip install|npm install|curl.*\|/);
});
