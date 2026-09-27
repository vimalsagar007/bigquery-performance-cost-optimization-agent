# BigQuery Performance & Cost Optimization Agent

[![CI Workflow](https://github.com/vimalsagar007/bigquery-performance-cost-optimization-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/vimalsagar007/bigquery-performance-cost-optimization-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

An enterprise-grade, AI-powered **BigQuery Performance and Cost Optimization Agent** built with Python 3.12+, FastAPI, Google Cloud BigQuery SDK, `google-genai` (Gemini on Vertex AI), and LangGraph.

The agent analyzes SQL query structure, BigQuery INFORMATION_SCHEMA execution history, dataset/table partitioning and clustering metadata, slot usage, and performance insights to identify cost anti-patterns and performance bottlenecks—delivering actionable, evidence-backed optimization recommendations.

---

## ⚠️ Important Safety Requirement (Version 1 Read-Only)

> **Version 1 IS STRICTLY READ-ONLY.**
> - The agent **NEVER** modifies, deletes, updates, or overwrites BigQuery production data.
> - Data Modification (DML/DDL) statements (`INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`) are rejected at the AST parser level before reaching BigQuery.
> - Generated optimization SQL is displayed **solely as a recommendation** and is **NEVER** executed automatically.

---

## Architecture Diagram

```
                                  +---------------------------------------+
                                  |            Client Applications        |
                                  |    (HTTP API / CLI / Web Console)     |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +-------------------+-------------------+
                                  |         FastAPI Web Service           |
                                  |        (app/main.py & routes)         |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +-------------------+-------------------+
                                  |       LangGraph Agent Coordinator     |
                                  |         (app/agents/graph.py)         |
                                  +-------------------+-------------------+
                                                      |
              +-------------------+-------------------+-------------------+-------------------+
              |                   |                   |                   |                   |
              v                   v                   v                   v                   v
     +-----------------+ +-----------------+ +-----------------+ +-----------------+ +-----------------+
     | SQL AST & Rules | | BigQuery Client | |  Dry-Run Engine | | Gemini AI Engine| | Safety Guardrail|
     | (sql_analyzer)  | |(bigquery_tools)| |  (dry_run.py)   | |(gemini_service) | | (sql_validator) |
     +-----------------+ +-----------------+ +-----------------+ +-----------------+ +-----------------+
              |                   |                   |                   |                   |
              +-------------------+-------------------+-------------------+-------------------+
                                                      |
                                                      v
                                  +-------------------+-------------------+
                                  |          Google Cloud Platform        |
                                  |    BigQuery & INFORMATION_SCHEMA      |
                                  +---------------------------------------+
```

---

## Features

- **28 Core BigQuery Tools**: Table metadata, partition/clustering inspector, INFORMATION_SCHEMA query history analyzer, AST parser, dry-run engine, cost estimator, slot-ms usage analyzer, and refactoring generator.
- **Strict Read-Only Guardrails**: Proactively blocks non-read query types (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.).
- **Zero-Cost Dry-Run Estimations**: Calculates bytes scanned and estimated costs before running analysis queries.
- **LangGraph Agent Orchestration**: Multi-node workflow handling intent detection, metadata analysis, cost/performance evaluation, and evidence validation.
- **Gemini on Vertex AI Reasoning**: Leverages `google-genai` SDK with strict grounding instructions to eliminate metric hallucination.
- **Natural Language `/chat` Endpoint**: Answers questions like *"Find my most expensive queries in the last 7 days"* or *"Optimize this SQL"*.
- **Distinction Between Estimated vs Measured Savings**: Clearly demarcates dry-run estimations from historical measured execution data.

---

## Agent Workflow

```
User Request ──► Intent Detection ──► Query & Table Metadata Analysis
                                              │
                                              ▼
Recommendations ◄── Gemini Grounding ◄── Cost & Slot Analysis
```

---

## 28 Core BigQuery Tools

| Tool # | Function Name | Purpose |
|---|---|---|
| 1 | `list_datasets(project_id)` | Lists BigQuery datasets |
| 2 | `list_tables(project_id, dataset_id)` | Lists tables within a dataset |
| 3 | `get_table_metadata(project_id, dataset_id, table_id)` | Fetches row counts, size, and metadata |
| 4 | `get_table_schema(project_id, dataset_id, table_id)` | Inspects field types and modes |
| 5 | `get_partitioning_info(...)` | Analyzes partition column and type |
| 6 | `get_clustering_info(...)` | Analyzes clustering column order |
| 7 | `get_recent_query_history(...)` | Queries `INFORMATION_SCHEMA.JOBS_BY_PROJECT` |
| 8 | `get_expensive_queries(...)` | Ranks top queries by total bytes billed |
| 9 | `get_slow_queries(...)` | Ranks top queries by slot-ms consumption |
| 10 | `get_failed_queries(...)` | Identifies failed query executions |
| 11 | `get_query_by_job_id(...)` | Fetches details for a specific job ID |
| 12 | `dry_run_query(sql)` | Dry runs SQL to estimate scan size |
| 13 | `analyze_query(sql)` | Runs full AST and anti-pattern suite |
| 14 | `detect_select_star(sql)` | Detects `SELECT *` and `SELECT * LIMIT` |
| 15 | `detect_missing_partition_filter(sql)` | Flags missing filters on partitioned tables |
| 16 | `detect_missing_clustering_filter(sql)` | Flags missing filters on clustered tables |
| 17 | `detect_large_joins(sql)` | Detects complex multi-table joins |
| 18 | `detect_cross_joins(sql)` | Detects Cartesian products / `CROSS JOIN` |
| 19 | `detect_repeated_subqueries(sql)` | Detects duplicated CTEs/subqueries |
| 20 | `detect_unnecessary_columns(sql)` | Flags excessive column projections |
| 21 | `detect_non_sargable_patterns(sql)` | Flags functions on `WHERE` clause columns |
| 22 | `analyze_bytes_processed(sql)` | Analyzes byte scale (MB, GB, TB) |
| 23 | `estimate_query_cost(sql)` | Calculates estimated cost using $/TiB rate |
| 24 | `analyze_slot_usage(...)` | Analyzes aggregate slot-ms and contention |
| 25 | `analyze_query_performance(...)` | Inspects execution stage breakdown |
| 26 | `generate_optimized_sql(sql)` | Generates refactored BigQuery SQL |
| 27 | `generate_optimization_report(sql)` | Assembles complete JSON report |
| 28 | `compare_original_vs_optimized(...)` | Compares original vs refactored metrics |

---

## Optimization Rules Summary

### Cost Optimization Rules
- `SELECT *` & `SELECT * LIMIT`: BigQuery charges per column scanned regardless of row `LIMIT`.
- Missing Partition Filter: Unfiltered queries on partitioned tables trigger 100% full table scans.
- Repeated Subqueries: Identical subqueries scan datasets multiple times; refactor into CTE `WITH`.
- Excessive Column Projection: Requesting unnecessary columns inflates bytes billed.

### Performance Optimization Rules
- `CROSS JOIN` / Cartesian Product: Causes quadratic memory explosion and slot starvation.
- Missing Clustering Filter: Misses block-level data pruning opportunities.
- Non-Sargable Predicates: Functions like `LOWER(col)` in `WHERE` prevent index/partition lookups.
- Global `ORDER BY` without `LIMIT`: Forces all sorting work onto a single BigQuery slot.

---

## Security & Guardrails

1. **AST & Syntax Filtering**: Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`.
2. **Read-Only BigQuery Execution**: Enforces `dry_run=True` for query analysis.
3. **No Credential Leaks**: Credentials are loaded strictly via Application Default Credentials (ADC). No secret keys or `.env` files are committed.

---

## Setup & Running Locally

### 1. Prerequisites
- Python 3.12+
- Authenticated `gcloud` SDK (`gcloud auth application-default login`)

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default Settings:
```env
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-02-63b2f55175ee
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
BQ_REGION=US
BQ_ON_DEMAND_PRICE_PER_TB=6.25
```

### 3. Install & Start API
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Examples

### Dry-Run Query (`POST /query/dry-run`)
```bash
curl -X POST "http://localhost:8000/query/dry-run" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current`"}'
```

### Analyze Query (`POST /analyze/query`)
```bash
curl -X POST "http://localhost:8000/analyze/query" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 10"}'
```

### Natural Language Chat (`POST /chat`)
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Find my most expensive queries in the last 7 days."}'
```

---

## Testing & Evaluation

### Run Unit & Integration Tests
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### Run Automated 20-Case Agent Evaluation Suite
```bash
python eval/run_eval.py
```

---

## Docker Deployment

```bash
docker-compose up --build
```

---

## License

MIT License - Copyright (c) 2026 Vimal Sagar ([@vimalsagar007](https://github.com/vimalsagar007))
