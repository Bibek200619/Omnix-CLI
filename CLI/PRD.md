PRD: OmniX CLI — Multi-Agent AI Terminal Tool
1. Product Overview

Product name: OmniX CLI
Product type: Multi-agent AI coding terminal
Primary interface: Terminal-based CLI with premium split-panel UI
Core idea: OmniX CLI lets developers build software using multiple specialized AI agents that share one common project brain. Instead of one model doing everything, users can assign different models to different agents, such as GPT for the master agent, Gemini for the frontend agent, Claude for backend work, and another provider for QA or database tasks.

The CLI should work like a modern coding assistant inside the terminal, but with a stronger agent workflow: planning, architecture generation, frontend implementation, backend implementation, routing, database schema creation, integration, QA audit, error fixing, and project memory updates.

The tool should feel like a premium developer product, similar to the reference terminal UI: dark theme, clean panels, visible token usage, model status, modified files, active agent, project context, and command-based control.

2. Product Goals
Main Goals
Create a multi-agent coding workflow inside the terminal
Master agent handles conversation, planning, task routing, and coordination.
Specialized agents handle frontend, backend, routing, database, QA, integration, and debugging.
Users can manually call agents using slash commands.
Allow users to assign different AI models to different agents
Example:
Master Agent → GPT
Frontend Agent → Gemini
Backend Agent → Claude
QA Agent → OpenRouter model
Database Agent → GPT or another provider
Keep all agents aligned using a shared project brain
All agents should use the same project memory.
Agents should not hallucinate separate requirements.
Every agent reads from the same source of truth before generating code.
Provide a premium CLI UI
Split-panel layout.
Active agent indicator.
Token usage panel.
Project memory status.
Modified files list.
Model/provider status.
Command input with rich terminal interactions.
Support Supabase integration
User connects Supabase using project URL and authentication credentials.
Database agent generates migrations.
Migration code can be applied directly to Supabase.
Tables, policies, and schema updates should be created with fewer manual errors.
Support project behavior files
OmniX should use an OmniX.md file.
OmniX.md defines project behavior, coding rules, agent behavior, style guides, and restrictions.
Unlike tools where only one main agent follows a behavior file, all OmniX agents should follow OmniX.md.
Support custom agent skills
Users can add reusable skills inside .agents/skills.
Agents should check these skills before performing related tasks.
Skills can define workflows, rules, reusable prompts, validators, and project-specific instructions.
3. Target Users
Primary Users
1. Solo developers

Developers who want an AI coding tool that can plan, generate, review, and fix code using multiple agents.

2. Startup builders

Users building SaaS apps, dashboards, tools, MVPs, landing pages, admin panels, and full-stack apps.

3. AI power users

Users who want control over which model handles which type of task.

4. Developers using multiple AI providers

Users who already have API keys for GPT, Gemini, Claude, OpenRouter, or other providers and want one CLI to coordinate them.

4. Core Concept

OmniX CLI should not behave like a single chatbot. It should behave like a multi-agent software team inside the terminal.

The basic agent flow is:

User
 ↓
Master Agent
 ↓
System Architect Agent
 ↓
Frontend Agent / Backend Agent / Routing Agent / Database Agent
 ↓
Integration Agent
 ↓
QA Agent
 ↓
If errors exist → Master Agent analyzes errors and assigns fixes
 ↓
If no errors → Files are written and project memory is updated

The Master Agent is the only agent that directly talks to the user by default. Other agents work in the background unless the user manually calls them using commands like /frontend, /backend, /database, /qa, etc.

5. Agent System
5.1 Master Agent
Purpose

The Master Agent is the central coordinator. It understands the user request, chooses the correct workflow, sends tasks to sub-agents, reviews results, and communicates with the user.

Responsibilities
Talk directly with the user.
Understand user intent.
Break large tasks into smaller tasks.
Choose which agents should work.
Assign instructions to agents.
Read and update project memory.
Read OmniX.md.
Check available skills in .agents/skills.
Manage context compaction.
Decide when to call QA.
Decide when to apply generated code.
Explain results to the user.
Example tasks
“Build a SaaS CRM dashboard.”
“Fix the backend error.”
“Create a pricing page.”
“Add authentication.”
“Connect Supabase.”
“Review this project.”
“Explain what changed.”
5.2 System Architect Agent
Purpose

The System Architect Agent designs the project blueprint before code generation starts.

