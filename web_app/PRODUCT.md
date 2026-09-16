# Product Specification

## 1. Product Name

**Omnix CLI Website**

The public web home for **Omnix CLI**, a terminal-based AI software-engineering orchestration platform.

## 2. Product Statement

Omnix CLI provides a Master Agent for project conversations and memory, plus explicit commands for specialized workflows. The separate `omnix build` orchestrator coordinates architecture, planning, artifact generation, integration, QA, and bounded repair cycles. `omnix chat` does not dispatch these workflows.

The website should make that concept immediately understandable and then make installation effortless.

## 3. Problem

Most AI coding products are presented as a chat box, autocomplete tool, or generic “AI developer.” That framing does not explain what makes Omnix different.

Omnix has a stronger idea:

- the user talks to one orchestration layer;
- the system remembers project goals and decisions;
- architecture can be delegated to a specialized Architect Agent;
- model/provider choice is abstracted from the user workflow;
- future phases expand the coordinated engineering team.

The current repository does not yet have a polished public surface that communicates this model or a dependable release/download experience.

## 4. Target Users

### Primary
Developers who:
- live in the terminal;
- use AI during software development;
- want project-level context rather than isolated prompts;
- care about repeatable architecture and engineering workflows;
- use multiple AI model providers;
- want less agent/tool micromanagement.

### Secondary
- student developers exploring agentic software engineering;
- technical founders;
- indie hackers;
- engineering teams evaluating AI orchestration;
- open-source contributors.

## 5. Jobs To Be Done

### Discovery
“When I hear about Omnix, help me understand what it actually does in under 30 seconds.”

### Evaluation
“When I compare Omnix with normal AI coding tools, show me why orchestration, memory, and specialized roles matter.”

### Trust
“Show me real CLI commands, current capabilities, requirements, roadmap boundaries, and source code so I know this is a real product.”

### Adoption
“Let me install the correct release for my environment with minimal friction.”

## 6. Core Value Proposition

**One conversation. An AI engineering team behind it.**

Supporting message:

> Keep project conversations, goals, and decisions in one place. Invoke specialist workflows explicitly, or use the preview build orchestrator to coordinate them.

The headline expresses the product direction. It must not imply that chat currently delegates work automatically.

## 7. Positioning

Omnix should not position itself as:
- “another AI chatbot”;
- “an AI that writes all your code automatically”;
- “a replacement for engineers”;
- a finished autonomous software factory.

It should position itself as:

**an agent-first engineering orchestration layer for the terminal.**

## 8. Current Product Capabilities

The website may advertise these as **Available in source preview**. Availability means implemented source behavior, not production readiness or a published release.

### Project foundation
- initialize an Omnix project;
- configure models/providers;
- validated `.project/` state files;
- persistent project memory.

### Provider layer
- model-agnostic provider architecture;
- OpenAI provider adapter;
- provider boundaries for Anthropic, Google, OpenRouter and DeepSeek;
- role-to-provider/model assignment inspection and configuration (`omnix models` does not discover a live provider model catalog);
- role connectivity checks.

### Master Agent
- state-aware project conversations;
- persistent conversation history;
- persistent goals;
- persistent decisions;
- project context derived from memory and architecture blueprint.

### Architect Agent
- architecture blueprint creation;
- blueprint refinement;
- schema validation;
- architecture retrieval.

### Additional implemented preview workflows
- Planner generates, evolves, validates, and persists task plans.
- Frontend, Backend, Database, and Routing workers generate versioned JSON artifacts; they do not establish that an application has been written to disk, built, or deployed.
- Execution Coordinator schedules workers according to task dependencies.
- Integration assembles artifacts and model-reported dependencies, conflicts, and coverage into a stored package; its workflows field remains an empty future-expansion boundary.
- QA produces model-assisted quality, coverage, gap, and risk reports. Scores are not runtime tests or independently measured coverage.
- Repair generates prioritized repair plans and artifacts from QA findings.
- `omnix build` coordinates the lifecycle and bounded repair cycles, persists reports/history, and finalizes a JSON project package. Do not describe this as a verified deployable application or guaranteed automatic repair.

## 9. Roadmap Capabilities

Live generation adapters for Anthropic, Google, OpenRouter, and DeepSeek remain **Roadmap**: their registered provider classes explicitly reject generation as unimplemented. There are no additional confirmed roadmap agent roles in the inspected snapshot; do not invent roles or dates to fill a timeline.

Automatic specialist dispatch from Master chat, runtime code validation, and production deployment are not established capabilities. Do not label them promised roadmap commitments without a product decision.

### Discovery evidence — 2026-09-14

Canonical repository: `https://github.com/Bibek200619/Omnix-CLI`, inspected at `99d72d9`.

