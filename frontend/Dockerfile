FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt

# Create static directory if not present
RUN mkdir -p /app/static

# Copy application code
COPY . .

# Ensuring index.html is inside the static folder
RUN if [ -f /app/index.html ]; then mv /app/index.html /app/static/index.html; fi

EXPOSE 9567

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9567"]
