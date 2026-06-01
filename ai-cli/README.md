# Omnix CLI

`omnix` is a terminal-based AI orchestration platform where the user talks to a
single Master Agent while specialized agents collaborate behind the scenes.

Phase 0 is implemented. It provides:

- `omnix init`
- `omnix config`
- `omnix chat`
- Validated `.project/` state files
- Persistent project memory

Phase 1 is implemented. It provides:

- Provider abstraction and registry
- OpenAI provider adapter
- Anthropic, Google, OpenRouter, and DeepSeek provider boundaries
- `.env` backed settings for provider secrets
- `omnix models`
- `omnix ping <role>`

Phase 2 is implemented. It provides:

- State-aware Master Agent
- Persistent conversation history
- Persistent project goals
- Persistent project decisions
- Structured Master Agent context from blueprint and memory
- `omnix memory`
- `omnix goals`
- `omnix decisions`

Phase 3 is implemented. It provides:

- Architect Agent
- Blueprint schema expansion
- Blueprint generation and refinement
- Strict architecture blueprint validation
- `omnix architect`
- `omnix blueprint`

Future phases add planning, worker agents, integration, QA, and repair loops.
Phase boundaries are enforced in code: the Master Agent records and discusses
project context, while the Architect Agent generates architecture blueprints but
does not generate project code.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy omnix_cli
```

If `uv` is not installed, use an equivalent Python 3.12+ virtual environment.

## Commands

```bash
omnix init --project-name "CRM" --description "SaaS CRM"
omnix config --set master=gpt-5 --set qa=gpt-5
omnix config --set master=openai:gpt-5
omnix config --json
omnix models
omnix ping master
omnix chat "Build authentication"
omnix config --set architect=openai:gpt-5
omnix architect
omnix blueprint
omnix memory
omnix goals
omnix decisions
```

By default commands operate in the current working directory. Use
`--workspace /path/to/project` to target another project root.
