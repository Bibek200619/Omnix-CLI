# AI Software Factory CLI

`aicli` is a terminal-based AI orchestration platform where the user talks to a
single Master Agent while specialized agents collaborate behind the scenes.

Phase 0 is implemented. It provides:

- `aicli init`
- `aicli config`
- `aicli chat`
- Validated `.project/` state files
- Persistent project memory

Future phases add providers, planning, architecture generation, worker agents,
integration, QA, and repair loops. Phase boundaries are enforced in code: the
Phase 0 Master Agent records chat intent but does not generate project code.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy aicli
```

If `uv` is not installed, use an equivalent Python 3.12+ virtual environment.

## Commands

```bash
aicli init --project-name "CRM" --description "SaaS CRM"
aicli config --set master=gpt-5 --set qa=gpt-5
aicli config --json
aicli chat "Build authentication"
```

By default commands operate in the current working directory. Use
`--workspace /path/to/project` to target another project root.
