# Omnix CLI

`omnix` is a terminal-based AI orchestration platform where the user talks to a
single Master Agent while specialized agents collaborate behind the scenes.

## Runtime and frontend migration

This directory contains the Python 3.12+ command engine and compatibility CLI. The
Rust frontend in `../rust-tui/` builds the `omnix` binary. It opens the terminal UI
without arguments and forwards existing subcommands to this engine. The Rust bridge
uses the versioned JSON Lines protocol in `omnix_cli.bridge`. Agents, providers,
project state, command handlers and engineering execution remain in Python. The Python
console entry point remains available for development and fallback use. See the
[migration architecture](../CLI_ARCHITECTURE.md) and
[tracking issue #69](https://github.com/Bibek200619/Omnix-CLI/issues/69).

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
for a searchable command catalog immediately above the composer; arrows select,
Enter/Tab inserts, and a second Enter runs. Shift+Return adds a message line.
With an empty composer, Up/Down scroll the transcript; Ctrl+P/Ctrl+N browse sent
input history. `/new` starts a separate conversation and `/resume` restores the
latest saved conversation. These controls preserve project settings and account
credentials. Normal messages talk to Master. Project setup, models, memory,
blueprints, tasks, artifacts, reports and account commands use their existing
handlers. `/context` opens project context; `/help` lists keyboard guidance.

Saved generated-artifact changes have green `+` additions, red `-` deletions,
line numbers and expandable details (`/changes`). These are artifact-content
comparisons, not a new source-code apply feature.

The TUI opens with a blinking block cursor and terminal-default colors. Use
`/theme blue` or `/theme white` to switch palettes for the current session.
`omnix tui --theme blue` and `omnix tui --theme white` select them at launch
(`light` remains an alias for white). `--theme terminal` inherits terminal colors,
`--theme mono` uses monochrome,
and `NO_COLOR=1` disables color. `OMNIX_ASCII=1` uses ASCII logo blocks. Ctrl+C
interrupts work; twice at idle exits. Workspace selection and remote-session approval
retain their native prompts.
See [the interaction contract](docs/TUI.md) for details.

## Install the `omnix` command

Python 3.12+ is required by the engine. From a checkout, install the Python fallback
CLI as a standalone `uv` tool:

```bash
uv tool install ./ai-cli
uv tool update-shell
omnix --version
omnix
```

`uv tool update-shell` adds uv's executable directory to supported shell startup
files when needed. Restart the terminal if `omnix` is not found. The Python package
defines an `omnix` console entry point for fallback use. Combined Rust/engine release
bundles are not available until a verified GitHub Release is published.

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
