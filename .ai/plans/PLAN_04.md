# PLAN_04 (VALIDATED): Sequential Agent Workflow — Single Branch, One Commit Per Task

**Created:** 2026-06-08
**Domain:** Development workflow / Git safety / Agent role separation
**Confidence:** HIGH

---

## Summary

Multiple agents share ONE filesystem. Branch-per-task requires `checkout` which is global — too risky without worktree isolation.

**Solution: Stay on one branch. One commit per task. Orchestrator owns ALL git. Implementors are git-read-only.**

```
main

commit A (TASK_001): feat(auth): add JWT refresh token rotation
commit B (TASK_002): fix(api): validate email format on registration
commit C (TASK_003): feat(upload): add CSV file type detection
...
```

Each task = one clean commit on the current branch. No branches, no merges, no branch cleanup.

**Core principles:**
1. Never leave the current branch
2. One task = one commit
3. Implementors never touch git write commands
4. Orchestrator is the sole git operator

---

## 1. Problem Statement

### Current issues

| Symptom | Root cause |
|---------|-----------|
| `git add*`: allow on implementor | Can stage anything, including unrelated files |
| `git commit *`: allow | Commits without orchestrator review |
| `git commit --amend*`: allow | Can rewrite history |
| `git checkout *`: ask | Can ask to switch branches — dangerous on shared FS |
| `git clean *`: ask | Can delete untracked files |
| `git stash *`: ask | Stash crosses worktree boundaries |
| `implementor.md` does both orchestration AND implementation | Role confusion |
| `implement-multiple_tasks.md` duplicates git rules from agent permissions | Bloated command |

### Why not branch-per-task?

`git checkout` is global — switching branches changes the working tree for ALL agents and the orchestrator simultaneously. Without VS Code Agent Manager worktrees (separate filesystems), branches are unsafe. Merge adds complexity and another failure point.

Single branch eliminates: branch creation, checkout, merge, merge conflict resolution, branch deletion.

---

## 2. Solution Architecture

### 2.1 Two-Agent Split

| Agent | Mode | Git Access | Responsibilities |
|-------|------|------------|------------------|
| **implementor-orchestrator** | `primary` | git add, commit, restore (NO checkout/branch/merge/push) | Spawns implementors, reviews diffs, commits, discards on failure |
| **implementor** | `subagent` | Read-only git (diff, log, show, status) | Edits files, runs tests, reports results |

### 2.2 Sequential Task Loop

```
For each task (one at a time):

  ORCHESTRATOR:
    1. Read task file from .ai/tasks/todo/
    2. Spawn implementor subagent via Task tool
    3. Wait for implementor to finish

  IMPLEMENTOR (subagent):
    4. Edit files (implementation)
    5. Run tests / lint / type checks
    6. Run git diff HEAD --stat to verify own changes
    7. Report: files changed, test results

  ORCHESTRATOR:
    8. git diff HEAD --stat               ← review what changed
    9. If changes look wrong:
        git restore .                     ← discard all uncommitted changes
        Re-spawn implementor with error details
    10. If changes look good:
        git add <specific files>          ← stage ONLY task-related files
        git commit -m "{type}({scope}): {description}" -m "Task: {TASK_FILE_NAME}"
    11. Continue to next task
```

### 2.3 Git command comparison

| Operation | Branch-per-task (old) | Single branch (new) |
|-----------|----------------------|---------------------|
| Start task | `git checkout -b task/...` | nothing |
| Implement | edit files | edit files |
| Review | `git diff --stat` | `git diff HEAD --stat` |
| Commit | `git add` + `git commit` | `git add` + `git commit` |
| Integrate | `git checkout main` + `git merge --no-ff` + `git branch -d` | nothing |
| **Total git ops per task** | **6** | **3** |

---

## 3. Permission Model

### 3.1 Permission Ordering — "Last Matching Rule Wins"

Kilo evaluates rules top-to-bottom. For a given command, ALL matching patterns are collected. The **LAST** matching pattern in list order determines the action.

