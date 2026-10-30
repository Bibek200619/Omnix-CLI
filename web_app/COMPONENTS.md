# Components

## 1. Component Strategy

### Approved redesign contracts — 2026-10-30

Keep existing primitives, source-backed product modules, release normalization and `/cli` path handling. The approved Figma revision supersedes historical visual descriptions below.

- `HeroTerminal` becomes a small client island with three user-selected transcript states: Initialize, Assign models, Inspect blueprint. Real locally captured CLI output is selectable DOM `pre/code`, never generated narration. Tabs follow keyboard conventions; no autoplay/live-region streaming. No-JavaScript readers retain the transcripts. Supporting proof uses shared transcript data, with excerpts labelled when shortened.
- `DownloadAction` uses a native modal dialog, real button trigger, initial focus, an explicit Tab loop, native Escape, Close, return focus, and View CLI setup navigation. Layout changes dismiss hidden header dialogs and restore a visible menu or brand target when the opener disappears. Disabled Coming later is not focusable. A no-JavaScript source-setup link remains. Header and final setup use the same component.
- Server-rendered sections retain semantic headings, complete command data and explicit provider statuses. Journey retains its existing user-controlled state/focus behavior but is laid out as a vertical connected route alongside terminal evidence. Command groups use native disclosure and exact copy controls.
- Pale file/model details have scoped light tokens; terminals, dialog and downstream content have dark tokens. Global primitives consume semantic tokens in either context. Decorative backgrounds never contain essential content.

Build primitives first, domain components second, sections last.

Pages should compose established components rather than creating local one-off styling.

## 2. Primitives

### Phase 2 implementation contracts — 2026-09-15

Import primitives directly from `website/components/ui/<name>`; no barrel export or polymorphic `asChild` API. Native HTML props/ref are forwarded where applicable. Styling lives in a shared CSS module and consumes semantic tokens. Callers provide meaningful visible labels; icon-only controls are outside this phase.

| Primitive | Contract |
|---|---|
| `Container` | A `div` with `width="page"` (default) or `"prose"`, shared gutters, and a bounded width. Use once per horizontal layout boundary; avoid nesting gutters. |
| `Section` | A semantic `section` requiring `id` and `title`, with `headingLevel` 2 (default) or 3 and `spacing="default"` or `"compact"`. Owns a labelled heading and vertical spacing; does not add a Container. |
| `Button` | Native button; `variant="primary"` (default), `"secondary"`, or `"ghost"`. Defaults to `type="button"`; `disabled` and `loading` use native disabled behavior. Loading keeps the original label and adds visible progress text plus `aria-busy`. No animation is required. |
| `Link` | Native anchor for navigation; underlined by default. `variant="primary"`, `"secondary"`, or `"ghost"` gives action styling. Same-tab navigation by default; `newTab` adds protected rel values and an accessible new-tab notice. HTTPS external destinations get a small decorative direction mark. Relative paths/anchors are supported; unsafe URL schemes are rejected. No disabled-anchor imitation. |
| `Badge` | Noninteractive span with required `status="available"`, `"roadmap"`, `"preview"`, or `"version"`. Fixed visible status labels; the version variant requires a `version` string. Roadmap uses a dashed border as well as text. Availability context remains the caller's responsibility. |
| `Code` | Selectable inline `code`, with safe wrapping for long identifiers. |
| `CodeBlock` | Required string `code` and accessible `label`; semantic `pre/code` within a labelled figure. Preserves whitespace, scrolls internally, supports keyboard scrolling, and optionally includes `copyable` CopyButton with a visible `copyLabel`. No HTML injection or syntax-highlighter dependency. |
| `CopyButton` | Required `text`; optional visible `label` defaults to `Copy command`. Writes only after a user click, prevents duplicate pending requests, announces success politely, and allows retry. Denied/missing Clipboard API reveals a labelled read-only text area with exact text, focuses/selects it, and gives keyboard/touch manual-copy instructions. No deprecated clipboard fallback or clipboard reads. |

Deployment paths: `Link` keeps native anchors and HTTPS destinations unchanged,
and prefixes app-relative paths with the build-time `NEXT_PUBLIC_BASE_PATH`.
Brand image and metadata paths use the same resolver. This keeps home/recovery
links inside `/cli` when deployed alongside the main Omnix app.

