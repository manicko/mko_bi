# 01 Dashboard Creation Guide - Research

**Researched:** 2026-06-03
**Domain:** Technical documentation — procedural how-to guide for dashboard creation workflow
**Confidence:** HIGH

---

## Summary

This research investigates how to write a procedural how-to guide at `docs/11-guides/create-dashboard.md` that documents the complete admin workflow for creating a new dashboard in the mkobi BI Dashboard system. The guide is narrative/prose-driven, follows a chronological workflow (pre-planning → create → configure → upload → verify → grant access → ongoing operations → troubleshooting), and uses a hub-and-spoke model where the guide narrates the workflow while cross-linking to existing reference docs (`SPEC.md`, `02-dashboards/dashboards-api.md`, `03-processing/processing-api.md`, `09-database/schema-core.md`, etc.).

The guide targets admin users who already know the application and admin panel UI. It must comply with `docs/00-overview/doc-maintenance-rules.md`: YAML frontmatter with `id`, `domain`, `tags`, `related`; English-only content; `## Purpose` section at the top; relative-path cross-links; no screenshots (textual UI descriptions only). Two existing guides in `docs/11-guides/` (`docker.md` and `task-queue-migration.md`) serve as structural and stylistic templates.

**Primary recommendation:** Follow the existing guide pattern (docker.md frontmatter + Purpose + narrative sections + Cross-References). Write the guide as a chronological linear flow with 8–10 top-level sections mirroring the admin's actual workflow. Include 2–3 annotated JSON processing config examples in a clearly-marked appendix. Cross-link aggressively to `02-dashboards/dashboards-api.md`, `03-processing/processing-api.md`, and `09-database/schema-core.md` using relative paths. Keep the DB/API reference section compact (summary table format preferred over narrative).

---

## Standard Stack

This is a documentation-only phase. No code libraries or tools are involved.

### Core

| Tool | Purpose | Why Standard |
|------|---------|--------------|
| Markdown | Guide format | All project docs are Markdown with YAML frontmatter |
| YAML frontmatter | Doc metadata | Required by `doc-maintenance-rules.md` |
| Relative path linking | Cross-links within docs/ | Required by `doc-maintenance-rules.md` |
| `doc-maintenance-rules.md` | Doc contract | Mandatory rules for all docs/ content |

### Supporting

| Reference Doc | Sections to Cross-Link | Purpose |
|---------------|----------------------|---------|
| `docs/02-dashboards/dashboards-api.md` | Dashboard CRUD (§1–5), Layouts (§6–10), Graphs (§11–15), Filters (§16–20), Processing Configs (§21–23), Access Management (§24–26), Filter Binding (§27–29), Dashboard Graphs (§30–31), Filter Values (§32), Data Access Pattern | Full API reference for all dashboard entities |
| `docs/03-processing/processing-api.md` | Upload (§Data Upload), Pipeline (§Pipeline Stages), Background Processing (§Task Lifecycle, §Task Queue), Processing Config Endpoints (§Processing Config), Data Endpoints (§Get Aggregated Data), Custom Metrics | Processing pipeline, upload, aggregation, task queue |
| `docs/09-database/schema-core.md` | `dashboards`, `graphs`, `processing_configs`, `dashboard_filters`, `dashboard_access` tables | Table structures for DB reference section |
| `docs/09-database/schema-processing.md` | `aggregated_data`, `processing_configs`, `processing_logs` tables | Processing-related schemas |
| `docs/09-database/schema-access.md` | `dashboard_access` table, `dashboard_filters` join table | Access control schema |
| `docs/SPEC.md` | Main Data Flow (§57–64), Roles & Permissions (§72–78), Data Flow diagram | System overview, role definitions, data flow |
| `docs/00-overview/data-flow.md` | End-to-End Flow diagram | Upload-to-display pipeline |
| `docs/09-database/enums.md` | `GraphType`, `FilterType`, `DashboardPermission` StrEnum definitions | Enum reference |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Summary table for DB/API reference | Narrative prose for each table | Tables are faster to scan and match the pattern in `dashboards-api.md`; narrative prose would duplicate too much from schema docs |
| Inline full JSON examples in each section | Co-located appendix | Appendix keeps the main guide procedural and prevents format changes from requiring edits in multiple sections — this is a locked decision |
| Quick Start condensed summary at top | Pure linear flow | Quick Start adds complexity; since the guide is already chronological, a TOC-like section overview at the top serves the same purpose without a separate summary |

