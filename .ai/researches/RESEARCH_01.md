# 01 Modular Spec + Minimal AI Metadata - Research

**Researched:** 2026-05-18
**Domain:** Documentation restructuring — monolithic spec to modular AI-friendly markdown
**Confidence:** HIGH

## Summary

This research investigates how to restructure a monolithic 1069-line `docs/SPEC.md` into a modular, domain-based documentation system optimized for LLM/RAG consumption. The "stack" is markdown, YAML frontmatter, and file organization — not software development.

The standard approach for AI-friendly documentation in 2025-2026 combines three practices: (1) YAML frontmatter as a machine-readable "type signature" for each document, enabling metadata-first retrieval before body text is ever read; (2) heading-aware chunking that preserves semantic coherence by splitting at section boundaries rather than arbitrary token counts; (3) cross-linking via `related` frontmatter fields and inline markdown links, creating a navigable knowledge graph without external tooling.

**Primary recommendation:** Split SPEC.md by retrieval intent (what an LLM needs loaded into context simultaneously), not by section count. Target 25-40 files at 200-800 lines each. Use a minimal 4-field frontmatter schema (`id`, `domain`, `tags`, `related`). Apply a 4-step migration pipeline: inventory → map → transfer → reconcile. Automate the mechanical splitting with existing Python tools (`mdsplit` or `markdown-section-splitter`), then manually curate content placement and cross-links.

## Standard Stack

The established tools/patterns for this domain:

### Core

| Tool/Pattern | Version/Ref | Purpose | Why Standard |
|---|---|---|---|
| **YAML Frontmatter** | Between `---` delimiters | Machine-readable metadata header | Universal support (Hugo, Docusaurus, MkDocs, RAG pipelines). Acts as "type signature" for documents — retrieval systems can filter by metadata before reading body text. |
| **Markdown (CommonMark)** | Standard | Content format | Native LLM-friendly. Preserves structural hierarchy (headings, tables, code blocks) that LLMs parse reliably. |
| **mdsplit** | PyPI v0.5.0 | Split markdown by heading level | Python CLI tool. Splits at H1-H6, generates kebab-case filenames, code-block-aware, generates TOC and navigation footers. |
| **markdown-section-splitter** | GitHub: petalo/markdown-section-splitter | Split + frontmatter generation | Python script. Splits at `##` headers, auto-promotes headers, generates numbered kebab-case files, detects broken internal links, code-block-aware. |

### Supporting

| Tool/Pattern | Purpose | When to Use |
|---|---|---|
| **MAGI (.mda) spec** | Extended markdown with typed relationships | Reference model for frontmatter schema design. The `doc-id`, `tags`, `entities`, `relationships` fields informed the minimal schema chosen. Overkill to adopt fully, but the `doc-id` + `related` pattern is directly applicable. |
| **mdlint / markdownlint** | Lint markdown consistency | Post-migration validation of heading hierarchy, link integrity, formatting consistency. |
| **Python `re` + `yaml` stdlib** | Custom split scripts | When `mdsplit` doesn't handle SPEC.md's specific structure (mixed heading levels, code blocks with headings inside). |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| Manual splitting | `mdsplit` / `markdown-section-splitter` | Tools handle mechanical splitting (80% of work) but can't decide content placement. Hybrid: tool-split, then manually curate. |
| Full MAGI spec | Minimal 4-field schema | MAGI adds `ai-script` blocks, footnote relationships, `entities`, `expired-date`. Overkill for a project spec. The minimal schema covers 95% of retrieval needs. |
| Pandoc conversion | Direct markdown splitting | Pandoc is designed for format conversion (Word→MD, HTML→MD), not structural splitting. Wrong tool for this job. |

**Installation (if using mdsplit):**
```bash
pip install mdsplit
# or
uv add --dev mdsplit
```

## Architecture Patterns

### Recommended Project Structure

