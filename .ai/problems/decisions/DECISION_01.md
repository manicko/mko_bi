# Phase 1: Dashboard Creation Guide - Context

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Write a how-to guide at `docs/11-guides/` documenting the complete admin workflow for creating a new dashboard — from pre-creation planning through configuration, first upload, access management, and ongoing operations. The guide targets admins who are already familiar with the application UI. It is a narrative, prose-driven guide (not an API reference), cross-linking to existing specs for field-level detail.
</domain>

<decisions>
## Implementation Decisions

### Content scope & depth

- Begin at the admin panel "Create Dashboard" action — no need to explain admin UI navigation
- Include a **DB/API reference section** summarizing the relevant tables (`dashboards`, `graphs`, `processing_configs`, `dashboard_filters`, `dashboard_access`) with links to `09-database/schema-core.md` and `02-dashboards/`
- Cover the **full lifecycle**: pre-planning → create → configure → upload → verify → grant access → ongoing operations → troubleshooting
- **Pre-creation section**: brief planning checklist — what data will be uploaded, what columns, what charts are needed, preparing the processing config
- **Post-upload section**: granting dashboard access to editors/viewers, ongoing operations (re-uploading data, modifying config, managing filters)
- End-to-end flow, not a fragmented reference

### Prerequisites & discovery

- Assume the reader is familiar with the application and admin panel; cover only dashboard-creation-specific knowledge in this guide
- **Hub-and-spoke model**: this guide narrates the workflow; cross-link to `SPEC.md`, `02-dashboards/`, `03-processing/`, `09-database/` for reference details
- One sentence at the start: "You must have the Admin role to create dashboards" — no deeper auth explanation
- **Processing config format**: include 2–3 annotated JSON examples (simple → medium → complexity) in a clearly-marked appendix section; the main guide stays procedural and links to `03-processing/processing-api.md` for field-level detail. Co-locate examples in one section so format changes require updating only one place
- **Layout system**: brief conceptual overview (rows/columns/graph slots as the admin sees them in the UI). Do NOT document the `layouts.definition` JSONB structure — admins interact with a visual editor, not raw JSON

### Document structure

- **Chronological workflow order** — each section maps to a phase the admin goes through (plan → create → configure → upload → verify → grant access → ongoing). Component-type organization would force the reader to jump around
- No screenshots — describe the UI textually (faster to maintain, doesn't go stale)

### File placement

- New file in `docs/11-guides/` (e.g., `create-dashboard.md`), alongside `docker.md` and `task-queue-migration.md`

### Doc maintenance compliance

- The guide MUST follow `docs/00-overview/doc-maintenance-rules.md`:
  - YAML frontmatter (`id`, `domain`, `tags`, `related`)
  - English-only content
  - `## Purpose` section at the top
  - Cross-links use relative paths (`../02-dashboards/dashboards-api.md`)
  - All documentation text in clear English

### KiloCode's Discretion

- Exact number and complexity of JSON examples in the appendix (2 or 3, as long as they cover simple→complex spectrum)
- Depth of the troubleshooting section — add common issues as needed based on existing error paths in the codebase
- Exact wording of section headings and UI descriptions
- Whether to include a "Quick Start" condensed summary at the top or keep the single linear flow
- Format of the DB/API reference section (summary table vs. narrative description)

</decisions>

<specifics>
## Specific Ideas

- The processing config is the most complex piece — the admin does an edit-code-edit loop. Handle by walking one concrete example end-to-end in the appendix, while keeping the main guide procedural
- Cross-link heavily: this guide is the narrative hub, not a replacement for existing specs
- Examples should be realistic but clearly labeled as examples (e.g., "Sales Dashboard") to avoid being mistaken for prescriptive templates

</specifics>

<deferred>
## Deferred Ideas

- Covering the processing config auto-wiring or column type detection behavior in depth — that belongs in `03-processing/` docs
- Documenting dashboard layout JSON schema — internal implementation detail, not admin-facing

</deferred>

---

_Phase: 01-dashboard-creation-guide_
_Context gathered: 2026-06-03_
