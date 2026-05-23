FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compilation or utilities)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/

# Expose FastAPI port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "src.serving.serve:app", "--host", "0.0.0.0", "--port", "8000"]