Responsibilities
Create project architecture.
Generate technical blueprint.
Decide folder structure.
Define frontend pages.
Define backend APIs.
Define database tables.
Define routes.
Define integration points.
Create project.blueprint.json.
Create migration planning files.
Create task instructions for sub-agents.
Output files
.project/blueprint/project.blueprint.json
.project/blueprint/project.routes.json
.project/blueprint/project.database.json
.project/blueprint/project.apis.json
Example output
{
  "project_name": "SaaS CRM",
  "frontend": {
    "pages": ["Dashboard", "Customers", "Deals", "Settings"],
    "components": ["Sidebar", "Header", "DataTable", "DealCard"]
  },
  "backend": {
    "apis": ["GET /customers", "POST /customers", "GET /deals", "POST /deals"]
  },
  "database": {
    "tables": ["users", "customers", "deals"]
  }
}
5.3 Frontend Agent
Purpose

The Frontend Agent handles UI generation, layouts, components, styling, pages, responsiveness, and frontend state.

Responsibilities
Generate React/Next.js components.
Create frontend pages.
Implement responsive layouts.
Follow design system rules.
Match the user’s requested UI style.
Connect frontend to APIs.
Use existing project components when available.
Avoid breaking existing UI patterns.
Example commands
/frontend create dashboard page
/frontend redesign the pricing section
/frontend build responsive sidebar
/frontend fix mobile layout
5.4 Backend Agent
Purpose

The Backend Agent handles server logic, APIs, authentication flows, data validation, and business logic.

Responsibilities
Generate API routes.
Create backend services.
Handle authentication logic.
Implement server actions.
Validate input.
Connect backend with database.
Create secure API handlers.
Follow backend architecture from the System Architect Agent.
Example commands
/backend create customer CRUD APIs
/backend add auth middleware
/backend fix API error
/backend create webhook handler
5.5 Routing Agent
Purpose

The Routing Agent manages navigation, routes, page structure, middleware routing, and app-level routing rules.

Responsibilities
Create route structure.
Add navigation links.
Handle protected routes.
Update sidebar/menu routes.
Map frontend pages to backend APIs.
Keep routing consistent with the blueprint.
Example commands
/routing add settings route
/routing protect dashboard routes
/routing fix broken navigation
/routing generate route map
5.6 Database Agent
Purpose

The Database Agent handles database schema, Supabase integration, migrations, tables, policies, and database safety checks.

Responsibilities
Generate database schemas.
Create Supabase migration SQL.
Create tables.
Create relationships.
Create indexes.
Create Row Level Security policies.
Validate database changes.
Apply migrations to Supabase when user confirms.
Sync local migration files with Supabase.
Supabase responsibilities

The CLI should allow the user to connect Supabase by entering:

SUPABASE_PROJECT_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PROJECT_REF

The service role key should be stored securely and never printed in terminal logs.

Example commands
/database create customers table
/database generate migration for deals
/database apply migration
/database pull schema
/database validate schema
/database create RLS policies
5.7 Integration Agent
Purpose

The Integration Agent merges and verifies outputs from all agents.

Responsibilities
Combine frontend, backend, routing, and database work.
Check whether generated files connect correctly.
Verify imports.
Verify route usage.
Verify API calls.
Verify database table references.
Detect conflicts between agents.
Prepare final code for QA.
Example tasks
Ensure frontend calls the correct backend routes.
Ensure backend uses correct database table names.
Ensure generated components are imported correctly.
Ensure no duplicate files are created unnecessarily.
5.8 QA Agent
Purpose

The QA Agent audits generated code and checks for errors before finalizing changes.

Responsibilities
Run static checks when available.
Review generated files.
Detect syntax errors.
Detect missing imports.
Detect incorrect database usage.
Detect broken routes.
Detect inconsistent naming.
Create a QA audit report.
Send errors back to Master Agent.
Example QA audit output
{
  "error_type": "schema_mismatch",
  "affected_agents": ["backend", "database"],
  "details": "Backend references customers.email but database schema created user_email.",
  "severity": "high",
  "recommended_fix": "Update backend service to use user_email or modify schema to email."
}
5.9 Debug Agent
Purpose

The Debug Agent focuses on fixing errors found by QA or runtime logs.

Responsibilities
Analyze stack traces.
Find root cause.
Suggest fix plan.
Apply targeted changes.
Avoid rewriting unrelated code.
Send fixed code back to QA.
Example commands
/debug fix this error
/debug explain stack trace
/debug find why build fails
/debug repair last failed task
5.10 Documentation Agent
Purpose

