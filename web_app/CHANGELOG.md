# Changelog

All meaningful changes to the Omnix CLI website specification and implementation should be recorded here.

Use a lightweight Keep-a-Changelog style.

## [Unreleased]

### Phase 0 and Phase 1 — 2026-09-14
- Inspected Python CLI source and separated its preview capabilities from the Node MVP.
- Corrected stale roadmap labels: Planner, workers, Integration, QA, Repair, execution coordination, and build orchestration already exist in source. Documented artifact/report limitations and the lack of Master chat dispatch.
- Confirmed Python >=3.12, package 0.1.0, 26 registered commands, one live provider adapter, four placeholders, and no public GitHub releases.
- Reviewed all useful local reference assets and preserved the official logo.
- Established a static Next.js foundation, semantic design tokens, structured product data, release state helpers, and automated quality commands under `website/`.
- Reserved subsequent UI work for Phase 2 onward; no final homepage or install CTA.

### Added
- Initial product specification.
- Website requirements.
- Information architecture.
- User-flow definitions.
- Design system.
- Component contracts.
- Frontend architecture.
- GitHub release/API integration contract.
- No-database decision for v1.
- Security requirements.
- Accessibility requirements.
- Testing strategy.
- Phased execution plan.
- Reference and originality rules.

### Decisions
- `web_app/*.md` is the canonical documentation source.
- `web_app/documents/*.md`, when present, is a secondary mirror only.
- Website v1 is static-first and does not require a database.
- Production download CTA depends on a verified CLI release/distribution path.
- Current and roadmap agent capabilities must be visually and semantically distinct.
- The “Angry Birds” influence is limited to progression/journey structure, not visual copying.

## Change Entry Template

```md
## [YYYY-MM-DD]

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Removed
- ...

### Decision
- ...
```
