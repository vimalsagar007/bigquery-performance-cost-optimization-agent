# Postman API Testing Guide

This guide provides step-by-step instructions for importing and running the **BigQuery Performance and Cost Optimization Agent** Postman collection against the live Google Cloud Run environment or local FastAPI instance.

---

## 📁 Postman Collection Location

The collection file is located at:
`postman/BigQuery_Optimization_Agent.postman_collection.json`

---

## 🚀 Quick Setup Instructions

### 1. Import Collection into Postman
1. Open **Postman**.
2. Click **Import** (top left).
3. Select `postman/BigQuery_Optimization_Agent.postman_collection.json` or drag and drop the file.
4. Click **Import**.

---

### 2. Configure Environment Variable (`baseUrl`)
The collection includes a pre-configured variable `baseUrl`:

- **Production Cloud Run**: `https://bq-agent-61256100941.us-central1.run.app`
- **Local FastAPI Server**: `http://localhost:8000`

To switch between production and local:
1. Click on the imported collection **"BigQuery Performance & Cost Optimization Agent"**.
2. Go to the **Variables** tab.
3. Update `baseUrl` initial/current value.

---

## 🧪 Endpoint Test Reference Guide

### Request 1: Health & Status Check
- **Method**: `GET`
- **URL**: `{{baseUrl}}/health`
- **Purpose**: Verifies read-only mode, active GCP project, and Vertex AI status.
- **Expected Status**: `200 OK`
- **Sample Response**:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "project_id": "qwiklabs-gcp-02-63b2f55175ee",
    "region": "US",
    "read_only_mode": true,
    "vertex_ai_enabled": true
  }
  ```

---

### Request 2: Dry Run Query (Zero Cost)
- **Method**: `POST`
- **URL**: `{{baseUrl}}/query/dry-run`
- **Body (`application/json`)**:
  ```json
  {
    "sql": "SELECT name, gender, number FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2020"
  }
  ```
- **Purpose**: Calculates estimated bytes scanned and cost without running the query.
- **Sample Response**:
  ```json
  {
    "valid": true,
    "estimated_bytes_processed": 100201250,
    "estimated_cost_usd": 0.00057,
    "statement_type": "SELECT",
    "referenced_tables": ["bigquery-public-data.usa_names.usa_1910_current"]
  }
  ```

---

### Request 3: Analyze SQL Query (Anti-Pattern Detection)
- **Method**: `POST`
- **URL**: `{{baseUrl}}/analyze/query`
- **Body (`application/json`)**:
  ```json
  {
    "sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 10"
  }
  ```
- **Purpose**: Runs AST parser and anti-pattern detectors, returning findings and refactored SQL recommendations.

---

### Request 4: Top Expensive Query History
- **Method**: `GET`
- **URL**: `{{baseUrl}}/history/expensive?days=7&limit=10`
- **Purpose**: Queries `INFORMATION_SCHEMA.JOBS_BY_PROJECT` for top expensive queries ranked by bytes billed.

---

### Request 5: Top Slow Queries (Slot-ms Consumption)
- **Method**: `GET`
- **URL**: `{{baseUrl}}/history/slow?days=7&limit=10`
- **Purpose**: Ranks historical jobs by slot-ms consumption to pinpoint CPU/memory bottlenecks.

---

### Request 6: Inspect Table Partition & Clustering Metadata
- **Method**: `GET`
- **URL**: `{{baseUrl}}/table/metadata?project_id=bigquery-public-data&dataset_id=usa_names&table_id=usa_1910_current`
- **Purpose**: Inspects row counts, byte size, partitioning type, partition column, and clustering fields.

---

### Request 7: Generate Optimization Report & Compare Metrics
- **Method**: `POST`
- **URL**: `{{baseUrl}}/optimize`
- **Body (`application/json`)**:
  ```json
  {
    "sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE state = 'CA'"
  }
  ```
- **Purpose**: Assembles a full JSON optimization report and compares original vs refactored metrics.

---

### Request 8: AI Agent Natural Language Chat
- **Method**: `POST`
- **URL**: `{{baseUrl}}/chat`
- **Body (`application/json`)**:
  ```json
  {
    "message": "Find my top 3 costliest query anti-patterns and explain how partition pruning saves money."
  }
  ```
- **Purpose**: Asks natural language questions to the Gemini-powered LangGraph agent coordinator.
