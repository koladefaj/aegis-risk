FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy shared library FIRST
COPY shared/ /shared/

# Copy dependency files
COPY services/risk-engine-service/pyproject.toml services/risk-engine-service/poetry.lock* ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Install shared package
RUN pip install /shared

# Copy application code
COPY services/risk-engine-service/app/ ./app/

# Copy alembic files
COPY services/risk-engine-service/alembic/ ./alembic/
COPY services/risk-engine-service/alembic.ini ./

EXPOSE 50052

CMD ["python", "-m", "app.main"]