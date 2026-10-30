# Interactive terminal

The approved design combines the R2 conversation shell with the first exploration's
project and workflow views. Implementation replaces the Python CLI's one-line
interactive prompt; existing explicit commands and their JSON output remain supported.

## Entry points and layout

- `omnix` opens the TUI in an interactive terminal; redirected invocation shows help.
- `omnix tui --workspace PATH` opens an explicit workspace.
- `omnix chat` opens the same interface when used interactively without a message.
- `omnix tui --plain` provides a linear, unstyled session for assistive technology,
  limited terminals and readable scrollback. `TERM=dumb` selects it automatically.
- The welcome mark uses block glyphs, never the app PNG. First input or output hides
  it for the session. Existing conversations open directly in the transcript.
- A persistent composer sits below the transcript. The optional context panel uses
  a rail at 110 columns and a separate view at narrower widths.
- Slate, light, terminal-default and monochrome themes use semantic colors. `NO_COLOR`
  disables color, and an ASCII fallback supports terminals without block glyphs.

## Commands and supporting views

The catalog is derived from the registered Typer command tree, including session
subcommands, so it cannot advertise unimplemented actions. Setup, model assignment,
memory, blueprint, task, artifact, integration, QA, repair, build, history and account
views invoke the existing handlers. They retain the handlers' validation and product
boundaries. Typing a normal message invokes Master chat, not specialist dispatch.

Local UI commands provide help, context, change expansion, theme selection and exit.
They are labelled separately from project commands. A leading `//` escapes an absolute
path into a chat message. Slashes within normal messages remain literal.

## Keyboard contract

- `/` opens the catalog; typing filters names and descriptions. Up/Down moves through
  every result, keeping the selected item visible. Enter or Tab inserts a command;
  a second Enter executes it. Escape dismisses and restores the pre-catalog draft.
- Enter sends; Ctrl+J inserts a newline. Editing supports normal cursor movement,
  Unicode, paste, selection and history through prompt_toolkit.
- Tab/Shift+Tab moves focus between available regions. PageUp/PageDown scrolls the
  transcript; output does not move focus away from the composer.
- Ctrl+C requests interruption of running work. At idle, a second Ctrl+C exits after
  an exit hint. Escape closes the context view and restores input focus.
- Space in the transcript toggles the selected generated-artifact patch; `/changes`
  opens the latest changes. Large patches have bounded display and accurate totals.

## Execution boundary

Commands run as child Python processes without a shell. Only registered commands
are dispatched, with the current workspace passed explicitly. Output streams into
the transcript; terminal escape/control sequences from external output are removed.
Input drafts stay editable during work. A second command cannot start concurrently.

Workspace selection (`link` without an explicit workspace ID) and remote-session
polling temporarily hand control to the existing terminal prompts, then return to
the TUI. This preserves native interactive selection and default-No remote approval;
the TUI never injects approval or silently enables remote execution.

## Changes and truthfulness

Before and after a project command, compare bounded snapshots of saved artifact
content. Show actual additions/removals with green `+` and red `-`, old/new line
numbers and neutral context. Identify these as **saved generated artifacts**, not
source files applied to the user's application. Empty/unchanged snapshots do not
produce a success event. The UI adds no arbitrary source-write/apply capability.

The source workflows still control architecture, planning, generation, integration,
QA, repair and build state. A stored artifact or model-assisted report does not mean
tests ran or an application was deployed. Provider/model labels reflect local
configuration, not a verified live connection. Credential storage and account
authorization remain in the existing integration code.

## Verification

Verify catalog coverage, insertion versus execution, welcome dismissal, focus,
themes/no-color, Unicode/ASCII, compact sizing, interruption and terminal cleanup.
Exercise real commands in temporary workspaces, including failure recovery and
artifact changes. Run the complete Python tests, Ruff, mypy and package build.
Use a real pseudo-terminal for resize, keyboard, cancellation and exit checks.
Do not execute paid provider calls, log into accounts or modify a real user project
as part of UI verification.
