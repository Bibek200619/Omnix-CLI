# Revision 2 — terminal behavior

Status: **approved Figma design reference**. R2 shell behavior has a Python TUI
implementation; this remains a static design file, not a clickable prototype. A Rust
Ratatui/Crossterm shell prototype exists, with the Python AI engine retained. The
prototype is not yet connected to the engine or full command catalog. The migration is tracked in
[#69](https://github.com/Bibek200619/Omnix-CLI/issues/69).

## Review links

New Figma page: **Omnix TUI · R2 Terminal behavior**. The website and first TUI design pages remain separate and unchanged by this revision.

| Board | Review |
| --- | --- |
| R01 Welcome / block mark | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-3) |
| R02 First input / logo removed | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-21) |
| R03 Slash catalog | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-36) |
| R04 Filtered catalog / command insertion | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-63) |
| R05 Proposed inline change | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-85) |
| R06 Completed change event / expanded patch | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-119) |
| R07 Compact diff / no-color contract | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-154) |
| R08 Behavior contract | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=60-403) |

This direction replaces the always-visible tab navigation/context rail as the default
conversation shell. Context and specialist views remain available on demand. The
existing first-pass screens remain a workflow inventory, not a reason to keep
permanent dashboard chrome. Keep the default theme black, provide white and blue
alternatives, and show a blinking block at the active composer. Use the Codex source
as a technical reference for cursor lifecycle, not as a source for Omnix branding or
screen layout.

## What was inspected

The supplied 42.6-second local recording was sampled across its duration, with 13 frames reviewed. It shows a centered, character-based Codex mark at approximately 9 seconds, its disappearance when a warning arrives by approximately 12 seconds, a catalog opening above the composer, scrolling selection, and a status response. The separate screenshot shows a coding-agent transcript with a green added line and change summary.

Only visual/interaction principles were retained. The user's account details, usage limits, working paths and session identifiers in the recording were not copied into Figma or review artifacts. No frames of that recording are included in this folder.

## Welcome and pixel mark

- Fresh session, empty draft, empty transcript and no active overlay: show the block mark with a ready composer.
- The first typed/pasted character, catalog opening or any incoming warning/error/response removes the mark immediately. Input never waits for an animation.
- Once hidden, it stays hidden for that session even if the draft is cleared. Existing conversation history opens directly in transcript mode.
- The mark is a separate welcome layer, never a watermark behind messages and never part of scrollback.
- The user requested a **terminal-specific pixel adaptation**. The reference Omnix swirl informed a 28-column × 11-row block silhouette; it is composed of editable `█` glyphs, not a PNG, a copied Codex logo or a new app icon.
- Three reference tones: light `#D9E9FF`, accent `#A6C8FF`, shadow `#6A91CF`. Use one foreground color in no-color/terminal-default mode; substitute `#` when block glyphs render poorly. Hide decorative logo output in linear/screen-reader-oriented mode.
- No image protocol, raster upload or custom font is required by the proposed runtime behavior. The original official logo file remains untouched.
- Figma models the states statically. Actual glyph widths, resize handling, no-color behavior and removal from the screen must be tested during implementation.

## Slash command catalog

A leading `/` in the composer opens the catalog directly above it. The normal transcript remains visible. Filtering searches the action name and description; blank `/` exposes the full catalog through a scrollable viewport. The view shows the visible range and result count. Commands with unmet prerequisites remain discoverable with the reason stated; roadmap functionality is not mixed into executable results.

Up/Down moves the selection and scrolls it into view. Enter or Tab inserts the selected command; a second Enter executes after arguments can be reviewed. Escape restores the draft and its cursor position. A no-match state retains the query and offers a clear-filter hint. Slashes inside ordinary messages and paths are literal; a leading path should be escapable or passed as message text rather than executed as an unknown action.

The **33 command actions** come from the registered commands in
`ai-cli/omnix_cli/cli/main.py`. The current Python TUI maps slash actions to those
handlers; the Rust TUI must preserve that mapping and each handler's validation:

| Group | Proposed aliases mapping to existing `omnix` commands |
| --- | --- |
| Setup | `/init`, `/config`, `/models`, `/ping` |
| Conversation and context | `/chat`, `/memory`, `/goals`, `/decisions` |
| Architecture and planning | `/architect`, `/blueprint`, `/plan`, `/tasks` |
| Execution | `/execute`, `/execute-all`, `/execution` |
| Integration and quality | `/integrate`, `/integration`, `/qa`, `/quality`, `/repair`, `/repairs` |
| Artifacts | `/artifacts`, `/artifact` |
| Build | `/build`, `/build-status`, `/builds` |
| Account and remote sessions | `/login`, `/logout`, `/link`, `/unlink`, `/status`, `/sessions work`, `/sessions history` |

No new help, permission, skills, billing, model-marketplace or resume backend command is implied by the catalog. Local TUI help can be designed separately from the source-backed action count.

## Inline changes

Each change appears beside the relevant tool event in the transcript with a file path, an accurate added/removed summary and an expandable unified diff. Additions use green text and a subdued green row; deletions use red text and a subdued red row. Unchanged context remains neutral. `+` and `-`, old/new line numbers and explicit state labels carry the meaning without color.

The fixture changes `src/greet.ts` from a simple greeting to trimming the name, handling an empty name and returning the greeting. It has exactly **three added lines and one removed line**. All code, paths, counters and result messages are illustrative.

State contract:

1. **Proposed:** show the candidate diff; say Not written.
2. **Writing:** show only while a real write operation is underway.
3. **Changed:** show only after the write succeeds, derived from the actual before/after contents.
4. **Failed:** retain the patch and the failure explanation; do not show a successful edit count.

Tests and other checks remain **Not run** until tools provide actual results. A changed file is not evidence that an application works. Generated artifacts are not silently treated as applied source files. The current Python TUI compares saved artifact snapshots around real commands; it does not apply generated output to application source. Preserve that boundary until source editing is separately designed and implemented. Rust file-change events must reflect actual engine results and must not be described as shipped until the bridge provides them.

Expanded diffs are keyboard reachable and retain focus when collapsed. Long lines wrap with continuation markers and unchanged source-line counts; narrow views retain file state and `+`/`-` markers. A linear output variant emits readable text without full-screen redraw. Large patches need bounded rendering and explicit expansion rather than flooding the transcript.

## Scope and review artifacts

Eight native editable artboards were added on the R2 page. The Python TUI implements
the conversation shell and selected interactions; the full workflow inventory still
guides the Rust migration tracked in the linked GitHub issues. No deployment or direct
push to `main` is permitted.

The saved R2 page and pixel welcome were independently opened in another Figma tab. Local artifacts are in `revision-2/`: `welcome-pixel-mark.png`, `slash-catalog.png`, `inline-diff.png`, `compact-diff.png`, the editable glyph/color matrix `pixel-mark.json`, and `omnix-design-r2-backup.fig`. The Figma backup includes all three pages, not just R2. PNGs were visually inspected; application tests were not rerun for this design-only change.

`welcome-terminal.png` and `diff-terminal.png` crop the same exported terminal regions for clearer in-conversation review; they add no content or effects.

Review the actual block shape, its startup placement, disappearance rule, catalog behavior and diff density before implementation. These mockups establish intended behavior; they do not verify a functioning TUI, keyboard interaction or assistive-technology support.
