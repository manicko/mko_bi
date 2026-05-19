# Project Commands

## Environment
- **OS:** Windows
- **Package manager (Python):** uv
- **Package manager (Frontend):** npm
- **Database:** PostgreSQL (localhost:5432, db: bidb, user: postgres, pass: 1234)

---

## Python (backend) — use `uv run` for all commands

| Task | Command |
|------|---------|
| Run tests | `uv run pytest <path>` |
| Lint (ruff) | `uv run ruff check <path>` |
| Type check (mypy) | `uv run mypy <path>` |
| Migrations | `uv run alembic ...` |
| Add dependency | `uv add <package>` |
| Add dev dependency | `uv add --dev <package>` |
| Database CLI | `set "PGPASSWORD=1234" & psql -h localhost -p 5432 -U postgres -d bidb` |

> **Always run from repo root:** `C:\py_dev\mkobi`

---

## TypeScript / React (frontend) — use `npm run` for all commands

> **Always run from:** `C:\py_dev\mkobi\frontend`

| Task | Command |
|------|---------|
| Type check | `npm run build` (runs `tsc -b && vite build`) |
| Lint (ESLint) | `npm run lint` |
| Run tests | `npm run test` (vitest) |
| Dev server | `npm run dev` |
| Production build | `npm run build` |
| Preview build | `npm run preview` |
| Add dependency | `npm install <package>` |
| Add dev dependency | `npm install --save-dev <package>` |

---

## Important

- **ALWAYS** run `C:\py_dev\mkobi\.ai\builders\build.bat` to update project info before starting work.
- **BEFORE starting any task:** audit → research → plan → implement.
