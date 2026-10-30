/** Captured from 0.1.0 in an isolated local project; no provider calls made. */
export const demoWorkspace = "/private/tmp/omnix-design-demo-atlas";
export const exampleModel = "gpt-4o-mini";
export const exampleAssignments = [
  { role: "Master", provider: "OpenAI", model: exampleModel },
  { role: "Architect", provider: "OpenAI", model: exampleModel },
] as const;

export const terminalDemo = [
  {
    id: "initialize",
    label: "Initialize",
    command: "omnix init --project-name Atlas",
    output: `Initialized Omnix CLI project at ${demoWorkspace}/.project`,
    caption:
      "Create local project state. Atlas starts with an empty blueprint.",
    evidence: "ai-cli/omnix_cli/cli/commands/init.py",
  },
  {
    id: "models",
    label: "Assign models",
    command: `omnix config --set master=openai:${exampleModel} --set architect=openai:${exampleModel}`,
    output: [
      "Role models:",
      "  master       gpt-4o-mini",
      "  planner      <unset>",
      "  architect    gpt-4o-mini",
      "  frontend     <unset>",
      "  backend      <unset>",
      "  database     <unset>",
      "  routing      <unset>",
      "  integration  <unset>",
      "  qa           <unset>",
      "  repair       <unset>",
    ].join("\n"),
    caption:
      "Example local assignments. Configuration does not make an API call.",
    evidence: "ai-cli/omnix_cli/cli/commands/config.py",
  },
  {
    id: "blueprint",
    label: "Inspect blueprint",
    command: "omnix blueprint",
    output: [
      "Project Blueprint",
      "Project Name\nAtlas",
      "Description\n<unset>",
      "Goals\nNone",
      "Pages\nNone",
      "Features\nNone",
      "Entities\nNone",
      "Modules\nNone",
      "Architecture Notes\nNone",
    ].join("\n\n"),
    caption:
      "The newly initialized blueprint, before any specialist generation.",
    evidence: "ai-cli/omnix_cli/cli/commands/blueprint.py",
  },
] as const;

export const demoCommands = terminalDemo
  .map((state) => state.command)
  .join("\n");
