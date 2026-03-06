FROM python:3.12-slim

WORKDIR /app

# Install gcc for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml + poetry.lock first for caching
COPY services/ml-service/pyproject.toml services/ml-service/poetry.lock* ./

# Disable virtualenvs, install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared libraries, proto files, and service code
COPY shared/ /shared/
COPY proto/ /proto/
COPY services/ml-service/app/ ./app/

# Optional: Train model at build time (skip if fails)
RUN python -m app.model.trainer || echo "Model training skipped"

# Expose service port
EXPOSE 50053

# Run service
CMD ["python", "-m", "app.main"]