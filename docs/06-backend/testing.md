---
id: testing
domain: backend
tags:
  - pytest
  - async-testing
  - fixtures
  - test-database
  - coverage
  - mocking
related:
  - backend-architecture
  - configuration
  - logging
---

# Testing

## Overview

The project uses **pytest** as its testing framework with async support via `pytest-asyncio`. Tests cover API endpoints, business logic services, data processing, authentication, configuration, and Pydantic model validation.

**Test directory:** `tests/`

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (DB, auth, Redis mock)
├── test_auth.py             # Auth API endpoint tests
├── test_auth_service.py     # AuthService unit tests
├── test_config.py           # Configuration loading tests
├── test_dashboards_api.py   # Dashboard API endpoint tests
├── test_data_service.py     # DataService unit tests
├── test_filters.py          # Filter API tests
├── test_graph_service.py    # GraphService unit tests
├── test_graphs.py           # Graph API tests
├── test_layouts.py          # Layout API tests
├── test_processing_logs.py  # Processing log tests
├── test_pydantic_models.py  # Pydantic model validation tests
├── test_repositories.py     # Repository layer tests
├── test_security.py         # Security utility tests
├── test_storage_manager.py  # File storage tests
├── test_upload_api.py       # Upload API endpoint tests
└── test_users_api.py        # User management API tests
```

## Test Categories

### API Tests

Test HTTP endpoints using `httpx.AsyncClient` with FastAPI's `ASGITransport`:

- **Fixtures:** `async_client` provides an in-memory HTTP client; `authenticated_client` adds JWT auth headers
- **Database:** Uses the same test session with SAVEPOINT rollback for isolation
- **Coverage:** Request validation, authentication, authorization, response schemas, error handling

### Service Tests

Test business logic in isolation using mocked repositories:

- **Pattern:** `unittest.mock.AsyncMock` for all repository dependencies
- **Coverage:** Business rules, data transformation, error conditions, edge cases
- **Examples:** `test_auth_service.py`, `test_data_service.py`, `test_graph_service.py`

### Configuration Tests

Test the multi-source configuration loading:

- Environment variable parsing
- Docker secrets (`_FILE` suffix)
- `.env` file loading
- YAML config loading
- Source priority validation
- Production credential enforcement

### Model Tests

Test Pydantic model validation:

- Field constraints and validators
- StrEnum value serialization
- Custom validators (e.g., CORS origins, admin credentials)

## Test Fixtures

Defined in `conftest.py`:

| Fixture              | Scope     | Description                                      |
| -------------------- | --------- | ------------------------------------------------ |
| `_auto_mock_redis`   | function  | Auto-mocks Redis for all tests (rate limiting bypassed) |
| `mock_redis`         | function  | Opt-in Redis mock that bypasses rate limiting    |
| `strict_redis`       | function  | In-memory Redis mock with real rate limiting     |
| `setup_test_database` | session  | Creates and migrates test database               |
| `async_test_engine`  | session   | Async SQLAlchemy engine with NullPool            |
| `async_session_maker` | session  | Async session factory                            |
| `async_db_session`   | function  | Per-test session with SAVEPOINT rollback         |
| `async_client`       | function  | httpx AsyncClient with overridden DB dependency  |
| `authenticated_client` | function | HTTP client with JWT auth headers               |
| `test_user`          | function  | Creates a test user and returns token            |
| `auth_headers`       | function  | Returns `{"Authorization": "Bearer <token>"}`    |

## Test Database

- **Database:** `bidb_test` (separate from production `bidb`)
- **Engine:** Uses `NullPool` to prevent connection pooling issues in tests
- **Isolation:** SAVEPOINT pattern — each test runs in a nested transaction that is rolled back after the test completes
- **Migrations:** Alembic migrations are applied to the test database on session setup
- **Recreation:** The test database is dropped and recreated when `RECREATE_TEST_DB=true`

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_auth_service.py

# Run with verbose output
uv run pytest tests/ -v

# Run specific test class
uv run pytest tests/test_auth_service.py::TestAuthService
```

## Coverage Areas

| Area          | Description                                              |
| ------------- | -------------------------------------------------------- |
| **API**       | All endpoint handlers, request validation, auth, errors  |
| **Processing**| Data upload, parsing (Polars), transformation, aggregation |
| **Auth**      | Login, registration, JWT creation/verification, password change |
| **Config**    | Settings loading from all sources, priority, validation  |
| **Security**  | Password hashing, token creation, rate limiting          |
| **Models**    | Pydantic model validation, StrEnum serialization         |
| **Repositories** | Data access layer, query correctness                  |

## Key Patterns

### Async Tests

All async tests use `pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
class TestAuthService:
    async def test_login_success(self, auth_service):
        result = await auth_service.login("user@example.com", "password")
        assert result is not None
```

### Mocking

Repositories and external services are mocked at the service layer:

```python
@pytest.fixture
def mock_user_repo():
    mock = AsyncMock()
    mock.get_by_email.return_value = None
    return mock
```

### Database Isolation

Tests that need database access use the `async_db_session` fixture which automatically rolls back all changes:

```python
async def test_create_user(async_db_session, test_user):
    # test_user is created in a SAVEPOINT
    # automatically rolled back after this test
    assert test_user["email"].endswith("@example.com")
```

## Cross-References

- [Backend Architecture](architecture.md) — System architecture and layer responsibilities
- [Configuration](configuration.md) — Test configuration via environment variables
- [Logging](logging.md) — Log output during test runs
- [Database Schema](../09-database/schema-core.md) — Test database structure and migrations
