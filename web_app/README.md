# Omnix CLI Website — Project Documentation

This directory is the canonical product, design, engineering, and QA specification for the Omnix CLI website.

The website has two jobs:

1. Explain what Omnix CLI is and why a developer would use it.
2. Move a qualified visitor from understanding the product to installing or downloading a real Omnix CLI release.

The site must feel like a premium developer product, not a generic AI landing-page template.

## Product Truth

Omnix CLI is a terminal-based AI software-engineering orchestration platform. The user can converse with a Master Agent and invoke specialized workflows through explicit commands or the separate build orchestrator.

The currently implemented product includes:

- `omnix init`
- `omnix config`
- `omnix chat`
- validated `.project/` state
- persistent project memory
- provider abstraction
- OpenAI adapter and provider boundaries for Anthropic, Google, OpenRouter, and DeepSeek
- `omnix models`
- `omnix ping <role>`
- state-aware Master Agent
- persistent conversation history
- persistent goals and decisions
- `omnix memory`
- `omnix goals`
- `omnix decisions`
- Architect Agent
- architecture blueprint generation/refinement/validation
- `omnix architect`
- `omnix blueprint`

Discovery on 2026-09-14 also confirmed Planner, Frontend, Backend, Database, Routing, Integration, QA, Repair, dependency-aware execution, and a build orchestrator in source. These are **available in the source preview**, not a verified stable release. Workers produce stored artifacts; QA produces model-assisted reports, not executed test results. `omnix chat` does not dispatch specialists. See `PRODUCT.md` for evidence and limitations.

## Documentation Map

| File | Purpose |
|---|---|
| `PRODUCT.md` | Product vision, audience, positioning, goals and non-goals |
| `REQUIREMENTS.md` | Functional and non-functional requirements |
| `USER_FLOWS.md` | Visitor journeys and interaction flows |
| `IA.md` | Site map, section hierarchy and navigation |
| `REFERENCES.md` | Visual/product references and anti-copy rules |
| `DESIGN_SYSTEM.md` | Visual tokens, layout, typography, motion and UI principles |
| `COMPONENTS.md` | Component inventory and behavior contracts |
| `ARCHITECTURE.md` | Frontend architecture and engineering boundaries |
| `API.md` | External integrations and release/download data contract |
| `DATABASE.md` | Data persistence policy; v1 intentionally has no product database |
| `SECURITY.md` | Web security and supply-chain expectations |
| `ACCESSIBILITY.md` | Accessibility standards and acceptance criteria |
| `TESTING.md` | Testing strategy and release gates |
| `PLAN.md` | Milestones, execution loop and definition of done |
| `CHANGELOG.md` | Documentation and product-site change history |

## Source-of-Truth Rule

The files directly under `web_app/` are canonical.

`web_app/documents/`, when present, is a secondary mirror for tools that expect a nested documents directory. Do not edit it independently or assume it is synchronized. Future automation may regenerate the mirror from the canonical files.

## Core Development Rule

Do not allow implementation to invent product or design decisions.

The order is:

**product → UX → visual system → components → implementation → testing → polish → AI-smell review**

If implementation discovers a missing decision, update the relevant document first and then continue.
