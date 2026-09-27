# Setup & Deployment Guide

## Prerequisites
- Python 3.12+
- Google Cloud SDK (`gcloud` CLI authenticated)
- Docker & Docker Compose (optional for containerized deployment)

## Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit variables:
- `GOOGLE_CLOUD_PROJECT`: Your GCP Project ID
- `GOOGLE_CLOUD_LOCATION`: BigQuery / Vertex AI region (e.g. `us-central1`)
- `GOOGLE_GENAI_USE_VERTEXAI`: `true`
- `BQ_REGION`: `US`
- `BQ_ON_DEMAND_PRICE_PER_TB`: `6.25`

## GCP Permissions Required
- `roles/bigquery.jobUser` (to run dry-runs)
- `roles/bigquery.resourceViewer` (to inspect table schemas and INFORMATION_SCHEMA)
- `roles/aiplatform.user` (to call Gemini models via Vertex AI)

## Local Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Access OpenAPI docs at `http://localhost:8000/docs`.
