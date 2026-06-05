# Use Python 3.12 as a stable and unified version
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Copy lock files
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv
# This ensures we have the exact same environment
RUN uv pip install --system --no-cache -r pyproject.toml

# Final stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    netcat-openbsd \
    sed \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Fix potential Windows CRLF line endings and set permissions for all scripts
# This makes it robust even if files were edited on Windows
RUN find scripts -name "*.sh" -exec sed -i 's/\r$//' {} + && \
    chmod +x scripts/*.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser ${APP_HOME}

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

# Explicitly use /bin/sh to run the entrypoint script
# This bypasses potential 'permission denied' when using volumes on Mac
ENTRYPOINT ["/bin/sh", "/app/scripts/entrypoint.sh"]
