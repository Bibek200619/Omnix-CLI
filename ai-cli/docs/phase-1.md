# Phase 1 Architecture

Phase 1 adds the provider layer while preserving all Phase 0 contracts.

## Boundaries

Implemented:

- `BaseProvider` async generation contract
- `ProviderRegistry` for provider lookup and construction
- OpenAI provider implementation using the Responses API
- Provider boundaries for Anthropic, Google, OpenRouter, and DeepSeek
- Typed provider exceptions
- Centralized `.env` settings via `pydantic-settings`
- Backward-compatible model configuration schema
- `omnix models`
- `omnix ping <role>`

Deferred:

- Planner, Architect, worker, Integration, and QA agents
- Parallel execution
- File generation
- Repair loops
- Non-OpenAI live provider request implementations

## Architecture Decisions

Agents do not instantiate provider classes. Provider construction is routed
through `ProviderRegistry`, which keeps provider selection outside agent logic
and makes role-to-provider assignments replaceable.

`models.json` now supports provider/model assignments:

```json
{
  "master": {
    "provider": "openai",
    "model": "gpt-5"
  }
}
```

The schema still accepts Phase 0 string values such as `"master": "gpt-5"`.
The existing `omnix config --set role=model` command remains valid. Use
`omnix config --set role=provider:model` to configure provider-backed pings.

Provider secrets are loaded from environment variables or `.env`, never from
`.project` state files.
