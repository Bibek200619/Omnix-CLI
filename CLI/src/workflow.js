import path from "node:path";
import {
  appendAgentLog,
  appendQaReport,
  loadBrain,
  loadConfig,
  loadMemory,
  saveMemory,
  updateGeneratedFiles
} from "./brain.js";
import { createBlueprintFromRequest, writeBlueprintFiles } from "./blueprint.js";
import { AGENTS } from "./constants.js";
import {
  nowIso,
  omnixPath,
  pathExists,
  readJson,
  slugify,
  titleCase,
  writeJson,
  writeText
} from "./files.js";
import { containsDestructiveSql, createMigrationPreview } from "./migrations.js";
import { getAgentRuntime } from "./providers.js";

export async function runMasterWorkflow(cwd, request, options = {}) {
  await startTaskRun(cwd, request);

  try {
    await updateTaskState(cwd, {
      status: "running",
      phase: "planning",
      progress: 10,
      next: "Generate architecture blueprint"
    });

    const brain = await loadBrain(cwd);
    const blueprint = createBlueprintFromRequest(request, {
      projectName: brain.projectMemory.project_name
    });
    await writeBlueprintFiles(cwd, blueprint);
    await appendAgentLog(cwd, {
      agent: "architect",
      event: "blueprint",
      details: `Blueprint generated for ${blueprint.project_name}.`
    });

    await updateTaskState(cwd, {
      phase: "generating",
      progress: 25,
      next: "Run specialist agents"
    });

    const pending = await createPendingChangeSet(cwd, request, blueprint, {
      replace: true,
      agents: options.agents || ["frontend", "backend", "routing", "database"]
    });

    await updateTaskState(cwd, {
      phase: "qa",
      progress: 80,
      next: "Audit pending changes"
    });

    let report = await runQualityLoop(cwd, pending);
    if (report.status === "failed") {
      await updateTaskState(cwd, {
        phase: "repair",
        progress: 88,
        next: "Repair QA findings"
      });
      const repaired = await repairPendingChanges(cwd, pending, report);
      if (repaired.changed) {
        await savePending(cwd, repaired.pending);
        report = await runQualityLoop(cwd, repaired.pending);
      }
    }

    await updateTaskState(cwd, {
      status: report.status === "passed" ? "ready" : "needs_fix",
      phase: report.status === "passed" ? "review" : "blocked",
      progress: report.status === "passed" ? 100 : 90,
      next: report.status === "passed" ? "/diff then /apply" : "/qa then /debug <issue>"
    });

    return {
      blueprint,
      pending: await loadPending(cwd),
      qa: report
    };
  } catch (error) {
    await updateTaskState(cwd, {
      status: "failed",
      phase: "interrupted",
      next: "/diff to inspect or /revert to discard",
      error: error?.message || String(error)
    });
    throw error;
  }
}

export async function runSingleAgent(cwd, agentId, request) {
  if (!AGENTS[agentId]) throw new Error(`Unknown agent: ${agentId}`);
  const brain = await loadBrain(cwd);
  const config = await loadConfig(cwd);
  const runtime = getAgentRuntime(config, agentId);
  const blueprint = createBlueprintFromRequest(request, {
    projectName: brain.projectMemory.project_name
  });

  if (agentId === "architect") {
    await writeBlueprintFiles(cwd, blueprint);
    await appendAgentLog(cwd, { agent: agentId, event: "blueprint", details: request });
    return { agent: runtime, message: "Blueprint files updated.", blueprint };
  }

  if (agentId === "qa") {
    const pending = await loadPending(cwd);
    const report = await runQualityLoop(cwd, pending);
    return { agent: runtime, message: `QA ${report.status}.`, report };
  }

  const pending = await createPendingChangeSet(cwd, request, blueprint, { agents: [agentId] });
  const report = await runQualityLoop(cwd, pending);
  return {
    agent: runtime,
    message: `${runtime.name} generated pending changes.`,
    pending,
    report
  };
}

