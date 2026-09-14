import path from "node:path";
import { AGENTS, COMMAND_GROUPS } from "./constants.js";

const ANSI = {
  reset: "\u001b[0m",
  dim: "\u001b[2m",
  bold: "\u001b[1m",
  blue: "\u001b[38;5;39m",
  cyan: "\u001b[38;5;45m",
  red: "\u001b[38;5;196m",
  green: "\u001b[38;5;83m",
  yellow: "\u001b[38;5;220m",
  gray: "\u001b[38;5;245m",
  dark: "\u001b[38;5;238m",
  bg: "\u001b[48;5;235m",
  composerBg: "\u001b[48;5;238m"
};

export function renderLogo() {
  return [
    "  ____                  _ __  __",
    " / __ \\ _ __ ___  _ __ (_) \\/ /",
    "| |  | | '_ ` _ \\| '_ \\| |\\  / ",
    "| |__| | | | | | | | | | |/  \\ ",
    " \\____/|_| |_| |_|_| |_|_/_/\\_\\"
  ].join("\n");
}

export function renderLayout(options = {}) {
  const terminalWidth = Number(options.width || process.stdout.columns || 112);
  const width = clamp(Number.isFinite(terminalWidth) ? terminalWidth : 112, 88, 240);
  const height = Math.max(22, options.height || process.stdout.rows || 32);
  const color = options.color ?? (Boolean(process.stdout.isTTY) && !process.env.NO_COLOR);
  const paintWith = (value, tone, bold = false) => color ? paint(value, tone, bold) : value;
  const dim = (value) => color ? paint(value, "gray") : value;

  const project = options.project || path.basename(process.cwd());
  const activeAgent = options.activeAgent || "master";
  const model = options.model || "local";
  const input = options.input || "OmniX >";
  const inputValue = options.inputValue;
  const placeholder = options.placeholder || "Implement {feature}";
  const suggestions = options.suggestions || [];
  const commandPalette = renderCommandPalette(suggestions, width, color, options.commandMeta || {});
  const composer = renderComposer({ input, inputValue, placeholder, width, color });

  const sidebarWidth = clamp(Math.floor(width * 0.3), 34, 52);
  const split = color ? paint("│", "dark") : "│";
  const splitText = `  ${split}  `;
  const splitWidth = 5;
  const mainWidth = width - sidebarWidth - splitWidth;
  const reserved = 8 + composer.split("\n").length + commandPalette.length;
  const bodyHeight = Math.max(8, height - reserved);
  const mainLines = prepareMainLines(options.main || [], mainWidth, bodyHeight, Boolean(options.followTail));
  const statusLines = prepareStatusLines(options.status || [], sidebarWidth, bodyHeight, color);

  const title = `${paintWith("OmniX", "blue", true)} ${paintWith("CLI", "red", true)}`;
  const meta = `${dim("Project")} ${project}  ${dim("Agent")} ${labelAgent(activeAgent)}  ${dim("Model")} ${model}`;
  const header = fitVisible(`${title}  ${meta}`, width);
  const rule = dim("─".repeat(width));
  const sectionHeader = [
    fitVisible(paintWith("Workspace", "cyan", true), mainWidth),
    splitText,
    fitVisible(paintWith("Status", "cyan", true), sidebarWidth)
  ].join("");
  const rows = [];

  for (let index = 0; index < bodyHeight; index += 1) {
    rows.push(`${fit(mainLines[index] || "", mainWidth)}${splitText}${fit(statusLines[index] || "", sidebarWidth)}`);
  }

  return [
    header,
    rule,
    sectionHeader,
    "",
    ...rows,
    "",
    rule,
    composer,
    ...commandPalette,
    renderFooter({ model, project, width, color })
  ].join("\n");
}

export function renderHelp() {
  const rows = COMMAND_GROUPS.map(([command, description]) => `${command.padEnd(40)} ${description}`);
  return [renderLogo(), "", "Commands", ...rows].join("\n");
}

export function renderAgentStatus(config) {
  return Object.entries(AGENTS).map(([id, agent]) => {
    const assigned = config.agents?.[id] || {};
    return `${agent.name.padEnd(24)} ${assigned.provider || agent.defaultProvider}/${assigned.model || agent.defaultModel}`;
  });
}

