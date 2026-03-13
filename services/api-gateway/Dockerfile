FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir --timeout 120 --retries 3 poetry

# Copy service code
COPY services/api-gateway/pyproject.toml services/api-gateway/poetry.lock* ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared library
COPY shared/ /shared/
RUN pip install /shared

# Copy Proto
COPY proto/ /proto/

# Copy application code
COPY services/api-gateway/app/ /app/app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]