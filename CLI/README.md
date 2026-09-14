# OmniX CLI

OmniX CLI is a dependency-free MVP for the multi-agent terminal workflow described in `PRD.md`.

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