export async function createPendingChangeSet(cwd, request, blueprint, options = {}) {
  const agents = options.agents || ["frontend", "backend", "routing", "database"];
  const existing = options.replace ? null : await loadPending(cwd);
  const pending = existing || {
    id: `change-${Date.now()}`,
    created_at: nowIso(),
    request,
    files: [],
    migrations: [],
    steps: [],
    state: makeTaskState(request, {
      status: "running",
      phase: "generating",
      progress: 20,
      next: "Run specialist agents"
    }),
    qa: null,
    integration: null
  };

  pending.request = request;
  pending.steps = pending.steps || [];
  pending.state = pending.state || makeTaskState(request);
  pending.updated_at = nowIso();

  for (let index = 0; index < agents.length; index += 1) {
    const agent = agents[index];
    updateStep(pending, agent, "running");
    pending.state = {
      ...pending.state,
      status: "running",
      phase: agent,
      progress: Math.max(25, Math.round(((index + 1) / agents.length) * 70)),
      next: `Finish ${agent} output`,
      updated_at: nowIso()
    };
    await savePending(cwd, pending);

    if (agent === "frontend") pending.files.push(...generateFrontendFiles(blueprint));
    if (agent === "backend") pending.files.push(...generateBackendFiles(blueprint));
    if (agent === "routing") pending.files.push(...generateRoutingFiles(blueprint));
    if (agent === "database") {
      const migration = await createMigrationPreview(cwd, request);
      pending.migrations.push({
        agent: "database",
        path: migration.path,
        tableName: migration.tableName,
        sql: migration.sql
      });
    }
    await appendAgentLog(cwd, {
      agent,
      event: "generate",
      details: request
    });
    updateStep(pending, agent, "completed");
  }

  pending.files = dedupeFiles(pending.files);
  pending.migrations = dedupeMigrations(pending.migrations);
  pending.state = {
    ...pending.state,
    phase: "qa",
    progress: 78,
    next: "Run QA audit",
    updated_at: nowIso()
  };
  await savePending(cwd, pending);
  await updateModifiedFiles(cwd, pending);
  return pending;
}

export async function loadPending(cwd) {
  return readJson(omnixPath(cwd, "pending", "changes.json"), null);
}

export async function savePending(cwd, pending) {
  await writeJson(omnixPath(cwd, "pending", "changes.json"), pending);
}

export async function startTaskRun(cwd, request) {
  const pending = {
    id: `change-${Date.now()}`,
    created_at: nowIso(),
    updated_at: nowIso(),
    request,
    files: [],
    migrations: [],
    steps: [],
    state: makeTaskState(request, {
      status: "running",
      phase: "starting",
      progress: 1,
      next: "Plan task"
    }),
    qa: null,
    integration: null
  };
  await savePending(cwd, pending);
  await updateModifiedFiles(cwd, pending);
  return pending;
}

export async function updateTaskState(cwd, patch) {
  const pending = await loadPending(cwd);
  if (!pending) return null;
  pending.state = {
    ...makeTaskState(pending.request),
    ...(pending.state || {}),
    ...patch,
    updated_at: nowIso()
  };
  pending.updated_at = nowIso();
  await savePending(cwd, pending);
  return pending;
}

export async function clearPending(cwd) {
  await writeJson(omnixPath(cwd, "pending", "changes.json"), null);
  await updateModifiedFiles(cwd, null);
}

