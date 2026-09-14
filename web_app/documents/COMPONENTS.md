<!-- MIRROR FILE: canonical source is ../COMPONENTS.md. Do not edit independently. -->

# Components

## 1. Component Strategy

Build primitives first, domain components second, sections last.

Pages should compose established components rather than creating local one-off styling.

## 2. Primitives

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
