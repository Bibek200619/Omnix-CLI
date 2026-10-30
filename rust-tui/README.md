# Omnix Rust terminal frontend prototype

This directory is the first Rust UI prototype for the approved Omnix TUI direction.
It is a separate binary (`omnix-tui`), not the production `omnix` command.

## Stack

- Rust 1.88 or newer
- Ratatui 0.30.2
- Crossterm 0.29
- `unicode-width` for terminal-cell cursor placement

The prototype has a black default theme, blue and white alternatives, a pixel welcome
mark that leaves on first input, a blinking block cursor, a small local slash palette,
and Ctrl+C terminal cleanup. The UI is intentionally separated from the existing
Python command engine.

## Run the prototype

```sh
cargo run
```

The Python engine bridge is not implemented yet. Normal messages are not sent, and
the local palette does not expose the Python CLI's 33 engine commands. The current
Python CLI remains the working product runtime until protocol, command parity, and
packaging work in [issue #69](https://github.com/Bibek200619/Omnix-CLI/issues/69)
is complete. See [`../CLI_ARCHITECTURE.md`](../CLI_ARCHITECTURE.md).