The Documentation Agent creates and updates docs.

Responsibilities
Update README.
Explain project architecture.
Document APIs.
Document Supabase setup.
Document environment variables.
Generate changelogs.
Update OmniX.md.
Example commands
/docs create README
/docs document API routes
/docs update setup guide
/docs explain current architecture
6. Shared Brain System

The most important part of OmniX CLI is the shared brain.

Without shared memory, each agent may generate different naming, different schema, different routing, and different assumptions. OmniX should prevent this.

Shared brain should include:
Project memory
Current task memory
Agent task history
Blueprint files
Database schema
Route map
API map
File map
Previous QA reports
User preferences
OmniX.md rules
Installed skills
Conversation summaries
Recommended memory files
.omnix/
  memory/
    project.memory.json
    chat.memory.json
    agent.memory.json
    qa.memory.json
    file.index.json
    route.map.json
    database.schema.json
  blueprint/
    project.blueprint.json
    project.apis.json
    project.routes.json
    project.database.json
  logs/
    agent-runs.log
    qa-audit.log
    migrations.log
  cache/
    compacted-context.json
Project memory example
{
  "project_name": "OmniX CLI",
  "tech_stack": {
    "frontend": "Terminal UI",
    "backend": "Node.js",
    "database": "Supabase",
    "language": "TypeScript"
  },
  "agents": {
    "master": "GPT",
    "frontend": "Gemini",
    "backend": "Claude",
    "database": "GPT",
    "qa": "OpenRouter"
  },
  "known_rules": [
    "All agents must read OmniX.md before code generation.",
    "Database changes must be validated before applying to Supabase.",
    "QA must run before final file write."
  ],
  "generated_files": [],
  "known_issues": []
}
7. Configuration System
7.1 First-Time Setup

When a user runs:

omnix --init

or

omnix init

The CLI should create:

OmniX.md
.agents/
  skills/
.omnix/
  config.json
  memory/
  blueprint/
  logs/
7.2 Setup Flow

The terminal should ask:

Welcome to OmniX CLI

1. Choose your master agent model
2. Choose your frontend agent model
3. Choose your backend agent model
4. Choose your database agent model
5. Choose your QA agent model
6. Connect Supabase
7. Create OmniX.md
8. Create .agents/skills
7.3 Provider Setup

Supported providers should include:

OpenAI
Google Gemini
Anthropic Claude
OpenRouter
Custom OpenAI-compatible endpoint
Local model endpoint
Other future providers
7.4 Model Assignment Example
{
  "agents": {
    "master": {
      "provider": "openai",
      "model": "gpt-5.5"
    },
    "frontend": {
      "provider": "google",
      "model": "gemini-pro"
    },
    "backend": {
      "provider": "anthropic",
      "model": "claude-sonnet"
    },
    "database": {
      "provider": "openai",
      "model": "gpt-5.5"
    },
    "qa": {
      "provider": "openrouter",
      "model": "selected-model"
    }
  }
}
8. OmniX.md Behavior File

OmniX.md is the global behavior file for the entire project.

All agents must follow it.

Example OmniX.md
# OmniX Project Behavior

## Project Rules

- Follow the existing project structure.
- Do not create duplicate files.
- Do not overwrite user code without confirmation.
- Prefer small, targeted changes.
- Always run QA after code generation.
- Database changes must be reviewed before applying to Supabase.

## Coding Style

- Use TypeScript.
- Use clean, readable code.
- Use meaningful names.
- Avoid unnecessary abstractions.
- Keep components reusable.

## Agent Rules

- Master Agent coordinates all tasks.
- System Architect Agent creates the blueprint before major work.
- Frontend Agent handles UI only.
- Backend Agent handles APIs and server logic.
- Database Agent handles schema and Supabase migration.
- QA Agent audits before final write.
- Integration Agent verifies all agent outputs work together.

## Safety Rules

- Never expose API keys.
- Never print service role keys.
- Never apply destructive database migrations without confirmation.
- Always create a migration preview before applying.
9. Agent Skills System

Users should be able to add skills inside:

.agents/skills/

Each skill can define a repeatable workflow.

Example structure
.agents/
  skills/
    nextjs-page-generator.md
    supabase-rls-policy.md
    api-validator.md
    landing-page-copywriter.md
