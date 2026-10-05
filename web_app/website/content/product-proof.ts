import { commands, type Command } from "@/content/commands";

export type CommandGroup = {
  id: string;
  title: string;
  description: string;
  commands: readonly Command[];
  primary?: boolean;
};

const commandByName = new Map<string, Command>(
  commands.map((command) => [command.name, command]),
);

function selectCommands(names: readonly string[]) {
  return names.map((name) => {
    const command = commandByName.get(name);
    if (!command) throw new Error(`Unknown Omnix command: ${name}`);
    return command;
  });
}

export const memoryRecords = [
  {
    name: "Conversation",
    file: "project.memory.json",
    detail: "Stored messages; the command reports their count",
    command: "omnix memory",
  },
  {
    name: "Goals",
    file: "project.memory.json",
    detail: "Active project outcomes detected by Master",
    command: "omnix goals",
  },
  {
    name: "Decisions",
    file: "project.memory.json",
    detail: "Project and architectural decisions",
    command: "omnix decisions",
  },
  {
    name: "Blueprint",
    file: "project.blueprint.json",
    detail: "The current validated architecture",
    command: "omnix blueprint",
  },
] as const;

export const commandGroups = [
  {
    id: "start",
    title: "Start and configure",
    description: "Create local state and assign models to roles.",
    commands: selectCommands(["init", "config", "models", "ping"]),
    primary: true,
  },
  {
    id: "context",
    title: "Conversation and context",
    description: "Talk to Master and inspect what the project remembers.",
    commands: selectCommands(["chat", "memory", "goals", "decisions"]),
    primary: true,
  },
  {
    id: "architecture",
    title: "Architecture",
    description: "Generate, refine, and read the saved blueprint.",
    commands: selectCommands(["architect", "blueprint"]),
    primary: true,
  },
  {
    id: "orchestration",
    title: "Preview orchestration commands",
    description:
      "Plan work, generate stored artifacts, assemble reports, and inspect build history.",
    commands: selectCommands([
      "plan",
      "tasks",
      "execute",
      "execute-all",
      "execution",
      "integrate",
      "integration",
      "qa",
      "quality",
      "repair",
      "repairs",
      "artifacts",
      "artifact",
      "build",
      "build-status",
      "builds",
    ]),
  },
] as const satisfies readonly CommandGroup[];

export const architectFlow = [
  {
    title: "Read project context",
    detail:
      "Load goals, decisions, recent conversation, and the existing blueprint from local project state.",
    evidence: "agents/architect/context_builder.py",
  },
  {
    title: "Request a complete proposal",
    detail:
      "Ask the configured provider for a structured architecture proposal using the saved project context.",
    evidence: "agents/architect/prompts.py",
  },
  {
    title: "Evolve the blueprint",
    detail:
      "Merge the proposal with existing goals, pages, features, entities, modules, and architecture notes.",
    evidence: "blueprint/evolution.py",
  },
  {
    title: "Validate, then save",
    detail:
      "Require a project name, features, entities, modules, and architecture notes before persisting the blueprint.",
    evidence: "blueprint/validation.py",
  },
] as const;
