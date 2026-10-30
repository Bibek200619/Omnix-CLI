import { links } from "@/lib/constants";

export const hero = {
  eyebrow: "Omnix CLI",
  headline: "Build software with an AI engineering team.",
  supporting:
    "Talk to a Master Agent that remembers your project. Run specialist workflows from the same terminal.",
  primary: { label: "Preview installation", href: "#download" },
  secondary: { label: "View on GitHub", href: links.source },
} as const;

// Only publish navigation to existing sections. Add future IA anchors with their sections.
export const navigation = [
  { label: "Product", href: "#product" },
  { label: "How it works", href: "#how-it-works" },
  { label: "CLI", href: "#cli" },
  { label: "Roadmap", href: "#roadmap" },
  { label: "GitHub", href: links.source },
] as const;
