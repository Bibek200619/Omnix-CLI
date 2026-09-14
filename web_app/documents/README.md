<!-- MIRROR FILE: canonical source is ../README.md. Do not edit independently. -->

# Omnix CLI Website — Project Documentation

This directory is the canonical product, design, engineering, and QA specification for the Omnix CLI website.

The website has two jobs:

1. Explain what Omnix CLI is and why a developer would use it.
2. Move a qualified visitor from understanding the product to installing or downloading a real Omnix CLI release.

The site must feel like a premium developer product, not a generic AI landing-page template.

## Product Truth

Omnix CLI is a terminal-based AI software-engineering orchestration platform. The user interacts with one Master Agent while specialized agents operate behind the scenes.

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

Planning agents, worker agents, integration, QA, and repair loops are roadmap functionality and must never be presented as already available.

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

The files directly under `project/` are canonical.

`project/documents/` is a synchronized mirror for tools that expect a nested documents directory. Do not edit the mirror independently. Any future automation should regenerate the mirror from the canonical files.

## Core Development Rule

Do not allow implementation to invent product or design decisions.

The order is:

**product → UX → visual system → components → implementation → testing → polish → AI-smell review**

If implementation discovers a missing decision, update the relevant document first and then continue.
