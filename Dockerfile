FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source structure for better layer caching
COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY src ./src

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code (includes any additional files)
COPY . .

# Create data directories (will be overridden by volume mount, but ensures they exist)
RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000"]
