# Omnix TUI — design review 1

**Latest direction:** [Revision 2 — welcome block mark, slash catalog and inline changes](REVISION-2.md). Review R2 for the updated default conversation shell; this file preserves the first-pass workflow inventory.

Status: **approved design reference**. The R2 conversation shell and core interaction
patterns have a Python implementation. A separate Rust/Ratatui/Crossterm shell
prototype now exists in `rust-tui/`, but it is not connected to the engine or the
complete source-backed command catalog. The full workflow inventory remains the
reference for ongoing work while Python retains real handlers and project behavior.
Mock conversations, task identifiers, model assignments and reports remain design
fixtures, not captured command output.

## Open the design

- [Start here / review map](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6220)
- [Main conversation workspace](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3806)
- [Foundations and patterns](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6299)
- [Keyboard contract and implementation boundary](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6257)

The existing Figma file retains its website title. The TUI occupies its own page, **Omnix TUI · Design exploration**; the approved website remains on Page 1. There are 42 top-level artboards: 39 screen/state/size variants, a review map and two foundation boards. Text and shapes are editable. Four native components on the foundations board define Composer, ContextRail, CommandRow and StatusMessages. Screen artwork follows those patterns; it is not assembled from linked component instances.

Suggested review order: workspace → command palette → Architect/blueprint → execution and reports → error recovery → account/session consent → compact and accessibility variants. Review the interaction contract before implementation.

## Direction

A conversation-first terminal workspace with a persistent composer and optional project context rail. Slate surfaces separate transcript, context and input without gradients or decorative cards. Pale blue marks focus and active work; plain-language state labels also communicate every state. The terminal uses its user's font and theme at runtime. IBM Plex Mono is the reference face for the mockups, not a runtime font requirement.

Reference principles retained: discoverable commands, readable transcripts, explicit agent/model context and restrained terminal chrome. Useful reference documentation: [OpenCode TUI](https://opencode.ai/docs/tui/), [Claude Code interactive mode](https://code.claude.com/docs/en/interactive-mode) and [Codex CLI](https://developers.openai.com/codex/cli/). The [Codex terminal source](https://github.com/openai/codex/blob/main/codex-rs/tui/src/custom_terminal.rs) is a technical reference for native cursor handling and Rust terminal lifecycle. Competitor branding, exact layouts and product claims are not copied. Website background transitions are not carried into the TUI.

The official Omnix logo/reference assets are unchanged. The terminal header uses the product name as text; it does not introduce a replacement logo or ASCII imitation.

## Product boundary

Source checked during this design pass: the Python application in `ai-cli/` (version 0.1.0, Python >=3.12), particularly `omnix_cli/cli/main.py`, its command handlers, state manager, workflow schemas and `integrations/omnix_sessions`. The separate Node shell in `CLI/` was inspected as a layout reference; its placeholder providers must not be presented as Python capabilities.

| Area | Current source capability | Proposed presentation / constraint |
| --- | --- | --- |
| Master | Conversation and local project context | Composer and transcript; no automatic specialist dispatch |
| Architect | Explicit invocation and saved validated blueprint | Invocation view and blueprint reader |
| Workflows | Planning, workers/execution, integration, QA, bounded repair, build orchestration | Dedicated views of existing workflow state; not proof generated apps run |
| Providers | OpenAI live adapter | Role/model assignment; other provider generation remains roadmap |
| Project state | Local memory, blueprint, models, tasks, artifacts and build reports | Readable views; configuration does not establish connectivity |
| Omnix account | Browser/device login, project link/unlink, status/logout | Separate account flow; do not collect credentials in the transcript |
| Remote sessions | Authorized linked device and compatible enabled server required | Explicit local consent for one capability, Decline selected by default |
| Reports | Model-assisted reports and generated artifacts | Do not label these as executed tests, deployment or runtime validation |

Relevant stored state includes `.project/project.memory.json`, `project.blueprint.json`, `models.json`, `tasks.json`, `artifacts/` and `build/{build_report,build_history,final_project_package}.json` under `.project/`.

The screen inventory records the intended experience, including views that remain to
be completed in the runtime. The Rust rewrite must preserve source-backed commands and
their real Python handlers. No new provider adapters, automated Master dispatch,
arbitrary shell execution, file-apply review, billing data or resume command are
implied. See [`CLI_ARCHITECTURE.md`](../../../CLI_ARCHITECTURE.md) for the migration
boundary and issue links.

## Screen inventory

| Screen | Figma |
| --- | --- |
| 01 First launch | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3592) |
| 02 Project setup | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3663) |
| 03 Provider setup | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3733) |
| 04 Conversation workspace | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3806) |
| 05 Master conversation | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3878) |
| 06 Command palette | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-3950) |
| 07 Role and model assignment | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4020) |
| 08 Project memory | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4091) |
| 09 Invoke Architect | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4164) |
| 10 Blueprint reader | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4237) |
| 11 Plan and task dependencies | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4312) |
| 12 Execution in progress | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4385) |
| 13 Build orchestration | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4458) |
| 14 Stored artifact browser | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4530) |
| 15 Artifact detail | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4601) |
| 16 Integration report | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4673) |
| 17 QA findings | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4744) |
| 18 Bounded repair | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4817) |
| 19 Build result | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4889) |
| 20 Missing configuration | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-4960) |
| 21 Provider error and recovery | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5029) |
| 22 Connect an Omnix account | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5100) |
| 23 Link a workspace | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5169) |
| 24 Remote session approval | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5239) |
| 25 Session history and offline state | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5311) |
| 26 Interrupted workflow | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5379) |
| 27 Empty history | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5445) |
| 28 Help and preferences | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5507) |
| 29 Dependency schedule | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5580) |
| 30 Build history | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5654) |
| 31 Unlink this project | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5725) |
| 32 Sign-out recovery | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5794) |
| 33 Compact 80 × 24 | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5859) |
| 34 Small 60 × 20 | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5887) |
| 35 Light theme | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5912) |
| 36 Monochrome / no-color | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-5984) |
| 37 Accessible linear output | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6056) |
| 38 Unknown command | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6082) |
| 39 Invalid project state | [Open](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=51-6151) |

