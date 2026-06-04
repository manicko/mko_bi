---
phase: 01
title: "Dashboard Creation Guide — docs/11-guides/create-dashboard.md"
domain: "Documentation — procedural how-to guide for admin dashboard creation workflow"
created: "2026-06-03"
status: planned
depends_on: []
---

# PLAN_01: Dashboard Creation Guide

## Phase Goal

Write a how-to guide at `docs/11-guides/create-dashboard.md` documenting the complete admin workflow for creating a new dashboard — from pre-creation planning through configuration, first upload, access management, and ongoing operations. The guide targets admins who are already familiar with the application UI. It is a narrative, prose-driven guide (not an API reference), cross-linking to existing specs for field-level detail.

## Architecture Decisions (LOCKED — from discuss-phase DECISION_01.md)

1. **File placement**: New file `docs/11-guides/create-dashboard.md`, alongside `docker.md` and `task-queue-migration.md`.
2. **Frontmatter**: YAML with `id: create-dashboard`, `domain: guides`, `tags: [guide, admin, dashboard-creation, workflow, howto]`, `related: [dashboards-api, processing-api, schema-core, data-flow, docker]`.
3. **`## Purpose`** section at the top (after frontmatter).
4. **One-sentence auth**: "You must have the Admin role to create dashboards." No deeper auth explanation.
5. **Chronological workflow order**: Sections map to admin phases: Pre-Creation Planning → Create → Configure Layout → Add Graphs → Add/Bind Filters → Set Up Processing Config → Upload Data → Verify → Grant Access → Ongoing Operations → Troubleshooting → Appendix → Cross-Links.
6. **No screenshots**: Describe UI textually.
7. **Hub-and-spoke model**: Guide narrates workflow in prose; cross-links to `SPEC.md`, `02-dashboards/`, `03-processing/`, `09-database/` for reference details. Never duplicates API field docs.
8. **Layout system**: Brief conceptual overview only (rows/columns/graph slots). Do NOT document `layouts.definition` JSONB.
9. **Processing config examples**: 2–3 annotated JSON examples in a co-located appendix (simple → medium → complexity).
10. **DB/API reference section**: Compact summary table of relevant tables with links to schema docs.
11. **English-only** content throughout.

## Scope Constraints (from DECISION_01.md — OUT OF SCOPE)

- Processing config auto-wiring or column type detection behavior in depth → belongs in `03-processing/`
- Dashboard layout JSON schema (`layouts.definition` JSONB) → internal implementation detail

## Waves

### Wave 1: Guide Writing (foundation — no deps)
- **TASK_001** — Write the first half of the guide: Frontmatter, Purpose, Prerequisites, Pre-Creation Planning, Create Dashboard, Configure Layout, Add Graphs

### Wave 2: Guide Writing Continuation (depends on Wave 1)
- **TASK_002** — Write the second half of the guide: Add/Bind Filters, Set Up Processing Config, Upload Data, Verify Results, Grant Dashboard Access, Ongoing Operations, Troubleshooting, Appendix (3 JSON examples), Cross-Links

### Wave 3: Verification (depends on Waves 1-2)
- **TASK_003** — Validate the complete guide: frontmatter compliance, relative cross-link paths, English-only, line-count threshold, terminology consistency

> **Note**: Waves 1 and 2 are sequential (same file), but each covers distinct sections. A single agent execute-phase should handle both in order without manual intervention.

## Dependency Graph

```
Wave 1:
  TASK_001 (write first half)

Wave 2:
  TASK_001 → TASK_002 (write second half, append to same file)

Wave 3:
  TASK_002 → TASK_003 (verify complete guide)
```

## must_haves (goal-backward validation)

1. File `docs/11-guides/create-dashboard.md` exists.
2. Valid YAML frontmatter with `id`, `domain`, `tags`, `related`.
3. `## Purpose` section at the top.
4. Prerequisites section with one-sentence admin role requirement.
5. All lifecycle sections in chronological order (plan → create → configure → upload → verify → grant access → ongoing → troubleshooting).
6. No screenshots — UI described textually.
7. Hub-and-spoke cross-linking: every section that references an API/schema doc uses a relative cross-link.
8. All cross-links use `../` prefix (relative from `11-guides/`).
9. Layout section is brief conceptual overview — no `layouts.definition` JSONB.
10. Processing config subsection links to `03-processing/processing-api.md` for field-level detail.
11. Appendix has 2–3 annotated JSON examples covering simple → complex.
12. DB/API reference section with summary table of relevant tables.
13. Troubleshooting section with common issues.
14. Cross-Links section at the end.
15. All content in English.
16. Line count below 800 (soft split threshold); if above, split at `##` boundary.

## Cross-Link Targets (all relative from `docs/11-guides/`)

| Target | Relative Path |
|--------|---------------|
| `docs/02-dashboards/dashboards-api.md` | `../02-dashboards/dashboards-api.md` |
| `docs/03-processing/processing-api.md` | `../03-processing/processing-api.md` |
| `docs/09-database/schema-core.md` | `../09-database/schema-core.md` |
| `docs/09-database/schema-processing.md` | `../09-database/schema-processing.md` |
| `docs/09-database/schema-access.md` | `../09-database/schema-access.md` |
| `docs/SPEC.md` | `../SPEC.md` |
| `docs/00-overview/data-flow.md` | `../00-overview/data-flow.md` |
| `docs/09-database/enums.md` | `../09-database/enums.md` |
| `docs/01-auth/auth-api.md` | `../01-auth/auth-api.md` (optional) |
| `docs/11-guides/docker.md` | `docker.md` (same dir) |

## Terminology (must be consistent)

- "graph" (not "chart")
- "dimension" / "metrics" (not "fields" or "columns")
- "permission" with levels `view` / `edit` / `admin` (`DashboardPermission` StrEnum)
- "filter" with types `select` / `multiselect` / `range` / `date` (`FilterType` StrEnum)
- "processing config" (not "data config" or "loader settings")
- "upload" (not "data source" or "import")
- "aggregated data" (not "raw data" or "row data")
