import { compactChatMemory, loadMemory, saveMemory, updateFileIndex } from "./brain.js";
import { loadPending } from "./workflow.js";

export async function contextSummary(cwd) {
  const project = await loadMemory(cwd, "project");
  const chat = await loadMemory(cwd, "chat");
  const fileIndex = await loadMemory(cwd, "fileIndex");
  const pending = await loadPending(cwd);
  return [
    `Project: ${project.project_name}`,
    `Generated files: ${(project.generated_files || []).length}`,
    `Known issues: ${(project.known_issues || []).length}`,
    `Chat sessions: ${(chat.sessions || []).length}`,
    `Indexed files: ${(fileIndex.files || []).length}`,
    `Pending files: ${pending ? (pending.files || []).length + (pending.migrations || []).length : 0}`
  ].join("\n");
}

export async function contextFiles(cwd) {
  const fileIndex = await updateFileIndex(cwd);
  return (fileIndex.files || []).slice(0, 200).join("\n") || "No files indexed.";
}

export async function pinInstruction(cwd, text) {
  if (!text) throw new Error("Usage: /pin <instruction>");
  const project = await loadMemory(cwd, "project");
  project.pins = project.pins || [];
  project.pins.push(text);
  await saveMemory(cwd, "project", project);
  return `Pinned: ${text}`;
}

export async function unpinInstruction(cwd, value) {
  const project = await loadMemory(cwd, "project");
  const pins = project.pins || [];
  if (!pins.length) return "No pins to remove.";
  const index = Number(value);
  if (Number.isInteger(index) && index >= 1 && index <= pins.length) {
    const [removed] = pins.splice(index - 1, 1);
    project.pins = pins;
    await saveMemory(cwd, "project", project);
    return `Unpinned: ${removed}`;
  }
  project.pins = pins.filter((pin) => pin !== value);
  await saveMemory(cwd, "project", project);
  return `Pins remaining: ${project.pins.length}`;
}

export async function summarizeConversation(cwd) {
  const project = await loadMemory(cwd, "project");
  const summary = {
    summary: `Working on ${project.project_name}.`,
    decisions: project.decisions || [],
    open_tasks: project.open_tasks || [],
    known_issues: project.known_issues || [],
    pins: project.pins || []
  };
  await compactChatMemory(cwd, summary);
  return JSON.stringify(summary, null, 2);
}

export async function memoryUpdate(cwd, category, text) {
  if (!category || !text) throw new Error("Usage: /memory-update <decisions|open_tasks|known_issues|known_rules> <text>");
  const project = await loadMemory(cwd, "project");
  const key = normalizeKey(category);
  project[key] = project[key] || [];
  project[key].push(text);
  await saveMemory(cwd, "project", project);
  return `Updated ${key}: ${text}`;
}

export async function memoryReset(cwd, category) {
  if (!category) throw new Error("Usage: /memory-reset <known_issues|open_tasks|decisions|pins>");
  const project = await loadMemory(cwd, "project");
  const key = normalizeKey(category);
  if (!Array.isArray(project[key])) return `Memory key is not resettable: ${key}`;
  project[key] = [];
  await saveMemory(cwd, "project", project);
  return `Reset ${key}.`;
}

function normalizeKey(value) {
  const key = String(value).replace(/-/g, "_");
  if (key === "tasks") return "open_tasks";
  if (key === "issues") return "known_issues";
  if (key === "rules") return "known_rules";
  return key;
}