**Correct structure:**
```yaml
bash:
    "*": allow                    # matches everything (first match for all)
    "git status*": allow          # redundant but explicit
    "git diff*": allow
    ...
    "git add*": deny              # LAST match for git add → DENY wins
    "git commit*": deny           # LAST match for git commit → DENY wins
    "shutdown*": deny             # DENY wins over "*": allow
```

For `git add file.py`:
1. Matches `"*": allow` → allow
2. Matches `"git add*": deny` → deny
3. **Last match: deny** → command blocked ✓

For `ls -la`:
1. Matches `"*": allow` → allow
2. No other match
3. **Last match: allow** → command permitted ✓

### 3.2 Implementor — Read-Only Git + Build/Test

Based on PLAN_03 Section 4.7, with all git write changed to DENY.

**Changes from current `implementor.md`:**
- `mode: all` → `mode: subagent`
- `git add*`: allow → **deny**
- `git commit *`: allow → **deny**
- `git commit --amend*`: allow → **deny**
- `git checkout *`: ask → **deny**
- `git clean *`: ask → **deny**
- `git stash *`: ask → **deny**
- Add: `git merge*`: deny
- Add: `git restore*`: deny
- Add: `git branch*`: deny (no branch operations at all)
- Add: `git reflog*`: deny (investigation tool, not needed)
- Add full PLAN_03 ASK list (rm, docker down, kubectl delete, etc.)
- Add full PLAN_03 DENY list (shutdown, format, etc.)
- `task: allow` → `task: deny`

