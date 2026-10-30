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

Dedicated commands also implement planning, workers, integration, QA, repair and
build orchestration. Master chat records and discusses project context; specialist
workflows require explicit invocation. Saved generated artifacts and model-assisted
reports do not establish that application code was applied, tested or deployed.

## Interactive terminal

Run `omnix` in a terminal to open the new conversation interface, or use
`omnix tui --workspace /path/to/project`. `omnix chat` without a message opens
the same interface. Existing commands and JSON output remain scriptable.

The block/pixel welcome mark disappears on the first input or output. Type `/`
for a searchable command catalog; arrows select, Enter/Tab inserts, and a second
Enter runs. Normal messages talk to Master. Project setup, models, memory,
blueprints, tasks, artifacts, reports and account commands use their existing
handlers. `/context` opens project context; `/help` lists keyboard guidance.

Saved generated-artifact changes have green `+` additions, red `-` deletions,
line numbers and expandable details (`/changes`). These are artifact-content
comparisons, not a new source-code apply feature.

Use `omnix tui --plain` for linear output without redraw, `--theme light` or
`--theme terminal` for alternate themes, `NO_COLOR=1` to disable colors, and
`OMNIX_ASCII=1` to use ASCII logo blocks. Ctrl+C interrupts work; twice at idle
exits. Workspace selection and remote-session approval retain their native prompts.
See [the interaction contract](docs/TUI.md) for details.

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
