FROM python:3.12-slim

WORKDIR /app

# Install gcc for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml + poetry.lock first
COPY services/risk-engine-service/pyproject.toml services/risk-engine-service/poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared libs, proto files, and service code
COPY shared/ /shared/
COPY proto/ /proto/
COPY services/risk-engine-service/app/ ./app/

# Expose service port
EXPOSE 50052

# Run service
CMD ["python", "-m", "app.main"]