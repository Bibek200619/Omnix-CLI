import { spawnSync } from "node:child_process";
import path from "node:path";
import { listFiles, readJson, readText } from "./files.js";
import { nowIso } from "./files.js";
import { loadPending, savePending } from "./workflow.js";

const TEXT_EXTENSIONS = new Set([
  ".js",
  ".jsx",
  ".ts",
  ".tsx",
  ".json",
  ".md",
  ".css",
  ".scss",
  ".html",
  ".txt",
  ".yml",
  ".yaml",
  ".toml",
  ".py",
  ".go",
  ".rs",
  ".java",
  ".rb",
  ".php",
  ".sql",
  ".sh"
]);

export async function projectOverview(cwd) {
  const files = await listFiles(cwd, {
    maxDepth: 6,
    ignore: [".git", "node_modules", ".omnix/cache", ".omnix/pending"]
  });
  const packageJson = await readJson(path.join(cwd, "package.json"), {});
  const scripts = Object.keys(packageJson.scripts || {});
  const byExtension = {};

  for (const file of files) {
    if (file.endsWith("/")) continue;
    const extension = path.extname(file) || "(none)";
    byExtension[extension] = (byExtension[extension] || 0) + 1;
  }

  const topExtensions = Object.entries(byExtension)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([extension, count]) => `${extension}: ${count}`)
    .join(", ");

  return [
    `Project: ${path.basename(cwd)}`,
    `Files scanned: ${files.filter((file) => !file.endsWith("/")).length}`,
    `Top extensions: ${topExtensions || "none"}`,
    `Package scripts: ${scripts.length ? scripts.join(", ") : "none"}`,
    "",
    "Useful next commands:",
    "/search <text>",
    "/read <file> [start] [end]",
    "/explain <file>",
    "/test",
    "/build"
  ].join("\n");
}

export async function listPackageScripts(cwd) {
  const packageJson = await readJson(path.join(cwd, "package.json"), {});
  const scripts = packageJson.scripts || {};
  const entries = Object.entries(scripts);
  if (!entries.length) return "No package scripts found.";
  return entries.map(([name, command]) => `${name.padEnd(12)} ${command}`).join("\n");
}

export async function searchProject(cwd, query, options = {}) {
  if (!query) throw new Error("Usage: /search <text>");
  const maxResults = options.maxResults || 40;
  const files = await listFiles(cwd, {
    maxDepth: 8,
    ignore: [".git", "node_modules", ".omnix/cache", ".omnix/pending"]
  });
  const needle = query.toLowerCase();
  const matches = [];

  for (const relativePath of files) {
    if (matches.length >= maxResults) break;
    if (relativePath.endsWith("/") || !isLikelyTextFile(relativePath)) continue;
    const fullPath = resolveProjectPath(cwd, relativePath);
    const content = await readText(fullPath, "");
    const lines = content.split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
      if (!lines[index].toLowerCase().includes(needle)) continue;
      matches.push(`${relativePath}:${index + 1}: ${lines[index].trim()}`);
      if (matches.length >= maxResults) break;
    }
  }

  return matches.length ? matches.join("\n") : `No matches for "${query}".`;
}

export async function readProjectFile(cwd, relativePath, startLine = 1, endLine = null) {
  if (!relativePath) throw new Error("Usage: /read <file> [start] [end]");
  const fullPath = resolveProjectPath(cwd, relativePath);
  const content = await readText(fullPath, null);
  if (content === null) throw new Error(`File not found: ${relativePath}`);
  const lines = content.split(/\r?\n/);
  const start = Math.max(1, Number(startLine) || 1);
  const end = Math.min(lines.length, Number(endLine) || start + 119);
  const width = String(end).length;

  return lines
    .slice(start - 1, end)
    .map((line, index) => `${String(start + index).padStart(width, " ")} | ${line}`)
    .join("\n");
}

export async function explainProjectFile(cwd, relativePath) {
  if (!relativePath) throw new Error("Usage: /explain <file>");
  const fullPath = resolveProjectPath(cwd, relativePath);
  const content = await readText(fullPath, null);
  if (content === null) throw new Error(`File not found: ${relativePath}`);
  const lines = content.split(/\r?\n/);
  const imports = collectMatches(lines, /^\s*import\s+.+|require\(["'][^"']+["']\)/);
  const exports = collectMatches(lines, /^\s*export\s+/);
  const declarations = collectMatches(lines, /^\s*(export\s+)?(async\s+)?(function|class|const|let|var)\s+[A-Za-z0-9_$]+/);

  return [
    `File: ${relativePath}`,
    `Lines: ${lines.length}`,
    `Imports: ${imports.length}`,
    `Exports: ${exports.length}`,
    `Declarations: ${declarations.length}`,
    "",
    "Notable declarations:",
    ...(declarations.slice(0, 12).length ? declarations.slice(0, 12) : ["none"]),
    "",
    "Exports:",
    ...(exports.slice(0, 8).length ? exports.slice(0, 8) : ["none"])
  ].join("\n");
}

export async function runPackageScript(cwd, scriptName) {
  const packageJson = await readJson(path.join(cwd, "package.json"), {});
  const scripts = packageJson.scripts || {};
  if (!scripts[scriptName]) {
    return `No "${scriptName}" script found in package.json.`;
  }

  const result = spawnSync("npm", ["run", scriptName], {
    cwd,
    encoding: "utf8",
    timeout: 120000,
    maxBuffer: 1024 * 1024 * 4
  });
  const output = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
  const status = result.status === 0 ? "passed" : `failed (${result.status ?? "terminated"})`;
  return [`${scriptName}: ${status}`, output].filter(Boolean).join("\n\n");
}

export async function stageFileWrite(cwd, relativePath, content) {
  if (!relativePath || content === undefined) throw new Error("Usage: /file-write <file> <content>");
  resolveProjectPath(cwd, relativePath);
  const pending = (await loadPending(cwd)) || {
    id: `change-${Date.now()}`,
    created_at: nowIso(),
    request: `manual file write ${relativePath}`,
    files: [],
    migrations: []
  };
  pending.files = pending.files || [];
  pending.files.push({
    agent: "master",
    action: "write",
    path: relativePath,
    content: String(content)
  });
  pending.updated_at = nowIso();
  await savePending(cwd, pending);
  return `Staged file write: ${relativePath}\nRun /diff, /qa, then /apply.`;
}

function collectMatches(lines, pattern) {
  return lines
    .map((line, index) => ({ line, lineNumber: index + 1 }))
    .filter(({ line }) => pattern.test(line))
    .map(({ line, lineNumber }) => `${lineNumber}: ${line.trim()}`);
}

function resolveProjectPath(cwd, relativePath) {
  const target = path.resolve(cwd, relativePath);
  const root = path.resolve(cwd);
  if (target !== root && !target.startsWith(`${root}${path.sep}`)) {
    throw new Error(`Path escapes project root: ${relativePath}`);
  }
  return target;
}

function isLikelyTextFile(relativePath) {
  return TEXT_EXTENSIONS.has(path.extname(relativePath).toLowerCase());
}
