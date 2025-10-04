FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies (remove libpython3.11-dev which does not exist in slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./
# Install Poetry and project (only main deps) without creating its own venv
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "poetry>=1.7.0" \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY . .

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
