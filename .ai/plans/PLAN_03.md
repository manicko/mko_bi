# PLAN_03: Agent Permission Model — Risky Commands Audit & Restructuring

**Created:** 2026-06-07
**Domain:** Agent security permissions
**Scope:** All 7 agent roles in `.kilo/agents/`

---

## Summary

This plan defines a comprehensive permission model for all agent roles. The core principle: **allow everything by default (`*`: allow), explicitly list only risky commands as `ask` or `deny`**. Safe commands (e.g., `git add`, `git commit`, `git status`) don't need enumeration — they fall through to the wildcard allow.

---

## 1. Agent Roles Summary

| # | Agent | Role Type | Bash Needs | Edit Needs |
|---|-------|-----------|------------|------------|
| 1 | **auditor** | Read-only analysis | Read-only (inspect running services) | `.md`, `.yaml`, `.yml` only |
| 2 | **audit-executor** | Read-only analysis | Read-only (inspect running services) | `.md`, `.yaml`, `.yml` only |
| 3 | **audit-orchestrator** | Coordination | Minimal (launch subagents) | `.md`, `.yaml`, `.yml` only |
| 4 | **researcher** | Research + docs | Read-only (verify tooling) | `.md`, `.mdx`, `.yaml`, `.yml` only |
| 5 | **planner** | Planning + task generation | Read-only (verify tooling) | `.md`, `.mdx`, `.yaml`, `.yml` only |
| 6 | **validator** | Validation (tests/lint) | Test/lint/Docker/psql/readonly | `.md`, `.yaml`, `.yml` only |
| 7 | **implementor** | Full implementation | Full (git, build, test, Docker, file ops) | All files (`*`: allow) |

---

## 2. Complete Risky Commands Inventory

### 2.1 Git — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `git reset --hard*` | **DENY** | Irreversible data loss — discards all uncommitted changes permanently |
| `git clean -fd*` | **DENY** | Irreversibly deletes untracked files and directories |
| `git clean -fdx*` | **DENY** | Same as above + removes gitignored files (could delete `.env`, build artifacts) |
| `git push --force*` | **DENY** | Overwrites remote history, can destroy team's work |
| `git push --force-with-lease*` | **DENY** | Safer force push but still dangerous for production branches |
| `git reset *` | **ASK** | Resets index — can be soft or hard, needs confirmation |
| `git checkout *` | **ASK** | Discards working directory changes for files, can lose work |
| `git clean *` | **ASK** | Removes untracked files — less dangerous than `-fd` but still destructive |
| `git stash *` | **ASK** | Stashes changes — generally safe but `git stash drop` is destructive |
| `git rebase *` | **ASK** | Rewrites history — dangerous on shared branches |
| `git push *` | **ASK** | Pushes to remote — needs confirmation to avoid pushing to wrong branch |
| `git commit --amend*` | **ASK** | Rewrites last commit — dangerous if already pushed |
| `git cherry-pick *` | **ASK** | Applies commits from other branches — can cause conflicts |
| `git branch -D*` | **ASK** | Force-deletes a branch — unmerged work is lost |
| `git branch -d*` | **ASK** | Deletes a branch — safe if merged, but confirm |
| `git tag -d*` | **ASK** | Deletes a tag — could affect release tracking |
| `git reflog expire*` | **DENY** | Destroys reflog — eliminates recovery mechanism |
| `git gc --prune=now*` | **ASK** | Aggressive garbage collection — can remove recoverable objects |
| `git filter-branch*` | **DENY** | Rewrites entire history — extremely dangerous |
| `git filter-repo*` | **DENY** | Rewrites entire history — extremely dangerous |
| `git update-ref -d*` | **ASK** | Deletes refs — can remove branch/tag references |

### 2.2 File System — Risky Commands (bash / PowerShell)

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `rm -rf *` | **ASK** | Recursive force delete — irreversible data loss |
| `rm -r *` | **ASK** | Recursive delete — dangerous with wildcards |
| `Remove-Item -Recurse -Force *` | **ASK** | PowerShell equivalent of `rm -rf` |
| `Remove-Item -Force *` | **ASK** | Force delete in PowerShell |
| `del /s /q *` | **ASK** | Silent recursive delete in cmd |
| `rd /s /q *` | **ASK** | Silent recursive directory removal in cmd |
| `format *` | **DENY** | Formats a drive — catastrophic data loss |
| `diskpart *` | **DENY** | Disk partitioning — can destroy data |
| `mkfs*` | **DENY** | Creates filesystem — destroys existing data |
| `dd if=* of=*` | **ASK** | Direct disk write — can overwrite anything |
| `shred *` | **ASK** | Secure file deletion — irreversible |
| `wipe *` | **ASK** | Secure file deletion — irreversible |
| `truncate -s 0 *` | **ASK** | Empties file content — data loss |
| `> *` (redirect overwrite) | **ASK** | Overwrites file content — data loss if important file |
| `mv * /dev/null` | **DENY** | Moves files to void — irreversible |
| `chmod -R 000 *` | **ASK** | Removes all permissions — can lock out access |
| `chmod -R 777 *` | **ASK** | Opens all permissions — security risk |
| `chown -R *` | **ASK** | Changes ownership — can break system access |

