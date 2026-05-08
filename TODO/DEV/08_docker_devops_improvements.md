---
## DATA PROCESSING
---

### TASK: Docker Production Readiness

FILE: Dockerfile, docker-compose.yml, docker-compose.override.yml, docker-compose.test.yml

GOAL: Ensure Docker setup is production-ready

IMPLEMENT:

* Check Dockerfile:
  - Uses production-ready base image
  - Pinned versions (not `latest`)
  - No dev dependencies in production stage
  - Multi-stage build if appropriate
  - Container does NOT run as root
  - No secrets baked into image
  - No `.env` copied into image
  - Healthcheck if needed
* Check docker-compose files:
  - Proper service separation (app, postgres)
  - Volumes configured correctly
  - Environment variables properly passed
  - Restart policies set
  - No unnecessary exposed ports
* Check runtime:
  - Correct startup command
  - Logging to stdout/stderr (not files only)
  - Configurable ports/hosts via env vars
  - No debug mode in production

LOGIC:

1. Review Dockerfile for security best practices
2. Review docker-compose files for production readiness
3. Ensure non-root user in container
4. Verify no hardcoded credentials
5. Test: `docker-compose config` validates
6. Test: `docker-compose up` starts correctly

DONE:

* [ ] Dockerfile uses non-root user
* [ ] No secrets in Docker image
* [ ] No dev dependencies in production stage
* [ ] docker-compose.yml properly configured
* [ ] Healthcheck added (if needed)
* [ ] Command `docker-compose config` passes

---

### TASK: Environment & Config Management

FILE: src/mkobi/config.py, src/mkobi/settings/app.yaml, .env.example

GOAL: Ensure proper configuration management

IMPLEMENT:

* Verify pydantic-settings usage
* Check env var priority: env vars > Docker secrets > .env > YAML > defaults
* Verify Docker secrets support (_FILE suffix)
* Ensure `.env` only for development
* Check `app.yaml` only for non-sensitive settings
* Verify all secrets in env vars (DATABASE__PASSWORD, JWT__SECRET_KEY)

LOGIC:

1. Review config.py for pydantic-settings BaseSettings
2. Verify nested env vars work (DATABASE__HOST, DATABASE__PORT)
3. Test Docker secrets support
4. Ensure no hardcoded secrets in code
5. Update .env.example with all required vars

DONE:

* [ ] Config uses pydantic-settings correctly
* [ ] Docker secrets supported
* [ ] No hardcoded secrets
* [ ] .env.example is complete
* [ ] Env var override works

---
