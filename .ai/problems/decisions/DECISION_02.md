# Phase 2: Documentation Maintenance Rules - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a rules/guidance document that defines how to properly update the project's documentation (SPEC.md and the modular docs structure) without degrading it. Covers: folder creation decisions, where to place different types of updates, naming conventions, content quality standards, cross-linking requirements, and translation rules. The rules doc is consumed by both agents and humans when making changes to docs or code.

</domain>

<decisions>
## Implementation Decisions

### Rules scope & format

- Detailed coverage of all key cases, but written laconicly (no bloat)
- Must cover: folder/file placement rules, content quality rules, naming conventions, cross-linking requirements, translation rules, update triggers
- Format: concise rules with brief rationale — not a tutorial, a reference

### Where the rules doc lives

- In `docs/00-overview/` — part of the modular docs structure
- Rationale: both agents and humans edit documentation; placing it in the docs structure makes it discoverable by people too
- File: `docs/00-overview/doc-maintenance-rules.md` (or similar)

### What triggers a documentation update

- Only **important/significant changes** warrant doc updates:
  - New features or capabilities
  - Changed behavior or business logic
  - New/changed API endpoints
  - New/changed database schema
  - Security-related changes
  - Changed constraints or edge cases
- Minor refactoring, bug fixes that don't change behavior, and cosmetic changes do NOT require doc updates
- When in doubt: update the docs

### Russian→English handling

- **All documentation is in English. Always.**
- No Russian text in any doc file
- When editing a section that contains Russian: translate it to English as part of the edit
- No dedicated translation pass — translate on touch

### Enforcement mechanism

- **Agent mandatory reads**: agents must read the rules document before any task that modifies documentation
- The rules doc is referenced in AGENTS.md or agent context files as a required pre-read
- Humans are encouraged to follow the same rules (advisory for humans, mandatory for agents)

### Folder and naming conventions (from prior architecture decisions)

- Numbered folder prefixes: top-level only (00-overview, 01-auth, …)
- File naming: kebab-case mandatory (e.g., `upload-flow.md`, `auth-api.md`)
- Folder nesting: flat by default; nest only when >5-7 files in one folder
- Max depth: 2 levels below domain root (domain/subgroup/file.md)
- ADRs: separate `90-adr/` folder — decision history, not current truth
- Reference: separate `99-reference/` folder — lookup/static material
- Generic filenames (api.md, overview.md) avoided at deeper levels; allowed at domain root

### Content rules (from prior architecture decisions)

- Each fact has exactly **one canonical home**; other locations have summaries + cross-links
- "Summarize, don't replicate"
- No silent dropping: unclear content goes to a temporary doc, never deleted
- Empty sections omitted entirely — no "N/A" filler
- Every file starts with `## Purpose` + `## Main Concepts` (required minimum)
- Recommended sections: `## Flows`, `## Constraints`, `## Edge Cases`, `## Related Docs`
- YAML frontmatter on every domain file: `id`, `domain`, `tags`, `related`

### KiloCode's Discretion

- Exact wording and formatting of the rules document
- Specific examples to include
- Whether to add a checklist template for common doc-update scenarios

</decisions>

<specifics>
## Specific Ideas

- The rules doc should be practical and scannable — agents read it before every doc-modifying task
- Reference the existing modular docs structure (`00-overview/` through `99-reference/`) as the canonical organization
- The project already has a migration map (PLAN_01111.md) that can serve as a concrete example of the rules in action
- Rules should prevent the "monolithic SPEC.md" problem from recurring — if a doc grows beyond ~800 lines, it should be split

</specifics>

<deferred>
## Deferred Ideas

- CI/CD enforcement of doc rules (e.g., linting frontmatter, checking for Russian text) — future phase, not now
- Automated doc generation from code — out of scope
- Translation workflow tooling — translate on touch is sufficient for now

</deferred>

---

_Phase: 02-doc-maintenance-rules_
_Context gathered: 2026-05-18_
