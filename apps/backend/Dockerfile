FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY apps/backend/app ./app

# ✅ COPY DATA FILES (THIS FIXES AIRPORT/HOTEL ERRORS)
COPY data ./data

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