### 2.3 Docker — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `docker compose down --volumes*` | **ASK** | Removes volumes — data loss |
| `docker compose down -v*` | **ASK** | Removes volumes — data loss |
| `docker volume rm*` | **ASK** | Removes Docker volumes — data loss |
| `docker volume prune*` | **ASK** | Removes all unused volumes — data loss |
| `docker system prune -a*` | **ASK** | Removes all unused images, containers, networks — aggressive cleanup |
| `docker system prune --volumes -a*` | **DENY** | Removes everything including volumes — catastrophic |
| `docker rm -f*` | **ASK** | Force removes running containers |
| `docker rmi -f*` | **ASK** | Force removes images |
| `docker image prune -a*` | **ASK** | Removes all unused images |
| `docker container prune*` | **ASK** | Removes all stopped containers |
| `docker network prune*` | **ASK** | Removes all unused networks |
| `docker build --no-cache*` | **ALLOW** | Safe — just rebuilds without cache |
| `docker compose down*` | **ASK** | Stops and removes containers — confirm intent |

### 2.4 Kubernetes — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `kubectl delete *` | **ASK** | Deletes resources — can destroy deployments |
| `kubectl delete pod*` | **ASK** | Deletes pods — service disruption |
| `kubectl delete deployment*` | **ASK** | Deletes deployments — service disruption |
| `kubectl delete service*` | **ASK** | Deletes services — network disruption |
| `kubectl delete namespace*` | **DENY** | Deletes entire namespace — catastrophic |
| `kubectl delete pv*` | **DENY** | Deletes persistent volumes — data loss |
| `kubectl delete pvc*` | **ASK** | Deletes persistent volume claims — potential data loss |
| `kubectl drain *` | **ASK** | Drains node — service disruption |
| `kubectl cordon *` | **ASK** | Cordons node — scheduling impact |
| `kubectl apply --force*` | **ASK** | Force apply — can overwrite running state |
| `kubectl rollout undo*` | **ASK** | Rollback — service impact |
| `kubectl exec*` | **ASK** | Executes commands in pods — security risk |
| `kubectl describe*` | **ALLOW** | Read-only — safe |
| `kubectl get*` | **ALLOW** | Read-only — safe |
| `kubectl logs*` | **ALLOW** | Read-only — safe |
| `kubectl top*` | **ALLOW** | Read-only metrics — safe |

### 2.5 Database — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `psql -c "DROP *"` | **ASK** | Drops database objects — data loss |
| `psql -c "TRUNCATE *"` | **ASK** | Truncates tables — data loss |
| `psql -c "DELETE FROM *"` | **ASK** | Deletes rows — data loss |
| `psql -c "ALTER *"` | **ASK** | Alters schema — can break application |
| `psql -c "CREATE *"` | **ALLOW** | Creating objects — generally safe |
| `psql -c "SELECT *"` | **ALLOW** | Read-only — safe |
| `psql -c "GRANT *"` | **ASK** | Grants permissions — security implications |
| `psql -c "REVOKE *"` | **ASK** | Revokes permissions — can break access |
| `redis-cli FLUSHDB*` | **ASK** | Flushes current Redis database — data loss |
| `redis-cli FLUSHALL*` | **DENY** | Flushes all Redis databases — catastrophic data loss |
| `redis-cli DEL *` | **ASK** | Deletes keys — data loss |

### 2.6 Network — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `curl *` | **ALLOW** | Generally safe for GET requests |
| `curl -X DELETE*` | **ASK** | DELETE requests — destructive |
| `curl -X PUT*` | **ASK** | PUT requests — can overwrite resources |
| `curl -X POST*` | **ASK** | POST requests — can create/modify resources |
| `wget *` | **ALLOW** | Download — generally safe |
| `iptables *` | **DENY** | Firewall rules — can lock out access |
| `ufw *` | **DENY** | Firewall rules — can lock out access |
| `netstat *` | **ALLOW** | Read-only — safe |
| `nmap *` | **ALLOW** | Network scanning — informational |