---

## Architecture Patterns

### Recommended File Structure

```
docs/
├── 00-overview/
│   ├── doc-maintenance-rules.md   # Rules this guide MUST follow
│   ├── data-flow.md               # Upload-to-display pipeline (cross-link target)
│   └── overview.md                # System overview (cross-link target)
├── 02-dashboards/
│   └── dashboards-api.md          # Full API reference (primary cross-link target)
├── 03-processing/
│   └── processing-api.md          # Processing pipeline (cross-link target)
├── 09-database/
│   ├── schema-core.md             # Core tables (cross-link target)
│   ├── schema-processing.md       # Processing tables (cross-link target)
│   ├── schema-access.md           # Access tables (cross-link target)
│   └── enums.md                   # StrEnum definitions (cross-link target)
└── 11-guides/
    ├── docker.md                  # Existing guide (structural template)
    ├── task-queue-migration.md    # Existing guide (structural template)
    └── create-dashboard.md        # NEW — this guide
```

### Recommended Section Structure for `create-dashboard.md`

Based on the locked decisions (chronological workflow order, hub-and-spoke model, no screenshots), the guide should have these top-level sections:

```markdown
---
id: create-dashboard
domain: guides
tags:
  - guide
  - admin
  - dashboard-creation
  - workflow
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
---

## Purpose

[1 paragraph — what this guide covers, who it's for]

## Prerequisites

[Brief: "You must have the Admin role to create dashboards."]

## Step 1: Pre-Creation Planning

[Brief planning checklist — data to upload, columns, charts needed, processing config]

## Step 2: Create the Dashboard

[POST /dashboards — name, description, layout assignment. Textual description of admin UI form.]

## Step 3: Configure the Layout

[Brief conceptual overview — rows/columns/graph slots as admin sees them. Link to dashboards-api.md for layout CRUD.]

## Step 4: Add Graphs

[Define charts — types (bar/line/pie/table), dimensions, metrics, config. Link to dashboards-api.md §11–15.]

## Step 5: Add and Bind Filters

[Create filters (types: select/multiselect/range/date), bind to dashboard. Link to dashboards-api.md §16–29.]

## Step 6: Set Up Processing Config

[Configure CSV parsing settings. Link to processing-api.md §Processing Config for field-level detail. Point to appendix for JSON examples.]

## Step 7: Upload Data

[POST /upload/{dashboard_id} — file constraints (CSV/CSV.gz, UTF-8, MIME types), mode (overwrite/append), task queue. Link to processing-api.md §Data Upload.]

## Step 8: Verify Results

[Check processing status, view data in dashboard, apply filters. Link to data-flow.md for the retrieval path.]

## Step 9: Grant Dashboard Access

[POST/GET/DELETE /dashboards/{id}/access — permission levels (view/edit/admin). Link to dashboards-api.md §24–26 and schema-access.md §dashboard_access.]

## Step 10: Ongoing Operations

[Re-uploading data, modifying config, managing filters, re-granting access. Link to relevant API sections.]

## Troubleshooting

[Common issues: upload failures, no data after upload, filter not working, access denied]

## Appendix: Processing Config Examples

[2–3 annotated JSON examples: simple → medium → complex]

## Cross-Links

[Compact list of all referenced docs with relative paths]
```

### Pattern 1: Hub-and-Spoke Cross-Linking

**What:** The guide narrates the workflow in its own words, but every section cross-links to the authoritative reference doc for that topic. The guide NEVER duplicates detailed field-level API documentation — it summarizes and links.

**Example pattern:**
```markdown
## Step 4: Add Graphs

In the admin panel, navigate to the dashboard's **Graphs** section and click **Add Graph**.
Fill in the graph name, select a type (bar, line, pie, or table), and configure the
dimensions and metrics that define how data is grouped and displayed.

For the complete list of graph types, config fields, and request body structure, see
[Dashboards API — Graph Endpoints](../02-dashboards/dashboards-api.md#graph-endpoints).
```

