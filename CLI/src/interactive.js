import { stdin as defaultStdin, stdout as defaultStdout } from "node:process";
import path from "node:path";
import { loadBrain } from "./brain.js";
import { executeCommand, splitArgs } from "./commands.js";
import { omnixPath, readJson } from "./files.js";
import { getAgentRuntime } from "./providers.js";
import { loadPending } from "./workflow.js";
import {
  completeSlashCommand,
  getCommandSuggestions,
  renderLayout,
  renderLogo,
  statusPanel
} from "./ui.js";

export async function runInteractive(cwd = process.cwd(), io = {}) {
  const stdin = io.stdin || defaultStdin;
  const stdout = io.stdout || defaultStdout;

  if (!stdin.isTTY || !stdout.isTTY) {
    const output = await executeCommand([], { cwd });
    stdout.write(`${output}\n`);
    return;
  }

  const state = {
    cwd,
    input: "",
    messages: [
      ...renderLogo().split("\n"),
      "",
      "OmniX CLI is ready.",
      "Type / for commands. Use arrows to scroll. Tab completes.",
      "Start with /init, /codebase, or /implement <task>."
    ],
    history: [],
    historyIndex: 0,
    commandIndex: 0,
    commandScroll: 0,
    busy: false
  };

  const previousRawMode = stdin.isRaw;
  stdin.setRawMode(true);
  stdin.resume();
  stdout.write("\u001b[?25l");

  await renderInteractiveState(state, stdout);

  await new Promise((resolve) => {
    let closed = false;

    const close = async () => {
      if (closed) return;
      closed = true;
      stdin.off("data", onData);
      if (typeof stdin.setRawMode === "function") stdin.setRawMode(Boolean(previousRawMode));
      stdin.pause();
      stdout.write("\u001b[?25h\n");
      resolve();
    };

    const onData = async (chunk) => {
      if (state.busy) return;
      await handleInputChunk(chunk.toString("utf8"), state, stdout, close);
    };

    stdin.on("data", onData);
  });
}

async function handleInputChunk(value, state, stdout, close) {
  for (let index = 0; index < value.length; index += 1) {
    const remaining = value.slice(index);
    const escapeSequence = readEscapeSequence(remaining);

    if (escapeSequence) {
      await handleKey(escapeSequence, state, stdout, close);
      index += escapeSequence.length - 1;
      continue;
    }

    const char = value[index];
    if (char === "\u0003") {
      state.messages.push("Interrupted.");
      await renderInteractiveState(state, stdout);
      await close();
      return;
    }

    await handleKey(char, state, stdout, close);
  }
}

export async function renderInteractiveState(state, stdout = defaultStdout) {
  const frame = await buildInteractiveFrame(state);
  stdout.write("\u001b[2J\u001b[H");
  stdout.write(frame);
}

export async function buildInteractiveFrame(state) {
  const initialized = Boolean(await readJson(omnixPath(state.cwd, "config.json"), null));
  const palette = commandPaletteForState(state);
  const main = selectMainLines(state.messages, palette.suggestions.length ? 10 : 20);

  if (!initialized) {
    return renderLayout({
      project: path.basename(state.cwd),
      activeAgent: "master",
      model: "local",
      main,
      status: decorateStatus([
        ["Status", "not initialized"],
        ["Next", "/init"],
        "",
        "Commands",
        "Type / to filter",
        "Use arrows to scroll"
      ], state),
      input: `OmniX > ${state.input}`,
      inputValue: state.input,
      suggestions: palette.suggestions,
      commandMeta: palette.meta,
      color: true,
      followTail: true
    });
  }

  const brain = await loadBrain(state.cwd);
  const pending = await loadPending(state.cwd);
  const agentId = brain.config.default_agent || "master";
  const runtime = getAgentRuntime(brain.config, agentId);

  return renderLayout({
    project: brain.config.project_name,
    activeAgent: agentId,
    model: runtime.model,
    main,
    status: decorateStatus(statusPanel(brain, pending), state),
    input: `OmniX > ${state.input}`,
    inputValue: state.input,
    suggestions: palette.suggestions,
    commandMeta: palette.meta,
    color: true,
    followTail: true
  });
}