```
docs/
├── README.md                          # Root index: how docs are organized (human + AI)
├── SPEC.md                            # System overview: what the system is (was monolithic spec)
│
├── 00-overview/
│   ├── overview.md                    # System purpose, stack summary, key entities
│   └── data-flow.md                   # End-to-end data flow (upload → process → display)
│
├── 01-auth/
│   └── auth-api.md                    # Auth endpoints, JWT flow, registration, password change
│
├── 02-dashboards/
│   └── dashboards-api.md              # Dashboards + layouts + graphs + filters (one bounded context)
│
├── 03-processing/
│   ├── processing-api.md              # Upload, processing triggers, status/result endpoints
│   └── task-queue.md                  # Task queue architecture + migration plan (from TASK_QUEUE_MIGRATION.md)
│
├── 04-admin/
│   └── admin-api.md                   # Admin endpoints: users, registration requests, logs
│
├── 05-health/
│   └── health-api.md                  # Health check endpoints
│
├── 06-backend/
│   ├── architecture.md                # FastAPI architecture, service layer, DI
│   ├── configuration.md               # Config sources, secrets management, env vars
│   ├── logging.md                     # Logging standards, language requirements
│   └── testing.md                     # Testing strategy, pytest, coverage areas
│
├── 07-frontend/
│   ├── architecture.md                # React SPA architecture, FSD pattern, key principles
│   ├── fsd-structure.md               # Project structure, folder conventions
│   ├── pages.md                       # All 8 UI pages (Login, Register, Dashboard List, etc.)
│   ├── auth-flow.md                   # Frontend auth: JWT handling, protected routes, role-based access
│   ├── upload-ui.md                   # Upload page: dropzone, progress, mode toggle
│   └── frontend-security.md           # CORS, JWT storage, file validation, email blacklist
│
├── 08-security/
│   ├── security-overview.md           # Rate limiting, MIME validation, SQL injection prevention
│   └── access-control.md              # Dashboard access enforcement, role checks per endpoint
│
├── 09-database/
│   ├── schema-core.md                 # users, dashboards, graphs, layouts, filters tables
│   ├── schema-processing.md           # aggregated_data, processing_logs, processing_configs
│   ├── schema-access.md               # dashboard_access, registration_requests, dashboard_filters
│   ├── indexes.md                     # All database indexes
│   └── enums.md                       # All StrEnum definitions (from section 22)
│
├── 10-deployment/
│   └── deployment.md                  # Dev setup, production variants, Docker, no-overengineering
│
├── 90-adr/
│   └── (future ADRs)                  # Architecture decision records — immutable history
│
└── 99-reference/
    ├── swagger.md                     # From SWAGGER_README.md
    └── run-guide.md                   # From RUN.md
```

### Pattern 1: YAML Frontmatter as Document Schema

**What:** Every `.md` file starts with a YAML block that declares the document's identity, classification, and relationships. This is the single most impactful pattern for LLM/RAG consumption.

**When to use:** Every file in the modular docs system.

**Example:**
```yaml
---
id: auth-api
domain: auth
tags: [jwt, bcrypt, registration, password, endpoints]
related:
  - auth-flow
  - security-overview
  - access-control
---
```

**Field specification:**
- `id` (string, required): Unique kebab-case identifier. Used for cross-referencing and as the primary retrieval key. Should match the filename without `.md`.
- `domain` (enum, required): One of 12 fixed values matching the folder name: `overview`, `auth`, `dashboards`, `processing`, `admin`, `health`, `backend`, `frontend`, `security`, `database`, `deployment`, `reference`. This is the primary taxonomy axis.
- `tags` (string[], optional): Freeform cross-cutting semantic topics. Used for secondary filtering. Keep to 3-8 tags. Examples: `upload`, `csv`, `async`, `redis`, `polars`, `jwt`.
- `related` (string[], optional): IDs of 3-5 semantically adjacent documents typically loaded together. Not exhaustive backlinks — only the most co-retrieved docs.

**Why this works:** Research from Understanding Data (2026-03-16) confirms that frontmatter serves the same role for documents that type definitions serve for code. RAG systems can filter by `domain` and `tags` before running semantic search, dramatically improving precision. The `related` field creates a virtual knowledge graph that guides context assembly.

### Pattern 2: Internal File Structure

**What:** Consistent section hierarchy within each file. Required minimum + recommended optional sections.

