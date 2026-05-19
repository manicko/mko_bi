# Phase 1: Legacy Documentation Integration - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate 4 orphaned documentation files from `docs/` root into the structured documentation system (numbered domain folders, YAML frontmatter, English-only, cross-linked). Two files (SWAGGER_README.md, RUN.md) are already deprecated with content absorbed elsewhere. Two files (README_DOCKER.md, TASK_QUEUE_MIGRATION.md) still hold unique content not yet integrated. Also evaluate whether `commands.md` belongs in user-facing docs.

This phase covers documentation structure and placement only — not implementation code changes.

</domain>

<decisions>
## Implementation Decisions

### New guides section

- Create a new numbered section `11-guides/` for operational/how-to content that doesn't belong to a specific domain (auth, dashboards, processing, etc.)
- This section is for guides that explain how to use, operate, or maintain the system from a user/operator perspective
- Numbering rationale: follows `10-deployment/`, precedes `90-adr/` (ADR section) and `99-reference/` (reference section)

### README_DOCKER.md → `11-guides/docker.md`

- Move content from `docs/README_DOCKER.md` to `docs/11-guides/docker.md`
- Add full YAML frontmatter (id, domain: guides, tags, related)
- Content is already in English and well-structured — minimal rewrite needed beyond adding frontmatter and cross-links
- Update the reference in `10-deployment/deployment.md` (line 161) to point to the new location
- Delete the original `docs/README_DOCKER.md`

### TASK_QUEUE_MIGRATION.md → `11-guides/task-queue-migration.md`

- Move content from `docs/TASK_QUEUE_MIGRATION.md` to `docs/11-guides/task-queue-migration.md`
- Add full YAML frontmatter
- Content is already in English and comprehensive — minimal rewrite needed
- Update any references from `10-deployment/deployment.md` or `03-processing/` docs to point to the new location
- Delete the original `docs/TASK_QUEUE_MIGRATION.md`

### SWAGGER_README.md — Delete

- Content already absorbed into `docs/99-reference/swagger.md` (which has frontmatter and is cross-linked)
- The original file is a deprecated stub with a redirect notice
- Delete `docs/SWAGGER_README.md` entirely — no content loss

### RUN.md — Delete

- Content already absorbed into `docs/99-reference/run-guide.md` (translated to English, has frontmatter)
- The original file is a deprecated stub in Russian with a redirect notice
- Delete `docs/RUN.md` entirely — no content loss

### commands.md — Keep as internal context

- `commands.md` is an internal agent reference (build commands, test commands, database CLI)
- It is NOT user-facing documentation — it lives in `.ai/context/` for agent consumption
- Do NOT move it into the docs structure
- No changes needed

### KiloCode's Discretion

- Exact frontmatter fields (tags, related) for the new guide files — follow the pattern established by existing docs in adjacent sections
- Cross-link wording and placement — follow existing conventions
- Whether to add a `README.md` index file to `11-guides/` — optional, add if it helps navigation

</decisions>

<specifics>
## Specific Ideas

- The `10-deployment/deployment.md` already references `README_DOCKER.md` at line 161 — this cross-link must be updated as part of the migration
- The `99-reference/` folder already exists and holds `swagger.md` and `run-guide.md` — these are the already-integrated versions of the deprecated files
- The doc-maintenance-rules specify `99-reference/` for guides and external docs — the new `11-guides/` section is a deliberate exception for operational guides that are more "how-to" than "reference"
- All new files must comply with doc-maintenance-rules: YAML frontmatter, `## Purpose` section, English-only, cross-links via relative paths

</deferred>

## Deferred Ideas

- Content restructuring or rewriting of the Docker or task queue migration content — this phase only moves and adds frontmatter, not content revision
- Adding a `README.md` index for the `11-guides/` section — can be done in a future doc maintenance pass
- Reviewing whether `99-reference/` contents should be reorganized — out of scope for this phase

</deferred>

---

_Phase: 01-legacy-docs-integration_
_Context gathered: 2026-05-19_