Example skill
# Skill: Supabase RLS Policy Generator

## When to use

Use this skill when creating or modifying Supabase tables.

## Rules

- Always enable Row Level Security.
- Create select, insert, update, and delete policies where required.
- Ask for confirmation before applying policies.
- Never expose service role keys.

## Output

Return SQL migration code and a safety explanation.

Before doing a task, an agent should check whether a matching skill exists. If yes, the agent should use the skill instructions.

10. Slash Commands

OmniX CLI should support rich slash commands.

10.1 Core Chat Commands
Command	Purpose
/new	Start a new chat session
/rename	Rename current chat
/review	Review a previous chat
/history	Show previous chats
/delete-chat	Delete a selected chat
/export-chat	Export current chat to Markdown or JSON
/clear	Clear visible terminal output
/help	Show all available commands
/exit	Exit OmniX CLI
10.2 Agent Commands
Command	Purpose
/master	Talk directly to the Master Agent
/architect	Call the System Architect Agent
/frontend	Assign task to Frontend Agent
/backend	Assign task to Backend Agent
/routing	Assign task to Routing Agent
/database	Assign task to Database Agent
/integration	Call Integration Agent
/qa	Run QA Agent
/debug	Run Debug Agent
/docs	Run Documentation Agent
/agent-status	Show current agent model assignments
/agent-set	Change model assigned to an agent
/agent-log	Show recent agent activity

Example:

/frontend create a responsive dashboard sidebar
/backend create customer CRUD APIs
/database create customers and deals tables
/qa audit the latest changes
10.3 Context Commands
Command	Purpose
/compact	Compact current chat context to save tokens
/memory	Show project memory summary
/memory-update	Manually update project memory
/memory-reset	Reset selected memory
/context	Show current context usage
/context-files	Show files currently included in context
/pin	Pin important instruction to memory
/unpin	Remove pinned instruction
/summarize	Summarize current conversation
/compact

The /compact command should summarize previous conversation and replace long chat history with a smaller structured memory object.

Example output:

{
  "summary": "User is building a SaaS CRM with dashboard, customers, deals, and settings pages.",
  "decisions": [
    "Use Supabase for database.",
    "Use TypeScript.",
    "Use protected dashboard routes."
  ],
  "open_tasks": [
    "Create customers table.",
    "Build deals page.",
    "Add QA validation."
  ]
}
10.4 Project Commands
Command	Purpose
/init	Initialize OmniX in current project
/scan	Scan current project structure
/blueprint	Generate or show project blueprint
/files	Show modified/generated files
/file-read	Read a specific file into context
/file-write	Write generated file changes
/apply	Apply pending changes
/revert	Revert last OmniX change
/diff	Show pending code diff
/tree	Show project folder tree
/status	Show project status
10.5 Model and Provider Commands
Command	Purpose
/providers	Show connected providers
/provider-add	Add a new provider API key
/provider-remove	Remove provider
/models	List available models from selected provider
/model-set	Set model for current agent
/agent-set	Set model for a specific agent
/keys	Show safe API key status without revealing keys
/key-update	Update an API key
/endpoint-add	Add custom OpenAI-compatible endpoint

Example:

/agent-set frontend gemini-pro
/agent-set master gpt-5.5
/provider-add openrouter
/models openrouter
10.6 Supabase Commands
Command	Purpose
/supabase-connect	Connect Supabase project
/supabase-status	Show Supabase connection status
/supabase-schema	Pull current schema
/supabase-migration	Generate migration
/supabase-apply	Apply migration after confirmation
/supabase-reset	Remove Supabase connection
/supabase-tables	List tables
/supabase-policies	Show RLS policies
/supabase-rls	Generate RLS policies
/supabase-seed	Generate seed data
/supabase-diff	Show local vs remote schema difference

Important rule:

Destructive migrations must require confirmation.

Example:

