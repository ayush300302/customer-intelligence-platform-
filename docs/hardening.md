# Production Hardening Guide

This document details the hardening choices for the Customer Intelligence Platform to scale, secure, and monitor the services in a production environment.

## 1. Batch Scoring Scaling
For the `/batch-score` endpoint, loading huge CSV files (e.g. millions of rows) directly into memory can trigger Out-Of-Memory (OOM) errors. 

**Hardening Strategy**:
- **Chunking**: Modify the batch scoring process to read and process files in chunks of 50,000 rows using `pandas.read_csv(chunksize=...)`.
- **Parallel Processing**: Use multi-processing to score chunks in parallel.
- **Asynchronous Processing**: Instead of a synchronous HTTP request, return an operation ID and process the file in a background queue (e.g., Celery, Redis Queue, or Azure Queue Storage).

## 2. Docker & Container Security
The application is fully containerized using a multi-stage Docker build to keep the image size small and secure.

**Hardening Strategy**:
- **Non-root User**: Run the container using a non-privileged user to limit the impact of potential container escapes:
  ```dockerfile
  RUN useradd -m appuser
  USER appuser
  ```
- **Read-Only Root Filesystem**: Configure the container to run with a read-only filesystem, mounting temporary directories (`/tmp`, `/app/models`) separately if writing is required.

## 3. Production Deployment on Azure
For a production deployment using Azure:

**Hardening Strategy**:
1. **Azure Container Apps (ACA)**:
   - Scale-to-zero to save cost during idle hours.
   - Autoscaling based on HTTP request volume or CPU usage.
2. **Azure Key Vault**:
   - Store the `GEMINI_API_KEY` securely in Key Vault.
   - Reference it directly inside the Container App environmental variables using managed identities.
3. **Azure Monitor & App Insights**:
   - Route FastAPI logs to Log Analytics workspace.
   - Track custom metrics (latency, error count, prediction distribution) in App Insights.

## 4. RAG Hardening
- **Index Re-building**: Implement a cron job in Azure (e.g. Azure Functions) to run `build_index.py` daily to ingest new complaints.
- **Refusal and Content Moderation**: Apply guardrails to filter input queries for adversarial attacks or PII, and refuse if similarity scores are low.
