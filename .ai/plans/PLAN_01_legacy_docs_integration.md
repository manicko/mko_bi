---
phase: 01
name: Legacy Documentation Integration
wave: 1
depends_on: []
files_modified:
  - docs/11-guides/docker.md
  - docs/11-guides/task-queue-migration.md
  - docs/10-deployment/deployment.md
files_deleted:
  - docs/README_DOCKER.md
  - docs/TASK_QUEUE_MIGRATION.md
  - docs/SWAGGER_README.md
  - docs/RUN.md
autonomous: true
risk: low
---

# Phase 01: Legacy Documentation Integration

## Purpose

Integrate 4 orphaned documentation files from `docs/` root into the structured documentation system. Two files hold unique content that must be migrated; two are deprecated stubs that can be deleted.

## Context

The `docs/` root contains legacy files from a previous documentation structure. The current system uses numbered domain folders (`00-overview/`, `01-auth/`, etc.) with YAML frontmatter, English-only content, and cross-links via relative paths. These files don't conform.

**Locked decisions (from DECISION_01.md):**
- Create `11-guides/` section for operational/how-to content
- `README_DOCKER.md` → `docs/11-guides/docker.md` (add frontmatter, cross-links)
- `TASK_QUEUE_MIGRATION.md` → `docs/11-guides/task-queue-migration.md` (add frontmatter, cross-links)
- `SWAGGER_README.md` — delete (content already in `99-reference/swagger.md`)
- `RUN.md` — delete (content already in `99-reference/run-guide.md`)
- `commands.md` — keep as-is (internal agent reference, not user-facing)
- Update cross-reference in `docs/10-deployment/deployment.md` line 160

## Tasks

<task id="01" name="Create 11-guides/ section directory">
Create the `docs/11-guides/` directory. This is the new home for operational/how-to guides that don't belong to a specific domain folder.

No index/README needed at this time (deferred per DECISION_01.md).
</task>

<task id="02" name="Migrate README_DOCKER.md to 11-guides/docker.md">
1. Create `docs/11-guides/docker.md` with full YAML frontmatter:
   - `id: docker-guide`
   - `domain: guides`
   - `tags: [docker, deployment, containers, development, testing, production]`
   - `related: [deployment, run-guide, task-queue-migration]`
2. Copy content from `docs/README_DOCKER.md` — it's already in English and well-structured
3. Add `## Purpose` section at the top (after frontmatter): "Docker setup and operations guide for the mkobi BI Dashboard system."
4. Add cross-links section at the bottom:
   ```
   ## Cross-References
   - [Deployment](../10-deployment/deployment.md) — Production deployment options
   - [Run Guide](../99-reference/run-guide.md) — Application configuration and startup
   - [Task Queue Migration](task-queue-migration.md) — Redis/RQ migration for background processing
   ```
5. Verify all internal links still work (none expected — the file has no cross-links to other docs)
</task>

<task id="03" name="Migrate TASK_QUEUE_MIGRATION.md to 11-guides/task-queue-migration.md">
1. Create `docs/11-guides/task-queue-migration.md` with full YAML frontmatter:
   - `id: task-queue-migration`
   - `domain: guides`
   - `tags: [task-queue, redis, rq, migration, background-processing, production]`
   - `related: [processing-api, deployment, docker-guide]`
2. Copy content from `docs/TASK_QUEUE_MIGRATION.md` — it's already in English and comprehensive
3. Add `## Purpose` section at the top (after frontmatter): "Migration plan for transitioning the task queue from in-memory asyncio.Queue to persistent Redis/RQ."
4. Update the existing cross-references section at the bottom of the file:
   - Change `[Processing API](processing-api.md)` → `[Processing API](../03-processing/processing-api.md)`
   - Change `[Overview](../00-overview/overview.md)` → `[System Overview](../00-overview/overview.md)`
   - Change `[Deployment](../10-deployment/deployment.md)` → keep as-is (already correct relative path from root, but needs to be `../10-deployment/deployment.md` from new location)
   - Change `[Backend Architecture](../06-backend/architecture.md)` → keep as-is (already correct relative path from root, but needs to be `../06-backend/architecture.md` from new location)
   - Change `[Security Overview](../08-security/)` → `[Security Overview](../08-security/security-overview.md)`
   - Add: `- [Docker Guide](docker-guide.md) — Docker deployment and Redis configuration`
