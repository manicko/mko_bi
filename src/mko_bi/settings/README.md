# Settings Configuration

This directory contains the application configuration files for `mko_bi`.

## Configuration Sources (Priority Order)

The application loads settings with the following priority (highest to lowest):

1. **Environment Variables** - Nested notation with double underscore (`__`)
2. **Docker Secrets Files** - Via `_FILE` suffix environment variables
3. **.env File** - For development convenience (loaded by pydantic-settings)
4. **YAML Config File** - `app.yaml` in this directory
5. **Default Values** - Defined in code

## Environment Variables

### Database Settings

```bash
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__DBNAME=bidb
DATABASE__USER=postgres
DATABASE__PASSWORD=your_secure_password
```

### JWT Settings

```bash
JWT__SECRET_KEY=your_super_secure_jwt_secret_key
JWT__ALGORITHM=HS256
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Redis Settings

```bash
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0
REDIS__PASSWORD=your_redis_password
```

### General Settings

```bash
ENV=production
DEBUG=false
API_BASE_URL=https://api.example.com
CORS_ORIGINS=["https://example.com"]
```

## Docker Secrets Support

For production deployments with Docker, you can use Docker secrets by setting environment variables with the `_FILE` suffix pointing to secret files:

```bash
DATABASE__PASSWORD_FILE=/run/secrets/db_password
JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret
REDIS__PASSWORD_FILE=/run/secrets/redis_password
```

The application will read the secret value from the specified file.

### Docker Compose Example

```yaml
version: '3.8'

services:
  app:
    image: mko_bi:latest
    environment:
      - DATABASE__PASSWORD_FILE=/run/secrets/db_password
      - JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret
      - ENV=production
    secrets:
      - db_password
      - jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

## Development Setup

For local development, create a `.env` file in the project root (not committed to git):

```bash
# .env (gitignored)
DATABASE__PASSWORD=local_dev_password
JWT__SECRET_KEY=dev_secret_key
```

Or set environment variables directly.

## Security Notes

- **Never commit secrets to git** - `app.yaml` should only contain non-sensitive settings
- Use strong, randomly generated secrets for production
- JWT secret key should be at least 32 characters long
- Consider using a secrets management service in production (HashiCorp Vault, AWS Secrets Manager, etc.)
