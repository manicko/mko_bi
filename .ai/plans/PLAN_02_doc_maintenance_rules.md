---
wave: 2
depends_on: []
files_modified:
  - docs/00-overview/doc-maintenance-rules.md
  - AGENTS.md
autonomous: true
---

# Plan 02: Documentation Maintenance Rules

## Goal
Create the `doc-maintenance-rules.md` reference document and wire it into AGENTS.md as a mandatory pre-read for all doc-modifying tasks.

## must_haves
- [ ] `docs/00-overview/doc-maintenance-rules.md` exists with all 12 sections
- [ ] Rules doc has YAML frontmatter (models the discipline)
- [ ] AGENTS.md references the rules doc as mandatory pre-read
- [ ] Rules doc is under 200 lines
- [ ] All text is English only (no Russian)
- [ ] Checklist templates included for: new feature, API change, schema change, doc splitting

## Tasks

### Task 1: Create doc-maintenance-rules.md
Create file `docs/00-overview/doc-maintenance-rules.md` with the following content:

```markdown
---
id: doc-maintenance-rules
domain: overview
tags:
  - documentation
  - governance
  - rules
related:
  - overview.md
---

## Purpose
Mandatory reference for agents and guidance for humans when creating, updating, or splitting documentation. Read this before any task that modifies files under `docs/`.

## Main Concepts
- **Single source of truth:** Each fact lives in exactly one file. Other files summarize + cross-link.
- **Translate on touch:** All docs are English. When editing a section containing Russian, translate it as part of the edit.
- **No silent dropping:** Unclear content goes to `docs/.tmp/` (gitignored), never deleted.
- **Frontmatter is contract:** Every domain doc starts with YAML frontmatter (`id`, `domain`, `tags`, `related`).

## Update Triggers
Update docs when:
- New feature added or behavior changed
- API endpoints added, changed, or removed
- Database schema changed
- Security model or constraints changed
- Edge cases or constraints discovered

Do NOT update docs for:
- Minor refactoring with no behavior change
- Bug fixes that don't change contracts
- Cosmetic or formatting-only changes

When in doubt: update the docs.

## File Placement Rules
- Top-level folders use numbered prefixes: `00-overview/`, `01-auth/`, … `10-deployment/`
- Place new docs in the domain folder matching their topic
- ADRs go in `90-adr/`; reference material goes in `99-reference/`
- Flat by default; nest only when >5-7 files exist in one folder
- Max depth: 2 levels below domain root

## Naming Conventions
- Filenames: kebab-case mandatory (`auth-api.md`, not `AuthApi.md`)
- Generic names (`utils.md`, `helpers.md`) allowed at domain root only
- At deeper levels, names must be specific and descriptive

## Frontmatter Requirements
Every domain doc file must start with:
```yaml
---
id: unique-doc-id
domain: domain-name
tags:
  - lowercase-tag
related:
  - related-doc-id
---
```
- `id`: kebab-case, unique across all docs
- `domain`: matches the folder name (e.g., `auth`, `database`)
- `tags`: at least one, lowercase with hyphens
- `related`: cross-references (empty array `[]` if none)

## Content Quality Rules
- Every file starts with `## Purpose` (1-3 sentences) + `## Main Concepts`
- Recommended sections: `## Flows`, `## Constraints`, `## Edge Cases`, `## Related Docs`
- Omit empty sections entirely — no "N/A" or "TBD" filler
- Sections with links must include 1-2 sentences of context (no bare links)
- Keep prose concise and scannable; prefer imperative rules over explanatory prose

## Cross-Linking Strategy
- One canonical home per fact (SSOT)
- Secondary locations: write a 1-2 sentence summary + `> See [Topic](path) for details.`
- Use relative paths for cross-links
- When moving/renaming a doc, search all `*.md` files for stale references

## Doc Splitting Threshold
- **Soft threshold:** 800 lines — plan a split
- **Hard threshold:** 1000 lines — must split
- Split at `##` heading boundaries
- Each resulting file gets its own frontmatter, `## Purpose`, and `## Main Concepts`
- Add cross-references in both directions after splitting

## Translation Rules
- All documentation is in English. Always.
- No Russian text in any doc file
- When editing a section that contains Russian, translate it to English as part of the edit
- No dedicated translation pass — translate on touch
- Known exception: `RUN.md` at project root (translate when next touched)

## Agent Enforcement
- Agents **must** read this document before any task that modifies files under `docs/`
- Include the relevant checklist template (below) in every doc-modifying task
- Verify frontmatter is present and complete on every modified file
- Verify no Russian text (grep for Cyrillic: `[а-яА-ЯёЁ]`)

## Checklist Templates

### New Feature
- [ ] Determine domain folder
- [ ] Create file with kebab-case name (or update existing)
- [ ] Add frontmatter (`id`, `domain`, `tags`, `related`)
- [ ] Write `## Purpose` + `## Main Concepts`
- [ ] Add content to appropriate sections
- [ ] Add cross-links from new file to related docs
- [ ] Add cross-links from related docs to new file
- [ ] Verify no Russian text
- [ ] Verify file under 800 lines

### API Change
- [ ] Locate canonical doc for the affected API
- [ ] Update endpoint descriptions and schemas
- [ ] Update code examples referencing changed endpoints
- [ ] Check cross-links from other docs for impact
- [ ] Update frontmatter tags if domain changed
- [ ] Verify no Russian text
- [ ] Verify file under 800 lines

### Schema Change
- [ ] Update the relevant schema doc
- [ ] Update ER diagrams or table definitions
- [ ] Update `indexes.md` if indexes changed
- [ ] Update `enums.md` if enums changed
- [ ] Cross-reference from schema doc to affected API docs
- [ ] Verify no Russian text
- [ ] Verify file under 800 lines

### Doc Splitting
- [ ] Confirm file exceeds 800-line soft threshold
- [ ] Identify split points at `##` heading boundaries
- [ ] Create new file(s) with kebab-case names
- [ ] Move content to new files
- [ ] Add frontmatter to each new file
- [ ] Add `## Purpose` + `## Main Concepts` to each new file
- [ ] Add cross-references in both directions
- [ ] Search for and update any links to the old file
- [ ] Verify all files under 800 lines
```

### Task 2: Update AGENTS.md
In `AGENTS.md`, add a reference to the rules doc in the "#Key links" section. Add this line after the existing links:
```
[Doc Maintenance Rules](C:\py_dev\mkobi\docs/00-overview/doc-maintenance-rules.md) — **read before any doc-modifying task**
```

## Validation
- Verify `doc-maintenance-rules.md` exists and has all 12 top-level sections (Purpose, Scope, Update Triggers, File Placement, Naming, Frontmatter, Content Quality, Cross-Linking, Doc Splitting, Translation, Agent Enforcement, Checklists)
- Verify the rules doc has valid YAML frontmatter
- Verify AGENTS.md contains a reference to the rules doc
- Verify the rules doc is under 200 lines
- Verify no Russian text in the rules doc

## Acceptance Criteria
- [ ] `doc-maintenance-rules.md` created with all 12 sections
- [ ] Rules doc has frontmatter with `id: doc-maintenance-rules`, `domain: overview`
- [ ] AGENTS.md references the rules doc as mandatory pre-read
- [ ] Rules doc is under 200 lines
- [ ] All text is English
- [ ] All 4 checklist templates present (new feature, API change, schema change, doc splitting)
