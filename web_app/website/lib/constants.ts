export const repository = {
  owner: "Bibek200619",
  name: "Omnix-CLI",
  url: "https://github.com/Bibek200619/Omnix-CLI",
} as const;

export const links = {
  source: repository.url,
  releases: `${repository.url}/releases`,
  issues: `${repository.url}/issues`,
  cliDocs: `${repository.url}/tree/main/ai-cli`,
} as const;

export const product = {
  name: "Omnix CLI",
  version: "0.1.0",
  minimumPython: "3.12",
  availability: "Source preview",
  inspectedCommit: "99d72d9",
  verifiedAt: "2026-09-14",
  description:
    "Project conversations, persistent memory, and specialized engineering workflows in your terminal.",
} as const;

export const brand = {
  logo: "/brand/omnix-logo.png",
  width: 180,
  height: 180,
} as const;
