# Omnix Rust terminal frontend

This is the Rust terminal frontend for Omnix. It currently builds as the separate
`omnix-tui` binary; Python remains the production `omnix` entry point until command
parity and cross-platform packaging are complete.

## Stack

- Rust 1.88 or newer
- Ratatui 0.30.2
- Crossterm 0.29
- `unicode-width` for terminal-cell cursor placement
- `serde` and `serde_json` for the versioned local bridge

The UI preserves the terminal's foreground and background colors, with no page-wide
surface or theme switcher. The focused composer gets a restrained charcoal band. Model
and workspace status use quiet warm and green accents, while keyboard hints stay muted.
It includes the pixel welcome mark, blinking block cursor,
multiline editing, paste, keyboard help, project context, and a searchable command
palette. The palette is loaded from the Python CLI's registered Typer commands at
startup, plus six local controls. It supports filtering, selection, scrolling,
insertion, draft restoration, and an ASCII fallback (`OMNIX_ASCII=1`). The slash
catalog stays attached to the composer; exact and prefix matches rank ahead of fuzzy
name or description matches. `/new` archives the active conversation
and starts a clean one. `/resume` restores the most recently saved conversation.
Conversation archives live under `.project/tui_sessions/`; long-term project memory
such as goals and decisions is retained when starting a new conversation.

With an empty composer, Up/Down and the mouse wheel scroll the transcript; Ctrl+P and
Ctrl+N browse submitted input history. Shift+Return adds a line to the draft; Ctrl+J
remains a fallback for terminals without modified-Enter reporting. Starting a new
conversation changes only conversation memory and its archive pointer; account identity,
OS credentials, and configured models are preserved. Existing unsegmented conversation
memory migrates into a resumable archive.

Plain messages run through `omnix chat`; slash commands run only when registered by the
Python CLI. The bridge launches subprocess arguments directly without a shell, streams
bounded output, reports exit status, supports interruption, and summarizes changes to
saved generated artifacts. It does not apply generated artifacts to application source.
Commands that require native interactive input temporarily restore the normal terminal
and hand control to the existing Python command, then return to the TUI.

Use `--plain` for linear, unstyled interaction; `TERM=dumb` selects it automatically.

## Run the Rust terminal UI

```sh
cargo run
cargo run -- --workspace PATH
cargo run -- --plain
```

The bridge uses `OMNIX_PYTHON` when set, otherwise it prefers `ai-cli/.venv/` in a
source checkout and falls back to `python3`. It loads the sibling `ai-cli/` package.
`TERM=dumb` selects linear output automatically. The current Python CLI remains the
production entry point until parity and packaging work in
[issue #69](https://github.com/Bibek200619/Omnix-CLI/issues/69) is complete. See
[`../CLI_ARCHITECTURE.md`](../CLI_ARCHITECTURE.md).

The Rust UI loads recent conversation memory, project/model context and the real
registered command catalog on startup. Tab and Shift+Tab move focus between the
composer, transcript and open context view. Space expands or collapses the latest
artifact diff when the transcript is focused; added and removed lines include old/new
line numbers. Diffs are limited to saved generated artifacts and do not apply source
changes. Terminal-default colors are preserved outside the focused composer band and
semantic status labels. `NO_COLOR` removes these accents and semantic diff colors while
`+`/`−` and state labels remain.