export function statusPanel(brain, pending = null) {
  const config = brain.config;
  const agent = config.default_agent || "master";
  const assigned = config.agents?.[agent] || {};
  const taskState = pending?.state || {};
  const pendingFileCount = pending?.files?.length || 0;
  const pendingMigrationCount = pending?.migrations?.length || 0;
  const pendingFiles = pending
    ? [...(pending.files || []).map((file) => file.path), ...(pending.migrations || []).map((item) => item.path)]
    : brain.fileIndex.modified_files || [];
  const steps = pending?.steps?.length
    ? pending.steps.map((step) => `${step.status === "completed" ? "done" : step.status}: ${step.agent}`)
    : ["idle"];

  return [
    ["Project", config.project_name],
    ["Task", compactValue(pending?.request || "none", 34)],
    ["Status", taskState.status || (pending ? "pending review" : "idle")],
    ["Phase", taskState.phase || (pending ? "review" : "ready")],
    ["Agent", labelAgent(agent)],
    ["Model", assigned.model || "not set"],
    ["QA", brain.qaMemory.latest_status || "not_run"],
    ["Pending", `${pendingFileCount} files, ${pendingMigrationCount} sql`],
    ["Next", taskState.next || (pending ? "/diff then /apply" : "/implement <task>")],
    "",
    "Environment",
    `Rules: ${brain.rules ? "loaded" : "missing"}`,
    `Skills: ${brain.skills.length}`,
    `Providers: ${providerSummary(config)}`,
    `Supabase: ${config.supabase?.connected ? "connected" : "not connected"}`,
    "",
    "Agents",
    ...steps.slice(0, 5),
    "",
    "Changed Files",
    ...(pendingFiles.length ? pendingFiles.slice(0, 6) : ["none"])
  ];
}

export function getCommandSuggestions(inputValue, limit = 12) {
  if (!String(inputValue || "").startsWith("/")) return [];
  const rawQuery = String(inputValue).slice(1).trimStart().toLowerCase();
  const query = rawQuery.split(/\s+/)[0] || "";

  const scored = COMMAND_GROUPS.map(([usage, description], index) => {
    const command = usage.split(/\s+/)[0];
    const commandName = command.slice(1).toLowerCase();
    let score = 0;
    if (!query) score = 1;
    else if (commandName === query) score = 100;
    else if (commandName.startsWith(query)) score = 80;
    else if (commandName.includes(query)) score = 40;
    return { usage, description, command, score, index };
  })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index);

  return scored.slice(0, limit);
}

export function completeSlashCommand(inputValue) {
  const suggestions = getCommandSuggestions(inputValue, 1);
  if (!suggestions.length) return inputValue;
  const command = suggestions[0].command;
  const rest = String(inputValue).replace(/^\/[^\s]*/, "").trimStart();
  return rest ? `${command} ${rest}` : `${command} `;
}

export function formatDiff(pending) {
  if (!pending) return "No pending changes.";
  const lines = ["Pending Changes", ""];
  if (pending.state) {
    lines.push(`Task: ${pending.request || "unknown"}`);
    lines.push(`Status: ${pending.state.status || "unknown"}`);
    lines.push(`Phase: ${pending.state.phase || "unknown"}`);
    lines.push(`Progress: ${pending.state.progress ?? 0}%`);
    lines.push(`Next: ${pending.state.next || "/apply after review"}`);
    if (pending.state.error) lines.push(`Error: ${pending.state.error}`);
    lines.push("");
  }
  if (pending.steps?.length) {
    lines.push("Agent Steps");
    for (const step of pending.steps) {
      lines.push(`- ${step.agent}: ${step.status}`);
    }
    lines.push("");
  }
  for (const file of pending.files || []) {
    lines.push(`+ ${file.path} (${file.agent})`);
  }
  for (const migration of pending.migrations || []) {
    lines.push(`+ ${migration.path} (database migration)`);
  }
  if (pending.qa) {
    lines.push("", `QA: ${pending.qa.status}`);
    for (const error of pending.qa.errors || []) {
      lines.push(`- ${error.severity}: ${error.details}`);
    }
    for (const warning of pending.qa.warnings || []) {
      lines.push(`- warning: ${typeof warning === "string" ? warning : warning.details}`);
    }
  }
  return lines.join("\n");
}

export function formatQaReport(report) {
  if (!report) return "QA has not run.";
  const lines = [
    "QA Result",
    `Status: ${report.status}`,
    `Errors: ${report.errors?.length || 0}`,
    `Warnings: ${report.warnings?.length || 0}`
  ];
  for (const error of report.errors || []) {
    lines.push(`- ${error.error_type}: ${error.details}`);
  }
  for (const warning of report.warnings || []) {
    lines.push(`- warning: ${typeof warning === "string" ? warning : warning.details}`);
  }
  return lines.join("\n");
}

function renderCommandPalette(suggestions, width, color, meta = {}) {
  if (!suggestions.length) return [];
  const paletteWidth = width;
  const total = meta.total ?? suggestions.length;
  const offset = meta.offset ?? 0;
  const selectedIndex = meta.selectedIndex ?? offset;
  const start = Math.min(offset + 1, total);
  const end = Math.min(offset + suggestions.length, total);
  const rows = [];

  const header = `Commands ${start}-${end} of ${total}   Up/Down scroll   Enter select   Tab complete`;
  rows.push(color ? paint(fitVisible(header, paletteWidth), "gray") : fitVisible(header, paletteWidth));

  for (let index = 0; index < suggestions.length; index += 1) {
    rows.push(formatSuggestion(suggestions[index], paletteWidth, color, {
      selected: offset + index === selectedIndex
    }));
  }

  return rows;
}