async function handleKey(value, state, stdout, close) {
  if (value === "\r" || value === "\n") {
    if (acceptHighlightedCommand(state)) {
      await renderInteractiveState(state, stdout);
      return;
    }
    await submitInput(state, stdout, close);
    return;
  }

  if (value === "\u007f" || value === "\b") {
    state.input = state.input.slice(0, -1);
    resetCommandSelection(state);
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value === "\t") {
    if (!acceptHighlightedCommand(state)) state.input = completeSlashCommand(state.input);
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value === "\u000c") {
    state.messages = [];
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value === "\u001b[A") {
    if (hasCommandPalette(state)) moveCommandSelection(state, -1);
    else showHistory(state, -1);
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value === "\u001b[B") {
    if (hasCommandPalette(state)) moveCommandSelection(state, 1);
    else showHistory(state, 1);
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value === "\u001b[5~" || value === "\u001b[6~") {
    if (hasCommandPalette(state)) moveCommandSelection(state, value === "\u001b[5~" ? -commandWindowSize() : commandWindowSize());
    await renderInteractiveState(state, stdout);
    return;
  }

  if (value.startsWith("\u001b")) return;

  for (const char of value) {
    if (char >= " " && char !== "\u007f") state.input += char;
  }
  resetCommandSelection(state);
  await renderInteractiveState(state, stdout);
}

async function submitInput(state, stdout, close) {
  const command = state.input.trim();
  if (!command) {
    await renderInteractiveState(state, stdout);
    return;
  }

  state.history.push(command);
  state.historyIndex = state.history.length;
  state.messages.push(`OmniX > ${command}`);
  state.input = "";
  resetCommandSelection(state);
  state.busy = true;
  await renderInteractiveState(state, stdout);

  try {
    const output = await executeCommand(splitArgs(command), {
      cwd: state.cwd,
      frame: false
    });
    if (command === "/clear" || command === "clear") {
      state.messages = [];
    } else if (output) {
      state.messages.push(...String(output).split(/\r?\n/));
    }
    if (command === "/exit" || command === "exit") {
      await renderInteractiveState(state, stdout);
      await close();
      return;
    }
  } catch (error) {
    state.messages.push(`Error: ${error?.message || String(error)}`);
  } finally {
    state.busy = false;
  }

  await renderInteractiveState(state, stdout);
}

function showHistory(state, direction) {
  if (!state.history.length) return;
  state.historyIndex = Math.max(0, Math.min(state.history.length, state.historyIndex + direction));
  state.input = state.history[state.historyIndex] || "";
}

function selectMainLines(lines, limit) {
  const flat = lines.flatMap((line) => String(line).split(/\r?\n/));
  return flat.slice(Math.max(0, flat.length - limit));
}

function readEscapeSequence(value) {
  return ["\u001b[5~", "\u001b[6~", "\u001b[A", "\u001b[B"].find((sequence) => value.startsWith(sequence));
}

function commandPaletteForState(state) {
  const all = getCommandSuggestions(state.input, 200);
  if (!all.length) return { suggestions: [], meta: {} };

  const limit = commandWindowSize();
  const selectedIndex = clamp(state.commandIndex ?? 0, 0, all.length - 1);
  const maxScroll = Math.max(0, all.length - limit);
  let offset = clamp(state.commandScroll ?? 0, 0, maxScroll);

  if (selectedIndex < offset) offset = selectedIndex;
  if (selectedIndex >= offset + limit) offset = selectedIndex - limit + 1;

  state.commandIndex = selectedIndex;
  state.commandScroll = offset;

  return {
    suggestions: all.slice(offset, offset + limit),
    meta: {
      total: all.length,
      offset,
      selectedIndex
    }
  };
}

function hasCommandPalette(state) {
  return String(state.input || "").startsWith("/") && getCommandSuggestions(state.input, 1).length > 0;
}

function moveCommandSelection(state, delta) {
  const all = getCommandSuggestions(state.input, 200);
  if (!all.length) return;
  const next = clamp((state.commandIndex ?? 0) + delta, 0, all.length - 1);
  state.commandIndex = next;
  const limit = commandWindowSize();
  if (next < (state.commandScroll ?? 0)) state.commandScroll = next;
  if (next >= (state.commandScroll ?? 0) + limit) state.commandScroll = next - limit + 1;
}

function resetCommandSelection(state) {
  state.commandIndex = 0;
  state.commandScroll = 0;
}

function acceptHighlightedCommand(state) {
  const input = String(state.input || "");
  if (!input.startsWith("/")) return false;
  const trimmed = input.trim();
  if (!trimmed || trimmed.includes(" ")) return false;

  const all = getCommandSuggestions(input, 200);
  if (!all.length) return false;
  const selected = all[clamp(state.commandIndex ?? 0, 0, all.length - 1)];
  if (!selected) return false;

  const exact = selected.command === trimmed;
  if (exact && trimmed !== "/") return false;

  state.input = `${selected.command} `;
  return true;
}

function commandWindowSize() {
  const rows = Number(process.stdout.rows || 32);
  return clamp(Math.floor(rows * 0.35), 6, 14);
}

function decorateStatus(status, state) {
  return [["CLI", state.busy ? "running" : "ready"], ...status];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(value, max));
}
