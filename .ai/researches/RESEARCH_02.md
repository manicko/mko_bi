# 02 Documentation Maintenance Rules - Research

**Researched:** 2026-05-18
**Domain:** Documentation governance, maintenance rules, YAML frontmatter standards, agent enforcement patterns
**Confidence:** HIGH

## Summary

This research covers Phase 02: creating a documentation maintenance rules document (`docs/00-overview/doc-maintenance-rules.md`) that defines how to properly update the project's modular docs structure without degrading it. The document serves as a reference for both agents and humans when modifying documentation.

The research investigated: (1) documentation maintenance best practices from industry sources, (2) YAML frontmatter standards and conventions, (3) "single source of truth" and cross-linking strategies, (4) content quality and doc-splitting thresholds, (5) agent enforcement patterns for mandatory pre-reads, and (6) checklist templates for common doc-update scenarios.

**Primary recommendation:** Structure the rules document as a concise reference (not a tutorial) with the following sections: Purpose, Update Triggers, File Placement Rules, Naming Conventions, Frontmatter Requirements, Content Quality Rules, Cross-Linking Strategy, Doc Splitting Threshold, Translation Rules, Agent Enforcement, and Checklist Templates. Reference it from AGENTS.md as a mandatory pre-read before any doc-modifying task. Keep the rules document itself under 200 lines to model the discipline it prescribes.

## Standard Stack

The rules document is markdown-only — no libraries required. The project's existing conventions are the "stack":

| Convention | Current Usage | Role in Rules |
|---|---|---|
| YAML frontmatter (`id`, `domain`, `tags`, `related`) | All domain docs since Phase 01 | Codify as mandatory schema |
| Numbered folder prefixes (`00-overview/`…`10-deployment/`) | All domain docs | Lock as canonical structure |
| Kebab-case filenames | All domain docs | Enforce as mandatory |
| `## Overview` section | All domain docs (inconsistent) | Replace with `## Purpose` + `## Main Concepts` |
| `## Related Docs` section | Only `overview.md` | Make mandatory on every file |
| Cross-links (`> See […](…)`) | Used in SPEC.md and domain docs | Formalize the "summarize, don't replicate" pattern |

## Architecture Patterns

### Recommended Rules Document Structure

```
doc-maintenance-rules.md
├── ## Purpose                   ← What this doc is and who it's for
├── ## Scope                     ← What it covers (and what it doesn't)
├── ## Update Triggers           ← When docs MUST be updated
├── ## File Placement Rules      ← Where to put new/updated content
├── ## Naming Conventions        ← Kebab-case, numbered prefixes, depth limits
├── ## Frontmatter Requirements  ← Mandatory/optional YAML fields
├── ## Content Quality Rules     ← Purpose+Main Concepts required, no N/A, etc.
├── ## Cross-Linking Strategy    ← One canonical home, summarize don't replicate
├── ## Doc Splitting Threshold   ← When to split (800-line soft, 1000-line hard)
├── ## Translation Rules         ← English only, translate on touch
├── ## Agent Enforcement         ← Mandatory pre-read, checklist requirement
└── ## Checklist Templates       ← Per-scenario checklists
```

### Pattern 1: "One Canonical Home" (SSOT for Docs)

**What:** Each fact, definition, or specification exists in exactly one file. Other files reference it via summary + cross-link.
**When to use:** Always, when writing or updating any doc content.
**Source:** Industry standard SSOT principle confirmed by Paligo, Google Tech Writing, and Docsie.io research.

Implementation in this project:
- SPEC.md is the **navigation hub** — it indexes and links, but domain docs hold the canonical content.
- Domain docs (e.g., `01-auth/auth-api.md`) are the **canonical home** for their topic.
- When two docs need the same information, the secondary doc writes a 1-2 sentence summary and links to the canonical source with `> See [Topic](path) for details.`

### Pattern 2: Frontmatter as Contract

**What:** Every domain doc file starts with YAML frontmatter that acts as a machine- and human-readable contract.
**Schema (locked by existing project convention):**

```yaml
---
id: unique-doc-id
domain: domain-name
tags:
  - lowercase-tag
  - multi-word-tag
related:
  - related-doc-id
  - path/to/other-doc.md
---
```

**Rules:**
- `id`: required, kebab-case, unique across all docs
- `domain`: required, matches the folder name (e.g., `auth`, `database`, `processing`)
- `tags`: required, at least one tag, lowercase with hyphens
- `related`: required (can be empty array `[]`), lists cross-references

### Pattern 3: Section Structure Convention

**Required on every domain doc file:**
```markdown
## Purpose
[1-3 sentences: what this doc covers and who it's for]

## Main Concepts
[Key concepts, definitions, or overview of the topic]
```

