# Accessibility

## 1. Standard

Target **WCAG 2.2 AA**.

Accessibility is a release requirement, not a polish task.

## 2. Semantic Structure

Use:
- one `<main>`;
- logical heading hierarchy;
- `<nav>` for navigation;
- real `<button>` elements for actions;
- real links for navigation;
- `<pre><code>` for terminal/code;
- lists for lists;
- appropriate dialog/disclosure semantics.

Do not recreate native controls with generic `<div>` elements.

## 3. Keyboard

All interactive features must work without a mouse.

Required:
- skip link;
- visible focus;
- logical tab order;
- no focus traps except an intentionally managed modal/dialog;
- Escape closes overlays;
- mobile navigation restores focus to trigger;
- tabs/disclosures follow expected keyboard interaction.

## 4. Motion

Respect `prefers-reduced-motion: reduce`.

For reduced motion:
- do not draw the orchestration path over long durations;
- no looping ambient motion;
- terminal playback becomes immediate or user-controlled;
- parallax is removed;
- information remains fully available.

## 5. Color and Contrast

- body text: WCAG AA contrast;
- large text: WCAG AA;
- controls and focus indicators remain visible;
- status is never color-only.

Agent state must include textual labels such as `Available` and `Roadmap`.

## 6. Terminal Accessibility

The terminal demo must:
- not rapidly stream unreadable text by default;
- expose readable DOM text;
- avoid excessive `aria-live`;
- not announce every decorative animation;
- allow copying real commands;
- maintain accessible contrast.

If auto-playing, announcements should be limited or the terminal should not be a live region.

## 7. Orchestration Diagram

Visual graph relationships must also exist in text/DOM order.

Screen-reader users should be able to understand:
1. user goal;
2. Master Agent;
3. context;
4. Architect Agent;
5. other implemented preview specialists and confirmed roadmap capabilities (currently additional live provider adapters).

Do not rely on SVG lines alone to communicate meaning.

## 8. Responsive Zoom

At 200% zoom:
- no essential content is clipped;
- no two-dimensional page scrolling for ordinary text;
- controls remain usable.

At 400%:
- core content reflows where WCAG requires.

## 9. Touch

Interactive target size should target at least 44×44 CSS px where practical.

Do not put tiny icon-only controls next to terminal text.

## 10. Images

Decorative visuals use empty alt text.
Meaningful diagrams require concise equivalents.
Do not duplicate nearby visible text in alt attributes.

## 11. Testing

Automated:
- axe;
- Lighthouse;
- semantic queries in component tests.

Manual:
- keyboard-only;
- VoiceOver or NVDA smoke test;
- 200% zoom;
- reduced motion;
- high contrast/forced colors where possible.

## 12. Acceptance Criteria

A feature is not done if:
- its state is available only on hover;
- focus is invisible;
- animation is required for understanding;
- roadmap/current status depends only on color;
- diagram content is inaccessible to screen readers;
- copied command cannot be selected manually.