**Complete permission block:**
```yaml
permission:
  read:
    "*": allow
    "*.env": allow
    "C:\\py_dev\\mkobi\\.env": allow
    "C:\\py_dev\\mkobi\\docker\\.env": allow
    "C:\\py_dev\\mkobi\\docker\\.env*": allow
    "C:\\py_dev\\mkobi\\docker\\.env.development": allow
    "C:\\py_dev\\mkobi\\docker\\.env.production": allow
  grep: allow
  glob: allow
  edit:
    "*": allow
    "*.env": allow
    "C:\\py_dev\\mkobi\\docker\\.env": allow
    "C:\\py_dev\\mkobi\\.env": allow
    "C:\\py_dev\\mkobi\\docker\\.env*": allow
    "C:\\py_dev\\mkobi\\docker\\.env.development": allow
    "C:\\py_dev\\mkobi\\docker\\.env.production": allow
  bash:
    # === DEFAULT: allow (first match for everything) ===
    "*": allow

    # === READ-ONLY GIT ===
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git show*": allow

    # === BUILD & TEST ===
    "uv *": allow
    "pytest*": allow
    "ruff*": allow
    "mypy*": allow
    "alembic*": allow
    "npm test*": allow
    "npm run lint*": allow
    "npm run typecheck*": allow
    "npm run build": allow

    # === DOCKER ===
    "docker compose": allow
    "docker compose config*": allow
    "docker compose up*": allow
    "docker compose down*": allow
    "docker compose ps*": allow
    "docker compose logs*": allow
    "docker compose build*": allow
    "docker compose restart*": allow
    "docker compose exec*": allow
    "docker compose run*": allow
    "docker ps*": allow
    "docker logs*": allow
    "docker build*": allow
    "docker run*": allow
    "docker exec*": allow
    "docker inspect*": allow
    "docker network*": allow
    "docker volume*": allow
    "docker system*": allow

    # === K8S: read-only ===
    "kubectl get*": allow
    "kubectl logs*": allow
    "kubectl top*": allow

    # === DB: verification ===
    "psql*": allow
    "redis-cli*": allow

    # === UTILITIES ===
    "curl*": allow

    # === ASK: potentially destructive git ===
    "git reset *": ask
    "git checkout *": ask
    "git clean *": ask
    "git stash *": ask
    "git rebase *": ask
    "git push *": ask
    "git commit --amend*": ask
    "git cherry-pick *": ask
    "git branch*": ask
    "git merge*": ask
    "git restore*": ask
    "git tag -d*": ask
    "git gc --prune=now*": ask
    "git update-ref -d*": ask

    # === ASK: potentially destructive filesystem ===
    "rm -rf *": ask
    "rm -r *": ask
    "Remove-Item -Recurse -Force *": ask
    "Remove-Item -Force *": ask
    "dd if=* of=*": ask
    "shred *": ask
    "wipe *": ask
    "truncate -s 0 *": ask
    "chmod -R 000 *": ask
    "chmod -R 777 *": ask
    "chown -R *": ask

    # === ASK: potentially destructive Docker ===
    "docker compose down --volumes*": ask
    "docker compose down -v*": ask
    "docker volume rm*": ask
    "docker volume prune*": ask
    "docker system prune -a*": ask
    "docker rm -f*": ask
    "docker rmi -f*": ask
    "docker image prune -a*": ask
    "docker container prune*": ask
    "docker network prune*": ask

    # === ASK: potentially destructive K8s ===
    "kubectl describe*": ask
    "kubectl delete *": ask
    "kubectl delete pod*": ask
    "kubectl delete deployment*": ask
    "kubectl delete service*": ask
    "kubectl delete pvc*": ask
    "kubectl drain *": ask
    "kubectl cordon *": ask
    "kubectl apply --force*": ask
    "kubectl rollout undo*": ask
    "kubectl exec*": ask

    # === ASK: potentially destructive DB ===
    "psql -c \"DROP *\"": ask
    "psql -c \"TRUNCATE *\"": ask
    "psql -c \"DELETE FROM *\"": ask
    "psql -c \"ALTER *\"": ask
    "psql -c \"GRANT *\"": ask
    "psql -c \"REVOKE *\"": ask
    "redis-cli FLUSHDB*": ask
    "redis-cli DEL *": ask

    # === ASK: potentially destructive system ===
    "kill -9 *": ask
    "killall *": ask
    "pkill *": ask
    "systemctl stop *": ask
    "systemctl disable *": ask

    # === ASK: potentially destructive packages ===
    "pip uninstall *": ask
    "npm uninstall *": ask
    "uv pip uninstall *": ask

    # === ASK: potentially destructive network ===
    "curl -X DELETE*": ask
    "curl -X PUT*": ask
    "curl -X POST*": ask

    # === DENY: irreversible git ===
    "git reset --hard*": deny
    "git clean -fd*": deny
    "git clean -fdx*": deny
    "git push --force*": deny
    "git push --force-with-lease*": deny
    "git filter-branch*": deny
    "git filter-repo*": deny
    "git reflog*": deny

    # === DENY: git write (orchestrator's job) ===
    "git add*": deny
    "git commit*": deny

    # === DENY: destructive filesystem ===
    "format*": deny
    "diskpart*": deny
    "mkfs*": deny
    "mv * /dev/null": deny
    "fdisk*": deny
    "parted*": deny

    # === DENY: system ===
    "shutdown*": deny
    "reboot*": deny
    "halt*": deny
    "poweroff*": deny
    "crontab -r*": deny
    "iptables*": deny
    "ufw*": deny
    "reg delete*": deny
    "Set-ExecutionPolicy*": deny

    # === DENY: dangerous Docker ===
    "docker system prune --volumes -a*": deny

    # === DENY: dangerous K8s ===
    "kubectl delete namespace*": deny
    "kubectl delete pv*": deny

    # === DENY: dangerous DB ===
    "redis-cli FLUSHALL*": deny

  todoread: allow
  todowrite: allow
  task: deny
  websearch: allow
  webfetch: allow
```

### 3.3 Orchestrator — Add + Commit + Restore Only

New agent. Git permissions are intentionally minimal — only what's needed for the single-branch workflow.