### 2.7 System — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `shutdown *` | **DENY** | Shuts down the system |
| `reboot *` | **DENY** | Reboots the system |
| `halt *` | **DENY** | Halts the system |
| `poweroff *` | **DENY** | Powers off the system |
| `kill -9 *` | **ASK** | Force kills process — can cause data corruption |
| `killall *` | **ASK** | Kills all processes by name — dangerous |
| `pkill *` | **ASK** | Kills processes by pattern — dangerous |
| `systemctl stop *` | **ASK** | Stops system services — can disrupt system |
| `systemctl disable *` | **ASK** | Disables system services — can break boot |
| `service * stop` | **ASK** | Stops system services |
| `crontab -e*` | **ASK** | Edits cron — can schedule dangerous tasks |
| `crontab -r*` | **DENY** | Removes all cron jobs — can break scheduled tasks |
| `mount *` | **ASK** | Mounts filesystems — can affect system |
| `umount *` | **ASK** | Unmounts filesystems — can cause data loss |
| `fdisk *` | **DENY** | Disk partitioning — can destroy data |
| `parted *` | **DENY** | Disk partitioning — can destroy data |

### 2.8 Package Managers — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `pip uninstall *` | **ASK** | Removes Python packages — can break dependencies |
| `npm uninstall *` | **ASK** | Removes npm packages — can break dependencies |
| `uv pip uninstall *` | **ASK** | Removes Python packages — can break dependencies |
| `apt remove *` | **ASK** | Removes system packages — can break system |
| `apt purge *` | **ASK** | Removes system packages + config — can break system |
| `yum remove *` | **ASK** | Removes system packages — can break system |
| `brew uninstall *` | **ASK** | Removes packages — can break dependencies |

### 2.9 Environment / Config — Risky Commands

| Command | Risk Level | Reason |
|---------|-----------|--------|
| `export *` | **ALLOW** | Sets env vars for session — generally safe |
| `setx *` | **ASK** | Permanently sets env vars — persistent change |
| `reg add*` | **ASK** | Modifies Windows registry — can break system |
| `reg delete*` | **DENY** | Deletes registry keys — can break system |
| `Set-ExecutionPolicy*` | **DENY** | Changes PowerShell execution policy — security risk |

---

## 3. Risk Classification Summary

### DENY — Never allowed (irreversible / catastrophic)

| Category | Commands |
|----------|----------|
| Git | `git reset --hard*`, `git clean -fd*`, `git clean -fdx*`, `git push --force*`, `git push --force-with-lease*`, `git reflog expire*`, `git filter-branch*`, `git filter-repo*` |
| Filesystem | `format *`, `diskpart *`, `mkfs*`, `mv * /dev/null` |
| Docker | `docker system prune --volumes -a*` |
| Kubernetes | `kubectl delete namespace*`, `kubectl delete pv*` |
| Database | `redis-cli FLUSHALL*` |
| Network | `iptables *`, `ufw *` |
| System | `shutdown *`, `reboot *`, `halt *`, `poweroff *`, `crontab -r*`, `fdisk *`, `parted *` |
| Registry | `reg delete*`, `Set-ExecutionPolicy*` |

### ASK — Requires user approval (destructive but sometimes needed)

| Category | Commands |
|----------|----------|
| Git | `git reset *`, `git checkout *`, `git clean *`, `git stash *`, `git rebase *`, `git push *`, `git commit --amend*`, `git cherry-pick *`, `git branch -D*`, `git branch -d*`, `git tag -d*`, `git gc --prune=now*`, `git update-ref -d*` |
| Filesystem | `rm -rf *`, `rm -r *`, `Remove-Item -Recurse -Force *`, `Remove-Item -Force *`, `del /s /q *`, `rd /s /q *`, `dd if=* of=*`, `shred *`, `wipe *`, `truncate -s 0 *`, `chmod -R 000 *`, `chmod -R 777 *`, `chown -R *` |
| Docker | `docker compose down*`, `docker compose down --volumes*`, `docker compose down -v*`, `docker volume rm*`, `docker volume prune*`, `docker system prune -a*`, `docker rm -f*`, `docker rmi -f*`, `docker image prune -a*`, `docker container prune*`, `docker network prune*` |
| Kubernetes | `kubectl delete *`, `kubectl delete pod*`, `kubectl delete deployment*`, `kubectl delete service*`, `kubectl delete pvc*`, `kubectl drain *`, `kubectl cordon *`, `kubectl apply --force*`, `kubectl rollout undo*`, `kubectl exec*` |
| Database | `psql -c "DROP *"`, `psql -c "TRUNCATE *"`, `psql -c "DELETE FROM *"`, `psql -c "ALTER *"`, `psql -c "GRANT *"`, `psql -c "REVOKE *"`, `redis-cli FLUSHDB*`, `redis-cli DEL *` |
| Network | `curl -X DELETE*`, `curl -X PUT*`, `curl -X POST*` |
| System | `kill -9 *`, `killall *`, `pkill *`, `systemctl stop *`, `systemctl disable *`, `service * stop`, `crontab -e*`, `mount *`, `umount *` |
| Packages | `pip uninstall *`, `npm uninstall *`, `uv pip uninstall *`, `apt remove *`, `apt purge *`, `yum remove *`, `brew uninstall *` |
| Config | `setx *`, `reg add*` |

