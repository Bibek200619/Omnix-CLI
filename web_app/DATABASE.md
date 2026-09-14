# Database

## 1. Decision

**Website v1 has no application database.**

This is intentional.

The website is a public product/installation surface and does not currently need:
- accounts;
- user profiles;
- saved preferences;
- billing;
- cloud projects;
- comments;
- CMS content;
- form submissions.

Adding a database would create operational and privacy cost without improving the primary user journey.

## 2. Sources of Data

### Static repository content
- product copy;
- capability status;
- command list;
- provider list;
- roadmap;
- design content.

### External release metadata
- GitHub Releases.

### Build/deployment metadata
- optional commit SHA/build version.

## 3. Local Browser State

Allowed when useful:
- terminal demo replay preference;
- dismissed non-critical UI state;
- selected install tab.

Prefer in-memory state unless persistence improves UX.

Do not store:
- terminal content entered by the user;
- GitHub credentials;
- provider keys;
- sensitive developer data.

## 4. Future Database Trigger

Reconsider a database only when a shipped requirement needs durable server-side data, e.g.:
- account-based cloud service;
- waitlist;
- documentation feedback;
- managed telemetry;
- web dashboard;
- team/project cloud synchronization.

Before adding one, update:
- PRODUCT.md
- REQUIREMENTS.md
- ARCHITECTURE.md
- API.md
- SECURITY.md
- privacy documentation

## 5. Supabase

Although the broader Omnix ecosystem may use Supabase, the marketing/download site should not connect to Supabase merely because it exists elsewhere.

Every persistent service must justify itself through a user requirement.
