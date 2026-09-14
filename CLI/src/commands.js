import path from "node:path";
import {
  appendAgentLog,
  assertInitialized,
  compactChatMemory,
  initProject,
  loadBrain,
  loadConfig,
  saveConfig,
  scanSkills,
  updateFileIndex
} from "./brain.js";
import { createBlueprintFromRequest, writeBlueprintFiles } from "./blueprint.js";
import {
  explainProjectFile,
  listPackageScripts,
  projectOverview,
  readProjectFile,
  runPackageScript,
  searchProject,
  stageFileWrite
} from "./code_tools.js";
import {
  deleteChat,
  exportChat,
  chatHistory,
  clearVisibleChat,
  newChat,
  recordChatMessage,
  renameChat,
  reviewChat
} from "./chat_tools.js";
import {
  contextFiles,
  contextSummary,
  memoryReset,
  memoryUpdate,
  pinInstruction,
  summarizeConversation,
  unpinInstruction
} from "./context_tools.js";
import {
  endpointAdd,
  keyStatus,
  keyUpdate,
  listModels,
  providerAdd,
  providerRemove,
  providersStatus,
  setCurrentModel
} from "./config_tools.js";
import { AGENTS } from "./constants.js";
import { listFiles, maskSecret, omnixPath, readJson } from "./files.js";
import { applyLatestMigration, connectSupabase, createMigrationPreview } from "./migrations.js";
import { getAgentRuntime } from "./providers.js";
import {
  skillAdd,
  skillEdit,
  skillInfo,
  skillRemove
} from "./skill_tools.js";
import {
  supabaseDiff,
  supabasePolicies,
  supabasePull,
  supabaseReset,
  supabaseRls,
  supabaseSchema,
  supabaseSeed,
  supabaseTables
} from "./supabase_tools.js";
import {
  costStatus,
  focusPanel,
  logo,
  notifications,
  setLayout,
  setTheme,
  togglePanel,
  tokenStatus
} from "./ui_tools.js";
import {
  applyPending,
  clearPending,
  loadPending,
  runMasterWorkflow,
  runQualityLoop,
  runSingleAgent,
  savePending
} from "./workflow.js";
import {
  formatDiff,
  formatQaReport,
  renderAgentStatus,
  renderHelp,
  renderLayout,
  renderLogo,
  statusPanel
} from "./ui.js";

