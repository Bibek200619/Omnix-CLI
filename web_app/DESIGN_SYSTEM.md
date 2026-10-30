# Design System

## 1. Design Direction

### Approved Figma redesign — 2026-10-30

The owner approved revision 2 in [the editable Figma file](https://www.figma.com/design/rvBXxqcHxccTKZwv648gof?node-id=10-17608). This decision supersedes the historical dark/mint treatment described in the phase notes below.

- Preserve the editorial opening: ice/cobalt/teal color, solid ink headline, broad authentic terminal, unchanged official logo. Use Manrope for display/body and IBM Plex Mono for commands, bundled locally.
- Color anchors: opening `#CADBFC` / `#E8F1FB`, ink `#14233B`, action `#2864DC`, terminal `#101D30`, slate/teal `#304A55`, graphite `#0C1118`, ending `#030405`. Semantic tokens own these values. Blue remains the action family; teal communicates context/state rather than a second primary CTA.
- Separate solid action/selection blue from the lighter dark-surface link/focus accent. Scoped light/dark themes recompute control and focus aliases locally, so nested controls preserve contrast rather than inheriting resolved parent surfaces.
- The entire page progresses from light/color through slate and graphite to near-black. Adjacent gradient endpoints match. Never reset full sections to white, repeat the same blue rectangle, or turn the whole site black. Pale surfaces are local file/model detail panels.
- Use a ~1200px inner content width, 20px mobile gutters, 64px maximum desktop headline and the existing spacing scale. A vertical connected journey, embedded memory ledger, role/provider/model rows, dense command disclosures and source-setup terminal provide varied composition.
- Background-only drift may use a native CSS scroll timeline, capped at 24px. Content remains fully opaque, in document order, with native scrolling. No scroll interception, animation dependency, particles or autoplay. Reduced motion uses the same static gradients and user-controlled terminal states.
- Download Omnix opens the availability dialog. The CLI is a source preview; the Omnix app is planned. Only View CLI setup is actionable; Coming later is visibly disabled. Do not imply an available app binary.

The Figma storyboard and player frames were static proposals. Implementation supplies actual keyboard-operable controls and verifies them in browsers; no recorded product video exists.

**Terminal × engineering diagram × editorial product page**

The website should feel premium because it is coherent and precise, not because it contains many effects.

## 2. Principles

### Purposeful visual elements
Every line, border, highlight and animation must communicate:
- grouping;
- hierarchy;
- state;
- direction;
- interaction; or
- progress.

### One signature accent
Use one primary Omnix accent family. Do not create a rainbow AI palette.

### Strong neutral foundation
Most of the UI should be neutral so code, agent state and CTA emphasis remain meaningful.

### Density with breathing room
Developer products can carry information density. Avoid both cramped dashboards and giant empty marketing spaces.

## 3. Color Tokens

Final brand values may change, but implementation must use semantic variables.

Example dark theme:

```css
--bg: #090a0c;
--surface-1: #0d0f12;
--surface-2: #12151a;
--surface-3: #181c22;

--text-1: #f4f6f8;
--text-2: #a7adb7;
--text-3: #737b87;

--border-1: rgba(255,255,255,.10);
--border-2: rgba(255,255,255,.16);

--accent: #8ee3c8;
--accent-strong: #b2f5df;
--success: #7dd3a7;
--warning: #e4c474;
--danger: #ec8e8e;
```

These are starting tokens, not permission to scatter raw hex values through components.

Phase 1 resolves these into semantic `--background`, `--text-primary`, `--text-secondary`, `--text-tertiary`, `--border-subtle`, and `--border-strong` names in `website/app/globals.css`. Tertiary text is lifted to `#9199a5` for AA readability on all three dark surfaces. Strong borders use `#657080` where a control boundary needs non-text contrast; subtle borders are decorative separators only. Mint `#8ee3c8` is the interaction accent, while the official blue logo is preserved unchanged.

Phase 1 uses locally bundled Geist and Geist Mono variable Latin fonts via `next/font/local` (no Google Fonts build-time request), a 1280 px maximum page width, 16–32 px responsive gutters, and the documented spacing scale. Font roles, type sizes, line heights, radius, focus, selection, and motion durations are tokens. Focus uses a 2 px accent outline with a 4 px offset. Motion is disabled in reduced-motion mode; forced-colors keeps system focus colors.

Foundation composition: a left-aligned logo/name row, one short preview heading, a source link, and a compact version/requirements line. No final hero, terminal demo, orchestration section, primitive library, or decorative animation is built in Phase 1.

## 4. Typography

Recommended:
- UI/display: Geist, Inter, or another high-quality neutral sans;
- code: JetBrains Mono, Geist Mono, or system monospace fallback.

Hierarchy:
- Hero: clamp-based, bold but not ultra-heavy.
- Section titles: editorial, compact line-height.
- Body: 16–18 px desktop, readable line length.
- Meta/labels: 12–14 px; never rely on tiny text for essential information.

Maximum body measure: approximately 65–72 characters.

## 5. Spacing

Use a limited spacing scale:
`4, 8, 12, 16, 24, 32, 48, 64, 96, 128`

Avoid arbitrary values unless an optical correction is documented.

## 6. Radius

Default:
- controls: 8–10 px;
- surfaces: 12–16 px;
- terminal: 14–18 px.

Avoid making every section a giant rounded rectangle.

## 7. Borders and Shadows

Borders should define technical surfaces.

Prefer:
- subtle 1 px borders;
- inner highlights sparingly;
- minimal shadows.

Do not use heavy diffuse shadows to make every card float.

## 8. Grid

Desktop:
- max page width ~1200–1280 px;
- 12-column conceptual grid;
- readable content measures within the grid.

Mobile:
- 16–20 px outer gutter.

Large desktop:
- preserve line lengths; do not stretch text to viewport width.

## 9. Terminal Surface

Terminal is a product demonstration, not decoration.

Requirements:
- semantic code/`pre`;
- realistic prompt/output;
- strong contrast;
- copyable commands;
- terminal chrome kept minimal;
- no fake macOS controls required;
- wrap or internal-scroll long code safely.

## 10. Agent Nodes

States:
- `available`
- `active-demo`
- `roadmap`
- `inactive`

Available:
- normal contrast;
- solid connection.

Roadmap:
- lower contrast;
- dashed/segmented connection;
- explicit text label.

Never communicate status using color alone.

## 11. Motion

Use motion to show:
- direction through orchestration;
- state transition;
- connection activation;
- terminal sequence;
- section entry.

Avoid:
- continuous floating;
- mouse-following glows;
- excessive parallax;
- spinning gradients;
- scroll hijacking.

Timing guidelines:
- micro interaction: 120–200 ms;
- surface transition: 180–280 ms;
- narrative activation: 300–600 ms;
- no long blocking sequences.

Reduced-motion mode must preserve the full story statically.

## 12. Iconography

Use one icon family or custom simple line icons.

Prefer semantic engineering icons:
- terminal
- memory
- architecture
- model/provider
- goal
- decision
- validation

Avoid emoji as product icons.

## 13. Buttons

Primary:
- one visually dominant action per section;
- action verb first: `Install Omnix`, `Copy command`, `View on GitHub`.

Secondary:
- quiet bordered or text action.

All:
- visible focus;
- >= 44 px touch target where practical;
- loading/disabled states when required.

## 14. Anti-Patterns

Reject a design if it contains several of:
- three equal feature cards beneath hero;
- giant gradient headline;
- multiple colored glow blobs;
- meaningless badge “AI POWERED”;
- fake social proof;
- 24+ px radius everywhere;
- animations that start before content is understood;
- generic “Supercharge your workflow” copy.

## 15. Design Acceptance Test

A screen passes when:
- hierarchy is obvious in grayscale;
- it remains understandable without motion;
- it uses system tokens;
- current and roadmap states cannot be confused;
- code examples are real;
- no section exists solely to look impressive.

## 16. Phase 2 primitive treatment

Keep the Phase 1 palette and font families. Add semantic control tokens for default/hover surfaces, disabled text, control padding, section rhythm, and code spacing. Primary buttons use mint with dark text; secondary buttons use a strong neutral boundary; ghost buttons remain quiet. Pressed controls use an inset outline. All control variants have a minimum 44 px height/width, visible focus offset, and wrapping labels. Inline text links retain underlines; action links share button geometry.

Badges use explicit text and border style, without animation or color-only meaning. Roadmap borders are dashed and text remains readable. Code uses surface-2, a restrained border and the existing terminal radius. Long blocks scroll inside a keyboard-focusable code region; ordinary text and inline code reflow. Selection and forced-colors focus continue to use global tokens.

The component review page uses a single reading column with labelled sections, compact specimen rows that wrap, and a small three-surface comparison solely to review hierarchy. This is a development reference, not the future homepage. No hero or decorative visual assets are added. The original Omnix logo stays unchanged.

## 17. Phase 3 header and hero

Use the existing near-black background (#090a0c), quiet terminal surface (#0d0f12), nested surface (#12151a), primary text (#f4f6f8), secondary text (#a7adb7), and mint action accent (#8ee3c8). Geist carries the editorial headline, capped at 56 px; Geist Mono distinguishes commands. Preserve the blue logo without effects.

Composition: a compact full-width header, then an asymmetric reading column alongside a command walkthrough. Align the terminal's upper rule with the product identity; the terminal is the proof for the adjacent message, not a floating window. At tablet widths, the walkthrough follows the copy and actions. Use existing spacing and radius tokens; no decorative grid, gradient, badge cluster, shadows, or character-by-character typing. Five ordered commands communicate real progression, with website narration visually separate from shell commands. The complete story is static and immediately readable in all motion modes.

The header is sticky on desktop only, with an opaque background and a quiet bottom border. Mobile uses an in-flow disclosure so the menu never covers the headline or traps focus. Only existing targets are presented: Product, CLI, GitHub, and source preview. Future anchors remain absent until their sections exist. Anchor offsets account for the desktop header.

## 18. Phase 4 orchestration journey

Keep the existing background (#090a0c), surface-1 (#0d0f12), surface-2 (#12151a), primary text (#f4f6f8), secondary text (#a7adb7), and mint accent (#8ee3c8). Geist carries the story; Geist Mono identifies commands, stage numbers, and persisted filenames. No new palette or font is needed.

The composition is a connected five-stage route: goal → Master → saved context → explicitly invoked Architect → validated blueprint. On wide screens a horizontal rail joins the stages; narrow screens use the same DOM order as a vertical rail. Numbers encode actual narrative order. Agent stages have bounded surfaces, context uses a compact file ledger, and the goal/result remain open. Avoid five identical feature cards. A selected stage has a heavier outline, an explicit current-step state, and a concise handoff explanation below the route. All core explanations remain visible at every step.

Progression is user-controlled: select a stage, or use Previous/Next on wide screens. The wide layout uses a shared explanation panel; the vertical layout puts the selected explanation immediately below its node so mobile visitors do not have to search for feedback. Selection persists across layout changes. No autoplay, scroll interception, or ambient motion. Text changes immediately at full contrast; fading text is excluded because it loses contrast during transitions. All core stage content remains available, including with reduced motion. Controls are at least 44 px and preserve keyboard focus. Without JavaScript the full route is static, with no inert playback controls.

A compact continuation names the existing build workflow and its artifact/report limits. A separate dashed provider branch is labelled Roadmap; it must never imply providers are the next execution stage or that implemented specialists are future work. The complete section lives at `#how-it-works`; navigation gains this target only when it exists.

## 19. Phase 5 product proof

Product proof uses four related but distinct editorial structures instead of repeating a card grid. Memory is a `.project/` file ledger, providers are a status table, commands form a dense index, and the Architect is a numbered implementation pipeline. These structures encode file ownership, compatibility status, discoverability, and execution order respectively.

The command index is the visual center of the phase. On wide screens its three core groups form columns; on narrow screens they read in source-workflow order. Every command row retains a 44 px copy control. The 16 orchestration commands use a native disclosure with explicit Show/Hide wording so the page stays scannable without hiding content behind JavaScript.

Provider state never depends on color: OpenAI has an Available badge and the four placeholder adapters have Roadmap text plus dashed row rules. The table scrolls within its own labelled region on narrow screens. The Architect flow shows product-level stages and source filenames only; hidden model reasoning is neither implied nor displayed. No new colors, fonts, dependencies, animations, or decorative imagery are introduced.

## 20. Phase 6 roadmap

Use the established dark surfaces, Geist/Geist Mono roles, and mint interaction accent. A solid vertical rail connects seven implemented capability groups in their engineering progression; compact numbered markers express that order, not release dates or CLI phase numbers. Each row pairs its summary with an Available badge and an implementation link. A separate dashed branch names the four future provider adapters with Roadmap badges. At desktop widths the future branch sits beside the implemented timeline; on mobile it follows in DOM order. No sticky panel, autoplay, progress percentage, delivery date, or repeated feature-card grid.

The section states that availability refers to source preview and that artifact/report generation does not establish a tested, deployable application. It adds the durable `#roadmap` destination. Retain the references' controlled spacing, clear hierarchy, and staged explanation without copying their compositions or imagery.

## 21. Phase 7 source setup

End the page with a practical setup surface at `#download`: release status and a compact requirement ledger on the left, one labelled source-setup CodeBlock on the right. Stack in reading order on mobile. Reuse the existing terminal surface, tokens, and copy recovery. Keep release publication separate from verified installation: all four metadata states retain source-preview setup until an additional distribution method is verified. A native disclosure contains concise setup recovery, and the hero/header preview actions navigate directly to this section. No platform tabs are needed for a single verified method.

## 22. Final review surfaces

Keep the reviewed page composition. Desktop navigation can wrap under text enlargement. Footer links wrap within the existing gutter and spacing scale. The 404 uses a short, quiet reading column and two clear recovery actions. The 1200×630 social image uses actual hero text and the unchanged official PNG with explicit numeric dimensions; its renderer mirrors the documented dark/neutral palette independently of browser CSS. No new decorative assets, font downloads, animation, or product-section redesign is introduced by final QA.
