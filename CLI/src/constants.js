export const OMNIX_DIR = ".omnix";
export const AGENTS_DIR = ".agents";

export const AGENTS = {
  master: {
    id: "master",
    name: "Master Agent",
    role: "Coordinates planning, routing, memory, QA, and user-facing responses.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  },
  architect: {
    id: "architect",
    name: "System Architect Agent",
    role: "Creates blueprint, routes, API map, and database plan before implementation.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  },
  frontend: {
    id: "frontend",
    name: "Frontend Agent",
    role: "Generates UI components, pages, responsive layouts, and client integration.",
    defaultProvider: "google",
    defaultModel: "gemini-pro"
  },
  backend: {
    id: "backend",
    name: "Backend Agent",
    role: "Generates API handlers, services, validation, auth flow, and server logic.",
    defaultProvider: "anthropic",
    defaultModel: "claude-sonnet"
  },
  routing: {
    id: "routing",
    name: "Routing Agent",
    role: "Keeps page routes, navigation, and protected route maps consistent.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  },
  database: {
    id: "database",
    name: "Database Agent",
    role: "Generates Supabase migrations, schemas, indexes, and RLS policy plans.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  },
  integration: {
    id: "integration",
    name: "Integration Agent",
    role: "Verifies agent outputs work together before QA and apply.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  },
  qa: {
    id: "qa",
    name: "QA Agent",
    role: "Audits generated files, routes, SQL safety, and consistency before apply.",
    defaultProvider: "openrouter",
    defaultModel: "selected-model"
  },
  debug: {
    id: "debug",
    name: "Debug Agent",
    role: "Applies targeted fixes for QA or runtime errors without broad rewrites.",
    defaultProvider: "anthropic",
    defaultModel: "claude-sonnet"
  },
  docs: {
    id: "docs",
    name: "Documentation Agent",
    role: "Creates setup docs, API docs, architecture notes, and changelogs.",
    defaultProvider: "openai",
    defaultModel: "gpt-5.5"
  }
};

export const PROVIDERS = {
  openai: { name: "OpenAI", enabled: true },
  google: { name: "Google Gemini", enabled: true },
  anthropic: { name: "Anthropic Claude", enabled: true },
  openrouter: { name: "OpenRouter", enabled: true },
  custom: { name: "Custom OpenAI-compatible", enabled: false },
  local: { name: "Local deterministic provider", enabled: true }
};

export const MEMORY_FILES = {
  project: "memory/project.memory.json",
  chat: "memory/chat.memory.json",
  agent: "memory/agent.memory.json",
  qa: "memory/qa.memory.json",
  fileIndex: "memory/file.index.json",
  routeMap: "memory/route.map.json",
  databaseSchema: "memory/database.schema.json"
};

export const BLUEPRINT_FILES = {
  project: "blueprint/project.blueprint.json",
  routes: "blueprint/project.routes.json",
  database: "blueprint/project.database.json",
  apis: "blueprint/project.apis.json"
};

export const COMMAND_GROUPS = [
  ["/init", "Initialize OmniX files and shared brain"],
  ["/master <message>", "Chat with Master Agent"],
  ["/implement <task>", "Plan, generate, QA, and stage code changes"],
  ["/status", "Show project, agent, QA, Supabase, and pending-change status"],
  ["/diff", "Show pending file and migration previews"],
  ["/qa", "Audit pending changes"],
  ["/apply", "Write pending changes after QA passes"],
  ["/revert", "Discard pending changes"],
  ["/agent-status", "Show model assignments for every agent"],
  ["/agent-set <agent> <model> [provider]", "Change one agent model assignment"],
  ["/model-set <model> [provider]", "Set model for the Master Agent"],
  ["/providers", "Show provider connection status"],
  ["/provider-add <provider> --key <key>", "Enable provider and save an API key"],
  ["/key-update <provider> <key>", "Update a saved provider API key"],
  ["/keys", "Show masked local key status"],
  ["/models <provider>", "List known models for a provider"],
  ["/codebase", "Summarize project files, languages, and scripts"],
  ["/search <text>", "Search project text files"],
  ["/read <file> [start] [end]", "Read a file with line numbers"],
  ["/test", "Run the test script"],
  ["/build", "Run the build script"],
  ["/supabase-connect", "Store masked Supabase connection metadata and local secrets"],
  ["/supabase-status", "Show safe Supabase connection status"],
  ["/supabase-migration <task>", "Generate a safe Supabase SQL migration preview"],
  ["/supabase-apply latest --yes", "Record a confirmed migration apply locally"],
  ["/memory", "Show project memory summary"],
  ["/new <title>", "Start a new chat session"],
  ["/history", "Show previous chats"],
  ["/clear", "Clear visible terminal output"],
  ["/help", "Show command help"],
  ["/exit", "Exit interactive mode"]
];