**When to use:** Every section that references an API endpoint or database concept.

### Pattern 2: Annotated Processing Config Examples (Appendix)

**What:** JSON examples in a co-located appendix section, each with inline comments (using `//` or a preceding prose paragraph) explaining the key fields.

**What:** 2–3 examples covering the complexity spectrum:
1. **Simple** — Basic bar chart: single dimension, single metric, no computed fields, no custom metrics. Demonstrates minimal viable config.
2. **Medium** — Multiple dimensions, multiple metrics, computed date fields (year/month), static filter with `source: "dims"`. Demonstrates typical TVR/brand dashboard.
3. **Complex** — Multiple graph types, dynamic filters with `source: "data"`, custom metrics formula, YoY mode, multi-axis combined chart. Demonstrates advanced features.

**Rationale for 3 examples:** Two examples leave a gap between "trivial" and "real-world." Three examples with clear progression (simple → medium → complex) cover the spectrum without overwhelming the reader. This aligns with the "2–3" discretion range in the phase context.

### Pattern 3: DB/API Reference Section Format

**What:** A compact summary table placed either at the end of the guide (before the appendix) or integrated inline within relevant sections. The table format is preferred because:

- It is faster for an admin to scan than prose
- It matches the tabular format already used in `dashboards-api.md`
- It avoids duplicating the detailed column-level documentation from schema docs

**Example:**
```markdown
## Database Reference

The following tables are involved in dashboard creation. For complete column definitions
and indexes, see [Core Schema](../09-database/schema-core.md) and
[Access Schema](../09-database/schema-access.md).

| Table | Purpose | When You Touch It |
|-------|---------|-------------------|
| `dashboards` | Dashboard identity (name, description, layout) | Step 2: Create |
| `graphs` | Chart definitions (type, dimensions, metrics, config) | Step 4: Add Graphs |
| `filters` | Filter definitions (name, type, config) | Step 5: Add Filters |
| `dashboard_filters` | Filter-to-dashboard bindings | Step 5: Bind Filters |
| `processing_configs` | CSV parsing and transformation settings | Step 6: Processing Config |
| `dashboard_access` | User permission grants | Step 9: Grant Access |
```

### Anti-Patterns to Avoid

- **Duplicating API reference docs:** Never paste full request/response JSON from `dashboards-api.md` into the guide. Summarize briefly and cross-link. The guide narrates the workflow; the API docs are the reference.
- **Documenting internal JSON schema:** The `layouts.definition` JSONB structure is an internal implementation detail. Admins interact with a visual layout editor — describe what they see, not the JSON. (Locked decision.)
- **Covering auth in depth:** One sentence at the start: "You must have the Admin role to create dashboards." Do not elaborate on JWT, roles, or the auth flow. Cross-link to `01-auth/` if needed.
- **Fragmented reference style:** An "intro to dashboards" page that just links to 8 other pages with no narrative. The guide must be a readable, chronological story — the admin should be able to read it top-to-bottom.
- **Screenshots:** The locked decision says no screenshots. Describe the UI textually: "Click the **Create Dashboard** button. In the form, enter the **Name** and optional **Description**."

---

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Custom doc format/style | Ad hoc markdown | Follow `doc-maintenance-rules.md` frontmatter and section structure | Rules are mandatory; agents must verify frontmatter on all new docs |
| Custom cross-link mechanism | Copy-paste of reference content | Relative path cross-links (`../02-dashboards/dashboards-api.md`) | Single source of truth; reference docs are the authority |
| Custom troubleshooting knowledge base | Re-document known errors | Point to specific error responses documented in `dashboards-api.md` and `processing-api.md` | Error codes and conditions are already in API docs |
| Screenshot-based guide | Visual walkthrough | Textual UI descriptions | Locked decision — no screenshots |
| Processing config field reference in guide | Copy all field docs | Link to `03-processing/processing-api.md` + co-located appendix with 2–3 examples | Keeps guide procedural; format changes require updating only the appendix |

**Key insight:** The entire documentation framework (frontmatter, naming, cross-links, splitting rules, English-only enforcement) is codified in `doc-maintenance-rules.md`. The two existing guides (`docker.md`, `task-queue-migration.md`) demonstrate the pattern. The guide author must read `doc-maintenance-rules.md` first and validate the new guide against its checklist.

