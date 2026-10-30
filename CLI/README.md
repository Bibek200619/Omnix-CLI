# OmniX CLI

OmniX CLI is a dependency-free MVP for the multi-agent terminal workflow described in `PRD.md`.

## Stack status

This directory is the earlier Node.js prototype and is not the active AI-engine
implementation. The current engine and working CLI commands live in `../ai-cli/`
and use Python 3.12+. The Rust frontend prototype is in `../rust-tui/` and uses
Ratatui and Crossterm; the bridge to the Python engine is still under design. The
approved target connects that frontend to the Python engine through a versioned
structured local interface. This prototype's deterministic provider
placeholders are not part of the target runtime. See
[`../CLI_ARCHITECTURE.md`](../CLI_ARCHITECTURE.md).

## Quick Start

```bash
npm run build
npm test
node ./bin/omnix.js init
node ./bin/omnix.js /help
```

## Current MVP

- Initializes `OmniX.md`, `.agents/skills`, and `.omnix` shared brain files.
- Supports agent model assignment with `/agent-set`.
- Generates architecture blueprint files before implementation work.
- Creates pending frontend, backend, routing, and Supabase migration changes.
- Runs integration and QA checks before `/apply`.
- Stores QA and agent logs in `.omnix/logs`.
- Masks Supabase secrets and writes service-role data only to `.omnix/config.local.json`.

The provider adapters are local deterministic placeholders. Real provider API calls can be added behind the existing provider interface without changing the command workflow.
