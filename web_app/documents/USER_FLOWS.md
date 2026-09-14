<!-- MIRROR FILE: canonical source is ../USER_FLOWS.md. Do not edit independently. -->

# User Flows

## Flow 1 — First-time visitor → understand → install

### Entry
User lands on `/`.

### Steps
1. Reads:
   **Build software with an AI engineering team.**
2. Sees terminal example and the Master Agent concept.
3. Scrolls into the orchestration journey.
4. Understands that the Master Agent maintains context and delegates specialized work.
5. Sees Architect marked as available and future roles marked as roadmap.
6. Reviews real CLI commands.
7. Reaches install/download section.
8. Chooses an installation method.
9. Copies the command or opens the latest release.
10. Optional: opens GitHub for source/details.

### Success
User understands what Omnix does before installing it.

### Failure cases
- No stable release: show preview/source-install state.
- Release API unavailable: show static fallback and GitHub Releases link.
- Clipboard permission fails: select command and show “Press Ctrl/Cmd+C”.

---

## Flow 2 — Technical evaluator → validate product

1. Lands on home page.
2. Goes directly to `How it works` or scrolls to architecture section.
3. Reviews:
   - Master Agent;
   - persistent memory;
   - goals/decisions;
   - Architect Agent;
   - provider abstraction.
4. Opens command explorer.
5. Opens GitHub.
6. Inspects source/tests/README.

Success: marketing statements match implementation.

---

## Flow 3 — Returning user → download latest version

1. Lands on site.
2. Uses sticky header “Download”.
3. Download section identifies current stable version.
4. User selects platform/method.
5. User copies install command or downloads the proper asset.

The user must not have to replay the marketing story.

---

## Flow 4 — Mobile visitor

1. Opens `/`.
2. Navigation collapses into an accessible menu.
3. Hero terminal fits without horizontal page scrolling.
4. Orchestration diagram changes from wide graph to vertical timeline.
5. Terminal commands allow horizontal scrolling only inside the code surface when unavoidable.
6. Install command has a large touch-friendly copy control.

---

## Flow 5 — Keyboard user

1. Uses skip link.
2. Tabs through navigation.
3. Reaches hero CTAs.
4. Controls terminal demo only if it exposes controls.
5. Traverses agent details in logical DOM order.
6. Opens command accordions/tabs using expected keyboard patterns.
7. Copies installation command.
8. Reaches footer.

No information may require hover.

---

## Flow 6 — Reduced-motion user

1. OS/browser reports `prefers-reduced-motion: reduce`.
2. Scroll-triggered movement becomes static or short fades.
3. Agent path is fully visible without animated drawing.
4. Terminal demo shows the final or step-controlled state.
5. No looping ambient movement is required to understand the page.

---

## Flow 7 — Roadmap exploration

1. User sees future agent node.
2. Node is visually labeled `Roadmap`.
3. Opening the node explains intended role without CTA implying availability.
4. User can continue to current capabilities.

---

## Flow 8 — Install failure recovery

The website should include a compact troubleshooting link near install instructions:

- verify Python 3.12+;
- verify command is on PATH;
- link to GitHub issues;
- link to installation documentation when available.

Do not build a large troubleshooting portal into v1.
