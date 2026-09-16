import { agents } from "@/content/agents";

export type JourneyStep = {
  id: string;
  title: string;
  kind: "goal" | "agent" | "context" | "result";
  summary: string;
  command?: string;
  files?: readonly string[];
  status?: "available" | "roadmap";
  handoff: string;
  detail: string;
  evidence: string;
};

const master = agents.find((agent) => agent.id === "master")!;
const architect = agents.find((agent) => agent.id === "architect")!;

// Website explanation of source behavior, not a live run or fabricated output.
// Rechecked 2026-09-16. Chat and Architect are separate user-invoked commands.
export const journeySteps = [
  {
    id: "goal",
    title: "Your goal",
    kind: "goal",
    summary: "Start with what you want to build.",
    command: 'omnix chat "Build authentication for Atlas"',
    handoff: "You start the conversation",
    detail:
      "In an initialized project, send your goal to the Master Agent. This is an example request, not a claim that authentication code has been generated.",
    evidence: "ai-cli/omnix_cli/cli/commands/chat.py",
  },
  {
    id: "master",
    title: master.name,
    kind: "agent",
    status: master.status,
    summary: "Keeps the conversation. Records detected goals and decisions.",
    handoff: "Master writes to project memory",
    detail:
      "Master reads project context and persists the conversation locally. It can use a configured model, but chat does not invoke the Architect or other specialists.",
    evidence: master.evidence,
  },
  {
    id: "context",
    title: "Project context",
    kind: "context",
    summary:
      "Goals, decisions, recent conversation, and the existing blueprint.",
    files: ["project.memory.json", "project.blueprint.json"],
    handoff: "Context is ready for the next command",
    detail:
      "The Architect reads saved memory and the existing blueprint from .project/. Context persists between commands; it is not an automatic handoff from chat.",
    evidence: "ai-cli/omnix_cli/agents/architect/context_builder.py",
  },
  {
    id: "architect",
    title: architect.name,
    kind: "agent",
    status: architect.status,
    summary:
      "You invoke the specialist. It generates or refines the architecture.",
    command: "omnix architect",
    handoff: "You explicitly invoke the Architect",
    detail:
      "After configuring the Architect’s provider, model, and API key, run omnix architect. It uses saved context to propose and evolve the blueprint, then validates it before saving.",
    evidence: architect.evidence,
  },
  {
    id: "blueprint",
    title: "Validated blueprint",
    kind: "result",
    summary: "A saved architecture with schema and completeness checks.",
    command: "omnix blueprint",
    handoff: "Read the saved result",
    detail:
      "Inspect the blueprint with omnix blueprint. Validation checks its structure and required architecture fields. It does not run, test, or deploy an application.",
    evidence: "ai-cli/omnix_cli/blueprint/validation.py",
  },
] as const satisfies readonly JourneyStep[];

export const journey = {
  title: "One project. Context that carries forward.",
  introduction:
    "Talk through the goal. Keep the decisions. Bring that context to the next specialist when you’re ready.",
  availability: "Available in source preview",
  boundary:
    "Chat keeps context. You invoke specialist commands explicitly, or use the separate build orchestrator.",
  buildCommand: 'omnix build "Build authentication for Atlas"',
  buildSummary:
    "The build orchestrator coordinates Architect, Planner, worker execution, Integration, QA, and bounded repair cycles.",
  buildLimit:
    "Outputs are stored JSON artifacts, packages, and model-assisted reports. They do not establish that an application runs or that its tests pass.",
  buildEvidence: "ai-cli/omnix_cli/orchestrator/autonomous.py",
} as const;
