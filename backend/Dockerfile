FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    libstdc++6 \
    python3-dev \
    libpython3.11-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy entire project before installing dependencies
COPY pyproject.toml poetry.lock ./
COPY . .

RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only main

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
