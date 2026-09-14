import { loadConfig, saveConfig } from "./brain.js";

export async function setTheme(cwd, theme = "omnix-dark") {
  const config = await loadConfig(cwd);
  config.ui = config.ui || {};
  config.ui.theme = theme;
  await saveConfig(cwd, config);
  return `Theme set to ${theme}.`;
}

export async function setLayout(cwd, layout = "split") {
  const config = await loadConfig(cwd);
  config.ui = config.ui || {};
  config.ui.layout = layout;
  await saveConfig(cwd, config);
  return `Layout set to ${layout}.`;
}

export function logo() {
  return [
    "OmniX CLI",
    "Multi-agent terminal coding workspace",
    "Plan, generate, review, QA, and apply code changes from one CLI."
  ].join("\n");
}

export async function focusPanel(cwd, panel = "chat") {
  const config = await loadConfig(cwd);
  config.ui = config.ui || {};
  config.ui.focus = panel;
  await saveConfig(cwd, config);
  return `Focus set to ${panel}.`;
}

export async function togglePanel(cwd, panel = "status") {
  const config = await loadConfig(cwd);
  config.ui = config.ui || {};
  config.ui.hidden_panels = config.ui.hidden_panels || [];
  if (config.ui.hidden_panels.includes(panel)) {
    config.ui.hidden_panels = config.ui.hidden_panels.filter((item) => item !== panel);
    await saveConfig(cwd, config);
    return `Panel shown: ${panel}.`;
  }
  config.ui.hidden_panels.push(panel);
  await saveConfig(cwd, config);
  return `Panel hidden: ${panel}.`;
}

export async function tokenStatus(cwd) {
  const config = await loadConfig(cwd);
  return [
    "Token tracking is local-estimate only in this MVP.",
    `Default agent: ${config.default_agent}`,
    "Input: 0",
    "Output: 0",
    "Cached: 0"
  ].join("\n");
}

export async function costStatus() {
  return "Estimated cost: $0.00 (local deterministic provider mode).";
}

export async function notifications(cwd, value = "toggle") {
  const config = await loadConfig(cwd);
  config.ui = config.ui || {};
  config.ui.notifications = value === "on" ? true : value === "off" ? false : !config.ui.notifications;
  await saveConfig(cwd, config);
  return `Notifications ${config.ui.notifications ? "enabled" : "disabled"}.`;
}
