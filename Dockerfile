FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compilation or utilities)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Create a non-privileged user and configure permissions
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/models && \
    chown -R appuser:appuser /app

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser models/ ./models/

# Expose FastAPI port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Run uvicorn server
CMD ["uvicorn", "src.serving.serve:app", "--host", "0.0.0.0", "--port", "8000"]
