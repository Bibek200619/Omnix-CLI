# Phase 0 Architecture

Phase 0 establishes the CLI foundation and validated project state.

## Boundaries

Implemented:

- CLI entrypoint with Typer
- `.project/` initialization
- Pydantic validation for blueprint, memory, model-role configuration, tasks,
  and audits
- Atomic JSON state persistence
- Deterministic Master Agent chat intake
- Tests for initialization, configuration, validation, and memory persistence

Deferred:

- Provider implementations
- LLM calls
- Task planning
- Blueprint generation by the Architect Agent
- Worker code generation
- Integration, QA, and repair loop execution

## Architecture Decisions

The package uses `omnix_cli` as the importable Python module and `omnix` as the
console command. The repository is branded as `omnix-cli`.

Project state lives in `.project/` so generated application files can remain
separate from orchestration metadata. All reads and writes pass through
`StateManager`, which validates files with Pydantic models and writes them
atomically.

The model system stores fixed role names with replaceable model values. Agents
do not know providers and cannot call providers in Phase 0.

The Master Agent exists in Phase 0 only as the user-facing command boundary. It
records user intent in persistent memory and refuses to generate code before the
later planning, integration, and QA phases exist.
