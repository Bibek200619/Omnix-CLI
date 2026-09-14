export type CapabilityStatus = "available" | "roadmap";
export type Agent = {
  id: string;
  name: string;
  status: CapabilityStatus;
  scope: "source-preview";
  summary: string;
  evidence: string;
};

// Availability describes inspected source behavior, not a stable distribution.
export const agents = [
  {
    id: "master",
    name: "Master Agent",
    summary:
      "Maintains conversations, goals, and decisions. Chat does not dispatch specialists.",
  },
  {
    id: "architect",
    name: "Architect Agent",
    summary:
      "Generates, refines, validates, and saves architecture blueprints.",
  },
  {
    id: "planner",
    name: "Planner Agent",
    summary: "Generates and evolves validated task plans.",
  },
  {
    id: "frontend",
    name: "Frontend Agent",
    summary: "Generates versioned frontend artifacts for assigned tasks.",
  },
  {
    id: "backend",
    name: "Backend Agent",
    summary: "Generates versioned backend artifacts for assigned tasks.",
  },
  {
    id: "database",
    name: "Database Agent",
    summary: "Generates versioned database artifacts for assigned tasks.",
  },
  {
    id: "routing",
    name: "Routing Agent",
    summary: "Generates versioned routing artifacts for assigned tasks.",
  },
  {
    id: "integration",
    name: "Integration Agent",
    summary:
      "Assembles a stored package and model-assisted dependency and conflict reports.",
  },
  {
    id: "qa",
    name: "QA Agent",
    summary:
      "Produces model-assisted quality reports; does not run an application test suite.",
  },
  {
    id: "repair",
    name: "Repair Agent",
    summary:
      "Generates repair plans and artifacts from QA findings; does not prove fixes work.",
  },
].map((agent): Agent => ({
  ...agent,
  status: "available",
  scope: "source-preview",
  evidence: `ai-cli/omnix_cli/agents/${agent.id}/agent.py`,
}));
