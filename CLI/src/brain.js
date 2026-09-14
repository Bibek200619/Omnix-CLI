import path from "node:path";
import {
  AGENTS_DIR,
  BLUEPRINT_FILES,
  MEMORY_FILES,
  OMNIX_DIR
} from "./constants.js";
import {
  appendLog,
  ensureDir,
  listFiles,
  nowIso,
  omnixPath,
  pathExists,
  projectPath,
  readJson,
  readText,
  writeJson,
  writeText
} from "./files.js";
import {
  defaultAgentMemory,
  defaultChatMemory,
  defaultConfig,
  defaultDatabaseSchema,
  defaultFileIndex,
  defaultProjectMemory,
  defaultQaMemory,
  defaultRouteMap,
  omnixMarkdownTemplate
} from "./templates.js";

const MEMORY_DEFAULTS = {
  [MEMORY_FILES.project]: defaultProjectMemory,
  [MEMORY_FILES.chat]: defaultChatMemory,
  [MEMORY_FILES.agent]: defaultAgentMemory,
  [MEMORY_FILES.qa]: defaultQaMemory,
  [MEMORY_FILES.fileIndex]: defaultFileIndex,
  [MEMORY_FILES.routeMap]: defaultRouteMap,
  [MEMORY_FILES.databaseSchema]: defaultDatabaseSchema
};

export async function initProject(cwd, options = {}) {
  const projectName = path.basename(cwd);
  const created = [];

  for (const dir of [
    projectPath(cwd, AGENTS_DIR, "skills"),
    omnixPath(cwd, "memory"),
    omnixPath(cwd, "blueprint"),
    omnixPath(cwd, "logs"),
    omnixPath(cwd, "cache"),
    omnixPath(cwd, "pending"),
    omnixPath(cwd, "pending", "migrations")
  ]) {
    if (!(await pathExists(dir))) created.push(path.relative(cwd, dir));
    await ensureDir(dir);
  }

  const configPath = omnixPath(cwd, "config.json");
  if (options.force || !(await pathExists(configPath))) {
    await writeJson(configPath, defaultConfig(cwd));
    created.push(path.relative(cwd, configPath));
  }

  const localIgnorePath = omnixPath(cwd, ".gitignore");
  if (!(await pathExists(localIgnorePath))) {
    await writeText(localIgnorePath, "config.local.json\ncache/\npending/\n");
    created.push(path.relative(cwd, localIgnorePath));
  }

  const behaviorPath = projectPath(cwd, "OmniX.md");
  if (options.force || !(await pathExists(behaviorPath))) {
    await writeText(behaviorPath, omnixMarkdownTemplate(projectName));
    created.push("OmniX.md");
  }

  for (const [memoryFile, factory] of Object.entries(MEMORY_DEFAULTS)) {
    const target = omnixPath(cwd, memoryFile);
    if (options.force || !(await pathExists(target))) {
      await writeJson(target, factory(cwd));
      created.push(path.relative(cwd, target));
    }
  }

  for (const blueprintFile of Object.values(BLUEPRINT_FILES)) {
    const target = omnixPath(cwd, blueprintFile);
    if (!(await pathExists(target))) {
      await writeJson(target, {});
      created.push(path.relative(cwd, target));
    }
  }

  await appendAgentLog(cwd, {
    agent: "master",
    event: "init",
    details: "OmniX project brain initialized."
  });

  return { projectName, created };
}

export async function assertInitialized(cwd) {
  const configPath = omnixPath(cwd, "config.json");
  if (!(await pathExists(configPath))) {
    throw new Error("OmniX is not initialized in this project. Run `omnix init` first.");
  }
}

export async function loadConfig(cwd) {
  await assertInitialized(cwd);
  return readJson(omnixPath(cwd, "config.json"), {});
}

export async function saveConfig(cwd, config) {
  await writeJson(omnixPath(cwd, "config.json"), config);
}

export async function loadMemory(cwd, key) {
  await assertInitialized(cwd);
  const file = MEMORY_FILES[key] || key;
  return readJson(omnixPath(cwd, file), {});
}