Only `CopyButton` requires a Client Component boundary. Other primitives work in Server Components; interactive consumers import Button into their own client boundary. Native loading/disabled buttons are excluded from tab order. Tabs and Disclosure are deferred until parallel or collapsible content is required.

The noindex `/design-system` route is a component review fixture, excluded from sitemap and marketing navigation. It displays real source-preview labels and CLI commands without executing them. A small client-only control example demonstrates all button variants and actual loading/disabled behavior. It is not a product landing section.

Example Server Component composition (use unique section IDs and preserve heading order):

```tsx
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { CodeBlock } from "@/components/ui/code-block";

<Container width="prose">
  <Section id="inspect" title="Inspect project state">
    <CodeBlock label="Read the blueprint" code="omnix blueprint" copyable />
  </Section>
</Container>;
```

### `Button`
Variants:
- primary
- secondary
- ghost

States:
- default
- hover
- focus-visible
- active
- disabled
- loading when applicable

### `Link`
External links must visually or accessibly indicate external navigation where useful.

### `Container`
Controls max width and responsive gutters.

### `Section`
Provides consistent vertical rhythm and optional anchor target.

### `Badge`
Use for semantic states:
- Available
- Roadmap
- Preview
- Version

### `Code`
Inline code token.

### `CodeBlock`
Accessible, selectable block with optional copy action.

### `Tabs`
Only use when content categories are parallel, e.g. install methods/platforms.
Must support keyboard navigation.

### `Disclosure`
For mobile navigation or optional command details.

## 3. Product Components

### `SiteHeader`
Phase 3: Server Component containing the official linked logo, desktop navigation, and an isolated MobileNav Client Component. Product links to `#product`, CLI to the hero walkthrough at `#cli`; GitHub and source-preview links use centralized URLs. Desktop is sticky; mobile remains in flow. No absent section links or scroll listeners.

Props/data:
- navigation items;
- GitHub URL;
- primary CTA.

Behavior:
- sticky on desktop;
- compact;
- keyboard accessible.

### `MobileNav`
Use disclosure/dialog semantics.
Must return focus to trigger on close.

Phase 3 uses a button with `aria-expanded`/`aria-controls` and a labelled navigation disclosure (not a modal or ARIA menu). Opening retains trigger focus; Tab enters the links. Escape or closing restores trigger focus. Internal link activation closes the menu and focuses the destination. Leaving the disclosure with Tab closes it without stealing focus. Desktop breakpoint changes reset it. A no-JavaScript fallback exposes the same links.

### `HeroTerminal`
Phase 3: Server Component with a labelled figure and ordered command rows. Each row contains selectable `pre/code` and an explicit website note. It owns this domain-specific annotated layout rather than nesting generic CodeBlocks. CopyButton copies only the five commands, without prompts or narration. The explicit configuration command uses the CLI README's OpenAI/gpt-5 example; availability depends on the user's provider account. No invented output, live provider calls, timers, streaming announcements, or playback controls. The prerequisites name source setup and the Architect's OpenAI API key requirement. Source evidence lives beside the content in `content/hero.ts`.

Purpose:
Demonstrate Omnix with a deterministic sequence.

Data model:
```ts
type TerminalStep = {
  command?: string
  output: TerminalLine[]
  delayHint?: number
}
```

Must support reduced motion.

### `OrchestrationJourney`
Signature narrative component.

Inputs:
- nodes;
- edges;
- status;
- explanatory copy.

Do not hardcode the diagram purely in canvas if it harms accessibility. DOM/SVG should retain semantic text.

Phase 4: `OrchestrationJourney` composes the Section/Container primitives, server-rendered stage content, a small `JourneyExplorer` client boundary, and source-preview/roadmap annotations. `content/journey.ts` holds the five-stage narrative and evidence paths; agent status/names and provider roadmap entries come from the existing product modules. `JourneyExplorer` adds stage selection, Previous/Next controls, current-step semantics and a labelled handoff explanation. It never executes a CLI command. Essential ordered-list content remains server rendered and available without JavaScript. CSS rails are decorative; text explains each relationship. No animation package or scroll observer is required.

