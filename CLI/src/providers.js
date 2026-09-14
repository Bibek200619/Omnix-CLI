import { AGENTS } from "./constants.js";

export class LocalProvider {
  constructor(name = "local") {
    this.name = name;
  }

  async listModels() {
    return [
      { id: "local-deterministic", name: "Local Deterministic" },
      { id: "local-fast", name: "Local Fast" }
    ];
  }

  async generate(input) {
    return {
      content: `[${input.agentId}] ${input.task}`.trim(),
      usage: estimateUsage(input)
    };
  }

  async *stream(input) {
    yield (await this.generate(input)).content;
  }
}

export function getAgentRuntime(config, agentId) {
  const agent = AGENTS[agentId];
  if (!agent) throw new Error(`Unknown agent: ${agentId}`);
  const assigned = config.agents?.[agentId] || {};
  return {
    ...agent,
    provider: assigned.provider || agent.defaultProvider,
    model: assigned.model || agent.defaultModel
  };
}

export function buildProviderRegistry() {
  return {
    local: new LocalProvider("local"),
    openai: new LocalProvider("openai-adapter-placeholder"),
    google: new LocalProvider("google-adapter-placeholder"),
    anthropic: new LocalProvider("anthropic-adapter-placeholder"),
    openrouter: new LocalProvider("openrouter-adapter-placeholder"),
    custom: new LocalProvider("custom-adapter-placeholder")
  };
}

function estimateUsage(input) {
  const text = JSON.stringify(input);
  return {
    input_tokens: Math.ceil(text.length / 4),
    output_tokens: Math.ceil(String(input.task || "").length / 5),
    cached_tokens: 0
  };
}
