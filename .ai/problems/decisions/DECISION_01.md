# Phase 1: Modular Spec + Minimal AI Metadata - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the monolithic `docs/SPEC.md` (1069 lines, mixing architecture, API, database, frontend, deployment, ADRs, flows, UI, business rules) into a modular, domain-based documentation system. Each file has single responsibility (200–800 lines), minimal LLM-oriented metadata, consistent internal structure, and cross-links. This is organizational work — producing structured documents from existing content, not building new capabilities.
</domain>

<decisions>
## Implementation Decisions

### Granularity Boundary

- **API:** One file per domain cluster — `auth-api.md`, `dashboards-api.md` (covers dashboards+layouts+graphs+filters as one bounded context), `processing-api.md`, `admin-api.md`, `health-api.md`
- **Security:** Canonical docs in `/08-security/` + short local summaries with cross-links in domain files. No full duplication, no pure references
- **DB Schema:** Split by structural concern — `schema-core.md` (users, dashboards, graphs, layouts, filters), `schema-processing.md` (aggregated_data, processing_logs, processing_configs), `schema-access.md` (dashboard_access, registration_requests, dashboard_filters), plus separate `indexes.md` and `enums.md`
- **Frontend:** By concern — `architecture.md`, `fsd-structure.md`, `pages.md` (all 8 pages in one file), `auth-flow.md`, `upload-ui.md`, `frontend-security.md`
- **Core splitting principle:** Split by "retrieval intent" — what LLM/user needs loaded into context simultaneously. Target ~25–40 total md files. Not 5 giant docs, not 120 tiny docs

### Metadata Schema

- **Frontmatter fields:** `id`, `domain`, `tags` (optional array), `related`. That's it
- **domain:** Fixed primary taxonomy (12 values: `overview`, `auth`, `dashboards`, `processing`, `backend`, `frontend`, `database`, `api`, `security`, `deployment`, `reference`, `adr`). Must match folder name
- **tags:** Optional freeform array for cross-cutting semantic topics (e.g., `upload`, `csv`, `async`, `backend`)
- **related:** Top 3-5 only — semantic adjacency docs usually loaded together, not exhaustive backlinks
- **layer field:** Dropped entirely — domain + path + embeddings provide sufficient signal; layer creates ambiguity for cross-cutting docs
- **Internal file structure:** Required minimum: `# Purpose` + `# Main Concepts`. Recommended: `# Flows`, `# Constraints`, `# Edge Cases`, `# Related Docs`. Optional: `# Examples`, `# Migration Notes`, `# Open Questions`, `# Performance Notes`. No N/A filler — omit empty sections entirely

### Migration Strategy

- **SPEC.md:** Convert to system overview / documentation index. Not deleted, not a redirect. Becomes the high-level entry point with architecture summary, domain links, key decisions, and main data flow
- **Root index:** Full `README.md` at `/docs/` root for human + AI navigation. SPEC.md = "what the system is", README.md = "how docs are organized"
- **Migration pipeline:** (1) Extract inventory (headings, code blocks, SQL, enums, constraints, warnings) → (2) Map each item to target file → (3) Transfer content → (4) Reconciliation pass. No silent dropping — unclear items go to temporary docs, never deleted
- **High-risk sections for loss:** `6.2 Rate Limiter Failure Behavior`, `6.3 Production Credential Enforcement`, `9.1 Formula Parser limitations`, `11.2 Task Queue Migration`, `15.1 Dashboard Access Enforcement`, `19.5 Application Startup Behavior`, `23.5 CORS validation behavior`
- **Shared content:** Canonical home for each fact + contextual summaries in other locations. "Summarize, don't replicate." Each piece of information has exactly one canonical owner

### Naming and Folder Conventions

- **Folder numbering:** Top-level only (`00-overview/`, `01-auth/`, … `99-reference/`). Sub-folders use plain names without number prefixes
- **File naming:** Kebab-case mandatory — all lowercase with hyphens (`upload-flow.md`, `custom-metrics.md`). Avoid generic names on deeper levels (`api.md` → `auth-api.md`, `security.md` → `upload-security.md`). Top-level `overview.md` within domain folders is an acceptable exception
- **Nesting depth:** Flat by default. Nest only when >5-7 files in a domain. Maximum practical depth: 2 levels below domain root (`domain/subgroup/file.md`)
- **ADRs:** Keep in separate `90-adr/`. ADRs are decision history, not current truth — never merge into domain docs. Immutable-ish, numbered sequentially (`ADR-001-jsonb-storage.md`)
- **Reference:** Keep in separate `99-reference/`. Lookup/static knowledge (enums, env vars, MIME types, error codes) — not domain knowledge. Prevents overview folder from becoming a junk container
- **Semantic zoning:** 00–09 = active system domains, 90 = architectural history, 99 = static lookup/reference

</decisions>

<specifics>
## Specific Ideas

- "If a document is almost always needed together — don't split it" (graphs+filters+layouts = one cluster; upload pipeline+task queue = one cluster; auth+processing = separate)
- "No silent dropping" — if a section's destination is unclear, create a temporary doc rather than deleting it
- "Summarize, don't replicate" — shared content gets a canonical home + contextual summaries elsewhere, never full duplication
- The entire architecture targets ~25–40 md files as the sweet spot for AI-friendly documentation
- Metadata schema is intentionally minimal: `id`, `domain`, `tags`, `related` — nothing enterprise (no owner, reviewers, jira, epic, priority, sprint, risk, compliance)
</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope
</deferred>

---

_Phase: 01-modular-spec_
_Context gathered: 2026-05-18_
