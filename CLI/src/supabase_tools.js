import path from "node:path";
import { loadMemory, saveMemory } from "./brain.js";
import { nowIso, omnixPath, timestampId, writeText } from "./files.js";
import { loadPending, savePending } from "./workflow.js";

export async function supabaseSchema(cwd) {
  const schema = await loadMemory(cwd, "databaseSchema");
  return JSON.stringify(schema, null, 2);
}

export async function supabaseTables(cwd) {
  const schema = await loadMemory(cwd, "databaseSchema");
  const tables = schema.tables || [];
  return tables.length ? tables.join("\n") : "No local tables recorded.";
}

export async function supabasePolicies(cwd) {
  const schema = await loadMemory(cwd, "databaseSchema");
  const migrations = schema.migrations || [];
  const policies = migrations.flatMap((migration) => migration.policies || []);
  return policies.length ? policies.join("\n") : "No local RLS policies recorded.";
}

export async function supabaseRls(cwd, tableName) {
  if (!tableName) throw new Error("Usage: /supabase-rls <table>");
  const sql = `alter table public.${tableName} enable row level security;

create policy "${tableName}_authenticated_select"
on public.${tableName}
for select
using (auth.uid() is not null);
`;
  const migration = await stageMigration(cwd, `${tableName}_rls`, tableName, sql);
  return [`RLS preview generated: ${migration.path}`, "", sql].join("\n");
}

export async function supabaseSeed(cwd, tableName) {
  if (!tableName) throw new Error("Usage: /supabase-seed <table>");
  const sql = `insert into public.${tableName} (id, created_at)
values (gen_random_uuid(), now());
`;
  const migration = await stageMigration(cwd, `${tableName}_seed`, tableName, sql);
  return [`Seed preview generated: ${migration.path}`, "", sql].join("\n");
}

export async function supabaseDiff(cwd) {
  const schema = await loadMemory(cwd, "databaseSchema");
  return [
    "Remote Supabase diff is not available in local offline mode.",
    `Local tables: ${(schema.tables || []).join(", ") || "none"}`,
    `Recorded migrations: ${(schema.migrations || []).length}`
  ].join("\n");
}

export async function supabasePull(cwd) {
  const schema = await loadMemory(cwd, "databaseSchema");
  schema.last_pull = nowIso();
  await saveMemory(cwd, "databaseSchema", schema);
  return "Recorded local schema pull timestamp. Remote pull requires Supabase CLI credentials.";
}

export async function supabaseReset(cwd, confirmed = false) {
  if (!confirmed) return "Supabase connection not reset. Re-run with --yes to confirm.";
  const schema = await loadMemory(cwd, "databaseSchema");
  schema.tables = [];
  schema.migrations = [];
  schema.last_pull = null;
  await saveMemory(cwd, "databaseSchema", schema);
  return "Local Supabase schema memory reset.";
}

async function stageMigration(cwd, name, tableName, sql) {
  const fileName = `${timestampId()}_${name}.sql`;
  const relativePath = path.join("supabase", "migrations", fileName);
  await writeText(omnixPath(cwd, "pending", "migrations", fileName), sql);
  const pending = (await loadPending(cwd)) || {
    id: `change-${Date.now()}`,
    created_at: nowIso(),
    request: name,
    files: [],
    migrations: []
  };
  pending.migrations.push({
    agent: "database",
    path: relativePath,
    tableName,
    sql
  });
  await savePending(cwd, pending);
  return { path: relativePath };
}
