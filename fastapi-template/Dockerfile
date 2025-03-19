FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the static directory if not present
RUN mkdir -p static

# Copy the source code
COPY . .

# Conditionally move index.html into the static folder if it exists
RUN if [ -f /app/index.html ]; then mv /app/index.html /app/static/index.html; else echo "index.html not found"; fi

EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]