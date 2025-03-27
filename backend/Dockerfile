FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run FastAPI with a longer timeout
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9567"]
