# Optimization Rules Directory

| Rule ID | Rule Name | Category | Severity | Description |
|---|---|---|---|---|
| `RULE_001` | SELECT * | COST | HIGH | Scans 100% of all table columns |
| `RULE_002` | SELECT * LIMIT | COST | HIGH | LIMIT does not reduce BigQuery column scan costs |
| `RULE_003` | Missing Partition Filter | COST | CRITICAL | Triggers full table scan on partitioned table |
| `RULE_004` | Missing Clustering Filter | PERFORMANCE | MEDIUM | Misses block pruning optimization |
| `RULE_005` | Excessive Columns | COST | MEDIUM | Projecting >20 columns unnecessarily |
| `RULE_009` | Large Joins | PERFORMANCE | MEDIUM | >=3 JOINs creating high network shuffle |
| `RULE_010` | CROSS JOIN | PERFORMANCE | CRITICAL | Cartesian product causing slot exhaustion |
| `RULE_011` | Unnecessary ORDER BY | PERFORMANCE | LOW | Global sort without LIMIT forces single-slot processing |
| `RULE_012` | Redundant DISTINCT | PERFORMANCE | LOW | Combining DISTINCT with GROUP BY duplicates shuffle work |
| `RULE_013` | Repeated Subqueries | COST | MEDIUM | Identical subquery executed multiple times |
| `RULE_021` | Non-Sargable Pattern | PERFORMANCE | HIGH | Functions on WHERE columns prevent partition/index pruning |
