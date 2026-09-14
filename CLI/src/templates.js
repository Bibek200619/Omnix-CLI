import path from "node:path";
import { AGENTS, PROVIDERS } from "./constants.js";

export function defaultConfig(cwd) {
  const projectName = path.basename(cwd);
  const agents = Object.fromEntries(
    Object.values(AGENTS).map((agent) => [
      agent.id,
      {
        provider: agent.defaultProvider,
        model: agent.defaultModel
      }
    ])
  );

  return {
    project_name: projectName,
    default_agent: "master",
    providers: PROVIDERS,
    agents,
    supabase: {
      connected: false,
      project_url: "",
      project_ref: ""
    },
    ui: {
      theme: "omnix-dark",
      layout: "split"
    }
  };
}

export function defaultProjectMemory(cwd) {
  return {
    project_name: path.basename(cwd),
    tech_stack: {
      frontend: "Terminal UI",
      backend: "Node.js",
      database: "Supabase",
      language: "JavaScript"
    },
    agents: Object.fromEntries(Object.values(AGENTS).map((agent) => [agent.id, agent.defaultModel])),
    known_rules: [
      "All agents must read OmniX.md before code generation.",
      "Database changes must be validated before applying to Supabase.",
      "QA must run before final file write."
    ],
    generated_files: [],
    known_issues: [],
    decisions: [],
    open_tasks: []
  };
}

export function defaultChatMemory() {
  return {
    sessions: [],
    compacted: null
  };
}

export function defaultAgentMemory() {
  return {
    runs: []
  };
}

export function defaultQaMemory() {
  return {
    reports: [],
    latest_status: "not_run"
  };
}

export function defaultFileIndex() {
  return {
    generated_files: [],
    modified_files: [],
    last_scan: null,
    files: []
  };
}

export function defaultRouteMap() {
  return {
    routes: [],
    protected_routes: []
  };
}

export function defaultDatabaseSchema() {
  return {
    tables: [],
    migrations: [],
    last_pull: null
  };
}

export function omnixMarkdownTemplate(projectName) {
  return `# OmniX Project Behavior

## Project Rules

- Follow the existing project structure.
- Do not create duplicate files.
- Do not overwrite user code without confirmation.
- Prefer small, targeted changes.
- Always run QA after code generation.
- Database changes must be reviewed before applying to Supabase.

## Coding Style

- Use clean, readable code.
- Use meaningful names.
- Avoid unnecessary abstractions.
- Keep components reusable.

## Agent Rules

- Master Agent coordinates all tasks.
- System Architect Agent creates the blueprint before major work.
- Frontend Agent handles UI only.
- Backend Agent handles APIs and server logic.
- Routing Agent handles navigation and route consistency.
- Database Agent handles schema and Supabase migration.
- Integration Agent verifies agent outputs work together.
- QA Agent audits before final write.

## Safety Rules

- Never expose API keys.
- Never print service role keys.
- Never apply destructive database migrations without confirmation.
- Always create a migration preview before applying.

## Project

- Name: ${projectName}
`;
}