---

## 4. Per-Role Permission Matrix

### 4.1 auditor — Read-Only Analysis

**Philosophy:** Auditors only read and analyze. They should never modify production code or delete files. They may need bash to inspect running services (Docker, logs).

**bash permission model:**
```yaml
bash:
  # === READ-ONLY: always allowed ===
  "docker compose": allow
  "docker compose config*": allow
  "docker compose ps*": allow
  "docker compose logs*": allow
  "docker ps*": allow
  "docker logs*": allow
  "docker inspect*": allow
  "docker network*": allow
  "docker volume*": allow
  "docker system*": allow

  "kubectl get*": allow
  "kubectl describe*": allow
  "kubectl logs*": allow
  "kubectl top*": allow

  "psql -c \"SELECT*\"": allow
  "psql -c \"SHOW*\"": allow
  "redis-cli GET*": allow
  "redis-cli KEYS*": allow

  "curl*": allow
  "Get-ChildItem*": allow

  # === DENY: destructive git ===
  "git reset --hard*": deny
  "git clean -fd*": deny
  "git clean -fdx*": deny
  "git push --force*": deny
  "git push --force-with-lease*": deny
  "git filter-branch*": deny
  "git filter-repo*": deny
  "git reflog expire*": deny

  # === DENY: destructive filesystem ===
  "rm -rf*": deny
  "rm -r*": deny
  "Remove-Item -Recurse -Force*": deny
  "Remove-Item -Force*": deny
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

  # === ASK: potentially destructive (auditor shouldn't need these) ===
  "git reset *": ask
  "git checkout *": ask
  "git clean *": ask
  "git stash *": ask
  "git rebase *": ask
  "git push *": ask
  "git commit --amend*": ask
  "git cherry-pick *": ask
  "git branch -D*": ask
  "git branch -d*": ask
  "git tag -d*": ask
  "git gc --prune=now*": ask
  "git update-ref -d*": ask

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

  "psql -c \"DROP *\"": ask
  "psql -c \"TRUNCATE *\"": ask
  "psql -c \"DELETE FROM *\"": ask
  "psql -c \"ALTER *\"": ask
  "psql -c \"GRANT *\"": ask
  "psql -c \"REVOKE *\"": ask
  "redis-cli FLUSHDB*": ask
  "redis-cli DEL *": ask

  "kill -9 *": ask
  "killall *": ask
  "pkill *": ask
  "systemctl stop *": ask
  "systemctl disable *": ask
  "service * stop": ask
  "crontab -e*": ask
  "mount *": ask
  "umount *": ask

  "pip uninstall *": ask
  "npm uninstall *": ask
  "uv pip uninstall *": ask
  "apt remove *": ask
  "apt purge *": ask
  "yum remove *": ask
  "brew uninstall *": ask

  "setx *": ask
  "reg add*": ask

  "curl -X DELETE*": ask
  "curl -X PUT*": ask
  "curl -X POST*": ask

  "dd if=* of=*": ask
  "shred *": ask
  "wipe *": ask
  "truncate -s 0 *": ask
  "chmod -R 000 *": ask
  "chmod -R 777 *": ask
  "chown -R *": ask

  # === DEFAULT: allow everything else ===
  "*": allow
```

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.mdx": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.2 audit-executor — Read-Only Analysis (same as auditor)

**Philosophy:** Identical to auditor — read-only analysis, no production code modification.

**bash permission model:** Same as auditor (Section 4.1)

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.3 audit-orchestrator — Coordination Only

**Philosophy:** Orchestrator only coordinates subagents. Minimal bash needs (maybe Docker to check services). No file modifications except docs.

