-- Examples of Expensive BigQuery SQL Anti-Patterns

-- 1. Full Table Scan with SELECT * and LIMIT
SELECT *
FROM `bigquery-public-data.usa_names.usa_1910_current`
LIMIT 10;

-- 2. Repeated Expensive Subquery Scan
SELECT
  (SELECT COUNT(DISTINCT name) FROM `bigquery-public-data.usa_names.usa_1910_current`) as total_names,
  (SELECT COUNT(DISTINCT name) FROM `bigquery-public-data.usa_names.usa_1910_current`) as repeat_total_names,
  state
FROM `bigquery-public-data.usa_names.usa_1910_current`
GROUP BY state;

-- 3. Non-Sargable Predicate scanning all partitions
SELECT name, state, number
FROM `bigquery-public-data.usa_names.usa_1910_current`
WHERE CAST(year AS STRING) = '2020';
