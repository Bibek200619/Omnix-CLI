# Phase 3 Architecture

Phase 3 adds the Architect Agent and the architecture blueprint system.

## Boundaries

Implemented:

- Architect Agent workflow
- Expanded `ProjectBlueprint` architecture fields
- Blueprint generation from goals, decisions, memory, and existing blueprint state
- Blueprint refinement through merge-based evolution
- Strict architecture blueprint validation before persistence
- `omnix architect`
- `omnix blueprint`

Deferred:

- Task planning
- Worker agents
- Code generation
- Database generation
- API generation
- Route generation
- Frontend generation
- Backend generation
- QA and integration agents
- Repair loops

## Blueprint Shape

Phase 3 adds architecture-level fields:

- `metadata`
- `goals`
- `pages`
- `features`
- `entities`
- `modules`
- `architecture_notes`
- `assumptions`
- `constraints`
- `future_enhancements`

The schema remains backward compatible with previous phase state files. Empty
blueprints created by `omnix init` still load, but `omnix architect` validates
that a complete architecture blueprint has a project name, at least one feature,
at least one entity, at least one module, and architecture notes before saving.

## Architect Agent Flow

`omnix architect` runs this flow:

1. Load current goals, decisions, memory, and blueprint.
2. Build structured Architect context.
3. Call the configured `architect` provider/model.
4. Parse structured JSON blueprint output.
5. Merge the proposal into the existing blueprint.
6. Validate the evolved blueprint.
7. Save `project.blueprint.json`.
8. Record an Architect Agent output summary in memory.

The Architect Agent owns product and system structure only. It does not generate
files, code, tasks, APIs, routes, database objects, or worker-agent plans.
