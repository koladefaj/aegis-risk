FROM python:3.12-slim

WORKDIR /app

# Install gcc for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml + poetry.lock first for caching
COPY services/llm-service/pyproject.toml services/llm-service/poetry.lock* ./

# Disable virtualenvs, install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared libraries, proto files, and service code
COPY shared/ /shared/
COPY proto/ /proto/
COPY services/llm-service/app/ ./app/

# Expose service port
EXPOSE 50054

# Run service
CMD ["python", "-m", "app.main"]