| Finding | Authoritative source |
|---|---|
| Version `0.1.0`, Python `>=3.12`, setuptools package/`omnix` entry point | `ai-cli/pyproject.toml`, `omnix_cli/__init__.py` |
| 26 registered commands | `ai-cli/omnix_cli/cli/main.py` |
| Master memory, no specialist dispatch | `agents/master/agent.py`, `cli/commands/chat.py` |
| Blueprint generation, evolution, validation | `agents/architect/agent.py`, `blueprint/evolution.py`, `blueprint/validation.py` |
| Planner, four workers, Integration, QA, Repair | Corresponding `ai-cli/omnix_cli/agents/*/agent.py` and command handlers |
| Dependency-aware execution and build lifecycle | `agents/coordinator/`, `orchestrator/autonomous.py` |
| OpenAI Responses API adapter; four placeholders | `ai-cli/omnix_cli/providers/` |

All paths in the middle rows are relative to `ai-cli/omnix_cli/`. Tests under `ai-cli/tests/` exercise these workflows with fakes; source inspection does not certify live provider quality.

Registered commands: `init`, `config`, `chat`, `architect`, `blueprint`, `models`, `ping`, `memory`, `goals`, `decisions`, `plan`, `tasks`, `execute`, `execute-all`, `execution`, `integrate`, `integration`, `qa`, `quality`, `repair`, `repairs`, `artifacts`, `artifact`, `build`, `build-status`, `builds`. `--version` is an option, not a command.

Project state uses Pydantic-validated JSON under `.project/`: `project.blueprint.json`, `project.memory.json`, `models.json`, `tasks.json`, and `artifacts/`, `integration/`, `qa/`, `repair/`, `execution/`, `build/` outputs. Goals, decisions, conversations, and agent outputs live in project memory. This is local file persistence, not a cloud database.

`CLI/` is a separate Node >=20 MVP, also named `omnix-cli` at 0.1.0, with deterministic placeholder providers and `.omnix/` state. Do not mix its commands or npm distribution with the Python product. The Python README and Master fallback messages contain stale phase language; website claims follow the executable source instead. No CLI files are changed by website discovery.

### Distribution decision

Phase 4 recheck (2026-09-16): Master persists conversation and detected goals/decisions without specialist dispatch. Architect loads memory plus the existing blueprint, then parses, evolves, validates and saves the generated blueprint. Validation checks schema and required architecture fields, not application runtime behavior. The separate build orchestrator runs specialist phases and bounded repair cycles. OpenAI remains the sole live adapter; four generation placeholders remain roadmap. The public GitHub release list is still empty. This was a source/API inspection, not a live model-quality test.

Phase 3 recheck (2026-09-15): public GitHub Releases API still returned an empty array. Package metadata, command registration, Master/Architect handlers, local state persistence, and provider implementation boundaries remain consistent with discovery. Hero CTAs link to the Python source preview and canonical repository. The walkthrough presents commands plus labelled website narration; it makes no claim to show live generated output.

GitHub's public releases endpoint returned an empty array on 2026-09-14; local tags are empty and no repository release workflow is present. The website's verified snapshot is `none`. No stable binary, checksum, signing, or official package-registry distribution has been verified.

Preview development setup from the repository is `cd ai-cli`, `uv sync --extra dev`, then `uv run omnix --help` (Python >=3.12). This uses the local package declared in `pyproject.toml`; do not advertise `pip install omnix-cli` or an npm package based on its name. Phase 1 exposes a source link only. Recheck releases before enabling installation UI.

Verification: a temporary copy installed successfully with `uv sync --extra dev --frozen`; its installed `omnix --help` listed all 26 commands and its test suite passed 137 tests. This used Python 3.14.6; the minimum requirement is established from package metadata, not a separate Python 3.12 compatibility run. No paid provider calls were made.

## 10. Product Principles

### Truth before hype
Real commands and real capabilities are more persuasive than exaggerated marketing.

### Demonstrate, do not describe
Whenever possible, show the CLI performing a real workflow instead of explaining the same workflow in paragraphs.

### One primary action
The primary CTA is installation/download. GitHub is secondary.

### Progressive disclosure
The hero communicates the idea. Deeper sections prove it.

### Developer credibility
Version, requirements, source, docs, and command examples must be easy to find.

### Restraint
Premium does not mean more decoration. Every visual element must have a hierarchy, comprehension, or interaction purpose.

## 11. Success Metrics

For an initial public launch, measure:

- hero → install CTA click-through rate;
- copy-install-command interactions;
- GitHub outbound clicks;
- download/release clicks;
- percentage of visitors reaching “How it works”;
- documentation navigation;
- page performance and Core Web Vitals;
- installation failure feedback if a feedback channel exists.

Do not add analytics until a privacy-conscious implementation is selected.

## 12. Non-Goals for Website v1

- account creation;
- SaaS dashboard;
- cloud project management;
- billing;
- team collaboration UI;
- embedded AI chat;
- browser-based code execution;
- full documentation portal;
- package registry;
- telemetry from the installed CLI;
- a custom CMS.

## 13. Launch Definition

Website v1 is successful when a new visitor can:

1. understand Omnix in one viewport;
2. see a believable real workflow;
3. distinguish current features from roadmap features;
4. inspect supported commands/providers;
5. reach GitHub;
6. obtain a real stable installation path;
7. use the site comfortably on mobile, desktop, keyboard and screen reader;
8. load the site quickly without heavy visual effects.