/supabase-migration create customers table
/supabase-apply latest
/supabase-schema
10.7 QA and Debug Commands
Command	Purpose
/qa	Run full QA audit
/qa frontend	QA only frontend files
/qa backend	QA only backend files
/qa database	QA only database changes
/audit	Generate structured audit report
/fix	Fix latest QA errors
/debug	Debug error pasted by user
/test	Run available tests
/typecheck	Run type check
/lint	Run lint
/build	Run project build
/explain-error	Explain error in simple language
10.8 Skill Commands
Command	Purpose
/skills	List available skills
/skill-add	Add new skill
/skill-edit	Edit existing skill
/skill-remove	Remove skill
/skill-use	Force use a specific skill
/skill-scan	Scan .agents/skills folder
/skill-info	Show details of one skill
10.9 UI Commands
Command	Purpose
/theme	Change terminal theme
/layout	Switch between compact, split, and full layouts
/logo	Show OmniX logo
/focus	Focus on chat, files, logs, or agents panel
/panel-toggle	Show/hide side panels
/tokens	Show token usage
/cost	Show estimated cost
/notifications	Toggle sound/visual alerts
11. Terminal UI Design

The UI should be inspired by the uploaded terminal reference image.

11.1 Visual Style

The UI should feel:

Premium
Modern
Dark
Minimal
Developer-focused
Fast
Clear
High-contrast
11.2 Logo

The OmniX logo should be:

X shape
Blue and red gradient
Modern glowing style
Used in startup screen, header, and empty state

Example text logo:

╔═╗┌┬┐┌┐┌┬ ┬═╗ ╦
║ ║││││││└┬┘╔╩╦╝
╚═╝┴ ┴┘└┘ ┴ ╩ ╚═

A more polished terminal version can use gradient coloring if the terminal supports it.

11.3 Main Layout

Recommended layout:

┌────────────────────────────────────────────────────────────────────┐
│ OmniX CLI   Project: my-app   Agent: Master   Model: GPT           │
├───────────────────────────────────────────────┬────────────────────┤
│                                               │ Context             │
│ Main conversation / agent output              │ 38,131 tokens       │
│                                               │ 4% used             │
│                                               │                    │
│                                               │ Token Usage         │
│                                               │ Input: 61,838       │
│                                               │ Output: 3,780       │
│                                               │ Cached: 730,112     │
│                                               │                    │
│                                               │ Active Agents       │
│                                               │ Master: GPT         │
│                                               │ Frontend: Gemini    │
│                                               │ Backend: Claude     │
│                                               │ QA: OpenRouter      │
│                                               │                    │
│                                               │ Modified Files      │
│                                               │ src/app/page.tsx    │
│                                               │ src/api/users.ts    │
├───────────────────────────────────────────────┴────────────────────┤
│ /frontend create pricing page                                      │
└────────────────────────────────────────────────────────────────────┘
11.4 UI Panels
Main Chat Panel

Shows:

User messages.
Master Agent responses.
Sub-agent progress.
Code summaries.
QA results.
Command outputs.
Right Status Panel

Shows:

Context
Token Usage
Current Cost
Active Agent
Current Model
Connected Providers
Supabase Status
Modified Files
QA Status
Project Path
Bottom Input Bar

Supports:

Slash command autocomplete
Multiline input
Command history
Model indicator
Current agent indicator

Example:

OmniX › /frontend create dashboard cards
File Change Panel

When files are generated or edited, show:

Modified Files
+ src/app/dashboard/page.tsx
+ src/components/Sidebar.tsx
~ src/lib/supabase.ts
QA Panel

After QA runs:

QA Result
Status: Failed
Errors: 2
Warnings: 3

1. Missing import in Sidebar.tsx
2. API route references wrong table name

If QA passes:

QA Result
Status: Passed
No blocking errors found.
12. Main User Flows
12.1 First-Time Setup Flow
User runs:
omnix --init

CLI creates:
- OmniX.md
- .agents/skills
- .omnix/config.json
- .omnix/memory
- .omnix/blueprint
- .omnix/logs

CLI asks:
- Choose master model
- Choose frontend model
- Choose backend model
- Choose database model
- Choose QA model
- Add API keys
- Connect Supabase

Final output:

OmniX initialized successfully.
Project brain created.
Agents configured.
Supabase connected.
Ready to build.
12.2 New Project Build Flow
User:
Build a SaaS CRM with dashboard, customers, deals, settings, and Supabase backend.

Master Agent:
Understands request.

System Architect Agent:
Creates blueprint.

Frontend Agent:
Creates UI.

Backend Agent:
Creates APIs.

Database Agent:
Creates Supabase schema and migration.

Integration Agent:
Connects UI, APIs, and database.

QA Agent:
Audits code.

If error:
Master Agent assigns fixes.

If no error:
Files are written.
Project memory is updated.
12.3 Manual Agent Flow
User:
/frontend build pricing page