**bash permission model:**
```yaml
bash:
  # === READ-ONLY: always allowed ===
  "docker compose": allow
  "docker compose config*": allow
  "docker compose ps*": allow
  "docker compose logs*": allow
  "docker ps*": allow
  "docker logs*": allow
  "docker inspect*": allow

  "kubectl get*": allow
  "kubectl describe*": allow
  "kubectl logs*": allow

  "Get-ChildItem*": allow
  "curl*": allow

  # === DENY: all destructive (same as auditor) ===
  "git reset --hard*": deny
  "git clean -fd*": deny
  "git clean -fdx*": deny
  "git push --force*": deny
  "git push --force-with-lease*": deny
  "git filter-branch*": deny
  "git filter-repo*": deny
  "git reflog expire*": deny
  "rm -rf*": deny
  "rm -r*": deny
  "Remove-Item -Recurse -Force*": deny
  "Remove-Item -Force*": deny
  "format*": deny
  "diskpart*": deny
  "mkfs*": deny
  "mv * /dev/null": deny
  "fdisk*": deny
  "parted*": deny
  "shutdown*": deny
  "reboot*": deny
  "halt*": deny
  "poweroff*": deny
  "crontab -r*": deny
  "iptables*": deny
  "ufw*": deny
  "reg delete*": deny
  "Set-ExecutionPolicy*": deny
  "docker system prune --volumes -a*": deny
  "kubectl delete namespace*": deny
  "kubectl delete pv*": deny
  "redis-cli FLUSHALL*": deny

  # === ASK: potentially destructive ===
  "git reset *": ask
  "git checkout *": ask
  "git clean *": ask
  "git stash *": ask
  "git rebase *": ask
  "git push *": ask
  "git commit --amend*": ask
  "git cherry-pick *": ask
  "git branch -D*": ask
  "git branch -d*": ask
  "git tag -d*": ask
  "git gc --prune=now*": ask
  "git update-ref -d*": ask

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

  "psql -c \"DROP *\"": ask
  "psql -c \"TRUNCATE *\"": ask
  "psql -c \"DELETE FROM *\"": ask
  "psql -c \"ALTER *\"": ask
  "psql -c \"GRANT *\"": ask
  "psql -c \"REVOKE *\"": ask
  "redis-cli FLUSHDB*": ask
  "redis-cli DEL *": ask

  "kill -9 *": ask
  "killall *": ask
  "pkill *": ask
  "systemctl stop *": ask
  "systemctl disable *": ask
  "service * stop": ask
  "crontab -e*": ask
  "mount *": ask
  "umount *": ask

  "pip uninstall *": ask
  "npm uninstall *": ask
  "uv pip uninstall *": ask
  "apt remove *": ask
  "apt purge *": ask
  "yum remove *": ask
  "brew uninstall *": ask

  "setx *": ask
  "reg add*": ask

  "curl -X DELETE*": ask
  "curl -X PUT*": ask
  "curl -X POST*": ask

  "dd if=* of=*": ask
  "shred *": ask
  "wipe *": ask
  "truncate -s 0 *": ask
  "chmod -R 000 *": ask
  "chmod -R 777 *": ask
  "chown -R *": ask

  # === DEFAULT: allow everything else ===
  "*": allow
```

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.4 researcher — Research + Docs

**Philosophy:** Researches and writes documentation. May need bash to verify tooling availability (e.g., `uv --version`, `node --version`). No production code modification.

**bash permission model:**
```yaml
bash:
  # === READ-ONLY: always allowed ===
  "uv --version": allow
  "node --version": allow
  "npm --version": allow
  "python --version": allow
  "git --version": allow
  "docker --version": allow

  "docker compose": allow
  "docker compose config*": allow
  "docker compose ps*": allow
  "docker compose logs*": allow
  "docker ps*": allow
  "docker logs*": allow
  "docker inspect*": allow

  "kubectl get*": allow
  "kubectl describe*": allow
  "kubectl logs*": allow

  "Get-ChildItem*": allow
  "curl*": allow

  # === DENY: all destructive (same as auditor) ===
  "git reset --hard*": deny
  "git clean -fd*": deny
  "git clean -fdx*": deny
  "git push --force*": deny
  "git push --force-with-lease*": deny
  "git filter-branch*": deny
  "git filter-repo*": deny
  "git reflog expire*": deny
  "rm -rf*": deny
  "rm -r*": deny
  "Remove-Item -Recurse -Force*": deny
  "Remove-Item -Force*": deny
  "format*": deny
  "diskpart*": deny
  "mkfs*": deny
  "mv * /dev/null": deny
  "fdisk*": deny
  "parted*": deny
  "shutdown*": deny
  "reboot*": deny
  "halt*": deny
  "poweroff*": deny
  "crontab -r*": deny
  "iptables*": deny
  "ufw*": deny
  "reg delete*": deny
  "Set-ExecutionPolicy*": deny
  "docker system prune --volumes -a*": deny
  "kubectl delete namespace*": deny
  "kubectl delete pv*": deny
  "redis-cli FLUSHALL*": deny

  # === ASK: potentially destructive ===
  "git reset *": ask
  "git checkout *": ask
  "git clean *": ask
  "git stash *": ask
  "git rebase *": ask
  "git push *": ask
  "git commit --amend*": ask
  "git cherry-pick *": ask
  "git branch -D*": ask
  "git branch -d*": ask
  "git tag -d*": ask
  "git gc --prune=now*": ask
  "git update-ref -d*": ask

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

  "psql -c \"DROP *\"": ask
  "psql -c \"TRUNCATE *\"": ask
  "psql -c \"DELETE FROM *\"": ask
  "psql -c \"ALTER *\"": ask
  "psql -c \"GRANT *\"": ask
  "psql -c \"REVOKE *\"": ask
  "redis-cli FLUSHDB*": ask
  "redis-cli DEL *": ask

  "kill -9 *": ask
  "killall *": ask
  "pkill *": ask
  "systemctl stop *": ask
  "systemctl disable *": ask
  "service * stop": ask
  "crontab -e*": ask
  "mount *": ask
  "umount *": ask

  "pip uninstall *": ask
  "npm uninstall *": ask
  "uv pip uninstall *": ask
  "apt remove *": ask
  "apt purge *": ask
  "yum remove *": ask
  "brew uninstall *": ask

  "setx *": ask
  "reg add*": ask

  "curl -X DELETE*": ask
  "curl -X PUT*": ask
  "curl -X POST*": ask

  "dd if=* of=*": ask
  "shred *": ask
  "wipe *": ask
  "truncate -s 0 *": ask
  "chmod -R 000 *": ask
  "chmod -R 777 *": ask
  "chown -R *": ask

  # === DEFAULT: allow everything else ===
  "*": allow
```

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.mdx": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.5 planner — Planning + Task Generation

