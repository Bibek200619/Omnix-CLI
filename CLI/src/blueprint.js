import { BLUEPRINT_FILES } from "./constants.js";
import { nowIso, omnixPath, slugify, titleCase, writeJson } from "./files.js";

const PAGE_KEYWORDS = [
  "dashboard",
  "customers",
  "deals",
  "settings",
  "pricing",
  "reports",
  "analytics",
  "profile",
  "billing",
  "login"
];

const TABLE_KEYWORDS = [
  "users",
  "customers",
  "deals",
  "orders",
  "products",
  "invoices",
  "subscriptions",
  "messages",
  "projects",
  "tasks"
];

export function createBlueprintFromRequest(userRequest, options = {}) {
  const request = String(userRequest || "").trim();
  const lower = request.toLowerCase();
  const requestedPages = PAGE_KEYWORDS.filter((page) => lower.includes(page));
  const requestedTables = TABLE_KEYWORDS.filter((table) => lower.includes(table));
  const needsAuth = /\bauth|login|signup|protected|users?\b/.test(lower);
  const needsSupabase = /supabase|database|schema|table|backend/.test(lower);
  const pages = requestedPages.length ? requestedPages : ["home"];
  const tables = [...new Set([...(needsAuth ? ["users"] : []), ...requestedTables])];
  const apis = tables.flatMap((table) => [`GET /api/${table}`, `POST /api/${table}`]);
  const routes = pages.map((page) => ({
    name: titleCase(page),
    path: page === "home" ? "/" : `/${slugify(page)}`,
    protected: page !== "pricing" && page !== "login" && page !== "home" && needsAuth
  }));

  return {
    project_name: options.projectName || inferProjectName(request),
    created_at: nowIso(),
    source_request: request,
    frontend: {
      framework: "Next.js",
      pages: pages.map(titleCase),
      components: inferComponents(pages)
    },
    backend: {
      runtime: "Node.js",
      apis,
      services: tables.map((table) => `${titleCase(table)}Service`)
    },
    routing: {
      routes
    },
    database: {
      provider: needsSupabase ? "Supabase" : "Not specified",
      tables: tables.map((table) => ({
        name: table,
        columns: defaultColumnsForTable(table)
      }))
    },
    integration_points: [
      "Frontend routes consume backend API handlers.",
      "Backend API handlers use database table names from project.database.json.",
      "QA audit must pass before pending files can be applied."
    ],
    agents: ["architect", "frontend", "backend", "routing", "database", "integration", "qa"]
  };
}

export async function writeBlueprintFiles(cwd, blueprint) {
  const routes = {
    project_name: blueprint.project_name,
    routes: blueprint.routing.routes
  };
  const database = {
    project_name: blueprint.project_name,
    provider: blueprint.database.provider,
    tables: blueprint.database.tables
  };
  const apis = {
    project_name: blueprint.project_name,
    apis: blueprint.backend.apis,
    services: blueprint.backend.services
  };

  await writeJson(omnixPath(cwd, BLUEPRINT_FILES.project), blueprint);
  await writeJson(omnixPath(cwd, BLUEPRINT_FILES.routes), routes);
  await writeJson(omnixPath(cwd, BLUEPRINT_FILES.database), database);
  await writeJson(omnixPath(cwd, BLUEPRINT_FILES.apis), apis);

  return { blueprint, routes, database, apis };
}

function inferProjectName(request) {
  const match = request.match(/\b(?:build|create|make)\s+(?:a|an|the)?\s*([^.,\n]+?)(?:\s+with|\s+using|$)/i);
  if (!match) return "OmniX Project";
  return titleCase(match[1].replace(/\b(app|application|site|tool)\b/gi, "").trim() || "OmniX Project");
}

function inferComponents(pages) {
  const components = new Set(["AppShell", "Sidebar", "Header"]);
  if (pages.includes("dashboard")) components.add("DashboardCards");
  if (pages.includes("customers") || pages.includes("deals")) components.add("DataTable");
  if (pages.includes("pricing")) components.add("PricingTable");
  if (pages.includes("analytics") || pages.includes("reports")) components.add("ChartPanel");
  return [...components];
}

function defaultColumnsForTable(table) {
  const common = ["id uuid primary key default gen_random_uuid()", "created_at timestamptz default now()"];
  const byTable = {
    users: ["email text not null", "full_name text"],
    customers: ["name text not null", "email text", "phone text", "company text"],
    deals: ["customer_id uuid", "title text not null", "amount numeric default 0", "stage text not null"],
    orders: ["customer_id uuid", "total numeric default 0", "status text not null"],
    products: ["name text not null", "price numeric default 0"],
    invoices: ["customer_id uuid", "amount numeric default 0", "due_at timestamptz"],
    subscriptions: ["user_id uuid", "plan text not null", "status text not null"],
    messages: ["user_id uuid", "body text not null"],
    projects: ["name text not null", "status text not null"],
    tasks: ["project_id uuid", "title text not null", "done boolean default false"]
  };
  return [...common, ...(byTable[table] || ["name text not null"])];
}