## Character geometry and tokens

The wide reference is 120 columns × 36 rows. The context rail appears from 110 columns; at 80 × 24 and 60 × 20, the experience uses a single column with context available on demand. Narrow views prioritize draft input and the current action. The outer 1200 × 1080 Figma sheets include annotations and are not terminal window dimensions.

Reference metrics: IBM Plex Mono 14 px, 22 px rows, 8.4 px cells. Actual implementation must measure terminal cells, handle wide characters and wrapping, and respect terminal font and resize behavior. Figma text uses nonbreaking spaces to preserve column alignment through SVG import; runtime text must use proper layout rather than copying those spaces blindly.

| Token | Slate value | Role |
| --- | --- | --- |
| Base | `#182333` | Main terminal surface |
| Raised | `#223246` | Input and context regions |
| Primary | `#EAF1FC` | Reading text |
| Muted | `#B2C2D8` | Supporting labels |
| Accent | `#A6C8FF` | Active work and focus |
| Selected | `#304C75` | Selected command background |
| Divider | `#51677F` | Nonessential structural lines |
| Success | `#9BD5C4` | State with text label |
| Warning | `#EACB93` | Review or consent required |
| Danger | `#F0ADB6` | Failure with recovery guidance |

Light reference: base `#EEF2F7`, raised `#DCE5EF`, primary `#17273D`, muted `#435975`, accent `#2559AD`. Terminal-default and no-color rendering are first-class implementation requirements. No extra animation, background video, gradient, glow or web-style font loading belongs in this TUI.

## Proposed keyboard contract

| Context / key | Behavior |
| --- | --- |
| Composer / Enter | Send the draft or execute an inserted command |
| Composer / Ctrl+J | Insert a newline |
| Composer / leading `/` | Open command palette |
| Palette / Up, Down | Move selection with visible caret |
| Palette / Enter or Tab | Insert selected command; a second Enter executes |
| Tab / Shift+Tab outside palette | Move between available focus regions |
| Focused transcript / PgUp, PgDn | Scroll without moving focus to new output |
| Esc | Close overlay and restore the previous focus/draft |
| Active work / Ctrl+C | Request interruption; show actual persisted state |
| Idle / Ctrl+C | Show exit hint; a second invocation confirms exit |
| Remote approval | Decline is the default; approve one named capability only |

Keys require terminal/OS validation before implementation. Do not fabricate a shipped `--plain` switch, resume command or theme setting from this proposal. Resize, overflow, focus restoration, user scroll position and drafts must be tested in a working implementation.

## Accessibility and recovery

- Every state has words and selection has a caret; color is supplementary.
- Keep a visible editing cursor. Do not steal input focus when new output arrives.
- Provide linear readable output without full-screen redraw or repeated spinner announcements. Preserve terminal-native selection and copy behavior where possible.
- Provide ASCII alternatives for Unicode diagrams and check width calculations for non-Latin input.
- Hide optional context at small sizes; never truncate the critical approval action or recovery instruction.
- Explain missing configuration, provider failure, invalid state and interruption. Do not silently reset project files or promise automatic recovery/resume.
- Keep provider secrets and device credentials out of transcripts and screenshots. Account sign-in and provider configuration are separate concepts.

Calculated design contrast: primary/base 13.93:1; muted/raised 7.19:1; selected text 7.65:1; accent/base 9.29:1; warning/base 10.14:1; danger/base 8.56:1; light muted/base 6.39:1. Decorative dividers are 2.71:1 and must never be the sole control boundary/focus indicator. These checks do not establish runtime WCAG or screen-reader conformance; real terminal, keyboard and assistive-technology testing remains necessary after implementation.

## Review artifacts and verification

- `omnix-tui-workspace.png`: final workspace export, visually reviewed after correcting character spacing.
- `omnix-tui-foundations.png`: final foundations export, visually reviewed.
- `omnix-tui-compact.png`: final 80 × 24 single-column export, visually reviewed.
- `omnix-design-backup.fig`: local Figma save containing **both the existing website page and the TUI page**; not a TUI-only file.

The saved TUI page and final review-map node were independently opened in a second Figma tab to verify persistence. The existing website page remains present. Source assets and CLI/application files were not changed. Lint, build and application tests are not applicable to this design-only pass and were not rerun.

Before implementation, review the palette, workspace density, context rail, command discovery, compact presentation and keyboard choices with the user. This proposal does not authorize implementation, deployment or a push.
