import { loadConfig, saveConfig } from "./brain.js";
import { PROVIDERS } from "./constants.js";
import { maskSecret, omnixPath, readJson, writeJson } from "./files.js";
import { buildProviderRegistry } from "./providers.js";

export async function providersStatus(cwd) {
  const config = await loadConfig(cwd);
  return Object.entries(config.providers || {})
    .map(([id, provider]) => `${id.padEnd(12)} ${provider.enabled ? "enabled" : "disabled"}  ${provider.name || ""}`)
    .join("\n");
}

export async function providerAdd(cwd, providerId, options = {}) {
  if (!providerId) throw new Error("Usage: /provider-add <provider> [--key value]");
  const config = await loadConfig(cwd);
  config.providers = config.providers || {};
  config.providers[providerId] = {
    ...(PROVIDERS[providerId] || { name: providerId }),
    ...(config.providers[providerId] || {}),
    enabled: true
  };
  await saveConfig(cwd, config);

  if (options.key) {
    const local = await readJson(omnixPath(cwd, "config.local.json"), {});
    local.providers = local.providers || {};
    local.providers[providerId] = { api_key: options.key };
    await writeJson(omnixPath(cwd, "config.local.json"), local, { mode: 0o600 });
  }

  return `Provider enabled: ${providerId}${options.key ? ` (${maskSecret(options.key)})` : ""}`;
}

export async function providerRemove(cwd, providerId) {
  if (!providerId) throw new Error("Usage: /provider-remove <provider>");
  const config = await loadConfig(cwd);
  config.providers = config.providers || {};
  config.providers[providerId] = {
    ...(config.providers[providerId] || { name: providerId }),
    enabled: false
  };
  await saveConfig(cwd, config);
  return `Provider disabled: ${providerId}`;
}

export async function listModels(providerId = "local") {
  const registry = buildProviderRegistry();
  const provider = registry[providerId] || registry.local;
  const models = await provider.listModels();
  return models.map((model) => `${model.id.padEnd(24)} ${model.name}`).join("\n");
}

export async function keyStatus(cwd) {
  const local = await readJson(omnixPath(cwd, "config.local.json"), {});
  const providers = Object.entries(local.providers || {}).map(([id, value]) => `${id}: ${maskSecret(value.api_key || "")}`);
  const supabase = local.supabase
    ? [
        `supabase.url: ${maskSecret(local.supabase.project_url || "")}`,
        `supabase.anon: ${maskSecret(local.supabase.anon_key || "")}`,
        `supabase.service: ${maskSecret(local.supabase.service_role_key || "")}`
      ]
    : [];
  const lines = [...providers, ...supabase];
  return lines.length ? lines.join("\n") : "No local keys stored.";
}

export async function keyUpdate(cwd, providerId, key) {
  if (!providerId || !key) throw new Error("Usage: /key-update <provider> <key>");
  return providerAdd(cwd, providerId, { key });
}

export async function endpointAdd(cwd, providerId, endpoint) {
  if (!providerId || !endpoint) throw new Error("Usage: /endpoint-add <provider> <url>");
  const config = await loadConfig(cwd);
  config.providers = config.providers || {};
  config.providers[providerId] = {
    ...(config.providers[providerId] || { name: providerId }),
    endpoint,
    enabled: true
  };
  await saveConfig(cwd, config);
  return `Endpoint saved for ${providerId}: ${endpoint}`;
}

export async function setCurrentModel(cwd, model, provider = null) {
  if (!model) throw new Error("Usage: /model-set <model> [provider]");
  const config = await loadConfig(cwd);
  const agent = config.default_agent || "master";
  config.agents[agent] = {
    ...(config.agents[agent] || {}),
    model,
    provider: provider || config.agents[agent]?.provider || "local"
  };
  await saveConfig(cwd, config);
  return `${agent} model set to ${config.agents[agent].provider}/${model}`;
}
