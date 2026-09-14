import { appendFile, chmod, mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { OMNIX_DIR } from "./constants.js";

export function projectPath(cwd, ...parts) {
  return path.join(cwd, ...parts);
}

export function omnixPath(cwd, ...parts) {
  return projectPath(cwd, OMNIX_DIR, ...parts);
}

export async function pathExists(filePath) {
  try {
    await stat(filePath);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

export async function ensureDir(dirPath) {
  await mkdir(dirPath, { recursive: true });
}

export async function readText(filePath, fallback = "") {
  try {
    return await readFile(filePath, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") return fallback;
    throw error;
  }
}

export async function writeText(filePath, value, options = {}) {
  await ensureDir(path.dirname(filePath));
  await writeFile(filePath, value, "utf8");
  if (options.mode) await chmod(filePath, options.mode);
}

export async function readJson(filePath, fallback = null) {
  const text = await readText(filePath, "");
  if (!text.trim()) return fallback;
  return JSON.parse(text);
}

export async function writeJson(filePath, value, options = {}) {
  await writeText(filePath, `${JSON.stringify(value, null, 2)}\n`, options);
}

export async function appendLog(filePath, value) {
  await ensureDir(path.dirname(filePath));
  await appendFile(filePath, `${value}\n`, "utf8");
}

export function maskSecret(value) {
  if (!value) return "";
  const text = String(value);
  if (text.length <= 4) return "****";
  if (text.length <= 8) return `${text.slice(0, 2)}****${text.slice(-2)}`;
  return `${text.slice(0, 4)}****${text.slice(-4)}`;
}

export function slugify(value, fallback = "item") {
  const slug = String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || fallback;
}

export function titleCase(value) {
  return String(value || "")
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export async function listFiles(root, options = {}) {
  const ignore = new Set(options.ignore || [".git", "node_modules", ".omnix/cache"]);
  const maxDepth = options.maxDepth ?? 4;
  const output = [];

  async function walk(current, depth) {
    if (depth > maxDepth) return;
    const entries = await readdir(current, { withFileTypes: true }).catch((error) => {
      if (error?.code === "ENOENT") return [];
      throw error;
    });

    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      const relative = path.relative(root, fullPath);
      const ignored = [...ignore].some((item) => relative === item || relative.startsWith(`${item}${path.sep}`));
      if (ignored) continue;

      if (entry.isDirectory()) {
        output.push(`${relative}/`);
        await walk(fullPath, depth + 1);
      } else {
        output.push(relative);
      }
    }
  }

  await walk(root, 0);
  return output.sort();
}

export function nowIso() {
  return new Date().toISOString();
}

export function timestampId(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}
