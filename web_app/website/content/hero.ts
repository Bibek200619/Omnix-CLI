import { links } from "@/lib/constants";

export const hero = {
  eyebrow: "Omnix CLI",
  headline: "Build software with an AI engineering team.",
  supporting:
    "Talk to a Master Agent that remembers your project. Run specialist workflows from the same terminal.",
  primary: { label: "View source preview", href: links.cliDocs },
  secondary: { label: "View on GitHub", href: links.source },
} as const;

// Only publish navigation to existing sections. Add future IA anchors with their sections.
export const navigation = [
  { label: "Product", href: "#product" },
  { label: "CLI", href: "#cli" },
  { label: "GitHub", href: links.source },
] as const;

// Notes are website narration, never claimed terminal output.
// Signatures rechecked with the installed CLI help on 2026-09-15.
export const terminalSteps = [
  {
    command: 'omnix init --project-name "Atlas"',
    note: "Initialize local project state in .project/.",
    evidence: "ai-cli/omnix_cli/cli/commands/init.py",
  },
  {
    command: 'omnix chat "Build authentication for Atlas"',
    note: "Discuss your goal with the Master Agent. Keep the conversation in memory.",
    evidence: "ai-cli/omnix_cli/agents/master/agent.py",
  },
  {
    command: "omnix config --set architect=openai:gpt-5",
    note: "Assign the Architect’s model. This example uses OpenAI.",
    evidence: "ai-cli/omnix_cli/cli/commands/config.py",
  },
  {
    command: "omnix architect",
    note: "Invoke the Architect to generate or refine a validated blueprint.",
    evidence: "ai-cli/omnix_cli/agents/architect/agent.py",
  },
  {
    command: "omnix blueprint",
    note: "Read the saved architecture blueprint.",
    evidence: "ai-cli/omnix_cli/cli/commands/blueprint.py",
  },
] as const;

export const terminalCommands = terminalSteps
  .map((step) => step.command)
  .join("\n");
