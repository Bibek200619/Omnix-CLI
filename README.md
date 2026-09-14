<div align="center">
  <img src="web_app/website/public/brand/omnix-logo.png" alt="Omnix logo" width="96" />

# Omnix CLI

**Agent-first software engineering orchestration from the terminal.**

Omnix CLI gives a developer one terminal interface for project context, architecture, planning, specialized engineering workers, integration, QA, repair, parallel execution, and autonomous build orchestration.

</div>

> [!IMPORTANT]
> Omnix CLI is currently a **source preview**. The package metadata is `0.1.0`, requires **Python 3.12+**, and there is not yet a verified stable GitHub Release or official binary/download flow. Do not treat the package version as a stable release claim.

## What Omnix CLI is

The product is organized around a Master Agent and specialized software-engineering capabilities. Project state is persisted under `.project/`, so goals, decisions, architecture, plans, execution history, QA results, repairs, and build records can survive across sessions.

The current implementation includes the full Phase 0–10 engineering pipeline:

| Phase | Capability | Status |
| --- | --- | --- |
| 0 | CLI foundation, project initialization, configuration, validated project state, persistent memory | Implemented |
| 1 | Provider abstraction/registry, OpenAI adapter, provider boundaries, model configuration | Implemented |
| 2 | State-aware Master Agent, conversation history, goals, decisions, project context | Implemented |
| 3 | Architect Agent, blueprint generation/refinement and validation | Implemented |
| 4 | Task planning and persisted task state | Implemented |
| 5 | Frontend, Backend, Database, and Routing worker agents with artifact generation | Implemented |
| 6 | Integration Agent and integrated project package generation | Implemented |
| 7 | QA Agent with quality, coverage, gap, and risk reporting | Implemented |
| 8 | Repair Agent and additive repair cycles/history | Implemented |
| 9 | DAG-based parallel multi-agent execution and execution history | Implemented |
| 10 | Autonomous build orchestration across architecture → planning → execution → integration → QA → repair → finalization | Implemented |

### Important product boundary

`omnix chat` is the conversational Master Agent surface for project context and decisions. The autonomous engineering pipeline is exposed through dedicated commands such as `omnix plan`, `omnix execute-all`, `omnix integrate`, `omnix qa`, `omnix repair`, and `omnix build`. Do not assume every specialized workflow is automatically invoked by Master chat.

## Architecture at a glance

```text
Developer
   │
   ▼
Omnix CLI
   │
   ├── Master Agent ─────────────── project context / goals / decisions
   │
   ├── Architect Agent ──────────── blueprint
   │
   ├── Planner ──────────────────── task graph
   │
   ├── Worker Agents
   │    ├── Frontend
   │    ├── Backend
   │    ├── Database
   │    └── Routing
   │
   ├── Integration Agent ────────── integrated package
   │
   ├── QA Agent ─────────────────── quality / coverage / gaps / risks
   │
   ├── Repair Agent ─────────────── repair plan + additive repair artifacts
   │
   └── Autonomous Orchestrator ──── end-to-end build lifecycle

.project/
   └── persistent project, execution, QA, repair, artifact, and build state
```

## Quick start from source

A stable package-registry/binary installation path has not been verified yet. For development or preview use, work from the repository source:

```bash
git clone https://github.com/Bibek200619/Omnix-CLI.git
cd Omnix-CLI/ai-cli
uv sync --extra dev
uv run omnix --help
```

If `uv` is not installed, use an equivalent Python 3.12+ virtual environment.

Initialize a project:

```bash
uv run omnix init --project-name "CRM" --description "SaaS CRM"
```

Configure a model and inspect available providers/models:

```bash
uv run omnix config --set master=openai:gpt-5
uv run omnix models
uv run omnix ping master
```

Then start with project context and architecture:

```bash
uv run omnix chat "Design authentication for this project"
uv run omnix architect
uv run omnix blueprint
```

Commands operate on the current working directory by default. Use `--workspace /path/to/project` where supported to target another project root.

## CLI commands

The current Typer application registers these commands:

| Area | Commands |
| --- | --- |
| Project setup | `omnix init`, `omnix config` |
| Conversation/context | `omnix chat`, `omnix memory`, `omnix goals`, `omnix decisions` |
| Models/providers | `omnix models`, `omnix ping` |
| Architecture | `omnix architect`, `omnix blueprint` |
| Planning | `omnix plan`, `omnix tasks` |
| Worker execution | `omnix execute`, `omnix execute-all`, `omnix execution` |
| Integration | `omnix integrate`, `omnix integration` |
| Quality | `omnix qa`, `omnix quality` |
| Repair | `omnix repair`, `omnix repairs` |
| Artifacts | `omnix artifacts`, `omnix artifact` |
| Autonomous builds | `omnix build`, `omnix build-status`, `omnix builds` |

