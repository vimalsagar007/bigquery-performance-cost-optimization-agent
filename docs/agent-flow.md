# Agent Workflow Specification

The agent operates as a LangGraph stateful graph with 9 execution nodes:

```
[User Request]
      │
      ▼
   (intent)  ──── Determines user goal (Query Analysis vs History vs Table inspection)
      │
      ▼
(query_analyzer) ──── Parses AST, extracts table dependencies
      │
      ▼
(metadata_analyzer) ──── Fetches schema, partitioning, clustering properties
      │
      ▼
(history_analyzer) ──── Queries INFORMATION_SCHEMA.JOBS for historical job execution stats
      │
      ▼
 (cost_analyzer) ──── Runs dry-run and calculates $/TB costs
      │
      ▼
(performance_analyzer) ──── Evaluates slot-ms, shuffle output, and execution stages
      │
      ▼
  (optimizer) ──── Runs anti-pattern rules and generates refactored SQL
      │
      ▼
  (validator) ──── Enforces strict read-only safety guardrails
      │
      ▼
(report_generator) ──── Formats final QueryOptimizationReport JSON
```