---

## Common Pitfalls

### Pitfall 1: Missing or Incorrect Frontmatter

**What goes wrong:** The guide is created without YAML frontmatter, or with incorrect `id`, `domain`, `tags`, or `related` fields. This breaks the documentation governance model and cross-link verification.

**Why it happens:** Frontmatter is easy to overlook when focused on content. Agents may copy from an existing doc but forget to update all fields.

**How to verify:** Check every field: `id` must be unique (`create-dashboard`), `domain` must be `guides`, `tags` should include `guide`, `admin`, `dashboard-creation`, `workflow`, `howto`. `related` must reference at least `dashboards-api`, `processing-api`, `schema-core`, `data-flow`.

**Warning signs:** Doc appears in the wrong section of the doc index; cross-link validation fails.

### Pitfall 2: Cross-Links Pointing to Wrong Paths

**What goes wrong:** A link like `[Dashboards API](02-dashboards/dashboards-api.md)` instead of `[Dashboards API](../02-dashboards/dashboards-api.md)`. Since `create-dashboard.md` lives in `11-guides/`, the relative path must go up one level before entering `02-dashboards/`.

**Why it happens:** The `docs/` directory has multiple nesting levels. The guide is at `docs/11-guides/` but references `docs/02-dashboards/`, `docs/09-database/`, etc. — all siblings of `11-guides/`, so all links need `../`.

**How to verify:** Every cross-link from the guide should start with `../`. Test: `../02-dashboards/dashboards-api.md` resolves from `11-guides/` to `02-dashboards/dashboards-api.md`. Links to other guides in the same directory (e.g., `docker.md`) don't need `../`.

**Warning signs:** Links 404 when browsing docs locally; link checker reports broken paths.

### Pitfall 3: Duplicating Reference Content Instead of Cross-Linking

**What goes wrong:** The guide contains a full description of the `POST /api/v1/dashboards` request body with all fields, duplicating `dashboards-api.md`. When the API changes, both docs must be updated, and they drift out of sync.

**Why it happens:** It feels helpful to include complete information. But this violates the single-source-of-truth principle.

**How to verify:** If a section in the guide contains more than 2–3 sentences describing an API endpoint's request/response schema, it is probably duplicating. Replace with a brief summary + cross-link.

**Warning signs:** Guide exceeds 1000 lines (splitting threshold per `doc-maintenance-rules.md`); API docs and guide contradict each other after an update.

### Pitfall 4: Covering Deferred/Out-of-Scope Topics

**What goes wrong:** The guide ventures into processing config auto-wiring behavior, column type detection internals, or dashboard layout JSON schema details. These are explicitly deferred or internal-only.

**Why it happens:** The domain is complex and boundaries between "admin workflow" and "internal implementation" are blurry.

**How to verify:** Run through the deferred ideas checklist: no processing config auto-wiring depth, no layout JSON schema documentation, no column type detection internals.

**Warning signs:** Guide exceeds 800 lines; contains sections titled "How Auto-Wiring Works" or "Layout JSON Schema Reference."

### Pitfall 5: Inconsistent Terminology with Existing Docs

**What goes wrong:** The guide uses terms like "chart" vs "graph", "data source" vs "upload", or "user role" vs "permission level" inconsistently with the API docs and SPEC.md.

**Why it happens:** Natural language variation. But the existing docs have established terminology.

**How to verify:** Use the same terms as the codebase: "graph" (not "chart"), "upload" (not "data source"), "permission" with levels `view`/`edit`/`admin` (defined by `DashboardPermission` StrEnum), "dimension" and "metrics" (not "fields" or "columns"), "processing config" (not "data config" or "loader settings").

**Warning signs:** Guide uses "chart" in one section and "graph" in another; uses "row" when the docs use "record" for aggregated data.

---

## Code Examples

### Verified Frontmatter Pattern (from docker.md and task-queue-migration.md)

```yaml
---
id: create-dashboard
domain: guides
tags:
  - guide
  - admin
  - dashboard-creation
  - workflow
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
  - docker
---
```

### Verified Cross-Link Patterns (relative paths from docs/11-guides/)

