# BigQuery Performance and Cost Optimization Agent - Architecture

## High-Level System Architecture

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

## Key Architectural Principles

1. **Version 1 Strictly Read-Only**: The agent enforces read-only access at the AST parser level and the BigQuery API level. DML/DDL queries are rejected immediately.
2. **Empirical Evidence First**: All recommendations require concrete proof (dry-run byte estimates, metadata schema properties, or INFORMATION_SCHEMA job metrics).
3. **No Metric Hallucination**: Gemini AI is constrained by strict Pydantic schemas and structured prompt context.
4. **Decoupled Analyzers**: AST detection, cost analysis, slot analysis, and LLM reasoning are separated into dedicated modules.
