# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Install the package
RUN uv pip install --no-deps -e .

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed package from builder
COPY --from=builder /app/.venv /app/.venv

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run as non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Entry point
ENTRYPOINT ["fhir-inspector-mcp"]