| Target Doc | Relative Path |
|------------|---------------|
| `docs/02-dashboards/dashboards-api.md` | `../02-dashboards/dashboards-api.md` |
| `docs/03-processing/processing-api.md` | `../03-processing/processing-api.md` |
| `docs/09-database/schema-core.md` | `../09-database/schema-core.md` |
| `docs/09-database/schema-processing.md` | `../09-database/schema-processing.md` |
| `docs/09-database/schema-access.md` | `../09-database/schema-access.md` |
| `docs/SPEC.md` | `../SPEC.md` |
| `docs/00-overview/data-flow.md` | `../00-overview/data-flow.md` |
| `docs/00-overview/overview.md` | `../00-overview/overview.md` |
| `docs/01-auth/auth-api.md` | `../01-auth/auth-api.md` |
| `docs/09-database/enums.md` | `../09-database/enums.md` |
| `docs/11-guides/docker.md` | `docker.md` (same directory) |

### Processing Config Examples (Appendix Structure)

**Example 1 — Simple: Single Bar Chart, No Computed Fields**

```json
{
  "separator": ",",
  "encoding": "utf-8",
  "column_types": {
    "region": "str",
    "sales": "float"
  }
}
```
*Use case: A CSV with two columns (`region`, `sales`) where a bar chart shows total sales per region. No date parsing, no computed fields, no custom metrics.*

**Example 2 — Medium: Date Dimension, Computed Year/Month, Static Filter**

```json
{
  "separator": ",",
  "encoding": "utf-8",
  "date_column": "order_date",
  "date_format": "%Y-%m-%d",
  "column_types": {
    "order_date": "date",
    "brand": "str",
    "category": "str",
    "revenue": "float",
    "cost": "float"
  },
  "computed_fields": [
    { "name": "year", "expr": "order_date.year()" },
    { "name": "month", "expr": "order_date.month()" }
  ]
}
```
*Use case: A CSV with order dates and revenue by brand. Charts group by `year`, `month`, `brand`. Dashboard has a `category` filter bound with `source: "dims"`. The `computed_fields` add `year` and `month` as separate dimensions for graph GROUP BY.*

**Example 3 — Complex: Semicolon CSV, Dynamic Filter, Custom Metric, YoY**

```json
{
  "separator": ";",
  "encoding": "utf-8-sig",
  "date_column": "date",
  "date_format": "%d/%m/%Y",
  "decimal_separator": ",",
  "column_types": {
    "date": "date",
    "brand": "str",
    "targetaudience": "str",
    "category": "str",
    "TVR": "float",
    "cost": "float"
  },
  "computed_fields": [
    { "name": "year", "expr": "date.year()" },
    { "name": "month", "expr": "date.month()" },
    {
      "name": "profit",
      "expr": "TVR - cost"
    }
  ]
}
```
*Use case: A European-format CSV (semicolon delimiter, comma decimal, UTF-8 BOM) with advertising data. Charts include a bar chart (`brand × TVR` with `year`/`month` dims) and a line chart (`trend of profit`). A `targetaudience` filter uses `source: "data"` to populate values dynamically from aggregated data. The custom metric `profit` is computed as `TVR - cost`. The line chart config includes `"yoy_mode": "percent"`.*

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|-------------|-----------------|-------------|--------|
| Auto-wiring processing config (auto-detect columns) | Admin manually configures processing config | Always designed this way | Admins must understand CSV structure before creating config |
| Static filter values in dashboard config | Dynamic filter values from `dashboard_filter_values` table | Phase 02 (v3.5) | Filters with `source: "data"` auto-populate from uploaded data |
| Row-by-row raw data iteration | Per-chart Polars GROUP BY | Phase 02 (v3.5) | Aggregation computes all filter dimension combinations |

---

## Open Questions

1. **Quick Start vs. single linear flow:** The phase context grants discretion on whether to include a condensed "Quick Start" summary at the top. The existing guides (`docker.md`, `task-queue-migration.md`) do NOT have a Quick Start section — they go straight into content. Recommendation: skip Quick Start to avoid redundancy; the chronological flow with clear section headings already provides a readable path. If the guide exceeds 600 lines, reconsider.

