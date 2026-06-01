---
name: audit-validate
description: Validate audit findings for safety, consistency, and applicability without code changes
agent: validator
alwaysApply: false
problems-only: true
---

# Audit Findings Validation Workflow

## Output Mode

`problems-only: true` — **the validator reports only rejected, merged, or reclassified findings, and cross-phase conflicts.**

- **Do NOT** restate findings that pass validation unchanged.
- **Do NOT** produce a clean bill of health for each phase.
- Only report: rejected findings (with reason), merged findings (with mapping), reclassified findings (old type → new type), cross-phase conflicts (same root cause found by multiple phases), and rollout safety issues (dependency problems).
- If all findings across all phases pass validation with no conflicts, write: `All audit findings validated. No rejections, merges, or conflicts.`
- If you need to start or stop docker environment to check functional or run test you should run it following the documantation instruction in dev mode BUT you mast return it to the same status as before - running or stopped
---

## Objective

Validate audit findings for architectural safety and consistency:

- `[SPEC-DEVIATION]` — verify the deviation is real and determine whether code or docs should change.
- `[BEST-PRACTICE]` — verify feasibility and ROI; reject if overengineered.
- `[DOC-UPDATE]` — verify the proposed doc change is accurate.

Separate validated findings into:

- **Mandatory fixes** — security, data loss, correctness issues.
- **Advisory recommendations** — improvements worth doing but not blocking.

---

## Constraints

- DO NOT modify source code.
- DO NOT generate implementation code.
- DO NOT redesign architecture.
- DO NOT create speculative refactors.
- ONLY validate safety, consistency, applicability, and survivability.
- Prefer conservative decisions.
- Prefer rejection over unsafe approval.

---

## Discovery Stage

Before validating findings, understand the project context:

1. Load all validated findings from previous audit phases.
2. Identify dependency relationships between findings.
3. Assess architectural stability of affected modules.
4. Verify findings remain applicable to current codebase state.

---

## Workflow

### Step 1 — Load Audit Findings

Extract: findings, recommendations, risks, affected modules, proposed architectural changes.

### Step 2 — Cross-Finding Dependency Analysis

Analyze: architectural boundaries, dependency chains, semantic stability, integration points, coupling hotspots.

- **If two findings from different phases address the same root cause**, flag as a merge candidate. Report which finding IDs overlap and which should be merged.
- **If findings from different phases conflict** (one says "add abstraction", another says "remove abstraction"), flag the conflict and recommend resolution. This is a CRITICAL validation issue.

### Step 3 — Validate Findings

For each finding, verify:

- Relevance to current architecture.
- Technical correctness (is the problem real?).
- Architectural consistency (does the fix fit?).
- Operational value (is the fix worth doing?).
- Current applicability (is the codebase still in this state?).

Mark findings as invalid if:

- Already implemented.
- Stale due to architecture changes.
- Duplicate of other findings.
- Low ROI.
- Architecture-breaking.
- Operationally unsafe.
- Overly complex.
- Conflicting with current direction.
- The code choice is better than proposed (reclassify as DOC-UPDATE).

DOCUMENT EACH REJECTION WITH A CLEAR REASON.

For `[SPEC-DEVIATION]` findings:
- Determine: should code change or docs change?
- If code is better than docs → reclassify as `[DOC-UPDATE]`.
- If docs are better than code → keep as spec deviation to fix.

For `[BEST-PRACTICE]` findings:
- Verify the recommendation is not overengineered.
- Verify ROI is positive for project scale.
- Reject if it adds complexity without clear maintenance benefit.

For `[DOC-UPDATE]` findings:
- Verify the proposed doc change accurately reflects code reality.

### Step 4 — Assess Rollout Safety

Validate: dependency graph correctness, rollout sequencing, task isolation, semantic targeting stability.

Detect: circular dependencies, hidden dependency chains, unsafe rollout ordering, fragile insertion points.

Reject rollout plans that: introduce excessive coupling, cannot survive unrelated code shifts, rely on fragile sequencing, create unsafe migration paths.

### Step 5 — Cross-Phase Evidence Verification

Verify that runtime evidence from one phase does not contradict another:

- If Phase 01 (backend) reports "all tests pass" but Phase 06 (tests) reports "test suite fails", there is a conflict. Report it.
- If Phase 04 (security) reports "all routes have auth" but Phase 01 (backend) shows unprotected routes, there is a conflict. Report it.
- If Phase 05 (docker) reports "containers start cleanly" but Phase 08 (config) reports "startup fails with missing config", there is a conflict. Report it.

---

## Report Output

Create normalized validated findings document: `.ai/audit/99-validation/{pahse_number}-{phase_name}-validated-findings.md`

The document preserves: original audit structure, domain grouping, severity levels, architectural context, affected modules.

The document excludes: rejected findings, stale findings, duplicate findings, unsafe recommendations, low-value recommendations.

### Report ONLY:

1. **Rejected findings** — finding ID, title, rejection reason.
2. **Merged findings** — original IDs, merged ID, rationale.
3. **Reclassified findings** — original type → new type, rationale.
4. **Cross-phase conflicts** — conflicting finding IDs, recommended resolution.
5. **Rollout safety issues** — dependency problems, ordering risks.
6. **Validated counts per phase** — mandatory vs advisory counts (brief summary).

Do NOT include: re-statements of findings that passed validation unchanged, per-phase "all clean" sections, positive confirmations.
