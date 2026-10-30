# Omnix CLI architecture migration

**Status:** approved direction; initial Rust UI prototype created. The current
production CLI runtime remains Python; the Rust prototype is not connected to the
engine, not the default `omnix` entry point, and not a distributable release. The
prototype uses Rust 1.88+, Ratatui 0.30.2 and Crossterm 0.29.

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

The initial UI shell is in [`rust-tui/`](rust-tui/). It demonstrates the black welcome
screen, local command palette, cursor and theme switching. It intentionally does not
send messages or run Python commands yet. The communication protocol and process
lifecycle must be specified before the Rust frontend depends on them. JSON Lines over
stdio is an option to evaluate, not a settled implementation detail. The contract
must cover version negotiation, requests, progress/output events, completion,
structured errors, cancellation, workspace identity and secret boundaries. See
[issue #70](https://github.com/Bibek200619/Omnix-CLI/issues/70).

## Migration stages

1. Define and version the Rust-to-Python contract.
2. Build the Ratatui/Crossterm shell against the approved Figma TUI, including compact
   terminals, keyboard interaction, accessible linear output and real command data.
3. Connect existing Python handlers through the contract and preserve command,
   validation, cancellation and consent behavior.
4. Package one `omnix` entry point with a documented Python runtime strategy for each
   supported platform.
5. Compare behavior and release readiness before removing or demoting the Python TUI.

The existing Python terminal UI remains available as a fallback through parity and
packaging work. The active product version and stable-release state remain governed by
the Python package metadata and verified release artifacts; a Rust crate alone is not
a product release.

## Tracking

- [#69 Rust frontend migration](https://github.com/Bibek200619/Omnix-CLI/issues/69)
- [#70 Versioned engine contract](https://github.com/Bibek200619/Omnix-CLI/issues/70)
- [#71 Ratatui/Crossterm frontend](https://github.com/Bibek200619/Omnix-CLI/issues/71)
- [#72 `omnix` packaging and runtime](https://github.com/Bibek200619/Omnix-CLI/issues/72)
- [#73 Documentation status](https://github.com/Bibek200619/Omnix-CLI/issues/73)