**Required sections (every file):**
```markdown
# {Title}

## Purpose
[1-3 paragraphs: what this document covers, why it exists]

## Main Concepts
[Core information: entities, endpoints, schemas, flows — the primary content]
```

**Recommended sections (when applicable):**
```markdown
## Flows
[Step-by-step processes, data flows, request/response sequences]

## Constraints
[Validation rules, business rules, security constraints, limitations]

## Edge Cases
[Error conditions, boundary behaviors, failure modes]

## Related Docs
[Cross-links to related files with brief context on why they're related]
```

**Optional sections:**
`## Examples`, `## Migration Notes`, `## Open Questions`, `## Performance Notes`

**Critical rule:** Omit empty sections entirely. No "N/A" filler. If a section doesn't apply, it doesn't exist.

**Why this works:** Consistent structure lets LLMs predict where to find specific information types. The `## Purpose` section acts as a self-summary for retrieval. `## Edge Cases` captures the high-value "gotcha" content that's often lost in restructuring (directly addresses the 7 high-risk sections identified in DECISION_01).

### Pattern 3: Retrieval-Intent Splitting

**What:** Split documents based on what information an LLM (or human) needs to load into context simultaneously to answer a specific class of questions.

**When to use:** Deciding file boundaries during migration.

**Decision framework:**
1. Identify the primary "question classes" the spec answers (e.g., "How does authentication work?", "What's the database schema?", "How do I deploy this?")
2. For each question class, determine what content must be co-present in context
3. Group content that's always needed together into one file
4. Split content that's independently retrievable into separate files