**Recommended (use when applicable):**
- `## Flows` — step-by-step processes or pipelines
- `## Constraints` — limitations, boundaries, non-obvious restrictions
- `## Edge Cases` — error conditions, boundary behaviors
- `## Related Docs` — explicit cross-links with context

**Anti-patterns to avoid:**
- Empty sections with "N/A" or "TBD" — omit the section entirely
- `## Overview` as the first content section — use `## Purpose` instead (Overview is too vague; Purpose forces specificity)
- Sections with only a link and no context — always add 1-2 sentences of summary

### Pattern 4: Doc Splitting Threshold

**Soft threshold:** 800 lines — start planning a split.
**Hard threshold:** 1000 lines — must split.

**Split strategy (from research):**
1. Identify logical section boundaries (use `##` headings as split points)
2. Create new file with kebab-case name in the same folder
3. Move related sections to the new file
4. Add cross-references in both directions
5. Each resulting file must be self-contained (has `## Purpose` + `## Main Concepts`)
6. Original file keeps a summary + link to the new file

**Current project status:** Largest doc is `STRUCT.md` at 3.9MB (auto-generated, exempt). Largest hand-written doc is `02-dashboards/dashboards-api.md` at 23KB (~768 lines) — approaching the soft threshold. All other docs are well within limits.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---|---|---|
| Doc freshness tracking | Custom review schedule system | "When in doubt: update the docs" rule + agent pre-read |
| Link validation | Custom script | Manual review during doc-update tasks (CI linting deferred) |
| Translation tracking | Translation workflow tool | "Translate on touch" — translate Russian when you touch a section |
| Content duplication detection | Custom diff tool | "One canonical home" discipline + cross-linking rules |
| Frontmatter validation | Custom schema checker | Agent reads rules doc, follows checklist |

**Key insight:** The rules document itself IS the enforcement mechanism. It's read by agents before doc-modifying tasks, and it contains checklist templates. No tooling needed at this stage.

## Common Pitfalls

### Pitfall 1: Rules Document Becomes a Tutorial

**What goes wrong:** Writing long explanations, examples, and teaching prose instead of concise rules.
**Why it happens:** The author wants to be helpful and thorough.
**How to avoid:** Every section should be scannable in <30 seconds. Rules are imperative ("Do X"), not explanatory ("You might want to consider X"). Examples are short and inline.
**Warning signs:** Any single section exceeds 20 lines. The document exceeds 200 lines total.

### Pitfall 2: Inconsistent Frontmatter Adoption

**What goes wrong:** Some files have frontmatter, some don't. Fields are inconsistent.
**Why it happens:** No enforcement, no validation, gradual drift.
**How to avoid:** The rules doc mandates frontmatter on every domain file. Agent checklist includes "Verify frontmatter is present and complete." Existing files already have frontmatter — maintain the convention.
**Warning signs:** A new file is created without `---` delimiters at the top.

### Pitfall 3: Silent Content Dropping

**What goes wrong:** When updating a doc, old content is deleted without being moved or linked.
**Why it happens:** Author assumes the content is obsolete.
**How to avoid:** "No silent dropping" rule — unclear content goes to a temporary doc (`docs/.tmp/` or similar), never deleted outright. If removing a section, add a comment in the PR explaining why.
**Warning signs:** Line count drops significantly without explanation in the commit.

### Pitfall 4: Cross-Link Rot

**What goes wrong:** Links point to files that no longer exist or sections that have been renamed.
**Why it happens:** Files are restructured without updating all references.
**How to avoid:** When moving/renaming a doc, search all `*.md` files for references to it. Update or remove broken links. Use relative paths (e.g., `../01-auth/auth-api.md`) rather than absolute.
**Warning signs:** A doc is renamed but old links remain.

### Pitfall 5: Russian Text Creep

**What goes wrong:** Russian text appears in doc files (the project originally had Russian content — `RUN.md` is entirely in Russian).
**Why it happens:** Authors copy-paste from old docs or write in their native language.
**How to avoid:** "All documentation is in English. Always." rule. When editing a section that contains Russian, translate it to English as part of the edit. No dedicated translation pass.
**Warning signs:** Any Cyrillic characters in a doc file (can be detected with grep: `[а-яА-ЯёЁ]`).

## Code Examples

### Example: Proper Cross-Linking (Summarize, Don't Replicate)

In `SPEC.md` (navigation hub), the auth section should read:
```markdown
### Auth & Access Control
JWT-based authentication with bcrypt password hashing. Three roles: Admin, Editor, Viewer.
> See [Auth API](../01-auth/auth-api.md) for endpoints and [Access Control](../08-security/access-control.md) for enforcement.
```