export async function executeCommand(argv, context = {}) {
  const cwd = context.cwd || process.cwd();
  const frame = context.frame !== false;
  const args = [...argv];
  const first = args[0];

  if (!first) {
    return welcome(cwd, frame);
  }

  if (first === "--init" || first === "init" || first === "/init") {
    const result = await initProject(cwd, { force: args.includes("--force") });
    return layout(cwd, {
      main: [
        "OmniX initialized successfully.",
        "Project brain created.",
        "Agents configured.",
        "",
        "Created/verified:",
        ...result.created.map((file) => `+ ${file}`)
      ],
      input: "OmniX > /help"
    }, frame);
  }

  const command = first.startsWith("/") ? first.slice(1) : first;
  const rest = args.slice(1);

  if (!first.startsWith("/") && !isKnownCommand(command)) {
    await assertInitialized(cwd);
    const request = args.join(" ");
    if (!shouldRunMasterWorkflow(request)) {
      return masterChat(cwd, request, frame);
    }

    const result = await runMasterWorkflow(cwd, request);
    return layout(cwd, {
      activeAgent: "master",
      main: [
        `Master workflow complete for: ${request}`,
        "",
        `Blueprint: ${result.blueprint.project_name}`,
        `Pending files: ${(result.pending?.files || []).length}`,
        `Pending migrations: ${(result.pending?.migrations || []).length}`,
        "",
        formatQaReport(result.qa),
        "",
        "Run /diff to inspect changes, then /apply after review."
      ],
      input: "OmniX > /diff"
    }, frame);
  }

  switch (command) {
    case "help":
      return renderHelp();
    case "exit":
      return "Goodbye.";
    case "status":
      await assertInitialized(cwd);
      return layout(cwd, { main: "Project status loaded.", input: "OmniX >" }, frame);
    case "agent-status":
      return agentStatus(cwd);
    case "agent-set":
      return agentSet(cwd, rest, frame);
    case "model-set":
      return setCurrentModel(cwd, rest[0], rest[1]);
    case "memory":
      return memorySummary(cwd);
    case "memory-update":
      return memoryUpdate(cwd, rest[0], rest.slice(1).join(" "));
    case "memory-reset":
      return memoryReset(cwd, rest[0]);
    case "context":
      return contextSummary(cwd);
    case "context-files":
      return contextFiles(cwd);
    case "pin":
      return pinInstruction(cwd, rest.join(" "));
    case "unpin":
      return unpinInstruction(cwd, rest.join(" "));
    case "summarize":
      return summarizeConversation(cwd);
    case "compact":
      return compact(cwd, rest.join(" "));
    case "skills":
    case "skill-scan":
      return skills(cwd);
    case "scan":
      return scan(cwd, frame);
    case "code":
    case "codebase":
      return projectOverview(cwd);
    case "search":
      return searchProject(cwd, rest.join(" "));
    case "read":
      return readProjectFile(cwd, rest[0], rest[1], rest[2]);
    case "file-read":
      return readProjectFile(cwd, rest[0], rest[1], rest[2]);
    case "file-write":
      return stageFileWrite(cwd, rest[0], rest.slice(1).join(" "));
    case "explain":
      return explainProjectFile(cwd, rest[0]);
    case "scripts":
      return listPackageScripts(cwd);
    case "test":
      return runPackageScript(cwd, "test");
    case "build":
      return runPackageScript(cwd, "build");
    case "lint":
      return runPackageScript(cwd, "lint");
    case "typecheck":
      return runPackageScript(cwd, "typecheck");
    case "tree":
      return tree(cwd);
    case "blueprint":
      return blueprint(cwd, rest.join(" "), frame);
    case "files":
    case "diff":
      return diff(cwd);
    case "apply":
      return apply(cwd, rest);
    case "revert":
      return revert(cwd);
    case "qa":
    case "audit":
      return qa(cwd);
    case "frontend":
    case "backend":
    case "routing":
    case "database":
    case "architect":
    case "integration":
    case "debug":
    case "docs":
    case "master":
      return agent(cwd, command, rest.join(" "), frame);
    case "implement":
      return agent(cwd, "master", rest.join(" "), frame, {
        forceWorkflow: true,
        usage: "/implement <task>"
      });
    case "fix":
      return agent(cwd, "debug", rest.join(" "), frame);
    case "supabase-connect":
      return supabaseConnect(cwd, parseOptions(rest));
    case "supabase-status":
      return supabaseStatus(cwd);
    case "supabase-schema":
      return supabaseSchema(cwd);
    case "supabase-pull":
      return supabasePull(cwd);
    case "supabase-migration":
      return supabaseMigration(cwd, rest.join(" "));
    case "supabase-apply":
      return supabaseApply(cwd, rest);
    case "supabase-reset":
      return supabaseReset(cwd, rest.includes("--yes"));
    case "supabase-tables":
      return supabaseTables(cwd);
    case "supabase-policies":
      return supabasePolicies(cwd);
    case "supabase-rls":
      return supabaseRls(cwd, rest[0]);
    case "supabase-seed":
      return supabaseSeed(cwd, rest[0]);
    case "supabase-diff":
      return supabaseDiff(cwd);
    case "providers":
      return providersStatus(cwd);
    case "provider-add":
      return providerAdd(cwd, rest[0], parseOptions(rest.slice(1)));
    case "provider-remove":
      return providerRemove(cwd, rest[0]);
    case "models":
      return listModels(rest[0] || "local");
    case "key-update":
      return keyUpdate(cwd, rest[0], rest[1]);
    case "endpoint-add":
      return endpointAdd(cwd, rest[0], rest[1]);
    case "keys":
      return keyStatus(cwd);
    case "skill-add":
      return skillAdd(cwd, rest[0], rest.slice(1).join(" "));
    case "skill-edit":
      return skillEdit(cwd, rest[0], rest.slice(1).join(" "));
    case "skill-remove":
      return skillRemove(cwd, rest[0], rest.includes("--yes"));
    case "skill-use":
    case "skill-info":
      return skillInfo(cwd, rest.join(" "));
    case "theme":
      return setTheme(cwd, rest[0]);
    case "layout":
      return setLayout(cwd, rest[0]);
    case "logo":
      return logo();
    case "focus":
      return focusPanel(cwd, rest[0]);
    case "panel-toggle":
      return togglePanel(cwd, rest[0]);
    case "tokens":
      return tokenStatus(cwd);
    case "cost":
      return costStatus(cwd);
    case "notifications":
      return notifications(cwd, rest[0]);
    case "new":
      return newChat(cwd, rest.join(" "));
    case "rename":
      return renameChat(cwd, rest.join(" "));
    case "review":
      return reviewChat(cwd, rest[0]);
    case "history":
      return chatHistory(cwd);
    case "delete-chat":
      return deleteChat(cwd, rest.find((item) => item !== "--yes"), rest.includes("--yes"));
    case "export-chat":
      return exportChat(cwd, rest[0] || "md");
    case "clear":
      return clearVisibleChat();
    default:
      throw new Error(`Unknown command: /${command}. Run /help.`);
  }
}