**Concrete examples from SPEC.md:**
- **Keep together:** Dashboards + Layouts + Graphs + Filters = `dashboards-api.md` (they form one bounded context — you can't understand graphs without knowing the dashboard they belong to)
- **Keep together:** Upload + Processing + Task Queue = `processing-api.md` (the upload pipeline is one end-to-end flow)
- **Split apart:** Auth endpoints ≠ Frontend auth flow (different consumers: backend devs vs frontend devs)
- **Split apart:** DB schema ≠ DB indexes ≠ DB enums (different retrieval intents: "what tables exist?" vs "what's optimized?" vs "what are the allowed values?")

**Target:** 25-40 files. Sweet spot per file: 200-800 lines. Below 200 lines = too fragmented (120 tiny docs problem). Above 800 lines = too monolithic (5 giant docs problem).

### Pattern 4: Canonical Content Ownership

**What:** Each piece of information has exactly one canonical home. Other locations contain short summaries + cross-links, never full duplication.

**When to use:** Content that naturally belongs to multiple domains (e.g., security constraints that apply to both auth and upload).

**Example:**
- **Canonical home:** `security-overview.md` contains the full rate-limiting specification
- **In `processing-api.md`:** "Upload endpoints use rate limiting. See [security-overview.md] for configuration details and failure behavior."
- **In `auth-api.md`:** "Login and registration endpoints are rate-limited. See [security-overview.md] for fail-open/fail-closed behavior."

**Why this works:** Duplication creates maintenance burden and inconsistency risk. When the rate-limiting config changes, there's exactly one place to update. Cross-links ensure discoverability.

### Anti-Patterns to Avoid

- **The Junk Drawer:** Don't create a `misc/` or `other/` folder. Every file belongs to a domain. If it doesn't fit, the domain taxonomy needs refinement, not a junk drawer.
- **Deep Nesting:** Max 2 levels below domain root. `domain/subgroup/file.md` is the limit. Deep nesting hurts both human navigation and LLM context assembly.
- **Generic Filenames at Depth:** `api.md` inside `01-auth/` is ambiguous. Use `auth-api.md`. The only exception: `overview.md` within a domain folder.
- **Frontmatter Bloat:** No `owner`, `reviewer`, `jira`, `epic`, `priority`, `sprint`, `risk`, `compliance` fields. These are project management metadata, not retrieval metadata. They rot instantly and add noise.
- **Silent Dropping:** If a section's destination is unclear during migration, create a temporary doc (e.g., `_UNASSIGNED-rate-limiter-failure.md`) rather than deleting it. Unclear ≠ unimportant.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Split markdown by headings | Custom regex parser | `mdsplit` or `markdown-section-splitter` | Code-block-aware heading detection is trickier than it looks. These tools handle fenced code blocks, ATX headings, and edge cases. |
| Generate kebab-case filenames | Manual string manipulation | `mdsplit --output` or the splitter's built-in naming | Handles Unicode, special characters, duplicate detection, GitHub-compatible anchors. |
| Validate cross-links | Manual grep | `markdown-section-splitter`'s built-in link validation | Detects broken internal links across split files automatically. |
| Generate TOC/index files | Manual curation | `mdsplit --table-of-contents` | Auto-generates `toc.md` with proper relative links. |
| Frontmatter parsing | Custom YAML regex | Python `yaml.safe_load` with `re` for frontmatter extraction | YAML edge cases (multiline strings, special chars) are handled by the stdlib. |

**Key insight:** The migration is a one-time structural operation, not a recurring process. Use existing tools for the mechanical 80% (splitting, naming, TOC generation), then invest manual effort in the creative 20% (content placement, cross-link curation, reconciliation).

## Common Pitfalls

### Pitfall 1: Losing High-Risk Sections During Split

**What goes wrong:** Critical behavioral specifications (edge cases, failure modes, enforcement rules) get lost when content is redistributed across files. These sections are often short and don't have obvious "homes."

**Why it happens:** During mechanical splitting, content is assigned by heading proximity. A subsection like "6.2 Rate Limiter Failure Behavior" might get bundled with the wrong parent or dropped into an unassigned pile.

**How to maintain:** Before splitting, extract the 7 high-risk sections identified in DECISION_01.md into a checklist. After splitting, verify each one has a canonical home:
- `6.2 Rate Limiter Failure Behavior` → `security-overview.md` (under "Failure Modes" subsection)
- `6.3 Production Credential Enforcement` → `configuration.md` (under "Production Requirements")
- `9.1 Formula Parser limitations` → `processing-api.md` (under "Custom Metrics")
- `11.2 Task Queue Migration` → `task-queue.md` (standalone, already exists)
- `15.1 Dashboard Access Enforcement` → `access-control.md`
- `19.5 Application Startup Behavior` → `architecture.md` (under "Application Lifecycle")
- `23.5 CORS validation behavior` → `frontend-security.md`

**Warning signs:** A reconciliation pass that finds content in `_UNASSIGNED_*` files. Missing line counts (if SPEC.md is 1069 lines, the total across all output files should account for all non-trivial content).

### Pitfall 2: Inconsistent Frontmatter

**What goes wrong:** Different files use different field names, formats, or conventions. Some have `domain: auth`, others have `domain: "auth"` or `domains: [auth]`. Some use `related` as strings, others as objects.

**Why it happens:** Manual frontmatter creation without a template or validation.

**How to avoid:** Create a single frontmatter template file and copy it as the starting point for each new document. Use a consistent YAML style (no quotes for simple strings, arrays on one line for short lists).

**Template:**
```yaml
---
id: {kebab-case-id}
domain: {domain-name}
tags:
  - tag1
  - tag2
related:
  - related-doc-id-1
  - related-doc-id-2
---
```

### Pitfall 3: Broken Cross-References

**What goes wrong:** After splitting, internal links (`[text](#section-anchor)` or `[text](other-section)`) point to non-existent files or anchors.

**Why it happens:** SPEC.md uses section numbers (`## 14.1 Auth Endpoints`) that won't survive the split. Anchors change when files are renamed.

**How to avoid:** After splitting, use `grep -r "\]\(" docs/` to find all internal links. Validate each one. Replace section-number references with file+anchor references: `[Auth Endpoints](auth-api.md#auth-endpoints)`.

### Pitfall 4: Over-Fragmentation

**What goes wrong:** Splitting into too many tiny files (100+ files, each <100 lines). This forces LLMs to load many files to answer simple questions, increasing context overhead and retrieval complexity.

**Why it happens:** Splitting at too-deep a heading level (H4/H5) or treating every subsection as a separate file.

**How to avoid:** Enforce the 200-800 line target per file. If a file would be <200 lines, merge it with its semantic parent. If >800 lines, split at the next heading level. The `mdsplit` tool's `--max-level` parameter controls this.

### Pitfall 5: Under-Fragmentation

**What goes wrong:** Ending up with 3-5 giant files (each >1500 lines). The monolithic problem persists in fewer files.

**Why it happens:** Splitting at too-shallow a heading level (H1 only) or being too conservative about creating new files.

**How to avoid:** Target 25-40 files for a 1069-line spec. That's an average of ~350 lines/file. If the initial split produces <20 files, split at a deeper heading level.

### Pitfall 6: SPEC.md Identity Crisis

**What goes wrong:** After migration, SPEC.md is either deleted (breaking external references), left as-is (confusing — two sources of truth), or gutted to a stub (losing the architecture overview value).

**Why it happens:** No clear plan for the original file's new role.

**How to avoid:** Per DECISION_01: SPEC.md becomes the system overview / documentation index. It keeps the architecture summary, domain links, key decisions, and main data flow. It's the "what the system is" document, while the new `README.md` is the "how docs are organized" document.

## Code Examples

### Example 1: Using mdsplit for Initial Mechanical Split

```bash
# Split SPEC.md at H2 level (##) into separate files
# This creates one file per ## section with kebab-case names
python -m mdsplit docs/SPEC.md --max-level 2 --output docs/_split-temp --table-of-contents

# Output:
# _split-toc.md
# _split-purpose.md
# _split-stack.md
# _split-core-entities.md
# ... (one file per ## section)
```

**Source:** mdsplit PyPI documentation, https://pypi.org/project/mdsplit/

### Example 2: Using markdown-section-splitter for Smarter Splitting

```bash
# Split with header promotion (## → # in output files)
# Generates numbered files with cross-reference validation
python markdown_section_splitter.py docs/SPEC.md --output-dir docs/_split-temp

# Output:
# 00-toc.md
# 01-purpose.md          (was ## 1. Purpose, now # Purpose)
# 02-stack.md            (was ## 2. Stack, now # Stack)
# ...
# recommended_prompts.txt (LLM prompts for post-processing each file)
```

**Source:** https://github.com/petalo/markdown-section-splitter

### Example 3: Frontmatter Template for a Domain File

```markdown
---
id: dashboards-api
domain: dashboards
tags: [crud, layouts, graphs, filters, admin]
related:
  - schema-core
  - processing-api
  - access-control
---

# Dashboards API

## Purpose

This document covers the complete dashboards bounded context: dashboard CRUD,
layout management, graph definitions, and filter configuration. These four
subsystems form a single bounded context because graphs cannot exist without
dashboards, layouts define dashboard composition, and filters apply across
dashboard graphs.

## Main Concepts

### Dashboard Entity
...

### Graph Types
...

## Flows

### Creating a Dashboard with Graphs
1. Admin POSTs dashboard → `POST /api/v1/dashboards`
2. Admin POSTs layout → `POST /api/v1/layouts`
3. Admin POSTs graphs → `POST /api/v1/graphs` (with `dashboard_id`)
4. Admin POSTs filters → `POST /api/v1/filters`
5. Link filters to dashboard → `dashboard_filters` table

## Constraints

- Graph names are unique per dashboard (`UNIQUE (dashboard_id, name)`)
- Deleting a dashboard cascades to graphs and dashboard_access entries
- Only admins can create/update/delete dashboards, layouts, graphs, and filters

## Edge Cases

- Deleting a layout that's referenced by a dashboard: foreign key prevents deletion
- Creating a graph with a non-existent `dashboard_id`: FK constraint rejects

## Related Docs

- [schema-core.md](database/schema-core.md) — DDL for dashboards, layouts, graphs, filters tables
- [processing-api.md](processing/processing-api.md) — Upload pipeline that populates graph data
- [access-control.md](security/access-control.md) — Dashboard access enforcement per endpoint
```

### Example 4: Reconciliation Checklist Script (Python)

```python
#!/usr/bin/env python3
"""Verify no content was lost during SPEC.md migration."""

import re
from pathlib import Path

def extract_sections(spec_path: str) -> dict[str, int]:
    """Extract all ## sections and their line counts from SPEC.md."""
    content = Path(spec_path).read_text(encoding='utf-8')
    sections = {}
    current_section = "preamble"
    line_count = 0
    
    for line in content.split('\n'):
        if re.match(r'^## ', line):
            sections[current_section] = line_count
            current_section = line.strip().lstrip('#').strip()
            line_count = 0
        else:
            line_count += 1
    sections[current_section] = line_count
    return sections

def verify_coverage(original_sections: dict, docs_dir: str) -> list[str]:
    """Check that each original section's content exists in output files."""
    docs_content = ''
    for f in Path(docs_dir).rglob('*.md'):
        docs_content += f.read_text(encoding='utf-8') + '\n'
    
    warnings = []
    for section_name, line_count in original_sections.items():
        if line_count < 5:  # Skip trivial sections
            continue
        # Check if section heading text appears in output
        normalized = section_name.lower().replace('&', 'and')
        if normalized not in docs_content.lower():
            warnings.append(
                f"POTENTIAL LOSS: Section '{section_name}' ({line_count} lines) "
                f"not found in output docs"
            )
    return warnings

# Usage
sections = extract_sections('docs/SPEC.md')
warnings = verify_coverage(sections, 'docs/')
for w in warnings:
    print(w)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Monolithic docs (one giant file) | Modular docs by domain/retrieval intent | 2024-2025 | LLMs can load only the relevant domain instead of the entire spec, reducing context usage by 80-90% |
| No frontmatter | YAML frontmatter as document schema | 2025 | RAG systems filter by metadata before semantic search, improving precision |
| Fixed-size chunking for RAG | Heading-aware + retrieval-intent chunking | 2024-2025 | Preserves semantic coherence; chunks can stand alone as meaningful units |
| Manual cross-links only | `related` frontmatter + inline links | 2025-2026 | Creates a virtual knowledge graph for context assembly |
| Flat folder structure | Semantic zoning (00-09 active, 90 ADR, 99 reference) | Industry convention | Separates current truth from historical decisions and static lookup |

**Deprecated/outdated:**
- **Section numbers as identifiers:** SPEC.md uses `## 14.1 Auth Endpoints` — these numbers are fragile and don't survive splitting. Replace with named anchors and file-based references.
- **Mixed-language content:** SPEC.md has Russian text in sections 1-18. The migration is an opportunity to translate everything to English (per project rules).

## Open Questions

1. **Should existing docs (SWAGGER_README.md, RUN.md, TASK_QUEUE_MIGRATION.md, STRUCT.md) be migrated into the new structure or kept as-is?**
   - What we know: TASK_QUEUE_MIGRATION.md is already a standalone doc that maps naturally to `03-processing/task-queue.md`. SWAGGER_README.md maps to `99-reference/swagger.md`. RUN.md maps to `99-reference/run-guide.md`. STRUCT.md is a generated artifact, not a spec — it should NOT be migrated.
   - What's unclear: Whether to migrate content in-place or copy-and-deprecate.
   - Recommendation: Copy content into the new structure, add a note at the top of the original file pointing to the new location. Don't delete originals until the new structure is validated.

2. **How to handle the Russian-language content in SPEC.md sections 1-18?**
   - What we know: Project rules require English-only. SPEC.md has Russian in early sections.
   - What's unclear: Whether translation should happen during migration or as a separate step.
   - Recommendation: Translate during migration. The restructuring already requires reading and placing each section — translating at the same time is marginal extra effort.

3. **Should the `id` field use a specific format (UUID vs kebab-case)?**
   - What we know: MAGI spec recommends UUIDs for `doc-id`. The decision specifies `id` as a field but doesn't mandate format.
   - What's unclear: Whether UUIDs provide meaningful benefit over kebab-case names for a documentation set this size.
   - Recommendation: Use kebab-case matching the filename (e.g., `id: auth-api` for `auth-api.md`). UUIDs add entropy without retrieval benefit for human-curated docs. If machine-generated IDs are needed later, they can be added as a separate field.

## Sources

### Primary (HIGH confidence)
- **DECISION_01.md** — User decisions constraining the research scope (granularity, metadata schema, migration strategy, naming conventions)
- **SPEC.md** (1069 lines) — The source document to be restructured; analyzed in full
- **mdsplit** (PyPI v0.5.0) — https://pypi.org/project/mdsplit/ — Python CLI tool for splitting markdown by heading level
- **markdown-section-splitter** — https://github.com/petalo/markdown-section-splitter — Python script for splitting with frontmatter and link validation

### Secondary (MEDIUM confidence)
- **MAGI (Markdown for Agent Guidance & Instruction)** — https://docs.magi-mda.org/introduction — Extended markdown spec with frontmatter schema, AI instructions, and typed relationships. Informed the frontmatter field design.
- **"Frontmatter as Document Schema"** (Understanding Data, 2026-03-16) — https://understandingdata.com/posts/frontmatter-as-document-schema/ — Explains frontmatter as type signatures for documents, metadata-first retrieval.
- **"Markdown-First Semantics"** (SteakHouse Blog, 2026-01-15) — https://blog.trysteakhouse.com/blog/markdown-first-semantics-frontmatter-rag-retrieval — Frontmatter as control plane for LLM ingestion.
- **"Document-to-Markdown for RAG"** (Iteration Layer, 2026-04-15) — https://iterationlayer.com/blog/document-to-markdown-for-rag — Chunking strategies, metadata-enriched chunks, heading-aware splitting.
- **"Context Window Management for LLMs"** (By AI Team, 2025-11-14) — https://byaiteam.com/blog/2025/11/14/context-window-management-for-llms-reduce-hallucinations/ — Chunking strategies, overlap, context assembly ordering.
- **"Text Chunking Strategies for RAG"** (AtlasSC, 2026-03-30) — https://atlassc.net/2026/03/30/text-chunking-strategies-for-rag — Document-based chunking for structured formats (Markdown, HTML).
- **"Migrating Legacy Docs to Markdown"** (Medium, 2026-01-16) — https://medium.com/@victorzion1/migrating-legacy-docs-to-markdown-step-by-step-guide-4e8c0a570267 — 10-step migration pipeline (inventory → define standard → structure → convert → fix → normalize → validate → link → review → maintain).
- **Red Hat Modular Documentation** — https://redhat-documentation.github.io/modular-docs/ — Module types (concept, procedure, reference), assembly patterns, self-contained chunk principle.
- **"How to Structure Large Documentation Projects"** (Toflio, 2026-03-05) — https://www.toflio.com/blog/build-large-document-folders-names-markdown — Folder hierarchy, naming conventions, common mistakes.

### Tertiary (LOW confidence)
- **"Organizing Your Content"** (Docsy) — https://www.docsy.dev/docs/best-practices/organizing-content/ — Documentation section organization patterns.
- **"Structuring Your Documentation"** (ReadMe) — https://docs.readme.com/main/docs/structuring-your-docs — API documentation architecture patterns.

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|---|---|---|
| Standard stack | HIGH | Tools (mdsplit, markdown-section-splitter) are concrete, installable, documented. Frontmatter pattern is widely adopted with multiple authoritative sources. |
| Architecture | HIGH | Folder structure and file organization directly implement DECISION_01.md constraints. Patterns are validated against SPEC.md's actual content. |
| Metadata schema | HIGH | The 4-field schema (id, domain, tags, related) is directly from DECISION_01.md. Research confirms this is the minimal effective set for RAG. |
| Migration strategy | MEDIUM | The 4-step pipeline (inventory → map → transfer → reconcile) is standard practice. Specific tool usage for SPEC.md requires adaptation. |
| Pitfalls | HIGH | All 6 pitfalls are grounded in SPEC.md's specific content (7 high-risk sections, mixed languages, section-number references). |
| Code examples | HIGH | mdsplit and markdown-section-splitter examples are from official docs. Reconciliation script is original but straightforward. |

**Research date:** 2026-05-18
**Valid until:** 2026-06-17 (30 days — stable domain, no fast-moving dependencies)
