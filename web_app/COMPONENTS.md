# Components

## 1. Component Strategy

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
| `CodeBlock` | Required string `code` and accessible `label`; semantic `pre/code` within a labelled figure. Preserves whitespace, scrolls internally, supports keyboard scrolling, and optionally includes `copyable` CopyButton. No HTML injection or syntax-highlighter dependency. |
| `CopyButton` | Required `text`; optional visible `label` defaults to `Copy command`. Writes only after a user click, prevents duplicate pending requests, announces success politely, and allows retry. Denied/missing Clipboard API reveals a labelled read-only text area with exact text, focuses/selects it, and gives keyboard/touch manual-copy instructions. No deprecated clipboard fallback or clipboard reads. |

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
Props/data:
- navigation items;
- GitHub URL;
- primary CTA.

Behavior:
- sticky after initial viewport;
- compact;
- keyboard accessible.

### `MobileNav`
Use disclosure/dialog semantics.
Must return focus to trigger on close.

### `HeroTerminal`
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

### `ProviderStrip`
Displays supported/configurable provider names as text, not fake partnership logos unless branding permission exists.

### `CommandExplorer`
Structured list of commands.

Each command:
- syntax;
- one-sentence purpose;
- optional example;
- copy button.

### `ArchitectFlow`
Step narrative:
requirements → context → architecture reasoning → blueprint → validation.

Do not display hidden model chain-of-thought. Use product-level process descriptions only.

### `RoadmapTimeline`
Clearly separates shipped and planned phases.

### `InstallPanel`
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
