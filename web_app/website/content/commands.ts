export type Command = { name: string; syntax: string; summary: string };

// Registered in ai-cli/omnix_cli/cli/main.py at 99d72d9. Arguments from handlers.
export const commands = [
  {
    name: "init",
    syntax: "omnix init",
    summary: "Initialize validated local project state.",
  },
  {
    name: "config",
    syntax: "omnix config",
    summary: "Inspect or configure role-to-provider/model assignments.",
  },
  {
    name: "chat",
    syntax: "omnix chat [MESSAGE]",
    summary: "Send a message to the state-aware Master Agent.",
  },
  {
    name: "architect",
    syntax: "omnix architect",
    summary: "Generate or refine an architecture blueprint.",
  },
  {
    name: "blueprint",
    syntax: "omnix blueprint",
    summary: "Display the saved architecture blueprint.",
  },
  {
    name: "models",
    syntax: "omnix models",
    summary: "Display configured role assignments, not a live model catalog.",
  },
  {
    name: "ping",
    syntax: "omnix ping ROLE",
    summary: "Check a configured role's provider connection.",
  },
  {
    name: "memory",
    syntax: "omnix memory",
    summary: "Display persistent project memory.",
  },
  {
    name: "goals",
    syntax: "omnix goals",
    summary: "Display recorded project goals.",
  },
  {
    name: "decisions",
    syntax: "omnix decisions",
    summary: "Display recorded project decisions.",
  },
  {
    name: "plan",
    syntax: "omnix plan",
    summary: "Generate or refine a task plan.",
  },
  {
    name: "tasks",
    syntax: "omnix tasks",
    summary: "Display the current task plan.",
  },
  {
    name: "execute",
    syntax: "omnix execute TASK_ID",
    summary: "Generate an artifact using the assigned worker.",
  },
  {
    name: "execute-all",
    syntax: "omnix execute-all",
    summary: "Schedule worker tasks respecting dependencies.",
  },
  {
    name: "execution",
    syntax: "omnix execution",
    summary: "Display execution status and history.",
  },
  {
    name: "integrate",
    syntax: "omnix integrate",
    summary: "Assemble artifacts and integration reports.",
  },
  {
    name: "integration",
    syntax: "omnix integration",
    summary: "Display the integration summary.",
  },
  {
    name: "qa",
    syntax: "omnix qa",
    summary: "Generate model-assisted quality reports.",
  },
  {
    name: "quality",
    syntax: "omnix quality",
    summary: "Display the stored quality summary.",
  },
  {
    name: "repair",
    syntax: "omnix repair",
    summary: "Generate repair plans and artifacts from QA findings.",
  },
  {
    name: "repairs",
    syntax: "omnix repairs",
    summary: "Display repair history and cycle summaries.",
  },
  {
    name: "artifacts",
    syntax: "omnix artifacts",
    summary: "List generated artifacts.",
  },
  {
    name: "artifact",
    syntax: "omnix artifact ARTIFACT_ID",
    summary: "Display a stored artifact.",
  },
  {
    name: "build",
    syntax: "omnix build GOAL",
    summary:
      "Coordinate the preview lifecycle with bounded repair cycles and a stored final package.",
  },
  {
    name: "build-status",
    syntax: "omnix build-status",
    summary: "Display the latest build report.",
  },
  {
    name: "builds",
    syntax: "omnix builds",
    summary: "Display build history and model-reported quality trends.",
  },
] as const satisfies readonly Command[];
