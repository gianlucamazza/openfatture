# Multi-stage Dockerfile for OpenFatture
# Build: docker build -t openfatture:latest .
# Run: docker run -it --rm -v $(pwd)/.env:/app/.env openfatture:latest

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (production only)
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY openfatture/ /app/openfatture/
COPY README.md LICENSE /app/

# Create directories for data
RUN mkdir -p /root/.openfatture/data /root/.openfatture/archivio /root/.openfatture/certificates

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import openfatture; print('healthy')" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "openfatture.cli.main"]
CMD ["--help"]
