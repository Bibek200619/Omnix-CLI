import type { CapabilityStatus } from "@/content/agents";
import { providers } from "@/content/providers";

export type RoadmapItem = {
  id: string;
  title: string;
  status: CapabilityStatus;
  summary: string;
  evidence: string;
};

export type ImplementedMilestone = {
  id: string;
  title: string;
  status: "available";
  summary: string;
  evidence: readonly string[];
};

// Engineering progression, not release dates or CLI phase numbers.
export const implementedMilestones = [
  {
    id: "foundation",
    title: "Project foundation",
    status: "available",
    summary: "Initialize validated local project state under .project/.",
    evidence: ["core/state_manager.py"],
  },
  {
    id: "providers",
    title: "Provider and model configuration",
    status: "available",
    summary:
      "Assign models to roles through the provider layer. OpenAI has a live generation adapter.",
    evidence: ["providers/openai.py", "cli/commands/config.py"],
  },
  {
    id: "master",
    title: "Master Agent and project memory",
    status: "available",
    summary:
      "Keep conversations, goals, and decisions. Invoke specialist workflows explicitly.",
    evidence: ["agents/master/agent.py"],
  },
  {
    id: "architect",
    title: "Architect and blueprint",
    status: "available",
    summary: "Generate, evolve, validate, and save the architecture blueprint.",
    evidence: ["agents/architect/agent.py"],
  },
  {
    id: "workers",
    title: "Planning and worker artifacts",
    status: "available",
    summary:
      "Plan tasks and generate versioned JSON artifacts with Frontend, Backend, Database, and Routing workers.",
    evidence: [
      "agents/planner/agent.py",
      "agents/frontend/agent.py",
      "agents/backend/agent.py",
      "agents/database/agent.py",
      "agents/routing/agent.py",
    ],
  },
  {
    id: "reports",
    title: "Integration, QA, and repair",
    status: "available",
    summary:
      "Assemble stored packages, produce model-assisted quality reports, and generate repair plans and artifacts.",
    evidence: [
      "agents/integration/agent.py",
      "agents/qa/agent.py",
      "agents/repair/agent.py",
    ],
  },
  {
    id: "build",
    title: "Coordinated execution and builds",
    status: "available",
    summary:
      "Schedule workers by task dependencies and coordinate the lifecycle with bounded repair cycles and a final JSON package.",
    evidence: [
      "orchestrator/autonomous.py",
      "agents/coordinator/coordinator.py",
    ],
  },
] as const satisfies readonly ImplementedMilestone[];

// No additional roadmap agent roles or delivery dates are established by source.
export const roadmap: readonly RoadmapItem[] = providers
  .filter((provider) => provider.status === "boundary-only")
  .map((provider) => ({
    id: `${provider.id}-generation`,
    title: `${provider.name} live generation`,
    status: "roadmap",
    summary: provider.summary,
    evidence: `ai-cli/omnix_cli/providers/${provider.id}.py`,
  }));