export async function applyPending(cwd, options = {}) {
  const pending = await loadPending(cwd);
  if (!pending) return { applied: false, files: [], message: "No pending changes to apply." };
  const report = pending.qa || (await runQualityLoop(cwd, pending));
  if (report.status !== "passed" && !options.force) {
    return {
      applied: false,
      files: [],
      message: "QA has not passed. Run /qa or fix the audit errors before /apply."
    };
  }

  const written = [];
  for (const file of pending.files || []) {
    const target = path.join(cwd, file.path);
    if ((await pathExists(target)) && !options.overwrite) {
      file.skipped = true;
      continue;
    }
    await writeText(target, file.content);
    written.push(file.path);
  }

  for (const migration of pending.migrations || []) {
    const target = path.join(cwd, migration.path);
    if ((await pathExists(target)) && !options.overwrite) continue;
    await writeText(target, migration.sql);
    written.push(migration.path);
  }

  await updateGeneratedFiles(cwd, written);
  await clearPending(cwd);
  await appendAgentLog(cwd, {
    agent: "master",
    event: "apply",
    details: `${written.length} files written.`
  });

  return { applied: true, files: written, message: `Applied ${written.length} file changes.` };
}

export async function runQualityLoop(cwd, pending = null) {
  const current = pending || (await loadPending(cwd));
  const integration = runIntegrationCheck(current);
  const qa = runQaAudit(current, integration);
  const report = {
    status: qa.errors.length ? "failed" : "passed",
    errors: qa.errors,
    warnings: qa.warnings,
    integration,
    checked_at: nowIso()
  };

  if (current) {
    current.integration = integration;
    current.qa = report;
    await savePending(cwd, current);
  }

  await appendQaReport(cwd, report);
  return report;
}

export async function repairPendingChanges(cwd, pending, report) {
  let changed = false;
  const next = structuredClone(pending);

  for (const error of report.errors || []) {
    if (error.error_type === "duplicate_file") {
      next.files = dedupeFiles(next.files || []);
      changed = true;
    }
  }

  if (changed) {
    await appendAgentLog(cwd, {
      agent: "debug",
      event: "repair",
      details: "Removed duplicate pending file entries found by QA."
    });
  }

  return { changed, pending: next };
}

export function runIntegrationCheck(pending) {
  const errors = [];
  const warnings = [];
  const files = pending?.files || [];
  const routesFile = files.find((file) => file.path.endsWith("omnix-routes.ts"));
  const pageFiles = files.filter((file) => file.path.includes("/app/") && file.path.endsWith("/page.tsx"));

  if (!pending) {
    warnings.push("No pending change set found.");
    return { status: "warning", errors, warnings };
  }

  if (pageFiles.length && !routesFile) {
    errors.push({
      error_type: "routing_error",
      affected_agents: ["frontend", "routing"],
      details: "Frontend pages were generated without a route map.",
      severity: "high",
      recommended_fix: "Run /routing for the same task before applying."
    });
  }

  const duplicatePaths = findDuplicates(files.map((file) => file.path));
  for (const duplicatePath of duplicatePaths) {
    errors.push({
      error_type: "duplicate_file",
      affected_agents: ["integration"],
      details: `Duplicate pending file: ${duplicatePath}`,
      severity: "medium",
      recommended_fix: "Keep one pending entry per file path."
    });
  }

  return {
    status: errors.length ? "failed" : "passed",
    errors,
    warnings
  };
}

export function runQaAudit(pending, integration) {
  const errors = [...(integration?.errors || [])];
  const warnings = [...(integration?.warnings || [])];

  if (!pending) {
    return { errors, warnings };
  }

  for (const file of pending.files || []) {
    if (/\{\{.+\}\}/.test(file.content)) {
      errors.push({
        error_type: "template_placeholder",
        affected_agents: [file.agent],
        details: `${file.path} still contains an unresolved template placeholder.`,
        severity: "high",
        recommended_fix: "Replace all template placeholders before applying."
      });
    }
    if (!balancedBrackets(file.content)) {
      errors.push({
        error_type: "syntax_risk",
        affected_agents: [file.agent],
        details: `${file.path} has unbalanced brackets.`,
        severity: "high",
        recommended_fix: "Fix generated syntax before applying."
      });
    }
  }

  for (const migration of pending.migrations || []) {
    if (containsDestructiveSql(migration.sql)) {
      errors.push({
        error_type: "destructive_sql",
        affected_agents: ["database"],
        details: `${migration.path} contains destructive SQL.`,
        severity: "critical",
        recommended_fix: "Require explicit destructive confirmation before applying."
      });
    }
    if (!/enable row level security/i.test(migration.sql)) {
      warnings.push(`${migration.path} does not enable RLS.`);
    }
  }

  return { errors, warnings };
}

