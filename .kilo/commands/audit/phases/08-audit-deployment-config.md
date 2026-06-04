---
name: 08-deployment-config
description: Configuration and startup audit covering config management, lifecycle, and production readiness
agent: audit-executor
alwaysApply: false
problems-only: true
---

# Phase 08 Audit — Configuration & Lifecycle

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.
- If you need to start or stop docker environment to check functional or run test you should run it following the documantation instruction in dev mode BUT you mast return it to the same status as before - running or stopped
---

## Discovery Stage

Before performing audit checks, discover the project's configuration architecture:

1. **Configuration Discovery** — Identify configuration sources (env, files, secrets), map configuration priority order, discover configuration validation strategy, find prod vs dev differences.
2. **Startup Discovery** — Identify application entry point, map startup sequence and dependencies, discover health check endpoints, find initialization tasks.
3. **Shutdown Discovery** — Identify graceful shutdown handling, map resource cleanup on shutdown, discover connection pool disposal, find background task termination.
4. **Environment Discovery** — Identify environment detection mechanism, map environment-specific behavior, discover production safety checks, find test environment isolation.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production) before verifying startup or shutdown behavior. Follow the setup instructions in `docs/11-guides/docker.md`. Confirm all required containers are in `running` or `healthy` state before proceeding. If the environment cannot be started, document why and skip dependent steps.

### Step R1 — Startup Sequence Verification

Start the application (or read the startup code if runtime is unavailable):

- Trace the startup sequence: config loading → dependency initialization → migration checks → server start.
- At each step, verify: errors are handled (no silent failures), dependencies are verified before use, the app fails fast if something is misconfigured.
- If the app starts successfully with missing/invalid config, that is a finding.

### Step R2 — Verify Configuration Validation at Startup

Read the configuration module:

- Identify all configuration values loaded from environment/files.
- For each required value: verify it is validated at startup (not just at first use).
- Verify production mode requires explicit secrets (not empty/default).
- Verify CORS origins are validated in production mode.
- Check that the app refuses to start in production with debug mode enabled.

### Step R3 — Test Configuration Error Paths

Identify what happens when configuration is missing or invalid:

- For each required config value, verify the app fails to start with a clear error message.
- If the app starts with a default value instead of failing, that is a finding (silent misconfiguration).

### Step R4 — Verify Graceful Shutdown

Stop the application and check logs/behavior:

- Are database connections closed?
- Are background tasks terminated gracefully?
- Are in-memory resources freed?
- Is the shutdown sequence clean (no errors in shutdown logs)?

### Step R5 — Overengineering Check

Read the configuration and startup code:

- Is the abstraction level appropriate for the project size?
- Are there unnecessary layers (e.g., 3 levels of config abstraction for a 5-file config)?
- Are there unused configuration modules or files?
- Do the chosen libraries/services have clear justification?

### Step R6 — Environment Consistency Check

Compare configuration across environments (dev, test, prod):

- Are database connection strings properly separated?
- Are there development-only features that could leak into production (debug endpoints, test data seeding)?
- Are logging levels appropriate per environment?
- Are there hardcoded values that differ between environments but should be configurable?

---

## Audit Scope

Configuration management, startup lifecycle, production readiness, overengineering.

---

## Audit Dimensions

### 1. Configuration Management

| Check | Description |
|-------|-------------|
| Configuration centralized in single module | One place to look for all config. |
| Secrets derived from environment variables | No hardcoded secrets. |
| Secret injection supports multiple sources | `_FILE`, env, files. |
| Production refuses insecure defaults | Fail-fast on bad config. |
| Configuration validated at startup | No delayed failures. |
| No hardcoded values in configuration | Everything configurable. |

**Evidence required:** Step R2 validation analysis. Step R3 error path testing. Read the config module completely.

### 2. Startup Lifecycle

| Check | Description |
|-------|-------------|
| Dependency check on startup | Imports succeed, no missing deps. |
| Database connectivity verified before accepting requests | DB check on startup. |
| Schema existence verified on startup | Schema validation. |
| Migrations run automatically when configured | Migrations are applied. |
| Admin user creation is idempotent | No duplicate admin on restart. |
| Stale temp files cleaned on startup | Cleanup of previous runs. |
| Test database recreated when configured | Fresh test DB. |

**Evidence required:** Step R1 startup trace. Read initialization code for each check.

### 3. Production Readiness

| Check | Description |
|-------|-------------|
| Production debug mode disabled | No debug in production. |
| Logging level appropriate for production | Not DEBUG in production. |
| Production credentials enforced | Real secrets required. |
| CORS origins validated in production | Specific origins only. |
| No development features in production mode | No debug endpoints, test data, etc. |

**Evidence required:** Step R2 production mode checks. Compare dev vs prod config files.

### 4. Overengineering Check

| Check | Description |
|-------|-------------|
| No unnecessary abstraction layers | Config is as simple as possible. |
| Configuration matches project complexity | No enterprise patterns in a simple project. |
| No duplicated configuration patterns | DRY config. |
| Libraries used have clear justification | Every dependency is necessary. |

**Evidence required:** Step R5 overengineering analysis. Compare the number of config files/modules to the number of actual config values.

---

## Report Output

Write findings to: `.ai/audit/08-deployment-config/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DC-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — startup logs, config validation output, shutdown behavior, file:line of overengineered config.
  2. **Not just:** "violates invariant X" — show the exact config key, the exact default value, and the exact production risk.
