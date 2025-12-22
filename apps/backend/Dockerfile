FROM python:3.11-slim

WORKDIR /app

# System dependencies (required by email-validator & cryptography)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (important for caching)
COPY requirements.txt .

# Upgrade pip and install Python deps
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip show email-validator

# Copy application code
COPY app ./app

# Expose port (match Render or Docker CMD)
EXPOSE 8001

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
