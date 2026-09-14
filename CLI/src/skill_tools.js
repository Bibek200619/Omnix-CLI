import { rm } from "node:fs/promises";
import path from "node:path";
import { scanSkills } from "./brain.js";
import { AGENTS_DIR } from "./constants.js";
import { pathExists, projectPath, readText, slugify, writeText } from "./files.js";

export async function skillAdd(cwd, name, body = "") {
  if (!name) throw new Error("Usage: /skill-add <name> [instructions]");
  const fileName = `${slugify(name)}.md`;
  const target = projectPath(cwd, AGENTS_DIR, "skills", fileName);
  if (await pathExists(target)) return `Skill already exists: ${path.join(AGENTS_DIR, "skills", fileName)}`;
  const content = body || [
    `# Skill: ${name}`,
    "",
    "## When to use",
    "",
    "- Describe when this skill should be used.",
    "",
    "## Rules",
    "",
    "- Add concrete rules here.",
    "",
    "## Output",
    "",
    "- Describe the expected output."
  ].join("\n");
  await writeText(target, `${content}\n`);
  return `Skill added: ${path.join(AGENTS_DIR, "skills", fileName)}`;
}

export async function skillInfo(cwd, name) {
  const skills = await scanSkills(cwd);
  if (!name) return skills.length ? skills.map((skill) => `${skill.name} - ${skill.path}`).join("\n") : "No skills found.";
  const target = skills.find((skill) => skill.path.includes(slugify(name)) || skill.name.toLowerCase().includes(name.toLowerCase()));
  if (!target) return `Skill not found: ${name}`;
  return await readText(projectPath(cwd, target.path), "");
}

export async function skillEdit(cwd, name, text) {
  if (!name || !text) throw new Error("Usage: /skill-edit <name> <text>");
  const fileName = `${slugify(name)}.md`;
  const target = projectPath(cwd, AGENTS_DIR, "skills", fileName);
  const existing = await readText(target, `# Skill: ${name}\n`);
  await writeText(target, `${existing.trimEnd()}\n\n${text}\n`);
  return `Skill updated: ${path.join(AGENTS_DIR, "skills", fileName)}`;
}

export async function skillRemove(cwd, name, confirmed = false) {
  if (!name) throw new Error("Usage: /skill-remove <name> --yes");
  if (!confirmed) return "Skill not removed. Re-run with --yes to confirm.";
  const fileName = `${slugify(name)}.md`;
  const target = projectPath(cwd, AGENTS_DIR, "skills", fileName);
  if (!(await pathExists(target))) return `Skill not found: ${path.join(AGENTS_DIR, "skills", fileName)}`;
  await rm(target);
  return `Skill removed: ${path.join(AGENTS_DIR, "skills", fileName)}`;
}
