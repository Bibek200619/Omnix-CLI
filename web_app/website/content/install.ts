import { repository } from "@/lib/constants";

// Verified from a clean public checkout with Python 3.12.13 on 2026-10-24.
// Source setup only: no package registry or downloadable artifact is certified.
export const sourceSetup = {
  label: "Source setup with uv",
  command: [
    `git clone --depth 1 ${repository.url}.git`,
    "cd Omnix-CLI/ai-cli",
    "uv sync --frozen",
    "uv run --frozen omnix --help",
  ].join("\n"),
  uvDocs: "https://docs.astral.sh/uv/getting-started/installation/",
} as const;
