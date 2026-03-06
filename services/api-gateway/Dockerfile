FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml + poetry.lock first for caching
COPY services/api-gateway/pyproject.toml services/api-gateway/poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared libraries, proto files, and application code
COPY shared/ /shared/
COPY proto/ /proto/
COPY services/api-gateway/app/ ./app/

# Expose port
EXPOSE 8000

# Run service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]