Frontend Agent:
Reads OmniX.md.
Reads project memory.
Reads route map.
Creates pricing page.
Sends output to Integration Agent.
QA Agent reviews.
Master Agent explains result.
12.4 Supabase Migration Flow
User:
/database create customers table with name, email, phone, company

Database Agent:
Generates SQL migration.

CLI:
Shows migration preview.

User:
Confirms apply.

CLI:
Applies migration to Supabase.

QA Agent:
Checks schema consistency.

Project memory:
Updates database.schema.json.
13. Supabase Integration Requirements
Required capabilities
Connect Supabase project.
Save connection securely.
Pull current schema.
Generate migration SQL.
Preview migration.
Apply migration after confirmation.
Generate RLS policies.
Validate schema.
Detect local vs remote differences.
Update project memory after migration.
Safety rules
Never print service role key.
Never apply destructive migration without confirmation.
Always preview SQL before applying.
Always store migration history.
Always update local schema memory after successful migration.
Warn user before dropping tables, columns, or policies.
Example migration preview
create table public.customers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  email text,
  phone text,
  company text,
  created_at timestamptz default now()
);

alter table public.customers enable row level security;

CLI should ask:

Apply this migration to Supabase? yes/no
14. Error Handling Workflow

OmniX should follow a strict error loop.

QA Agent finds error
 ↓
QA report is sent to Master Agent
 ↓
Master Agent analyzes error
 ↓
Master Agent sends specific fix instruction to correct sub-agent
 ↓
Sub-agent fixes only affected files
 ↓
Integration Agent checks result
 ↓
QA Agent audits again
 ↓
If no error, finalize
Example QA error
{
  "error_type": "routing_error",
  "affected_agents": ["frontend", "routing"],
  "details": "Sidebar links to /customers but route file was created at /customer.",
  "fix_instruction": "Update route file to /customers or update sidebar link consistently."
}
15. File System Behavior

OmniX should not blindly write files. It should use a safe file operation system.

File write stages
1. Generate code
2. Show diff
3. Run integration check
4. Run QA
5. Ask for confirmation if needed
6. Write files
7. Update memory
File commands
/diff
/apply
/revert
/files
/file-read
/file-write
File change example
Pending Changes

+ src/app/dashboard/page.tsx
+ src/components/DashboardCards.tsx
~ src/app/layout.tsx

Run /apply to save these changes.
Run /revert to discard them.
16. Context and Token Management

Because multiple agents use multiple models, token management is important.

Requirements
Show context usage in UI.
Show token usage by model.
Show cost estimate.
Support /compact.
Store compacted conversation in memory.
Avoid sending unnecessary full history to every agent.
Send only relevant files and memory to each agent.
Context strategy

Each agent should receive:

1. Current user task
2. Relevant project memory
3. Relevant OmniX.md rules
4. Relevant blueprint section
5. Relevant files
6. Relevant skill instructions
7. Previous related QA reports

Agents should not receive unrelated full chat history unless necessary.

17. Security Requirements
API Key Security
API keys must be hidden.
Do not print full API keys.
Store keys securely.
Show only masked values.

Example:

OpenAI: sk-****9f2a
Gemini: ****x91p
Supabase: connected
Supabase Security
Service role key must never be sent to frontend.
Service role key must never be printed.
Migration execution should be confirmed.
Destructive SQL requires extra confirmation.
Local Project Security
Do not delete files without confirmation.
Do not overwrite large files without warning.
Do not modify environment files without showing diff.
Do not expose .env values in logs.
18. Config Files
.omnix/config.json
{
  "project_name": "my-app",
  "default_agent": "master",
  "providers": {
    "openai": {
      "enabled": true
    },
    "google": {
      "enabled": true
    },
    "anthropic": {
      "enabled": true
    },
    "openrouter": {
      "enabled": true
    }
  },
  "agents": {
    "master": {
      "provider": "openai",
      "model": "gpt-5.5"
    },
    "frontend": {
      "provider": "google",
      "model": "gemini-pro"
    },
    "backend": {
      "provider": "anthropic",
      "model": "claude-sonnet"
    },
    "database": {
      "provider": "openai",
      "model": "gpt-5.5"
    },
    "qa": {
      "provider": "openrouter",
      "model": "selected-model"
    }
  },
  "supabase": {
    "connected": true,
    "project_url": "masked",
    "project_ref": "masked"
  }
}
19. Recommended Technical Architecture
CLI Runtime

