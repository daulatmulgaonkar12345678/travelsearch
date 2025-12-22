FROM python:3.11-slim

WORKDIR /app

# Install system deps (optional but safe)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ✅ Copy FastAPI app
COPY app ./app

# ✅ Copy data files (airports & hotels)
COPY data ./data

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
