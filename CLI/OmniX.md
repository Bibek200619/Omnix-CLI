# OmniX Project Behavior

## Project Rules

- Follow the existing project structure.
- Do not create duplicate files.
- Do not overwrite user code without confirmation.
- Prefer small, targeted changes.
- Always run QA after code generation.
- Database changes must be reviewed before applying to Supabase.

## Coding Style

- Use clean, readable code.
- Use meaningful names.
- Avoid unnecessary abstractions.
- Keep components reusable.

## Agent Rules

- Master Agent coordinates all tasks.
- System Architect Agent creates the blueprint before major work.
- Frontend Agent handles UI only.
- Backend Agent handles APIs and server logic.
- Routing Agent handles navigation and route consistency.
- Database Agent handles schema and Supabase migration.
- Integration Agent verifies agent outputs work together.
- QA Agent audits before final write.

## Safety Rules

- Never expose API keys.
- Never print service role keys.
- Never apply destructive database migrations without confirmation.
- Always create a migration preview before applying.

## Project

- Name: Omnix-CLI
