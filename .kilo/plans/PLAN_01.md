---
wave: 1
depends_on: []
files_modified:
  - docs/11-guides/extend-graphs-filters.md
autonomous: true
---

# Plan 01: Adding New Graphs & Filters Guide

## Goal

Create a how-to guide at `docs/11-guides/extend-graphs-filters.md` that documents the workflow for adding new graph types and extending filter capabilities in the mkobi BI Dashboard System.

## Context

**Phase 01** — Developer documentation / extensibility guide for charts and filters.

All structural decisions are locked by the phase context (decisions block). The guide follows the hub-and-spoke model: narrate the extension workflow, cross-link to existing specs, never duplicate API field docs.

**Reference template:** `docs/11-guides/create-dashboard.md` — same frontmatter structure, Purpose-first, Prerequisites, step-by-step sections, Appendix with annotated code examples, DB/API Reference table, Cross-Links.

## Tasks

### Task 1: Write the extend-graphs-filters guide

**File:** `docs/11-guides/extend-graphs-filters.md`

Single documentation file. Must comply with `docs/00-overview/doc-maintenance-rules.md`:

1. **YAML frontmatter** — `id: extend-graphs-filters`, `domain: guides`, `tags` (guide, graphs, filters, extensibility, charts), `related` (dashboards-api, processing-api, schema-core, data-flow)
2. **`## Purpose` section** — English-only, summarizes what the guide covers
3. **Prerequisites section** — Cross-link to SPEC.md and dashboards-api
4. **Conceptual Overview** — End-to-end pipeline: StrEnum → DB ENUM → JSONB config → API response → frontend rendering
5. **Graph Extension Section** — Step-by-step: add to `GraphType` StrEnum → create Plotly component → wire in `ChartRenderer` → admin UI forms
6. **Filter Extension Section** — Step-by-step: add to `FilterType` StrEnum → add `FilterField` case → admin UI forms
7. **Data Pipeline Implications** — When aggregation changes are needed (scatter, heatmap) vs. when they aren't (new filter pickers)
8. **Quick Reference Table** — Graph type → backend enum → frontend component → Plotly trace type
9. **Appendix** — 2 annotated code examples:
   - **Simple:** Adding a "scatter" graph type (backend StrEnum + DB migration + frontend component)
   - **Medium:** Adding a "heatmap" graph type (requires aggregation changes)
   - **Complex:** Adding a "search" filter type (new `FilterField` case + MUI TextField with autocomplete)
10. **Cross-Links section** — dashboards-api, processing-api, schema-core, data-flow

**Doc maintenance compliance checklist:**
- [ ] YAML frontmatter with `id`, `domain`, `tags`, `related`
- [ ] `## Purpose` section at the top
- [ ] All content in English
- [ ] Cross-links use relative paths (`../02-dashboards/dashboards-api.md`)
- [ ] Under 800 lines (soft threshold)
- [ ] Hub-and-spoke model: reference existing specs, don't duplicate field docs

## Verification

**Inline (single-task):** Guide file passes doc-rules checklist above. Verify all cross-link targets exist. Verify frontmatter fields are present. Verify line count stays under 800.

No separate verification task is created — this is a single-file, low-risk documentation task with inline verification.

## must_haves

- Guide exists at `docs/11-guides/extend-graphs-filters.md`
- Valid YAML frontmatter (id, domain, tags, related)
- `## Purpose` section present
- Graph extension section covers all 4 steps (StrEnum → component → wiring → Admin UI)
- Filter extension section covers all 4 steps (StrEnum → FilterField case → wiring → Admin UI)
- Data pipeline implications section distinguishes between graph types that need aggregation changes and those that don't
- Quick reference table present (graph type → backend enum → frontend component → Plotly trace type)
- Appendix contains exactly 2–3 annotated code examples covering simple → complex spectrum
- All cross-links use relative paths and point to existing files
- Under 800 lines
- No duplicated API field documentation from cross-linked specs