function formatSuggestion(suggestion, width, color, options = {}) {
  if (!suggestion) return " ".repeat(width);
  const commandWidth = clamp(Math.floor(width * 0.34), 20, 42);
  const descriptionWidth = width - commandWidth - 5;
  const marker = options.selected ? "›" : " ";
  const plainCommand = fit(suggestion.usage, commandWidth);
  const plain = fitVisible(`${marker} ${plainCommand}  ${fit(suggestion.description, descriptionWidth)}`, width);

  if (options.selected && color) {
    return `${ANSI.composerBg}${ANSI.cyan}${plain}${ANSI.reset}`;
  }

  const command = color ? paint(plainCommand, "cyan", true) : plainCommand;
  return fitVisible(`${marker} ${command}  ${fit(suggestion.description, descriptionWidth)}`, width);
}

function renderComposer({ input, inputValue, placeholder, width, color }) {
  const rawValue = inputValue ?? String(input).replace(/^OmniX\s*>\s*/, "");
  const hasValue = String(rawValue || "").length > 0;
  const display = hasValue ? rawValue : placeholder;
  const promptLine = fitVisible(`  › ${display}`, width);
  const hintLine = fitVisible("    Enter to send   / commands   Tab complete   Ctrl+C exit", width);
  const blankLine = " ".repeat(width);

  if (!color) return [blankLine, promptLine, hintLine].join("\n");

  const promptTone = hasValue ? "" : ANSI.gray;
  return [
    `${ANSI.composerBg}${blankLine}${ANSI.reset}`,
    `${ANSI.composerBg}${promptTone}${promptLine}${ANSI.reset}`,
    `${ANSI.composerBg}${ANSI.gray}${hintLine}${ANSI.reset}`
  ].join("\n");
}

function renderFooter({ model, project, width, color }) {
  const text = `${model} · ${project}`;
  return color ? paint(fitVisible(text, width), "gray") : fitVisible(text, width);
}

function prepareMainLines(value, width, limit, followTail = false) {
  const source = normalizeLines(value);
  const wrapped = source.flatMap((line) => wrapLine(line, width));
  return followTail ? wrapped.slice(Math.max(0, wrapped.length - limit)) : wrapped.slice(0, limit);
}

function prepareStatusLines(value, width, limit, color) {
  const lines = [];
  for (const item of value) {
    if (Array.isArray(item)) {
      const [label, detail] = item;
      const key = color ? paint(fit(String(label), 10), "gray") : fit(String(label), 10);
      lines.push(`${key} ${fit(String(detail), width - 11)}`);
    } else {
      lines.push(...wrapLine(String(item || ""), width));
    }
  }
  return lines.slice(0, limit);
}

function normalizeLines(value) {
  if (Array.isArray(value)) return value.flatMap((line) => String(line).split(/\r?\n/));
  return String(value || "").split(/\r?\n/);
}

function wrapLine(value, width) {
  const text = String(value);
  if (!text) return [""];
  if (/^\s/.test(text) || /\s{2,}/.test(text)) return hardWrap(text, width);
  const words = text.split(/\s+/);
  const rows = [];
  let current = "";

  for (const word of words) {
    if (!current) {
      current = word;
      continue;
    }
    if (stripAnsi(`${current} ${word}`).length <= width) {
      current += ` ${word}`;
    } else {
      rows.push(current);
      current = word;
    }
  }

  if (current) rows.push(current);
  return rows.flatMap((line) => hardWrap(line, width));
}

function hardWrap(value, width) {
  const clean = stripAnsi(value);
  if (clean.length <= width) return [value];
  const rows = [];
  for (let index = 0; index < clean.length; index += width) {
    rows.push(clean.slice(index, index + width));
  }
  return rows;
}

function labelAgent(agentId) {
  return AGENTS[agentId]?.name?.replace(" Agent", "") || agentId;
}

function providerSummary(config) {
  const enabled = Object.entries(config.providers || {})
    .filter(([, provider]) => provider.enabled)
    .map(([id]) => id);
  return enabled.length ? enabled.join(", ") : "none";
}

function compactValue(value, maxLength) {
  const text = String(value || "");
  if (text.length <= maxLength) return text;
  return `${text.slice(0, Math.max(0, maxLength - 1))}~`;
}

function fit(value, width) {
  const clean = stripAnsi(String(value));
  if (clean.length === width) return value;
  if (clean.length < width) return `${value}${" ".repeat(width - clean.length)}`;
  return `${clean.slice(0, Math.max(0, width - 1))}~`;
}

function fitVisible(value, width) {
  return fit(value, width);
}

function stripAnsi(value) {
  return value.replace(/\u001b\[[0-9;]*m/g, "");
}

function paint(value, color, bold = false) {
  const prefix = `${bold ? ANSI.bold : ""}${ANSI[color] || ""}`;
  return `${prefix}${value}${ANSI.reset}`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(value, max));
}
