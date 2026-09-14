import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { COMMAND_GROUPS } from "../src/constants.js";
import { executeCommand } from "../src/commands.js";
import { readJson } from "../src/files.js";
import { buildInteractiveFrame } from "../src/interactive.js";
import { completeSlashCommand, getCommandSuggestions, renderLayout } from "../src/ui.js";

test("init creates OmniX shared brain files", async () => {
  const cwd = await tempProject();
  try {
    const output = await executeCommand(["init"], { cwd });
    assert.match(output, /OmniX initialized successfully/);
    assert.equal(await exists(path.join(cwd, "OmniX.md")), true);
    assert.equal(await exists(path.join(cwd, ".agents", "skills")), true);
    assert.equal(await exists(path.join(cwd, ".omnix", "config.json")), true);
    assert.equal(await exists(path.join(cwd, ".omnix", "memory", "project.memory.json")), true);
    assert.equal(await exists(path.join(cwd, ".omnix", "blueprint", "project.blueprint.json")), true);
    assert.equal(await exists(path.join(cwd, ".omnix", "logs", "agent-runs.log")), true);
  } finally {
    await cleanup(cwd);
  }
});

test("agent-set updates config and status", async () => {
  const cwd = await tempProject();
  try {
    await executeCommand(["init"], { cwd });
    const output = await executeCommand(["/agent-set", "frontend", "gemini-2.5-pro", "google"], { cwd });
    assert.match(output, /Frontend Agent set to google\/gemini-2.5-pro/);
    const config = await readJson(path.join(cwd, ".omnix", "config.json"));
    assert.equal(config.agents.frontend.model, "gemini-2.5-pro");
    assert.equal(config.agents.frontend.provider, "google");
  } finally {
    await cleanup(cwd);
  }
});

test("master workflow writes blueprint and QA-passed pending changes", async () => {
  const cwd = await tempProject();
  try {
    await executeCommand(["init"], { cwd });
    const output = await executeCommand(["Build", "a", "SaaS", "CRM", "with", "dashboard,", "customers,", "deals,", "settings,", "and", "Supabase", "backend"], { cwd });
    assert.match(output, /Master workflow complete/);
    assert.match(output, /QA Result/);
    assert.match(output, /Status: passed/);

    const blueprint = await readJson(path.join(cwd, ".omnix", "blueprint", "project.blueprint.json"));
    assert.deepEqual(blueprint.frontend.pages, ["Dashboard", "Customers", "Deals", "Settings"]);
    assert.equal(blueprint.database.tables.some((table) => table.name === "customers"), true);

    const pending = await readJson(path.join(cwd, ".omnix", "pending", "changes.json"));
    assert.equal(pending.state.status, "ready");
    assert.equal(pending.state.phase, "review");
    assert.equal(pending.steps.every((step) => step.status === "completed"), true);
    assert.equal(pending.qa.status, "passed");
    assert.equal(pending.files.some((file) => file.path === "src/lib/omnix-routes.ts"), true);

    const applyOutput = await executeCommand(["/apply"], { cwd });
    assert.match(applyOutput, /Applied/);
    assert.equal(await exists(path.join(cwd, "src", "lib", "omnix-routes.ts")), true);
    assert.equal(await exists(path.join(cwd, "supabase", "migrations")), true);
  } finally {
    await cleanup(cwd);
  }
});

test("master chat does not create pending work for greetings or questions", async () => {
  const cwd = await tempProject();
  try {
    await executeCommand(["init"], { cwd });

    const greeting = await executeCommand(["hello"], { cwd, frame: false });
    assert.match(greeting, /Master Agent: hello/);
    assert.match(greeting, /No task was created/);
    assert.equal(await readJson(path.join(cwd, ".omnix", "pending", "changes.json"), null), null);

    const question = await executeCommand(["how", "to", "set", "model?"], { cwd, frame: false });
    assert.match(question, /\/model-set <model> \[provider\]/);
    assert.equal(await readJson(path.join(cwd, ".omnix", "pending", "changes.json"), null), null);

    const masterGreeting = await executeCommand(["/master", "hello"], { cwd, frame: false });
    assert.match(masterGreeting, /No task was created/);
    assert.equal(await readJson(path.join(cwd, ".omnix", "pending", "changes.json"), null), null);

    const chat = await readJson(path.join(cwd, ".omnix", "memory", "chat.memory.json"));
    const messages = chat.sessions.flatMap((session) => session.messages || []);
    assert.equal(messages.some((message) => message.role === "user" && message.content === "hello"), true);
    assert.equal(messages.some((message) => message.role === "assistant" && /No task was created/.test(message.content)), true);
  } finally {
    await cleanup(cwd);
  }
});