### `AgentNode`
Fields:
- name;
- role;
- status;
- availability label;
- short explanation.

### `ContextStack`
Visualizes:
- memory;
- goals;
- decisions;
- blueprint.

Phase 5: `MemorySection` groups memory records under `project.memory.json` and the blueprint under its separate `project.blueprint.json` in a definition-list file ledger. The memory command reports a stored-message count, not message bodies. The section explicitly describes local persistence and the manual specialist boundary.

### `ProviderStrip`
Displays supported/configurable provider names as text, not fake partnership logos unless branding permission exists.

Phase 5: `ProvidersSection` uses a semantic table rather than provider logos. OpenAI is labelled Available; Anthropic, Google, OpenRouter, and DeepSeek use textual Roadmap badges and dashed row boundaries. The horizontally scrollable table is keyboard reachable on narrow screens.

### `CommandExplorer`
Structured list of commands.

Each command:
- syntax;
- one-sentence purpose;
- optional example;
- copy button.

`CliSection` presents all executable commands from `content/commands.ts` and derives its visible count from that data. As of 2026-10-30 this is 33 entries, including five optional account commands and two session subcommands alongside the original ten core commands. Sixteen preview-orchestration commands remain in a native `details` disclosure. Session copy explains server/link/compatibility requirements and offline history. Every row uses the shared CopyButton and remains present in server-rendered HTML. Copying preserves documented syntax; uppercase arguments are explicitly marked as placeholders to replace before running.

### `ArchitectFlow`
Step narrative:
requirements → context → architecture reasoning → blueprint → validation.

Do not display hidden model chain-of-thought. Use product-level process descriptions only.

Phase 5: `ArchitectSection` shows the verified implementation sequence—read context, request a structured proposal, evolve the existing blueprint, then validate and save. Source filenames are evidence labels, not links or simulated output.

### `RoadmapTimeline`
Clearly separates shipped and planned phases.

Phase 6: `RoadmapSection` renders a semantic ordered list of implemented capability groups and a separate unordered list of confirmed future provider adapters. `content/roadmap.ts` owns milestone summaries/evidence and preserves the existing provider-derived roadmap export used by the orchestration journey. Every implemented group has an Available badge in explicit source-preview context; every future adapter has a Roadmap badge and a dashed boundary. Source links use the canonical repository URL. All content is server rendered with no new interaction boundary.

### `InstallPanel`

Phase 7: `InstallSection` accepts a normalized ReleaseState, renders an explicit publication/failure notice, and retains verified source setup in every state. It uses the shared CodeBlock/CopyButton, a semantic requirements list, official documentation/release links, and a native troubleshooting disclosure. `HomePage` composes synchronous sections for testing; the async App Router entry owns the cached server fetch. No browser API token or direct artifact/registry download is introduced.

Fields:
- release status;
- version;
- requirement;
- methods/platforms;
- command;
- copy button;
- release link.

State variants:
- stable
- prerelease
- preview/no-release
- API unavailable

### `ReleaseBadge`
Never show `latest` without resolved release metadata or explicit static fallback.

### `CopyButton`
Must:
- use Clipboard API when available;
- show success feedback;
- fall back gracefully.

### `Footer`
Keep concise.

## 4. Section Components

Suggested:
- `HeroSection`
- `ConceptSection`
- `JourneySection`
- `MemorySection`
- `ProvidersSection`
- `CliSection`
- `ArchitectSection`
- `RoadmapSection`
- `DownloadSection`

Sections should not own global product data.

## 5. Shared Data

Create structured content modules, e.g.:

```ts
export const commands = [...]
export const agents = [...]
export const roadmap = [...]
export const providers = [...]
```

This prevents marketing copy from drifting across sections.

## 6. Component Review Checklist

Before a component is accepted:
- semantic element choice is correct;
- keyboard behavior works;
- focus visible;
- loading/empty/error states handled if applicable;
- responsive state defined;
- reduced motion defined if animated;
- no arbitrary design tokens;
- no duplicated product truth;
- unit test added where behavior is non-trivial.