Recommended stack:

Language: TypeScript
Runtime: Node.js
Terminal UI: React Ink or similar terminal UI framework
Config format: JSON + Markdown
Memory format: JSON
Agent behavior: Markdown instructions
Database: Supabase
Provider system: adapter-based
Provider Adapter System

Each AI provider should use the same internal interface.

interface ModelProvider {
  name: string;
  listModels(): Promise<Model[]>;
  generate(input: AgentInput): Promise<AgentOutput>;
  stream(input: AgentInput): AsyncIterable<string>;
}
Agent Interface
interface Agent {
  id: string;
  name: string;
  role: string;
  provider: string;
  model: string;
  run(task: AgentTask): Promise<AgentResult>;
}
Agent Task
interface AgentTask {
  taskId: string;
  userRequest: string;
  agentType: string;
  context: {
    projectMemory: object;
    blueprint?: object;
    files?: string[];
    skills?: string[];
    qaReports?: object[];
  };
}
20. MVP Scope
MVP should include
CLI initialization.
OmniX.md creation.
.agents/skills folder creation.
Provider API key setup.
Assign model to each agent.
Master, Frontend, Backend, Database, QA agents.
Basic shared project memory.
/new, /rename, /review, /compact.
/frontend, /backend, /database, /qa, /debug.
Supabase connection.
Migration preview.
Manual migration apply.
Terminal split UI.
Token usage panel.
Modified files panel.
QA report output.
21. Future Features
Advanced agent workflows
Parallel agent execution.
Agent voting.
Agent self-review.
Multi-model comparison.
Automatic best-model selection per task.
Advanced Supabase support
Visual schema summary.
Auto RLS policy generation.
Database seed generation.
Migration rollback.
Local/remote schema diff viewer.
Advanced UI
Mouse support.
Command palette.
File tree navigation.
Inline diff viewer.
Agent timeline panel.
Cost graph.
Theme marketplace.
Team features
Shared project memory.
Shared OmniX config.
Workspace profiles.
Agent presets.
Exportable project brain.
22. Success Metrics
Product success
User can initialize a project in under 2 minutes.
User can assign different models to different agents.
User can generate frontend, backend, and database code from one request.
User can connect Supabase successfully.
User can apply a migration with preview and confirmation.
QA catches common integration errors.
Agents stay consistent using shared memory.
Quality metrics
Fewer duplicate files.
Fewer schema mismatch errors.
Fewer route mismatch errors.
Lower token cost after /compact.
Clearer visibility into what each agent changed.
23. Acceptance Criteria
Initialization

OmniX passes MVP initialization if:

omnix --init

creates:

OmniX.md
.agents/skills
.omnix/config.json
.omnix/memory
.omnix/blueprint
.omnix/logs

and lets the user assign models to agents.

Agent Assignment

The CLI passes agent assignment if the user can run:

/agent-set frontend gemini-pro
/agent-set master gpt-5.5

and the right status panel updates immediately.

Shared Brain

The CLI passes shared brain requirements if:

All agents read project memory.
All agents follow OmniX.md.
QA reports are stored.
Blueprint files are reused.
Agents do not generate conflicting table names, routes, or APIs.
Supabase

Supabase integration passes if:

User can connect project credentials.
CLI can pull schema.
CLI can generate migration SQL.
CLI previews migration before applying.
CLI applies migration only after confirmation.
CLI updates local database memory after success.
UI

The UI passes if it includes:

Header
Main chat panel
Right status panel
Bottom command input
Token usage
Active agent
Current model
Modified files
Supabase status
QA status

and visually matches the premium dark terminal style from the reference image.

24. Final Product Summary

OmniX CLI is a premium multi-agent terminal coding tool where each agent can use a different AI model but still work from one shared project brain. The Master Agent talks to the user and coordinates all work. The System Architect Agent creates the blueprint. Frontend, Backend, Routing, and Database agents generate specialized code. The Integration Agent merges the work. The QA Agent audits everything. If errors are found, the Master Agent sends targeted fixes back to the right sub-agent.

The CLI should support rich slash commands, context compaction, project memory, model assignment, custom skills, Supabase integration, migration preview/apply, and a modern terminal UI with token usage, agent status, modified files, and QA results.

The most important principle:

Every agent must share the same project memory, follow OmniX.md, and pass QA before final changes are applied.