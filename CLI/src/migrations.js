import path from "node:path";
import { loadMemory, saveMemory } from "./brain.js";
import { maskSecret, nowIso, omnixPath, readJson, timestampId, writeJson, writeText } from "./files.js";
import { slugify } from "./files.js";

const DESTRUCTIVE_SQL = /\b(drop|truncate|delete\s+from|alter\s+table\s+\S+\s+drop)\b/i;

export function generateMigrationSql(task) {
  const request = String(task || "").trim();
  const tableName = inferTableName(request);
  const columns = inferColumns(request);
  const columnSql = columns.map((column) => `  ${column}`).join(",\n");

  return {
    tableName,
    sql: `create table if not exists public.${tableName} (
  id uuid primary key default gen_random_uuid(),
${columnSql ? `${columnSql},\n` : ""}  created_at timestamptz default now()
);

alter table public.${tableName} enable row level security;

create policy "${tableName}_select_own"
on public.${tableName}
for select
using (auth.uid() is not null);

create policy "${tableName}_insert_own"
on public.${tableName}
for insert
with check (auth.uid() is not null);
`
  };
}

export async function createMigrationPreview(cwd, task) {
  const migration = generateMigrationSql(task);
  const fileName = `${timestampId()}_${slugify(migration.tableName)}.sql`;
  const relativePath = path.join("supabase", "migrations", fileName);
  const previewPath = omnixPath(cwd, "pending", "migrations", fileName);
  await writeText(previewPath, migration.sql);

  return {
    ...migration,
    path: relativePath,
    previewPath
  };
}

export async function connectSupabase(cwd, options) {
  const config = await readJson(omnixPath(cwd, "config.json"), {});
  const localSecrets = {
    supabase: {
      project_url: options.projectUrl || "",
      anon_key: options.anonKey || "",
      service_role_key: options.serviceRoleKey || "",
      project_ref: options.projectRef || ""
    }
  };

  config.supabase = {
    connected: Boolean(options.projectUrl && options.projectRef),
    project_url: maskSecret(options.projectUrl || ""),
    project_ref: maskSecret(options.projectRef || "")
  };

  await writeJson(omnixPath(cwd, "config.json"), config);
  await writeJson(omnixPath(cwd, "config.local.json"), localSecrets, { mode: 0o600 });

  return config.supabase;
}

export async function applyLatestMigration(cwd, options = {}) {
  if (!options.confirmed) {
    return {
      applied: false,
      message: "Migration not applied. Re-run with --yes after reviewing the SQL preview."
    };
  }

  const pending = await readJson(omnixPath(cwd, "pending", "changes.json"), null);
  const migration = pending?.migrations?.at(-1);
  if (!migration) {
    return { applied: false, message: "No pending migration found." };
  }

  if (DESTRUCTIVE_SQL.test(migration.sql) && !options.confirmDestructive) {
    return {
      applied: false,
      message: "Destructive SQL requires --confirm-destructive."
    };
  }

  const schema = await loadMemory(cwd, "databaseSchema");
  schema.migrations = schema.migrations || [];
  schema.migrations.push({
    path: migration.path,
    table: migration.tableName,
    applied_at: nowIso(),
    status: "recorded"
  });
  schema.tables = [...new Set([...(schema.tables || []), migration.tableName])].sort();
  await saveMemory(cwd, "databaseSchema", schema);

  return {
    applied: true,
    message: `Recorded migration apply for ${migration.path}.`
  };
}

export function containsDestructiveSql(sql) {
  return DESTRUCTIVE_SQL.test(sql);
}

function inferTableName(request) {
  const lower = request.toLowerCase();
  const explicit = lower.match(/\b(?:table|for)\s+([a-z][a-z0-9_ -]*)/)?.[1];
  if (explicit) return slugify(explicit.split(/\s+(?:with|that|and)\s+/)[0]).replace(/-/g, "_");
  const fallback = lower.match(/\b(customers|deals|users|orders|products|invoices|tasks|projects)\b/)?.[1];
  return fallback || "items";
}

function inferColumns(request) {
  const match = request.match(/\bwith\s+(.+)$/i);
  const source = match?.[1] || "";
  const candidates = source
    .split(/,|\band\b/i)
    .map((item) => slugify(item.trim()).replace(/-/g, "_"))
    .filter(Boolean)
    .filter((item) => !["table", "field", "fields", "column", "columns"].includes(item));

  const unique = [...new Set(candidates)].slice(0, 12);
  return unique.map((name) => `${name} ${guessSqlType(name)}`);
}

function guessSqlType(name) {
  if (name.endsWith("_id")) return "uuid";
  if (name.includes("email")) return "text";
  if (name.includes("amount") || name.includes("price") || name.includes("total")) return "numeric default 0";
  if (name.includes("date") || name.endsWith("_at")) return "timestamptz";
  if (name.startsWith("is_") || name.startsWith("has_")) return "boolean default false";
  return "text";
}
