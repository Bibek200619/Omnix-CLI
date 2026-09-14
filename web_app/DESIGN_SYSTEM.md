# Design System

## 1. Design Direction

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
