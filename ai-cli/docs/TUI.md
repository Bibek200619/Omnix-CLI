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
  it while the conversation is active; an empty draft restores the mark. The 28 × 11 mark, centered welcome copy, two-cell gutter,
  three-row composer and compact status strip follow the R2 terminal frame.
  Existing conversations open directly in the transcript.
- The empty welcome state reports whether this project has local Omnix account
  credentials and points to `/login` when none are connected. Provider configuration
  remains separate and is not described as account connectivity.
- A persistent composer sits below the transcript. The optional context panel uses
  a rail at 110 columns and a separate view at narrower widths.
- The command catalog is anchored immediately above the composer, with at most eight
  suggestions visible. Longer results scroll with Up/Down, without leaving a gap
  between the final suggestion and the input.
- Terminal-default colors are the default theme. `/theme blue` and `/theme white`
  (`light` is a white alias) remain optional. Black and monochrome modes are also
  available. The composer uses a native blinking block cursor. `NO_COLOR` disables
  semantic colors, and an ASCII fallback supports terminals without block glyphs.

## Commands and supporting views

The catalog is derived from the registered Typer command tree, including session
subcommands, so it cannot advertise unimplemented actions. Setup, model assignment,
memory, blueprint, task, artifact, integration, QA, repair, build, history and account
views invoke the existing handlers. They retain the handlers' validation and product
boundaries. Typing a normal message invokes Master chat, not specialist dispatch.

Local UI commands provide help, context, change expansion, theme selection, conversation
creation/resumption and exit. They are labelled separately from project commands. A
leading `//` escapes an absolute path into a chat message. Slashes within normal messages
remain literal.

## Keyboard contract

- `/` opens the command catalog above the composer. Typing filters names and
  descriptions. Up/Down moves through results, keeping the selected item visible.
  Enter or Tab inserts a command; a second Enter executes it. Escape dismisses and
  restores the pre-catalog draft. Removing `/` also closes the catalog immediately.
  A blank catalog lists 33 registered CLI actions and seven local controls.
- `/new` archives the active conversation and clears only conversation history;
  long-term goals, decisions and other project memory stay intact. `/resume` restores
  the most recently saved prior conversation. Archives are stored under
  `.project/tui_sessions/` and shared with the Rust bridge. Existing conversation
  memory without session boundaries migrates as one resumable legacy conversation.
  New conversations do not change project identity, provider configuration, or
  OS-stored Omnix credentials.
- Enter sends; Shift+Return inserts a newline. Ctrl+J remains a fallback for terminals
  that do not report modified Enter. With an empty composer, Up/Down scroll the
  transcript; Ctrl+P/Ctrl+N browse submitted input history. Mouse-wheel scrolling
  also moves the transcript. Editing supports normal cursor movement, Unicode, paste,
  selection and history through prompt_toolkit.
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

## Rust frontend migration

The Rust `omnix` binary uses the same registered Python command handlers via the
versioned JSON Lines bridge in `omnix_cli.bridge`. It loads recent conversation
memory, project/model context and the command catalog at startup; streams output;
supports cancellation and native terminal handoff; and displays collapsible,
line-numbered changes to saved generated artifacts. The binary opens the TUI with no
arguments and forwards existing subcommands to the Python engine. The Python console
entry point remains available as a source-development fallback. Combined release
assets are not published yet; target support and Python runtime requirements are
documented in [`../../packaging/README.md`](../../packaging/README.md). Build from the
repository with `cargo run --manifest-path rust-tui/Cargo.toml` after installing the
engine into `ai-cli/.venv/`.

## Verification

Verify catalog coverage, insertion versus execution, welcome dismissal, focus,
themes/no-color, Unicode/ASCII, compact sizing, interruption and terminal cleanup.
Exercise real commands in temporary workspaces, including failure recovery and
artifact changes. Run the complete Python tests, Ruff, mypy and package build.
Use a real pseudo-terminal for resize, keyboard, cancellation and exit checks.
Do not execute paid provider calls, log into accounts or modify a real user project
as part of UI verification.