async function welcome(cwd, frame = true) {
  const initialized = Boolean(await readJson(omnixPath(cwd, "config.json"), null));
  if (!initialized) {
    const options = {
      project: path.basename(cwd),
      main: [
        ...renderLogo().split("\n"),
        "",
        "Run `omnix init` to create OmniX.md, .agents/skills, and the shared project brain.",
        "After init, type / for the command picker."
      ],
      status: [["Status", "not initialized"], ["Next", "/init"], "", "Commands", "Type / to filter"],
      input: "OmniX > /init"
    };
    return frame ? renderLayout(options) : plainMain(options);
  }
  return layout(cwd, {
    main: ["Welcome back to OmniX CLI.", "Use /help for commands or describe a build task."],
    input: "OmniX >"
  }, frame);
}

async function layout(cwd, options, frame = true) {
  if (!frame) return plainMain(options);
  const brain = await loadBrain(cwd);
  const pending = await loadPending(cwd);
  const activeAgent = options.activeAgent || brain.config.default_agent || "master";
  const runtime = getAgentRuntime(brain.config, activeAgent);
  return renderLayout({
    project: brain.config.project_name,
    activeAgent,
    model: runtime.model,
    main: options.main,
    status: statusPanel(brain, pending),
    input: options.input
  });
}

function plainMain(options) {
  const lines = Array.isArray(options.main) ? options.main : String(options.main || "").split(/\r?\n/);
  return lines.filter((line, index) => line !== "" || index < lines.length - 1).join("\n");
}

async function agentStatus(cwd) {
  const config = await loadConfig(cwd);
  return renderAgentStatus(config).join("\n");
}

async function agentSet(cwd, args, frame = true) {
  await assertInitialized(cwd);
  const [agentId, model, provider] = args;
  if (!AGENTS[agentId]) throw new Error(`Unknown agent '${agentId}'.`);
  if (!model) throw new Error("Usage: /agent-set <agent> <model> [provider]");
  const config = await loadConfig(cwd);
  config.agents[agentId] = {
    provider: provider || config.agents[agentId]?.provider || AGENTS[agentId].defaultProvider,
    model
  };
  await saveConfig(cwd, config);
  await appendAgentLog(cwd, {
    agent: "master",
    event: "agent-set",
    details: `${agentId} -> ${config.agents[agentId].provider}/${model}`
  });
  return layout(cwd, {
    activeAgent: agentId,
    main: [`${AGENTS[agentId].name} set to ${config.agents[agentId].provider}/${model}.`],
    input: "OmniX > /agent-status"
  }, frame);
}