5. Verify all cross-links use relative paths and point to correct locations
</task>

<task id="04" name="Update cross-references in deployment.md">
In `docs/10-deployment/deployment.md`:
1. Line 160: Change `See \`README_DOCKER.md\` for the full Docker specification.` → `See [Docker Guide](../11-guides/docker.md) for the full Docker specification.`
2. Line 289: The cross-reference `[Task Queue](../03-processing/task-queue.md)` is already correct — no change needed (the task-queue.md in 03-processing already exists and is the right target)
3. Verify no other references to the deleted files exist in deployment.md
</task>

<task id="05" name="Delete deprecated stub files">
Delete the following files (content already absorbed elsewhere):
1. `docs/README_DOCKER.md` — content migrated to `11-guides/docker.md`
2. `docs/TASK_QUEUE_MIGRATION.md` — content migrated to `11-guides/task-queue-migration.md`
3. `docs/SWAGGER_README.md` — deprecated stub, content in `99-reference/swagger.md`
4. `docs/RUN.md` — deprecated stub (Russian), content in `99-reference/run-guide.md`

Verify each file has a redirect notice or is confirmed as fully absorbed before deletion.
</task>

<task id="06" name="Update SPEC.md documentation index">
In `docs/SPEC.md`, update the Documentation Index:
1. Under the "Reference" section, remove:
   - `- [Docker Setup](README_DOCKER.md) — Multi-stage Dockerfile, Docker Compose, quick start.`
   - `- [Task Queue Migration](TASK_QUEUE_MIGRATION.md) — In-memory TaskQueue to Redis/RQ migration plan.`
   - `- [Swagger UI Guide](SWAGGER_README.md) — Using the interactive API docs at \`/docs/\`.`
2. Add under a new "Guides" section (after "Deployment" and before "Reference"):
   ```
   ### Guides
   - [Docker Setup](11-guides/docker.md) — Multi-stage Dockerfile, Docker Compose, quick start.
   - [Task Queue Migration](11-guides/task-queue-migration.md) — In-memory TaskQueue to Redis/RQ migration plan.
   ```
3. Verify the Reference section still has the correct entries for `99-reference/swagger.md` and `99-reference/run-guide.md`
</task>

## Validation Criteria

- [ ] `docs/11-guides/` directory exists
- [ ] `docs/11-guides/docker.md` exists with valid YAML frontmatter (id, domain, tags, related)
- [ ] `docs/11-guides/task-queue-migration.md` exists with valid YAML frontmatter
- [ ] Both new files have `## Purpose` section
- [ ] Both new files have `## Cross-References` section with relative paths
- [ ] `docs/10-deployment/deployment.md` line 160 references `11-guides/docker.md` (not `README_DOCKER.md`)
- [ ] `docs/README_DOCKER.md` deleted
- [ ] `docs/TASK_QUEUE_MIGRATION.md` deleted
- [ ] `docs/SWAGGER_README.md` deleted
- [ ] `docs/RUN.md` deleted
- [ ] `docs/SPEC.md` updated with Guides section
- [ ] `docs/commands.md` untouched (internal reference, not modified)
- [ ] All cross-links in new files use relative paths
- [ ] No broken references to deleted files remain in any docs

## Must Haves (goal-backward validation)

- All 4 orphaned files are either migrated or deleted (none left in `docs/` root)
- New guide files follow the doc-maintenance-rules (frontmatter, Purpose, English-only, cross-links)
- Cross-references in `deployment.md` point to new locations
- SPEC.md index reflects the new structure
- No content loss — all unique content preserved in new locations

## Risk Assessment

- **Risk: LOW** — Documentation-only changes, no code modifications
- **Rollback: Trivial** — Git revert restores all deleted files
- **Coupling: Minimal** — Only `deployment.md` and `SPEC.md` cross-references affected