NOT:
```markdown
### Auth & Access Control
[Full copy of auth-api.md content pasted here]
```

### Example: Mandatory Frontmatter

Every domain doc file must start with:
```yaml
---
id: unique-doc-id
domain: domain-name
tags:
  - primary-tag
  - secondary-tag
related:
  - related-doc-path
---
```

### Example: Doc Splitting Decision

When `dashboards-api.md` exceeds 800 lines:
```
BEFORE: dashboards-api.md (900 lines)
  ├── Dashboard CRUD
  ├── Layout CRUD
  ├── Graph CRUD
  ├── Filter CRUD
  └── Data retrieval

AFTER:
  ├── dashboards-api.md (400 lines) — Dashboard CRUD + Layout CRUD + summary + links
  ├── dashboards-graphs.md (300 lines) — Graph CRUD + Filter CRUD
  └── dashboards-data.md (200 lines) — Data retrieval
```

Each new file gets its own frontmatter, `## Purpose`, and `## Main Concepts`.

## Agent Enforcement Pattern

### How to Make Rules Mandatory for Agents

1. **Reference in AGENTS.md:** Add a line in the "Key links" section:
   ```
   [Doc Maintenance Rules](C:\py_dev\mkobi\docs\00-overview/doc-maintenance-rules.md)
   ```
2. **Add to agent instruction files:** In `.kilo/agents/*.md`, add a permission step:
   ```
   Before modifying any file in docs/, read doc-maintenance-rules.md first.
   ```
3. **Checklist requirement:** Every doc-modifying task includes a verification step referencing the rules.

### Pre-Read Pattern (from research)

The vLLM project's AGENTS.md uses this pattern effectively:
> "Read this before modifying AGENTS.md or any guide it links to."

Apply the same pattern: the rules doc is referenced as a mandatory pre-read before any task that modifies `docs/` content. This is advisory for humans, mandatory for agents.

### Enforcement Hierarchy (from AgentPatterns.ai research)

| Rule Type | Layer | Example |
|---|---|---|
| Style preference | Advisory (rules doc) | "Prefer concise prose" |
| File placement | Mandatory (agent pre-read) | "New auth docs go in 01-auth/" |
| Naming convention | Mandatory (agent pre-read) | "kebab-case filenames" |
| Frontmatter | Mandatory (agent pre-read) | "Every file has YAML frontmatter" |
| English only | Mandatory (agent pre-read) | "No Russian text in docs" |

## Checklist Templates

### Checklist: New Feature Doc Update
```
- [ ] Determine which domain folder the feature belongs to
- [ ] Check if a file already exists for this topic; if not, create one with kebab-case name
- [ ] Add mandatory frontmatter (id, domain, tags, related)
- [ ] Write ## Purpose (1-3 sentences) + ## Main Concepts
- [ ] Add content to appropriate section (Flows, Constraints, Edge Cases)
- [ ] Add cross-links FROM the new file TO related docs
- [ ] Add cross-links FROM related docs TO the new file
- [ ] Update SPEC.md Documentation Index if new domain file
- [ ] Verify no Russian text (grep for Cyrillic)
- [ ] Verify file is under 800 lines
```

### Checklist: API Change Doc Update
```
- [ ] Locate the canonical doc for the affected API
- [ ] Update endpoint descriptions, request/response schemas
- [ ] Update any code examples that reference changed endpoints
- [ ] Check for cross-links from other docs that may be affected
- [ ] Update frontmatter tags if the API domain changed
- [ ] Verify no Russian text
- [ ] Verify file is under 800 lines
```

### Checklist: Schema Change Doc Update
```
- [ ] Update the relevant schema doc (schema-core.md, schema-processing.md, or schema-access.md)
- [ ] Update any ER diagrams or table definitions
- [ ] Update indexes.md if indexes changed
- [ ] Update enums.md if enums changed
- [ ] Cross-reference from schema doc to affected API docs
- [ ] Verify no Russian text
- [ ] Verify file is under 800 lines
```

### Checklist: Doc Splitting
```
- [ ] Confirm file exceeds 800-line soft threshold
- [ ] Identify logical split points (## heading boundaries)
- [ ] Create new file(s) with kebab-case names
- [ ] Move content to new files
- [ ] Add frontmatter to each new file
- [ ] Add ## Purpose + ## Main Concepts to each new file
- [ ] Add cross-references in both directions
- [ ] Update SPEC.md Documentation Index
- [ ] Verify all files under 800 lines
- [ ] Search for and update any links to the old file
```

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| Monolithic SPEC.md | Modular docs with SSOT | Easier maintenance, no single point of failure |
| No frontmatter | YAML frontmatter on every file | Machine-readable metadata, enables tooling |
| "Update docs later" | "Update docs in same task" | Docs stay current, no doc debt |
| Generic section names | `## Purpose` + `## Main Concepts` required | Consistent structure, faster scanning |
| Copy-paste reuse | Cross-link + summary | No duplication, single source of truth |
| No split threshold | 800-line soft / 1000-line hard | Prevents monolithic doc recurrence |