**Philosophy:** Creates task YAMLs and plans. May need bash to verify tooling. No production code modification.

**bash permission model:** Same as researcher (Section 4.4)

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.mdx": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.6 validator — Validation (Tests/Lint/Docker)

**Philosophy:** Runs tests, linting, type checking, Docker operations. Needs broader bash access than auditors but still no production code modification. Needs `psql` and `redis-cli` for verification.

**bash permission model:**
```yaml
bash:
  # === BUILD & TEST: always allowed ===
  "uv *": allow
  "npm test*": allow
  "pnpm test*": allow
  "yarn test*": allow
  "npm run lint*": allow
  "pnpm lint*": allow
  "yarn lint*": allow
  "npm run typecheck*": allow
  "pnpm typecheck*": allow
  "yarn typecheck*": allow
  "pytest*": allow
  "ruff*": allow
  "mypy*": allow
  "alembic*": allow

  # === DOCKER: read-only allowed ===
  "docker compose": allow
  "docker compose config*": allow
  "docker compose ps*": allow
  "docker compose logs*": allow
  "docker compose build*": allow
  "docker ps*": allow
  "docker logs*": allow
  "docker build*": allow
  "docker inspect*": allow
  "docker network*": allow
  "docker volume*": allow
  "docker system*": allow

  # === K8S: read-only allowed ===
  "kubectl get*": allow
  "kubectl logs*": allow
  "kubectl top*": allow

  # === DB: read-only allowed ===
  "psql -c \"SELECT*\"": allow
  "psql -c \"SHOW*\"": allow
  "redis-cli GET*": allow
  "redis-cli KEYS*": allow

  # === UTILITIES: allowed ===
  "curl*": allow
  "Get-ChildItem*": allow

  # === DOCKER: lifecycle allowed (start/stop for testing) ===
  "docker compose up*": allow
  "docker compose restart*": allow
  "docker compose exec*": allow
  "docker compose run*": allow
  "docker run*": allow
  "docker exec*": allow

  # === DENY: destructive git ===
  "git reset --hard*": deny
  "git clean -fd*": deny
  "git clean -fdx*": deny
  "git push --force*": deny
  "git push --force-with-lease*": deny
  "git filter-branch*": deny
  "git filter-repo*": deny
  "git reflog expire*": deny

  # === DENY: destructive filesystem ===
  "rm -rf*": deny
  "rm -r*": deny
  "Remove-Item -Recurse -Force*": deny
  "Remove-Item -Force*": deny
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

  # === ASK: potentially destructive ===
  "git *": ask
  "git add*": ask
  "git commit*": ask
  "git status*": ask
  "git diff*": ask
  "git log*": ask
  "git reset *": ask
  "git checkout *": ask
  "git clean *": ask
  "git stash *": ask
  "git rebase *": ask
  "git push *": ask
  "git commit --amend*": ask
  "git cherry-pick *": ask
  "git branch -D*": ask
  "git branch -d*": ask
  "git tag -d*": ask
  "git gc --prune=now*": ask
  "git update-ref -d*": ask

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

  "psql*": ask
  "psql -c \"DROP *\"": ask
  "psql -c \"TRUNCATE *\"": ask
  "psql -c \"DELETE FROM *\"": ask
  "psql -c \"ALTER *\"": ask
  "psql -c \"GRANT *\"": ask
  "psql -c \"REVOKE *\"": ask
  "psql -c \"CREATE *\"": ask
  "redis-cli FLUSHDB*": ask
  "redis-cli DEL *": ask

  "kill -9 *": ask
  "killall *": ask
  "pkill *": ask
  "systemctl stop *": ask
  "systemctl disable *": ask
  "service * stop": ask
  "crontab -e*": ask
  "mount *": ask
  "umount *": ask

  "pip uninstall *": ask
  "npm uninstall *": ask
  "uv pip uninstall *": ask
  "apt remove *": ask
  "apt purge *": ask
  "yum remove *": ask
  "brew uninstall *": ask

  "setx *": ask
  "reg add*": ask

  "curl -X DELETE*": ask
  "curl -X PUT*": ask
  "curl -X POST*": ask

  "dd if=* of=*": ask
  "shred *": ask
  "wipe *": ask
  "truncate -s 0 *": ask
  "chmod -R 000 *": ask
  "chmod -R 777 *": ask
  "chown -R *": ask

  # === DEFAULT: ask (validator has broader needs but still cautious) ===
  "*": ask
```