**Complete permission block:**
```yaml
permission:
  read: allow
  grep: allow
  glob: allow
  task: allow           # Spawn implementor subagents
  todoread: allow
  todowrite: allow

  edit:
    "*.yaml": allow     # Update task files, order files
    "*.md": allow       # Update plan/progress docs
    "*": deny

  bash:
    # === DEFAULT: allow ===
    "*": allow

    # === GIT: orchestrator needs only add, commit, restore ===
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git show*": allow
    "git add*": allow
    "git commit*": allow
    "git restore*": allow

    # === BUILD & TEST: for verification ===
    "uv run pytest*": allow
    "uv run ruff check*": allow
    "uv run mypy*": allow
    "npm run build": allow
    "npm run test": allow
    "npm run lint": allow

    # === DOCKER: read-only verification ===
    "docker compose": allow
    "docker compose config*": allow
    "docker compose ps*": allow
    "docker compose logs*": allow
    "docker ps*": allow
    "docker logs*": allow
    "docker inspect*": allow

    # === K8S: read-only ===
    "kubectl get*": allow
    "kubectl describe*": allow
    "kubectl logs*": allow

    # === UTILITIES ===
    "curl*": allow

    # === ASK: potentially destructive git ===
    "git reset *": ask
    "git checkout *": ask
    "git clean *": ask
    "git stash *": ask
    "git rebase *": ask
    "git push *": ask
    "git commit --amend*": ask
    "git cherry-pick *": ask
    "git branch*": ask
    "git merge*": ask
    "git tag -d*": ask
    "git gc --prune=now*": ask
    "git update-ref -d*": ask

    # === ASK: potentially destructive filesystem ===
    "rm -rf *": ask
    "rm -r *": ask
    "Remove-Item -Recurse -Force *": ask
    "Remove-Item -Force *": ask
    "dd if=* of=*": ask
    "shred *": ask
    "wipe *": ask
    "truncate -s 0 *": ask
    "chmod -R 000 *": ask
    "chmod -R 777 *": ask
    "chown -R *": ask

    # === ASK: potentially destructive Docker ===
    "docker compose down*": ask
    "docker compose down --volumes*": ask
    "docker compose down -v*": ask
    "docker volume rm*": ask
    "docker volume prune*": ask
    "docker system prune -a*": ask
    "docker rm -f*": ask
    "docker rmi -f*": ask
    "docker image prune -a*": ask
    "docker container prune*": ask
    "docker network prune*": ask

    # === ASK: potentially destructive K8s ===
    "kubectl delete *": ask
    "kubectl delete pod*": ask
    "kubectl delete deployment*": ask
    "kubectl delete service*": ask
    "kubectl delete pvc*": ask
    "kubectl drain *": ask
    "kubectl cordon *": ask
    "kubectl apply --force*": ask
    "kubectl rollout undo*": ask
    "kubectl exec*": ask

    # === ASK: potentially destructive DB ===
    "psql -c \"DROP *\"": ask
    "psql -c \"TRUNCATE *\"": ask
    "psql -c \"DELETE FROM *\"": ask
    "psql -c \"ALTER *\"": ask
    "psql -c \"GRANT *\"": ask
    "psql -c \"REVOKE *\"": ask
    "redis-cli FLUSHDB*": ask
    "redis-cli DEL *": ask

    # === ASK: potentially destructive system ===
    "kill -9 *": ask
    "killall *": ask
    "pkill *": ask
    "systemctl stop *": ask
    "systemctl disable *": ask

    # === ASK: potentially destructive packages ===
    "pip uninstall *": ask
    "npm uninstall *": ask
    "uv pip uninstall *": ask

    # === ASK: potentially destructive network ===
    "curl -X DELETE*": ask
    "curl -X PUT*": ask
    "curl -X POST*": ask

    # === DENY: irreversible git ===
    "git reset --hard*": deny
    "git clean -fd*": deny
    "git clean -fdx*": deny
    "git push --force*": deny
    "git push --force-with-lease*": deny
    "git filter-branch*": deny
    "git filter-repo*": deny
    "git reflog*": deny

    # === DENY: destructive filesystem ===
    "format*": deny
    "diskpart*": deny
    "mkfs*": deny
    "mv * /dev/null": deny
    "fdisk*": deny
    "parted*": deny

    # === DENY: system ===
    "shutdown*": deny
    "reboot*": deny
    "halt*": deny
    "poweroff*": deny
    "crontab -r*": deny
    "iptables*": deny
    "ufw*": deny
    "reg delete*": deny
    "Set-ExecutionPolicy*": deny

    # === DENY: dangerous Docker ===
    "docker system prune --volumes -a*": deny

    # === DENY: dangerous K8s ===
    "kubectl delete namespace*": deny
    "kubectl delete pv*": deny

    # === DENY: dangerous DB ===
    "redis-cli FLUSHALL*": deny
```