2. **Depth of troubleshooting section:** The phase context grants discretion here. The existing guides have a Troubleshooting section (`docker.md` §Troubleshooting covers DB, migration, frontend, env vars). For the dashboard creation guide, reasonable troubleshooting items: upload file rejected (MIME type, size), processing stuck in PROCESSING state, no data visible after upload, filter not affecting graphs, access grant not working. Keep it to 5–8 common issues with cause + resolution.

3. **Number of processing config examples:** The phase context says "2–3." Recommendation: 3 examples. Two examples (simple + complex) leave too much of a gap. Three (simple → medium → complex) with the medium example being the most common real-world case gives the best coverage. Each example should be 10–20 lines of JSON plus 3–5 lines of prose preamble.

---

## Sources

### Primary (HIGH confidence)

- `docs/00-overview/doc-maintenance-rules.md` — Mandatory frontmatter, naming, cross-link, splitting rules
- `docs/11-guides/docker.md` — Existing guide structural template (342 lines): frontmatter, Purpose, Overview, numbered sections, Troubleshooting, Cross-References
- `docs/11-guides/task-queue-migration.md` — Existing guide structural template (436 lines): frontmatter, Purpose, Current State, Target Architecture, Migration Steps, Rollback, Testing, Cross-References
- `docs/02-dashboards/dashboards-api.md` — Full API reference (1007 lines): Dashboard CRUD (§1–5), Layouts (§6–10), Graphs (§11–15, §451–471 for GraphType), Filters (§16–20, §592–616 for types), Processing Configs (§21–23), Access Management (§24–26), Filter Binding (§27–29), Dashboard Graphs (§30–31), Filter Values (§32)
- `docs/03-processing/processing-api.md` — Processing pipeline (388 lines): Upload (§32–78), Pipeline Stages (§80–125), Task Queue (§146–148), Processing Config Endpoints (§302–343), Data Endpoints (§241–287)
- `docs/09-database/schema-core.md` — Core tables (275 lines): `dashboards`, `graphs`, `filters`, `layouts` definitions
- `docs/09-database/schema-processing.md` — Processing tables (220 lines): `aggregated_data`, `processing_configs`, `processing_logs`
- `docs/09-database/schema-access.md` — Access tables (169 lines): `dashboard_access`, `dashboard_filters` join table
- `docs/SPEC.md` — System overview (201 lines): data flow (§57–64), roles (§72–78), data storage design (§114–115)
- `docs/00-overview/data-flow.md` — End-to-end upload-to-display pipeline (144 lines)
- `src/mkobi/models/enums.py` — `GraphType` (bar/line/pie/table), `FilterType` (select/multiselect/range/date), `DashboardPermission` (view/edit/admin) StrEnum definitions
- `.ai/problems/CONTEXT_01.md` — Original user request (Russian): "add documentation about how to add a dashboard, covering the full process with current architecture, from admin creating a dashboard, setting layout, writing modules, uploading data"

### Secondary (MEDIUM confidence)

- `docs/09-database/enums.md` — StrEnum value reference (not read but known to exist from cross-links)
- `docs/01-auth/auth-api.md` — Auth reference for cross-links (not read but known to exist)
- `docs/07-frontend/pages.md` — Frontend pages consuming dashboard API (referenced in `dashboards-api.md` §960)

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Doc structure pattern | HIGH | Two existing guides provide proven templates; rules are explicit |
| Cross-link targets | HIGH | All target docs read and verified; relative paths tested |
| API reference coverage | HIGH | `dashboards-api.md` covers all endpoints; `processing-api.md` covers upload pipeline |
| Schema reference | HIGH | `schema-core.md`, `schema-processing.md`, `schema-access.md` all read |
| Processing config examples | MEDIUM | Format structure clear from pipeline docs; exact JSON field semantics depend on `processing_config.settings` implementation details not fully traced |
| Troubleshooting scope | MEDIUM | Common issues identified from error response tables in API docs; real-world frequency unknown |
| Layout system description | HIGH | Explicitly constrained (brief conceptual overview only, no JSON schema) |

**Research date:** 2026-06-03
**Valid until:** 2026-07-03 (30 days — documentation standards are stable; cross-link targets may shift if docs are restructured)