## Open Questions

1. **Should `docs/.tmp/` be the official location for "no silent dropping" temporary docs?**
   - What we know: The rule says unclear content goes to a temporary doc, never deleted.
   - What's unclear: Whether `.tmp/` should be gitignored or committed.
   - Recommendation: Create `docs/.tmp/` and add it to `.gitignore`. Content there is staging, not permanent.

2. **Should the rules doc itself have frontmatter?**
   - What we know: The rules doc is in `docs/00-overview/`, which is a domain folder.
   - What's unclear: Whether meta-docs (docs about docs) follow the same rules.
   - Recommendation: Yes — the rules doc should have frontmatter with `domain: overview` to model the discipline it prescribes.

3. **How to handle `RUN.md` (fully in Russian)?**
   - What we know: `RUN.md` at project root is entirely in Russian (51 lines of Cyrillic).
   - What's unclear: Whether it should be translated, moved to `docs/`, or left as-is since it's not in the modular docs structure.
   - Recommendation: Add a note in the rules doc that `RUN.md` is a known exception (project root, not modular docs). Translate it when it's next touched. Don't create a dedicated translation task.

## Sources

### Primary (HIGH confidence)
- Existing project docs structure (`docs/` folder) — direct observation
- Existing frontmatter conventions (`01-auth/auth-api.md`, `09-database/schema-core.md`, etc.) — direct observation
- DECISION_02.md — locked user decisions constraining this research
- AGENTS.md — current agent instruction patterns
- `.kilo/agents/researcher.md` — agent role and output format

### Secondary (MEDIUM confidence)
- vLLM AGENTS.md (https://docs.vllm.ai/en/latest/contributing/editing-agent-instructions/) — pre-read pattern, line budget discipline, change checklist
- Google Tech Writing: Organizing Large Documents (https://developers.google.com/tech-writing/two/large-docs) — splitting thresholds, progressive disclosure
- Google Developer Documentation Style Guide: Cross-references (https://developers.google.com/style/link-text) — linking best practices
- AgentPatterns.ai: Enforcing Agent Behavior (https://agentpatterns.ai/instructions/enforcing-agent-behavior-with-hooks/) — enforcement hierarchy, advisory vs deterministic rules
- GitHub Docs YAML Frontmatter (https://docs.github.com/en/contributing/syntax-and-versioning-for-github-docs/using-yaml-frontmatter) — frontmatter field conventions

### Tertiary (LOW confidence — web search, not individually verified)
- Docsio: Documentation Maintenance Guide 2026 — refresh cadence, ownership model, triage severity
- Docsio: Documentation Governance 4-Layer Model — ownership, lifecycle, quality, access layers
- Paligo: Single Source of Truth — SSOT principles, reference vs copy-paste
- Paligo: 5 Principles of Single-Sourcing — "Only Talk to Your Friends" linking principle
- Docsie.io: Cross-links Best Practices — bidirectional linking, descriptive link text
- Skill Seekers: Large Documentation Handling — size thresholds for splitting (500/2000/5000+ pages)
- GitHub: codeh-cli split-large-file.md — 450-line threshold, split workflow
- DigitalOcean: Chunking Best Practices — section-based splitting strategy
- Fern: Documentation Maintenance Best Practices — reusable snippets, automation
- Structured MADR: YAML Frontmatter Spec — required fields, tag conventions
- Jekyll: Front Matter — predefined variables, defaults
- Mintlify: Frontmatter Reference — field types, validation
- MarkdownLang: Frontmatter — common fields, validation patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — based on direct observation of existing project conventions
- Architecture patterns: HIGH — based on existing project structure + locked decisions from DECISION_02.md
- Frontmatter schema: HIGH — already implemented across all domain docs
- Agent enforcement: MEDIUM — based on vLLM pattern (verified) + AgentPatterns.ai (web search)
- Checklist templates: MEDIUM — synthesized from multiple sources, adapted to project
- Doc splitting threshold: MEDIUM — 800-line threshold from DECISION_02.md, splitting strategy from Google Tech Writing + GitHub examples
- Translation rules: HIGH — locked decision from DECISION_02.md

**Research date:** 2026-05-18
**Valid until:** 2026-06-18 (30 days — stable domain, no fast-moving dependencies)
