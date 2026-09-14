export type Provider = {
  id: string;
  name: string;
  status: "live-adapter" | "boundary-only";
  summary: string;
};

export const providers = [
  {
    id: "openai",
    name: "OpenAI",
    status: "live-adapter",
    summary:
      "Responses API adapter; requires an API key and configured model. Live quality was not certified by website discovery.",
  },
  ...[
    { id: "anthropic", name: "Anthropic" },
    { id: "google", name: "Google" },
    { id: "openrouter", name: "OpenRouter" },
    { id: "deepseek", name: "DeepSeek" },
  ].map((provider) => ({
    ...provider,
    status: "boundary-only" as const,
    summary:
      "Registered configuration boundary. Live generation is not implemented.",
  })),
] satisfies readonly Provider[];