test("supabase connection masks secrets and migration preview is safe", async () => {
  const cwd = await tempProject();
  try {
    await executeCommand(["init"], { cwd });
    const output = await executeCommand([
      "/supabase-connect",
      "--url",
      "https://example.supabase.co",
      "--anon-key",
      "anon-secret-value",
      "--service-role-key",
      "service-role-secret",
      "--ref",
      "example-ref"
    ], { cwd });
    assert.doesNotMatch(output, /service-role-secret/);
    assert.match(output, /stored locally and masked/);

    const config = await readJson(path.join(cwd, ".omnix", "config.json"));
    assert.equal(config.supabase.connected, true);
    assert.notEqual(config.supabase.project_url, "https://example.supabase.co");

    const migration = await executeCommand(["/supabase-migration", "create", "customers", "table", "with", "name,", "email,", "phone"], { cwd });
    assert.match(migration, /enable row level security/i);
    assert.match(migration, /create policy/i);

    const qa = await executeCommand(["/qa"], { cwd });
    assert.match(qa, /Status: passed/);
  } finally {
    await cleanup(cwd);
  }
});

test("slash command suggestions show all commands and filter while typing", () => {
  const all = getCommandSuggestions("/", 200);
  assert.equal(all.length, COMMAND_GROUPS.length);
  assert.equal(all[0].command, "/init");

  const filtered = getCommandSuggestions("/supabase", 20);
  assert.equal(filtered.length > 0, true);
  assert.equal(filtered.every((item) => item.command.includes("supabase")), true);

  assert.equal(completeSlashCommand("/supabase-st"), "/supabase-status ");
});

test("visible slash commands stay focused on core workflows", () => {
  const visible = COMMAND_GROUPS.map(([usage]) => usage.split(/\s+/)[0]);
  assert.equal(visible.length <= 32, true);

  for (const command of [
    "/frontend",
    "/backend",
    "/routing",
    "/database",
    "/theme",
    "/layout",
    "/tokens",
    "/cost",
    "/skill-add",
    "/file-write"
  ]) {
    assert.equal(visible.includes(command), false);
  }

  for (const command of ["/init", "/master", "/implement", "/diff", "/apply", "/keys", "/codebase", "/help"]) {
    assert.equal(visible.includes(command), true);
  }
});

