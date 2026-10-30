# Omnix CLI architecture migration

**Status:** the Rust TUI builds the `omnix` binary and connects to the Python engine
through the versioned local bridge. The binary defaults to the TUI and forwards
existing subcommands to Python. Release automation targets macOS arm64 and Linux
x86_64. No combined release artifact is published yet. It uses Rust 1.88+, Ratatui
0.30.2 and Crossterm 0.29.

## Target architecture

```text
Developer
   │
   ▼
Rust terminal frontend
Ratatui + Crossterm
   │
   ▼
Versioned structured local communication layer
   │
   ▼
Python AI engine
agents · providers · project state · command handlers · execution
```

The Rust application will own terminal rendering, input, navigation, keyboard
behavior, themes and the interactive experience. The Python engine remains responsible for
agent behavior, provider adapters, project state, command validation and engineering
workflows. The migration does not rewrite those capabilities in Rust or introduce
duplicate provider logic.

The Rust UI shell is in [`rust-tui/`](rust-tui/). It uses the user's terminal-default
foreground and background, and provides the pixel welcome mark, editable composer,
live command catalog, context panel, progress/output transcript and saved-artifact
change summaries. It does not force a black background or a theme palette.

The first bridge contract is version 1, implemented in
[`ai-cli/omnix_cli/bridge.py`](ai-cli/omnix_cli/bridge.py), over newline-delimited JSON
on a local child process's stdin/stdout. The startup `ready` event includes the
workspace, project context and registered command catalog. Rust sends `run`, `cancel`
and `shutdown` requests; Python emits `started`, `output`, `patch`, `context`,
`handoff`, `complete`, `cancelled` or `error` events with request IDs. Only registered
commands can be dispatched. Commands are tokenized without a shell, inherit the
selected workspace, and use existing Python handlers. Output is bounded and terminal
control sequences are stripped before display. Account linking and approved remote
work hand control back to the native terminal for their existing interactive prompts;
the Rust UI does not bypass their consent flow. Secret values are not included in
protocol events. See [issue #70](https://github.com/Bibek200619/Omnix-CLI/issues/70)
for further contract hardening and protocol tests.

## Migration stages

1. Harden and test the versioned Rust-to-Python contract, including protocol errors,
   interrupted process cleanup and cross-platform behavior.
2. Bring the Ratatui/Crossterm shell to the approved Figma TUI, including compact
   terminal layouts, keyboard interaction, and visual QA.
3. Finish command parity through the bridge and preserve explicit interactive handoff
   for commands that need terminal input while retaining consent behavior.
4. Publish verified combined `omnix` and Python-engine bundles for macOS arm64 and
   Linux x86_64. The installer provisions the engine in an isolated virtual
   environment and requires Python 3.12 or newer; project state remains outside the install.
5. Extend the release matrix only after clean-machine checks cover the target platform.
6. Compare behavior and release readiness before removing or demoting the Python TUI.

The existing Python console entry point remains available as a fallback. The active
product version and stable-release state remain governed by the Python package
metadata and verified release artifacts; a Rust crate alone is not a product release.

## Tracking

- [#69 Rust frontend migration](https://github.com/Bibek200619/Omnix-CLI/issues/69)
- [#70 Versioned engine contract](https://github.com/Bibek200619/Omnix-CLI/issues/70)
- [#71 Ratatui/Crossterm frontend](https://github.com/Bibek200619/Omnix-CLI/issues/71)
- [#72 `omnix` packaging and runtime](https://github.com/Bibek200619/Omnix-CLI/issues/72)
- [#73 Documentation status](https://github.com/Bibek200619/Omnix-CLI/issues/73)