**edit permission model:**
```yaml
edit:
  "*.md": allow
  "*.yaml": allow
  "*.yml": allow
  "*": deny
```

---

### 4.7 implementor — Full Implementation

**Philosophy:** The only agent that modifies production code. Needs the broadest permissions but still with guardrails on the most dangerous operations.

**bash permission model:**
```yaml
bash:
  # === GIT: safe operations allowed ===
  "git status*": allow
  "git diff*": allow
  "git log*": allow
  "git add*": allow
  "git commit*": allow
  "git show*": allow
  "git branch*": allow

  # === BUILD & TEST: always allowed ===
  "uv *": allow
  "npm test*": allow
  "pnpm test*": allow
  "yarn test*": allow
  "npm run lint*": allow
  "pnpm lint*": allow
  "yarn lint*": allow
  "npm run typecheck*": allow
  "pnpm typecheck*": allow
  "yarn typecheck*": allow
  "pytest*": allow
  "ruff*": allow
  "mypy*": allow
  "alembic*": allow

  # === DOCKER: lifecycle allowed ===
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

  # === K8S: read-only allowed ===
  "kubectl get*": allow
  "kubectl logs*": allow
  "kubectl top*": allow

  # === DB: allowed for verification ===
  "psql*": allow
  "redis-cli*": allow

  # === UTILITIES: allowed ===
  "curl*": allow
  "Get-ChildItem*": allow

  # === DENY: irreversible git ===
  "git reset --hard*": deny
  "git clean -fd*": deny
  "git clean -fdx*": deny
  "git push --force*": deny
  "git push --force-with-lease*": deny
  "git filter-branch*": deny
  "git filter-repo*": deny
  "git reflog expire*": deny

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

  # === ASK: potentially destructive git ===
  "git reset *": ask
  "git checkout *": ask
  "git clean *": ask
  "git stash *": ask
  "git rebase *": ask
  "git push *": ask
  "git commit --amend*": ask
  "git cherry-pick *": ask
  "git branch -D*": ask
  "git branch -d*": ask
  "git tag -d*": ask
  "git gc --prune=now*": ask
  "git update-ref -d*": ask

  # === ASK: potentially destructive filesystem ===
  "rm -rf *": ask
  "rm -r *": ask
  "Remove-Item -Recurse -Force *": ask
  "Remove-Item -Force *": ask
  "del /s /q *": ask
  "rd /s /q *": ask
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
  "service * stop": ask
  "crontab -e*": ask
  "mount *": ask
  "umount *": ask

  # === ASK: potentially destructive packages ===
  "pip uninstall *": ask
  "npm uninstall *": ask
  "uv pip uninstall *": ask
  "apt remove *": ask
  "apt purge *": ask
  "yum remove *": ask
  "brew uninstall *": ask

  # === ASK: potentially destructive config ===
  "setx *": ask
  "reg add*": ask

  # === ASK: potentially destructive network ===
  "curl -X DELETE*": ask
  "curl -X PUT*": ask
  "curl -X POST*": ask

  # === DEFAULT: allow everything else ===
  "*": allow
```

**edit permission model:**
```yaml
edit:
  "*": allow
  "*.env": allow
  "C:\\py_dev\\mkobi\\docker\\.env": allow
  "C:\\py_dev\\mkobi\\.env": allow
  "C:\\py_dev\\mkobi\\docker\\.env*": allow
  "C:\\py_dev\\mkobi\\docker\\.env.development": allow
  "C:\\py_dev\\mkobi\\docker\\.env.production": allow
```

---

## 5. Current vs Proposed Changes

### 5.1 auditor — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | `allow` (unrestricted) | Explicit allow/ask/deny with full deny list |
| `edit` | `.md`, `.yaml`, `.yml` allow; `*` deny | Add `.mdx` allow |