export async function saveMemory(cwd, key, value) {
  const file = MEMORY_FILES[key] || key;
  await writeJson(omnixPath(cwd, file), value);
}

export async function loadBrain(cwd) {
  await assertInitialized(cwd);
  return {
    config: await loadConfig(cwd),
    rules: await readText(projectPath(cwd, "OmniX.md"), ""),
    projectMemory: await loadMemory(cwd, "project"),
    chatMemory: await loadMemory(cwd, "chat"),
    agentMemory: await loadMemory(cwd, "agent"),
    qaMemory: await loadMemory(cwd, "qa"),
    fileIndex: await loadMemory(cwd, "fileIndex"),
    routeMap: await loadMemory(cwd, "routeMap"),
    databaseSchema: await loadMemory(cwd, "databaseSchema"),
    skills: await scanSkills(cwd)
  };
}

export async function scanSkills(cwd) {
  const skillsDir = projectPath(cwd, AGENTS_DIR, "skills");
  const files = await listFiles(skillsDir, { maxDepth: 2, ignore: [] }).catch(() => []);
  const markdown = files.filter((file) => file.endsWith(".md"));
  const skills = [];

  for (const file of markdown) {
    const fullPath = path.join(skillsDir, file);
    const content = await readText(fullPath, "");
    const title = content.match(/^#\s+(.+)$/m)?.[1]?.trim() || path.basename(file, ".md");
    skills.push({
      name: title,
      path: path.join(AGENTS_DIR, "skills", file),
      preview: content.split(/\r?\n/).slice(0, 6).join("\n")
    });
  }

  return skills;
}

export async function updateFileIndex(cwd) {
  const fileIndex = await loadMemory(cwd, "fileIndex");
  const files = await listFiles(cwd, {
    maxDepth: 5,
    ignore: [".git", "node_modules", ".omnix/cache", ".omnix/pending"]
  });
  fileIndex.files = files;
  fileIndex.last_scan = nowIso();
  await saveMemory(cwd, "fileIndex", fileIndex);
  return fileIndex;
}

export async function appendAgentLog(cwd, entry) {
  const enriched = { at: nowIso(), ...entry };
  await appendLog(omnixPath(cwd, "logs", "agent-runs.log"), JSON.stringify(enriched));

  if (await pathExists(omnixPath(cwd, "memory", "agent.memory.json"))) {
    const agentMemory = await loadMemory(cwd, "agent");
    agentMemory.runs = agentMemory.runs || [];
    agentMemory.runs.push(enriched);
    agentMemory.runs = agentMemory.runs.slice(-100);
    await saveMemory(cwd, "agent", agentMemory);
  }
}

export async function appendQaReport(cwd, report) {
  const enriched = { at: nowIso(), ...report };
  await appendLog(omnixPath(cwd, "logs", "qa-audit.log"), JSON.stringify(enriched));

  const qaMemory = await loadMemory(cwd, "qa");
  qaMemory.reports = qaMemory.reports || [];
  qaMemory.reports.push(enriched);
  qaMemory.reports = qaMemory.reports.slice(-50);
  qaMemory.latest_status = report.status;
  await saveMemory(cwd, "qa", qaMemory);
}

export async function updateGeneratedFiles(cwd, files) {
  const projectMemory = await loadMemory(cwd, "project");
  const fileIndex = await loadMemory(cwd, "fileIndex");
  const unique = new Set([...(projectMemory.generated_files || []), ...files]);
  projectMemory.generated_files = [...unique].sort();
  fileIndex.generated_files = [...new Set([...(fileIndex.generated_files || []), ...files])].sort();
  fileIndex.modified_files = [];
  await saveMemory(cwd, "project", projectMemory);
  await saveMemory(cwd, "fileIndex", fileIndex);
}

export async function compactChatMemory(cwd, summary) {
  const chatMemory = await loadMemory(cwd, "chat");
  chatMemory.compacted = {
    summary,
    compacted_at: nowIso()
  };
  chatMemory.sessions = [];
  await saveMemory(cwd, "chat", chatMemory);
  return chatMemory.compacted;
}
