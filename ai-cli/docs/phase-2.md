# Phase 2 Architecture

Phase 2 adds the first state-aware AI component: the Master Agent.

## Boundaries

Implemented:

- Master Agent conversation handling
- Structured context from blueprint and memory
- Provider-backed Master Agent responses when `master` has provider/model config
- Deterministic local fallback when no master provider is configured
- Persistent conversations
- Persistent goals
- Persistent decisions
- Rule-based goal and decision detection
- `aicli memory`
- `aicli goals`
- `aicli decisions`

Deferred at the end of Phase 2:

- Planner, Architect, worker, Integration, and QA agents
- Task decomposition
- Workflow orchestration
- Blueprint generation
- Code generation
- File generation
- Repair loops

## Memory Shape

`project.memory.json` remains backward compatible with earlier phases. New fields
are defaulted by the Pydantic schema, so older project memory files validate and
are upgraded on the next save.

Phase 2 memory stores:

- `goals`
- `conversations`
- `decisions`
- `known_issues`
- `agent_outputs`
- existing Phase 0/1 memory fields

## Master Agent Flow

`aicli chat` now runs this flow:

1. Load memory and blueprint.
2. Save the user conversation.
3. Detect simple goals and decisions.
4. Build structured Master Agent context.
5. Call the configured master provider when available.
6. Save the assistant conversation.
7. Record the turn in `agent_outputs`.

The Master Agent only discusses and remembers project context in Phase 2. If the
user asks for implementation work, it must explain that implementation agents
are not available yet.