test("interactive frame renders slash command panel before init", async () => {
  const cwd = await tempProject();
  try {
    const frame = await buildInteractiveFrame({
      cwd,
      input: "/",
      messages: ["Welcome"],
      history: [],
      historyIndex: 0
    });
    assert.match(frame, /Commands/);
    assert.match(frame, /Up\/Down scroll/);
    assert.match(frame, /\/init/);
    assert.match(frame, /› \//);
    assert.doesNotMatch(frame, /^\+/m);
    assert.doesNotMatch(frame, /\| Workspace/);
  } finally {
    await cleanup(cwd);
  }
});

test("interactive slash command panel can render a scrolled selection", async () => {
  const cwd = await tempProject();
  const exitIndex = COMMAND_GROUPS.findIndex(([usage]) => usage.split(/\s+/)[0] === "/exit");
  try {
    const frame = await buildInteractiveFrame({
      cwd,
      input: "/",
      messages: ["Welcome"],
      history: [],
      historyIndex: 0,
      commandIndex: exitIndex,
      commandScroll: exitIndex
    });
    assert.match(frame, /\/exit/);
    assert.match(frame, /Commands/);
  } finally {
    await cleanup(cwd);
  }
});

test("composer uses the available terminal width", () => {
  const frame = renderLayout({
    width: 190,
    height: 34,
    color: false,
    main: ["Ready"],
    status: [["Status", "ready"]],
    inputValue: "Explain this codebase"
  });

  const composerLine = frame.split("\n").find((line) => line.includes("› Explain this codebase"));
  assert.ok(composerLine);
  assert.equal(composerLine.length, 190);
});

test("coding commands scan, search, read, explain, and scripts", async () => {
  const cwd = await tempProject();
  try {
    await mkdir(path.join(cwd, "src"), { recursive: true });
    await writeFile(
      path.join(cwd, "src", "sample.js"),
      [
        "import fs from 'node:fs';",
        "",
        "export function greet(name) {",
        "  return `hello ${name}`;",
        "}"
      ].join("\n"),
      "utf8"
    );
    await writeFile(
      path.join(cwd, "package.json"),
      JSON.stringify({ scripts: { build: "node --check src/sample.js" } }, null, 2),
      "utf8"
    );

    const overview = await executeCommand(["/codebase"], { cwd });
    assert.match(overview, /Files scanned:/);
    assert.match(overview, /Package scripts: build/);
    assert.match(await executeCommand(["/code"], { cwd }), /Files scanned:/);

    const search = await executeCommand(["/search", "hello"], { cwd });
    assert.match(search, /src\/sample.js:4/);

    const read = await executeCommand(["/read", "src/sample.js", "1", "3"], { cwd });
    assert.match(read, /1 \| import fs/);
    assert.match(read, /3 \| export function greet/);

    const explain = await executeCommand(["/explain", "src/sample.js"], { cwd });
    assert.match(explain, /Imports: 1/);
    assert.match(explain, /Exports: 1/);

    const scripts = await executeCommand(["/scripts"], { cwd });
    assert.match(scripts, /build\s+node --check src\/sample.js/);

    const lint = await executeCommand(["/lint"], { cwd });
    assert.match(lint, /No "lint" script found/);
  } finally {
    await cleanup(cwd);
  }
});

test("chat, context, provider, skill, ui, and supabase command families work locally", async () => {
  const cwd = await tempProject();
  try {
    await executeCommand(["init"], { cwd });

    const chat = await executeCommand(["/new", "Sprint", "Chat"], { cwd });
    assert.match(chat, /New chat started/);
    assert.match(await executeCommand(["/rename", "Renamed", "Chat"], { cwd }), /Renamed current chat/);
    assert.match(await executeCommand(["/history"], { cwd }), /Renamed Chat/);
    assert.match(await executeCommand(["/export-chat", "json"], { cwd }), /Exported chat/);

    assert.match(await executeCommand(["/pin", "Always", "run", "QA"], { cwd }), /Pinned/);
    assert.match(await executeCommand(["/memory-update", "open_tasks", "Finish", "CLI"], { cwd }), /Updated open_tasks/);
    assert.match(await executeCommand(["/context"], { cwd }), /Chat sessions:/);
    assert.match(await executeCommand(["/summarize"], { cwd }), /open_tasks/);
    assert.match(await executeCommand(["/unpin", "1"], { cwd }), /Unpinned/);

    assert.match(await executeCommand(["/provider-add", "openai", "--key", "sk-test-secret"], { cwd }), /Provider enabled: openai/);
    assert.match(await executeCommand(["/providers"], { cwd }), /openai\s+enabled/);
    assert.match(await executeCommand(["/key-update", "google", "google-secret"], { cwd }), /Provider enabled: google/);
    assert.doesNotMatch(await executeCommand(["/keys"], { cwd }), /google-secret/);
    assert.match(await executeCommand(["/models", "local"], { cwd }), /local-deterministic/);
    assert.match(await executeCommand(["/model-set", "local-fast", "local"], { cwd }), /master model set/);

    assert.match(await executeCommand(["/skill-add", "API Validator"], { cwd }), /Skill added/);
    assert.match(await executeCommand(["/skill-edit", "API Validator", "Check", "status", "codes"], { cwd }), /Skill updated/);
    assert.match(await executeCommand(["/skill-info", "api-validator"], { cwd }), /Check status codes/);
    assert.match(await executeCommand(["/skill-remove", "API Validator", "--yes"], { cwd }), /Skill removed/);

    assert.match(await executeCommand(["/theme", "compact-dark"], { cwd }), /Theme set/);
    assert.match(await executeCommand(["/layout", "compact"], { cwd }), /Layout set/);
    assert.match(await executeCommand(["/panel-toggle", "status"], { cwd }), /Panel hidden/);
    assert.match(await executeCommand(["/tokens"], { cwd }), /Token tracking/);
    assert.match(await executeCommand(["/cost"], { cwd }), /\$0\.00/);

    assert.match(await executeCommand(["/file-write", "src/manual.txt", "hello", "world"], { cwd }), /Staged file write/);
    assert.match(await executeCommand(["/diff"], { cwd }), /src\/manual.txt/);

    assert.match(await executeCommand(["/supabase-rls", "customers"], { cwd }), /RLS preview generated/);
    assert.match(await executeCommand(["/supabase-seed", "customers"], { cwd }), /Seed preview generated/);
    assert.match(await executeCommand(["/supabase-schema"], { cwd }), /"tables"/);
    assert.match(await executeCommand(["/supabase-diff"], { cwd }), /Remote Supabase diff/);
    assert.match(await executeCommand(["/supabase-reset", "--yes"], { cwd }), /reset/);
  } finally {
    await cleanup(cwd);
  }
});

async function tempProject() {
  return mkdtemp(path.join(os.tmpdir(), "omnix-test-"));
}

async function cleanup(cwd) {
  await rm(cwd, { recursive: true, force: true });
}

async function exists(filePath) {
  try {
    await readFile(filePath);
    return true;
  } catch (error) {
    if (error?.code === "EISDIR") return true;
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}