async function memorySummary(cwd) {
  const brain = await loadBrain(cwd);
  return JSON.stringify(
    {
      project_name: brain.projectMemory.project_name,
      generated_files: brain.projectMemory.generated_files,
      known_issues: brain.projectMemory.known_issues,
      decisions: brain.projectMemory.decisions,
      open_tasks: brain.projectMemory.open_tasks,
      qa_status: brain.qaMemory.latest_status
    },
    null,
    2
  );
}

async function compact(cwd, summary) {
  await assertInitialized(cwd);
  const compacted = await compactChatMemory(cwd, summary || "Conversation compacted by user command.");
  return JSON.stringify(compacted, null, 2);
}

async function skills(cwd) {
  await assertInitialized(cwd);
  const found = await scanSkills(cwd);
  if (!found.length) return "No skills found in .agents/skills.";
  return found.map((skill) => `${skill.name} - ${skill.path}`).join("\n");
}

async function scan(cwd, frame = true) {
  await assertInitialized(cwd);
  const fileIndex = await updateFileIndex(cwd);
  return layout(cwd, {
    main: [`Scanned ${fileIndex.files.length} files.`, "", ...fileIndex.files.slice(0, 20)],
    input: "OmniX > /status"
  }, frame);
}

async function tree(cwd) {
  const files = await listFiles(cwd, { maxDepth: 3, ignore: [".git", "node_modules", ".omnix/cache"] });
  return files.slice(0, 120).join("\n");
}

async function blueprint(cwd, request, frame = true) {
  await assertInitialized(cwd);
  if (!request) {
    const current = await readJson(omnixPath(cwd, "blueprint", "project.blueprint.json"), {});
    return JSON.stringify(current, null, 2);
  }
  const brain = await loadBrain(cwd);
  const generated = createBlueprintFromRequest(request, { projectName: brain.projectMemory.project_name });
  await writeBlueprintFiles(cwd, generated);
  await appendAgentLog(cwd, { agent: "architect", event: "blueprint", details: request });
  return layout(cwd, {
    activeAgent: "architect",
    main: [
      "Blueprint generated.",
      "",
      `Pages: ${generated.frontend.pages.join(", ") || "none"}`,
      `Routes: ${generated.routing.routes.map((route) => route.path).join(", ") || "none"}`,
      `Tables: ${generated.database.tables.map((table) => table.name).join(", ") || "none"}`
    ],
    input: "OmniX > /diff"
  }, frame);
}

async function diff(cwd) {
  await assertInitialized(cwd);
  const pending = await loadPending(cwd);
  return formatDiff(pending);
}

async function apply(cwd, args) {
  await assertInitialized(cwd);
  const result = await applyPending(cwd, {
    force: args.includes("--force"),
    overwrite: args.includes("--overwrite")
  });
  return result.message + (result.files.length ? `\n${result.files.map((file) => `+ ${file}`).join("\n")}` : "");
}

async function revert(cwd) {
  await assertInitialized(cwd);
  await clearPending(cwd);
  return "Pending changes discarded.";
}

async function qa(cwd) {
  await assertInitialized(cwd);
  const pending = await loadPending(cwd);
  const report = await runQualityLoop(cwd, pending);
  return formatQaReport(report);
}

async function agent(cwd, agentId, request, frame = true, options = {}) {
  await assertInitialized(cwd);
  if (!request && agentId !== "qa") {
    if (agentId === "master" && !options.forceWorkflow) return masterChat(cwd, "", frame);
    throw new Error(`Usage: ${options.usage || `/${agentId} <task>`}`);
  }
  if (agentId === "master") {
    if (!options.forceWorkflow && !shouldRunMasterWorkflow(request)) {
      return masterChat(cwd, request, frame);
    }

    const result = await runMasterWorkflow(cwd, request);
    return layout(cwd, {
      activeAgent: "master",
      main: [
        "Master Agent coordinated the workflow.",
        `Blueprint: ${result.blueprint.project_name}`,
        `QA: ${result.qa.status}`,
        "",
        "Run /diff to review pending changes."
      ],
      input: "OmniX > /diff"
    }, frame);
  }
  const result = await runSingleAgent(cwd, agentId, request);
  return layout(cwd, {
    activeAgent: agentId,
    main: [
      result.message,
      result.report ? formatQaReport(result.report) : "",
      result.blueprint ? `Blueprint: ${result.blueprint.project_name}` : ""
    ],
    input: "OmniX > /diff"
  }, frame);
}

