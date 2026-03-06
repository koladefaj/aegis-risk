FROM python:3.12-slim

WORKDIR /app

# Install gcc for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml + poetry.lock first
COPY services/notification-service/pyproject.toml services/notification-service/poetry.lock* ./

# Disable virtualenvs, install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# Copy shared libs and proto
COPY shared/ /shared/
COPY proto/ /proto/

# Copy your service code
COPY services/notification-service/app/ ./app/

# Expose port
EXPOSE 50051

# Run your service
CMD ["python", "-m", "app.main"]