function generateFrontendFiles(blueprint) {
  return blueprint.routing.routes.map((route) => {
    const segment = route.path === "/" ? "" : slugify(route.path);
    const pageName = `${titleCase(route.name)}Page`.replace(/\s+/g, "");
    const filePath = path.posix.join("src", "app", segment, "page.tsx");
    return {
      agent: "frontend",
      action: "create",
      path: filePath,
      content: `export default function ${pageName}() {
  return (
    <main className="omnix-page">
      <header>
        <p>Generated by OmniX Frontend Agent</p>
        <h1>${route.name}</h1>
      </header>
      <section>
        <p>${route.protected ? "Protected workspace route" : "Public route"} for ${blueprint.project_name}.</p>
      </section>
    </main>
  );
}
`
    };
  });
}

function generateBackendFiles(blueprint) {
  return blueprint.database.tables.map((table) => {
    const serviceName = `${titleCase(table.name)}Service`.replace(/\s+/g, "");
    return {
      agent: "backend",
      action: "create",
      path: path.posix.join("src", "app", "api", table.name, "route.ts"),
      content: `const tableName = "${table.name}";

export async function GET() {
  return Response.json({ table: tableName, rows: [] });
}

export async function POST(request: Request) {
  const body = await request.json();
  return Response.json({ table: tableName, created: body }, { status: 201 });
}

export const ${serviceName} = { tableName };
`
    };
  });
}

function generateRoutingFiles(blueprint) {
  const routes = blueprint.routing.routes.map((route) => ({
    name: route.name,
    path: route.path,
    protected: route.protected
  }));

  return [
    {
      agent: "routing",
      action: "create",
      path: path.posix.join("src", "lib", "omnix-routes.ts"),
      content: `export const omnixRoutes = ${JSON.stringify(routes, null, 2)} as const;
`
    }
  ];
}

function dedupeFiles(files) {
  const byPath = new Map();
  for (const file of files || []) {
    byPath.set(file.path, file);
  }
  return [...byPath.values()].sort((a, b) => a.path.localeCompare(b.path));
}

function dedupeMigrations(migrations) {
  const byPath = new Map();
  for (const migration of migrations || []) {
    byPath.set(migration.path, migration);
  }
  return [...byPath.values()].sort((a, b) => a.path.localeCompare(b.path));
}

function makeTaskState(request, overrides = {}) {
  return {
    status: "running",
    phase: "starting",
    progress: 0,
    next: "Plan task",
    request,
    started_at: nowIso(),
    updated_at: nowIso(),
    ...overrides
  };
}

function updateStep(pending, agent, status) {
  const existing = pending.steps.find((step) => step.agent === agent);
  if (existing) {
    existing.status = status;
    existing.updated_at = nowIso();
    return;
  }
  pending.steps.push({
    agent,
    status,
    started_at: nowIso(),
    updated_at: nowIso()
  });
}

async function updateModifiedFiles(cwd, pending) {
  const fileIndex = await loadMemory(cwd, "fileIndex");
  fileIndex.modified_files = pending
    ? [
        ...(pending.files || []).map((file) => file.path),
        ...(pending.migrations || []).map((migration) => migration.path)
      ].sort()
    : [];
  await saveMemory(cwd, "fileIndex", fileIndex);
}

function findDuplicates(values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates];
}

function balancedBrackets(value) {
  const stack = [];
  const pairs = { ")": "(", "]": "[", "}": "{" };
  for (const char of value) {
    if (char === "(" || char === "[" || char === "{") stack.push(char);
    if (char === ")" || char === "]" || char === "}") {
      if (stack.pop() !== pairs[char]) return false;
    }
  }
  return stack.length === 0;
}