async function masterChat(cwd, message, frame = true) {
  const input = String(message || "").trim();
  await recordChatMessage(cwd, "user", input || "/master");
  const reply = masterChatReply(input);
  await recordChatMessage(cwd, "assistant", reply);
  await appendAgentLog(cwd, {
    agent: "master",
    event: "chat",
    details: input || "empty master chat"
  });

  return layout(cwd, {
    activeAgent: "master",
    main: reply.split(/\r?\n/),
    input: "OmniX >"
  }, frame);
}

function masterChatReply(message) {
  const text = normalizeIntentText(message);

  if (!text || /^(hi|hello|hey|yo|thanks|thank you|ok|okay|cool|nice)\b[!. ]*$/.test(text)) {
    return [
      "Master Agent: hello.",
      "No task was created. Ask a question here, or use /implement <task> when you want code changes."
    ].join("\n");
  }

  if (/\b(model|agent model|set model|change model)\b/.test(text)) {
    return [
      "Master Agent: use /model-set for the current agent, or /agent-set for one specialist.",
      "",
      "/model-set <model> [provider]",
      "/agent-set frontend gemini-2.5-pro google",
      "/agent-set backend claude-sonnet anthropic",
      "/agent-status"
    ].join("\n");
  }

  if (/\b(api key|apikey|provider key|openai key|gemini key|anthropic key|old key|keys)\b/.test(text)) {
    return [
      "Master Agent: keys are stored locally and shown masked by default.",
      "",
      "/provider-add openai --key sk-your-key",
      "/key-update openai sk-your-key",
      "/keys",
      "",
      "Raw local keys are in .omnix/config.local.json. Do not commit or paste that file."
    ].join("\n");
  }

  if (/\b(command|commands|help|what can you do)\b/.test(text)) {
    return [
      "Master Agent: press / in interactive mode for the command picker, or run /help.",
      "Use /implement <task> only when you want me to generate pending code changes."
    ].join("\n");
  }

  if (/\b(pending|diff|apply|unfinished|stopped|resume|task)\b/.test(text)) {
    return [
      "Master Agent: check staged work with /diff.",
      "Use /apply only after review, or /revert to discard unfinished pending changes.",
      "I did not start a new task from this message."
    ].join("\n");
  }

  return [
    "Master Agent: I treated this as chat, not a build request.",
    "No task was created. I only start the workflow for clear build/change/fix requests or explicit /implement commands."
  ].join("\n");
}

function shouldRunMasterWorkflow(message) {
  const text = normalizeIntentText(message);
  if (!text) return false;

  const actionVerb = "(build|create|make|implement|add|update|change|fix|repair|debug|refactor|generate|scaffold|write|edit|remove|delete|set up|setup|connect|integrate|migrate|design|improve|enhance|convert|replace)";

  if (new RegExp(`^(please\\s+)?${actionVerb}\\b`).test(text)) return true;
  if (new RegExp(`^(can|could|would|will)\\s+you\\s+(please\\s+)?${actionVerb}\\b`).test(text)) return true;
  if (new RegExp(`^(let's|lets)\\s+${actionVerb}\\b`).test(text)) return true;

  if (/^(i|we)\s+(want|need|wanna|would like|wand)\b/.test(text)) {
    if (/\b(know|understand|learn|explain|tell|ask|question|answer)\b/.test(text)) return false;
    return true;
  }

  return false;
}

function normalizeIntentText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[“”]/g, "\"")
    .replace(/[’]/g, "'")
    .replace(/\s+/g, " ");
}

