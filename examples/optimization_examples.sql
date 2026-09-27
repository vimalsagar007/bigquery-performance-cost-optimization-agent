-- Before & After Optimization Comparison Examples

-- Example 1: SELECT * Elimination
-- BEFORE:
SELECT *
FROM `bigquery-public-data.usa_names.usa_1910_current`
WHERE state = 'CA';

-- AFTER:
SELECT state, name, number, year
FROM `bigquery-public-data.usa_names.usa_1910_current`
WHERE state = 'CA';

-- Example 2: CTE for Duplicate Subqueries
-- BEFORE:
SELECT
  a.state,
  (SELECT AVG(number) FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2010) as avg_2010,
  (SELECT MAX(number) FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2010) as max_2010
FROM `bigquery-public-data.usa_names.usa_1910_current` a
GROUP BY a.state;

-- AFTER:
WITH stats_2010 AS (
  SELECT AVG(number) as avg_2010, MAX(number) as max_2010
  FROM `bigquery-public-data.usa_names.usa_1910_current`
  WHERE year = 2010
)
SELECT a.state, s.avg_2010, s.max_2010
FROM `bigquery-public-data.usa_names.usa_1910_current` a
CROSS JOIN stats_2010 s
GROUP BY a.state, s.avg_2010, s.max_2010;