Use `omnix <command> --help` (or `uv run omnix <command> --help` from source) for the current command signature and options.

## Providers

The provider layer is model/provider-agnostic by design. The repository currently contains a working **OpenAI adapter** plus boundaries for **Anthropic, Google, OpenRouter, and DeepSeek**. Treat a provider as available only when its adapter is implemented and configured; placeholder boundaries are not equivalent to live support.

Provider credentials are loaded from environment-backed settings. Never commit `.env` files or API keys.

## Persistent project state

Omnix stores validated project-local state under `.project/`. Depending on the workflows you run, that state can include:

- project memory and conversation history;
- goals and decisions;
- architecture blueprints;
- plans and tasks;
- generated worker artifacts;
- integration results;
- execution plans, reports, and history;
- QA reports;
- repair plans, artifacts, reports, and cycle history;
- autonomous build reports/history and final package metadata.

This state is part of the product model: Omnix is designed to understand an ongoing project, not just answer isolated prompts.

## Autonomous build workflow

The Phase 10 build orchestrator coordinates the implemented engineering stages as one explicit workflow:

```text
Architect
   ↓
Planner
   ↓
Parallel worker execution
   ↓
Integration
   ↓
QA
   ↓
Repair (when required)
   ↓
Finalize
```

Start an autonomous build with the command supported by your current project state:

```bash
uv run omnix build
```

Inspect build state/history with:

```bash
uv run omnix build-status
uv run omnix builds
```

## Website

The public Omnix CLI website lives under:

```text
web_app/website/
```

Website specifications and product/design documentation live directly under `web_app/`.

The current website implementation includes:

- product/release truth discovery;
- Next.js + React + strict TypeScript foundation;
- reusable design-system primitives;
- responsive Header + Hero;
- official Omnix branding;
- a source-backed CLI walkthrough;
- accessibility, responsive, Vitest, and Playwright coverage for the implemented phases.

The website intentionally does not expose a fake stable-download CTA while the repository has no verified stable release.

### Website development

```bash
cd web_app/website
npm install
npm run dev
```

Use the scripts defined in `web_app/website/package.json` for formatting, linting, typechecking, tests, production build, and Playwright checks.

## Development checks

For the Python CLI:

```bash
cd ai-cli
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy omnix_cli
```

For the website, run its repository-defined quality scripts from `web_app/website/` before opening or merging a PR.

## Repository workflow

Changes intended for `main` should be developed on a feature/fix/chore branch and merged through a pull request. Do **not** push directly to `main`.

Current project tracking is organized through GitHub Issues and the shared **Omnix Development Board**:

- Omnix CLI website tracker: [#44](https://github.com/Bibek200619/Omnix-CLI/issues/44)
- Omnix CLI ↔ Omnix integration epic: [#45](https://github.com/Bibek200619/Omnix-CLI/issues/45)
- Shared board-link tracker: [#54](https://github.com/Bibek200619/Omnix-CLI/issues/54)
- Omnix-side board anchor: [Omnix #224](https://github.com/Bibek200619/Omnix/issues/224)
- Omnix Development Board: https://github.com/users/Bibek200619/projects/9

## Future: one Omnix product experience

Omnix CLI and the main **Omnix** application remain separate codebases today, but their future integration is already planned.

The intended product boundary is:

```text
Omnix
workspace / identity / collaboration / permissions / approvals / cloud coordination
                            │
                            │ versioned integration contract
                            ▼
Omnix CLI
local software-engineering execution / agents / artifacts / QA / repair / builds
```

The integration roadmap deliberately preserves standalone/offline CLI operation and avoids turning Omnix into a generic remote shell. See [Omnix-CLI #45](https://github.com/Bibek200619/Omnix-CLI/issues/45) and [Omnix #217](https://github.com/Bibek200619/Omnix/issues/217).

## Repository layout

```text
Omnix-CLI/
├── ai-cli/                 # Python Omnix CLI implementation
├── web_app/
│   ├── *.md                # Website/product/design specifications
│   ├── ref/                # Visual references and original brand assets
│   └── website/            # Next.js public website
├── CODEX.md                # Repository instructions for Codex
├── GEMINI.md               # Additional project context
├── agent.md                # Agent workflow guidance
└── README.md
```

## Current release state

- Source package version: `0.1.0`
- Python requirement: `>=3.12`
- Stable GitHub Release: **not yet verified / currently absent**
- Official binary/download flow: **not yet available**
- Source preview: **available**

Until a real release pipeline is established, use the repository source and do not publish unofficial install commands as if they were supported distribution methods.

## License

No repository license is currently declared. Add an explicit license before treating the project as generally redistributable open-source software.
