# Product Specification

## 1. Product Name

**Omnix CLI Website**

The public web home for **Omnix CLI**, a terminal-based AI software-engineering orchestration platform.

## 2. Product Statement

Omnix CLI lets a developer communicate with a single Master Agent that maintains project context and coordinates specialized AI roles behind the scenes.

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

> Give Omnix a software goal. The Master Agent keeps project context, records decisions, and routes specialized work to the right agent instead of forcing you to manage a collection of disconnected AI chats.

## 7. Positioning

Omnix should not position itself as:
- “another AI chatbot”;
- “an AI that writes all your code automatically”;
- “a replacement for engineers”;
- a finished autonomous software factory.

It should position itself as:

**an agent-first engineering orchestration layer for the terminal.**

## 8. Current Product Capabilities

The website may advertise these as available now:

### Project foundation
- initialize an Omnix project;
- configure models/providers;
- validated `.project/` state files;
- persistent project memory.

### Provider layer
- model-agnostic provider architecture;
- OpenAI provider adapter;
- provider boundaries for Anthropic, Google, OpenRouter and DeepSeek;
- model discovery/configuration;
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

## 9. Roadmap Capabilities

These must carry a visible **Roadmap**, **Planned**, or **Coming later** status:

- Planner Agent
- worker/developer agents
- integration agent/workflows
- QA agent
- automated repair loops
- autonomous implementation pipelines

Never animate or phrase these in a way that implies users can invoke them today.

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
