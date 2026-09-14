import type { CapabilityStatus } from "@/content/agents";
import { providers } from "@/content/providers";

export type RoadmapItem = {
  id: string;
  title: string;
  status: CapabilityStatus;
  summary: string;
  evidence: string;
};

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