---

## 4. Implementation Steps

### Step 1: Create  `implementor-subagent.md` based on `implementor.md`

**File:** `.kilo/agents/implementor.md`

1. `mode: all` → `mode: subagent`
2. Replace `permission.bash` block with Section 3.2
3. `task: allow` → `task: deny`
4. Add to agent body:
   - "You have NO git write access. You are a subagent that edits files and runs tests."
5. Remove orchestration responsibilities

### Step 2: Create `implementor-orchestrator.md` based on `implementor.md`

**File:** `.kilo/agents/implementor-orchestrator.md` (NEW)

**Mode:** `primary`

**Permission:** Section 3.3

**Agent body includes:**
- Sequential task loop (Section 2.2)
- "Always use `git add <specific files>`, NEVER `git add -A` or `git add .`"
- "If changes look wrong: `git restore .` then re-spawn implementor"
- "Read `order.yaml` for execution order"

### Step 3: Rewrite `implement-multiple_tasks.md` -> `implement-multiple-tasks.md`

**File:** `.kilo/commands/implement/implement-multiple_tasks.md`

1. `agent: planner` → `agent: implementor-orchestrator`
2. Remove `⛔ GIT USAGE POLICY` section
3. Remove `⛔ GIT RULES — FORBIDDEN FOREVER` from subagent prompt
4. Remove commit step from subagent prompt (Step 9)
5. Add orchestrator review + commit after implementor returns:

```
## 3.Z Review and Commit (after implementor returns)
git diff HEAD --stat
# If bad: git restore . and re-spawn implementor
# If good:
git add <specific files from diff>
git commit -m "{type}({scope}): {description}" -m "Task: {TASK_FILE_NAME}"
```

6. Update success criteria: "Git commit created per task by orchestrator"


---

## 5. File Change Summary

| # | File | Action | Key Changes |
|---|------|--------|-------------|
| 1 | `.kilo/agents/implementor.md` | **Rewrite** | `mode: subagent`. All git write → DENY. Read-only git kept. Full PLAN_03 ASK/DENY. `task: deny`. |
| 2 | `.kilo/agents/implementor-orchestrator.md` | **Create** | New primary agent. Git: add/commit/restore only. No checkout/branch/merge/push. Sequential task loop. |
| 3 | `.kilo/commands/implement/implement-multiple_tasks.md` | **Rewrite** | `agent: implementor-orchestrator`. Remove git rules. Add orchestrator review + commit. |

---

## 6. Safety Properties

| Before | After |
|--------|-------|
| `git add*`: allow | `git add*` → DENY |
| `git commit *`: allow | `git commit*` → DENY |
| `git commit --amend*`: allow | `git commit --amend*` → DENY |
| `git checkout *`: ask | `git checkout*` → DENY |
| `git clean *`: ask | `git clean*` → DENY |
| `git stash *`: ask | `git stash*` → DENY |
| `task: allow` | `task` → DENY |
| No PLAN_03 risk inventory | Full PLAN_03 DENY + ASK lists |
| Git rules duplicated in command | Git rules ONLY in agent permissions |
| 6 git ops per task (branch+checkout+add+commit+merge+delete) | 3 git ops per task (add+commit+restore if needed) |

---

## 7. Limitations and Future Work

- **True parallelism**: Requires VS Code Agent Manager worktrees
- **Push to remote**: Neither agent pushes. User pushes manually.
- **Future**: Agent Manager worktrees for parallel implementors

---

## 8. Rollback Plan

```powershell
# Restore previous agent files
git checkout HEAD -- .kilo/agents/implementor.md .kilo/commands/implement/
# Remove new agent file
Remove-Item -Path ".kilo/agents/implementor-orchestrator.md" -Force
```
