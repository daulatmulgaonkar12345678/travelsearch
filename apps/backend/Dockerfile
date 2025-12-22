FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install deps
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy FastAPI app
COPY app ./app

# Copy data directory from project root
COPY data ./data

# Expose port
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
