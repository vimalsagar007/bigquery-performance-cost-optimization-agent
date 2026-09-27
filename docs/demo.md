# Demo Walkthrough

## 1. Dry Run a Public Dataset Query
```bash
curl -X POST "http://localhost:8000/query/dry-run" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current`"}'
```

## 2. Analyze Query for Anti-Patterns
```bash
curl -X POST "http://localhost:8000/analyze/query" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 10"}'
```

## 3. Natural Language Chat
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Find my most expensive queries in the last 7 days."}'
```