### 5.2 audit-executor — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | `allow` (unrestricted) | Same as auditor — explicit allow/ask/deny |
| `edit` | `.md`, `.yaml`, `.yml` allow; `*` deny | No change |

### 5.3 audit-orchestrator — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | `allow` (unrestricted) | Same as auditor — explicit allow/ask/deny |
| `edit` | `.md`, `.yaml`, `.yml` allow; `*` deny | No change |

### 5.4 researcher — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | `allow` (unrestricted) | Same as auditor — explicit allow/ask/deny |
| `edit` | `.md`, `.mdx`, `.yaml`, `.yml` allow; `*` deny | No change |

### 5.5 planner — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | `allow` (unrestricted) | Same as researcher — explicit allow/ask/deny |
| `edit` | `.md`, `.mdx`, `.yaml`, `.yml` allow; `*` deny | No change |

### 5.6 validator — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | Explicit allow list + `"*": ask` | Expanded allow list (Docker lifecycle, K8s read-only, psql full, redis-cli full) + full deny list for destructive ops + `"*": ask` |
| `edit` | `.md`, `.yaml`, `.yml` allow; `*` deny | No change |

### 5.7 implementor — Changes

| Aspect | Current | Proposed |
|--------|---------|----------|
| `bash` | Explicit allow/ask/deny (already good) | Refined: expanded deny list (added `git filter-repo*`, `git reflog expire*`, `fdisk*`, `parted*`, `iptables*`, `ufw*`, `reg delete*`, `Set-ExecutionPolicy*`, `redis-cli FLUSHALL*`, `docker system prune --volumes -a*`, `kubectl delete namespace*`, `kubectl delete pv*`) + expanded ask list (added filesystem, Docker, K8s, DB, system, packages, config, network destructive ops) |
| `edit` | `*`: allow + `.env` files | No change |

---

## 6. Key Design Decisions

### 6.1 Default Allow with Explicit Deny/Ask

The model uses `"*": allow` as the fallback for most agents. Only risky commands are explicitly listed as `ask` or `deny`. This means:
- Safe commands like `git add`, `git commit`, `git status` don't need enumeration
- New safe commands automatically work without config changes
- Only dangerous operations require explicit handling

### 6.2 Three-Tier Risk Model

| Tier | Action | Examples |
|------|--------|----------|
| **DENY** | Blocked entirely | `git reset --hard`, `git push --force`, `rm -rf`, `shutdown`, `format` |
| **ASK** | Requires user approval | `git push`, `git rebase`, `docker compose down`, `kubectl delete`, `psql DROP` |
| **ALLOW** | No restriction | Everything not explicitly listed (via `"*": allow`) |

### 6.3 Role-Based Access Progression

```
auditor ≈ audit-executor ≈ audit-orchestrator ≈ researcher ≈ planner < validator < implementor
(read-only)                                                    (test/lint)     (full access)
```

- **Read-only agents** (auditor, audit-executor, audit-orchestrator, researcher, planner): Same restrictive bash, edit only docs
- **Validator**: Broader bash for test/lint/Docker lifecycle, still no code edits
- **Implementor**: Full bash with guardrails, full edit access

### 6.4 What's NOT in the Lists

The following are intentionally omitted because they're safe and fall through to `"*": allow`:
- `git add`, `git commit`, `git status`, `git diff`, `git log`, `git show`, `git branch`
- `git clone`, `git fetch`, `git pull`, `git merge`
- `ls`, `cat`, `head`, `tail`, `wc`, `sort`, `uniq`, `grep`, `find`, `echo`
- `cd`, `pwd`, `which`, `where`
- `mkdir`, `touch`, `cp`, `mv` (non-destructive usage)
- `npm install`, `npm run build`, `uv pip install`
- `docker compose up`, `docker compose build`, `docker compose logs`
- `pytest`, `ruff check`, `mypy`, `alembic upgrade`

---

## 7. Implementation Steps

1. **Update `auditor.md`** — Replace `bash: allow` with explicit permission model (Section 4.1)
2. **Update `audit-executor.md`** — Replace `bash: allow` with explicit permission model (Section 4.2)
3. **Update `audit-orchestrator.md`** — Replace `bash: allow` with explicit permission model (Section 4.3)
4. **Update `researcher.md`** — Replace `bash: allow` with explicit permission model (Section 4.4)
5. **Update `planner.md`** — Replace `bash: "*": allow` with explicit permission model (Section 4.5)
6. **Update `validator.md`** — Refine existing permission model (Section 4.6)
7. **Update `implementor.md`** — Refine existing permission model (Section 4.7)

---

## 8. Sources

- Existing agent files: `.kilo/agents/*.md`
- Git documentation: https://git-scm.com/docs
- Docker documentation: https://docs.docker.com/reference/
- Kubernetes documentation: https://kubernetes.io/docs/reference/kubectl/
