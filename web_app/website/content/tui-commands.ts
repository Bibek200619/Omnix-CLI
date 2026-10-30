import type { Command } from "@/content/commands";

// Local interactive controls from ai-cli/omnix_cli/tui/catalog.py. These are
// not registered `omnix <subcommand>` commands.
export const tuiCommands = [
  {
    name: "help",
    syntax: "/help",
    summary: "Show keyboard guidance and the available command catalog.",
  },
  {
    name: "context",
    syntax: "/context",
    summary: "Show or hide the local project context panel.",
  },
  {
    name: "changes",
    syntax: "/changes [PATCH]",
    summary:
      "Expand saved generated-artifact changes; an optional number selects a patch.",
  },
  {
    name: "theme",
    syntax: "/theme THEME",
    summary: "Choose a color theme for the current TUI session.",
  },
  {
    name: "new",
    syntax: "/new",
    summary:
      "Save the current conversation and start fresh; project settings and account credentials stay connected.",
  },
  {
    name: "resume",
    syntax: "/resume",
    summary: "Restore the most recently saved previous conversation.",
  },
  {
    name: "exit",
    syntax: "/exit",
    summary: "Close the interactive terminal interface.",
  },
] as const satisfies readonly Command[];
