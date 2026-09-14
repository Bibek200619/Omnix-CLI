# Information Architecture

## 1. Site Model

Website v1 should be intentionally small.

### Routes

#### `/`
Primary product and conversion page.

#### `/docs` — optional for v1
Only create if installation/usage documentation grows beyond what the landing page can reasonably hold.

#### `/download` — optional
Use only if platform-specific distribution becomes complex. Otherwise use `/#download`.

#### `/privacy` — only if analytics or submitted user data requires it
Do not create empty legal boilerplate pages.

## 2. Home Page Section Order

### 01 — Header
- Omnix mark/name
- Product
- How it works
- CLI
- Roadmap
- GitHub
- Download

### 02 — Hero
Purpose: answer “What is this?” immediately.

Content:
- eyebrow: `OMNIX CLI`
- headline: `Build software with an AI engineering team.`
- short explanation
- Download/Install CTA
- GitHub CTA
- terminal demo

### 03 — Concept bridge
Headline:
`One conversation. The right specialist behind it.`

Short explanation of the Master Agent.

### 04 — Orchestration journey
The signature “Angry Birds progression” section:
- project goal;
- Master Agent;
- persistent context;
- Architect Agent;
- future roles;
- result.

This is a narrative graph/timeline, not a collection of feature cards.

### 05 — Project memory
Explain:
- memory;
- goals;
- decisions;
- blueprint.

Show a `.project/` file/tree metaphor only if it matches implementation.

### 06 — Provider layer
Explain that model selection is configurable behind roles.

Avoid unverified claims that every provider adapter is fully production-ready; distinguish adapters/boundaries where needed.

### 07 — Real CLI
Command explorer with authentic commands and short descriptions.

### 08 — Architect spotlight
Show the current specialized-agent workflow:
goal → context → architecture analysis → validated blueprint.

### 09 — Roadmap
Visual timeline:
- Foundation — available
- Provider layer — available
- Master Agent — available
- Architect Agent — available
- Planner — roadmap
- Worker agents — roadmap
- Integration — roadmap
- QA/repair — roadmap

### 10 — Download
- version
- status
- requirements
- install command
- release link
- source link

### 11 — Footer
- GitHub
- License, when confirmed
- Docs, when available
- Issues
- Version/build information if useful

## 3. Navigation Behavior

Desktop:
- compact sticky navigation;
- transparent/quiet at top;
- subtle solid surface after scroll.

Mobile:
- no giant full-screen animated menu;
- use a simple accessible disclosure/drawer;
- Download remains easy to reach.

## 4. Content Hierarchy

The visitor should learn in this order:

1. What Omnix is.
2. Why orchestration is different.
3. What is available now.
4. How the CLI actually feels.
5. Why project memory matters.
6. Which specialist exists today.
7. What comes next.
8. How to install it.

## 5. URL Anchors

Use durable anchors:
- `#product`
- `#how-it-works`
- `#memory`
- `#cli`
- `#architect`
- `#roadmap`
- `#download`

Do not couple anchor IDs to visual copy that is likely to change.