async function supabaseConnect(cwd, options) {
  await assertInitialized(cwd);
  const projectUrl = options.url || options.projectUrl || "";
  const projectRef = options.ref || options.projectRef || "";
  const anonKey = options.anonKey || "";
  const serviceRoleKey = options.serviceRoleKey || "";
  const status = await connectSupabase(cwd, { projectUrl, projectRef, anonKey, serviceRoleKey });
  return [
    "Supabase connection saved.",
    `Project URL: ${status.project_url || "missing"}`,
    `Project ref: ${status.project_ref || "missing"}`,
    "Service role key: stored locally and masked"
  ].join("\n");
}

async function supabaseStatus(cwd) {
  const config = await loadConfig(cwd);
  return JSON.stringify(config.supabase, null, 2);
}

async function supabaseMigration(cwd, request) {
  await assertInitialized(cwd);
  if (!request) throw new Error("Usage: /supabase-migration <migration task>");
  const migration = await createMigrationPreview(cwd, request);
  const pending = (await loadPending(cwd)) || {
    id: `change-${Date.now()}`,
    created_at: new Date().toISOString(),
    request,
    files: [],
    migrations: []
  };
  pending.migrations.push({
    agent: "database",
    path: migration.path,
    tableName: migration.tableName,
    sql: migration.sql
  });
  await savePending(cwd, pending);
  return [`Migration preview generated: ${migration.path}`, "", migration.sql].join("\n");
}

async function supabaseApply(cwd, args) {
  await assertInitialized(cwd);
  const result = await applyLatestMigration(cwd, {
    confirmed: args.includes("--yes"),
    confirmDestructive: args.includes("--confirm-destructive")
  });
  return result.message;
}

async function keys(cwd) {
  await assertInitialized(cwd);
  const local = await readJson(omnixPath(cwd, "config.local.json"), {});
  const supabase = local.supabase || {};
  return [
    `Supabase URL: ${maskSecret(supabase.project_url || "") || "missing"}`,
    `Anon key: ${maskSecret(supabase.anon_key || "") || "missing"}`,
    `Service role key: ${maskSecret(supabase.service_role_key || "") || "missing"}`
  ].join("\n");
}

function parseOptions(args) {
  const options = {};
  for (let index = 0; index < args.length; index += 1) {
    const item = args[index];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const next = args[index + 1];
    options[key] = next && !next.startsWith("--") ? next : true;
    if (next && !next.startsWith("--")) index += 1;
  }
  return options;
}

function isKnownCommand(command) {
  return new Set([
    "help",
    "init",
    "status",
    "agent-status",
    "agent-set",
    "model-set",
    "memory",
    "memory-update",
    "memory-reset",
    "context",
    "context-files",
    "pin",
    "unpin",
    "summarize",
    "compact",
    "skills",
    "skill-scan",
    "scan",
    "code",
    "codebase",
    "search",
    "read",
    "file-read",
    "file-write",
    "explain",
    "scripts",
    "test",
    "build",
    "lint",
    "typecheck",
    "fix",
    "tree",
    "blueprint",
    "files",
    "diff",
    "apply",
    "revert",
    "qa",
    "audit",
    "frontend",
    "backend",
    "routing",
    "database",
    "architect",
    "integration",
    "debug",
    "docs",
    "master",
    "implement",
    "supabase-connect",
    "supabase-status",
    "supabase-schema",
    "supabase-pull",
    "supabase-migration",
    "supabase-apply",
    "supabase-reset",
    "supabase-tables",
    "supabase-policies",
    "supabase-rls",
    "supabase-seed",
    "supabase-diff",
    "providers",
    "provider-add",
    "provider-remove",
    "models",
    "key-update",
    "endpoint-add",
    "keys",
    "skill-add",
    "skill-edit",
    "skill-remove",
    "skill-use",
    "skill-info",
    "theme",
    "layout",
    "logo",
    "focus",
    "panel-toggle",
    "tokens",
    "cost",
    "notifications",
    "new",
    "rename",
    "review",
    "history",
    "delete-chat",
    "export-chat",
    "clear",
    "exit"
  ]).has(command);
}

export function splitArgs(value) {
  return value.match(/"[^"]+"|'[^']+'|\S+/g)?.map((item) => item.replace(/^['"]|['"]$/g, "")) || [];
}
