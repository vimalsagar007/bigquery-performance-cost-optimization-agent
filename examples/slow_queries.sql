-- Examples of Slow BigQuery Queries (High Slot-ms Consumption)

-- 1. Unnecessary Global ORDER BY without LIMIT
SELECT name, gender, number
FROM `bigquery-public-data.usa_names.usa_1910_current`
ORDER BY number DESC;

-- 2. Redundant DISTINCT with GROUP BY
SELECT DISTINCT state, gender, COUNT(*)
FROM `bigquery-public-data.usa_names.usa_1910_current`
GROUP BY state, gender;

-- 3. Cartesian CROSS JOIN on large tables
SELECT a.name, b.name
FROM `bigquery-public-data.usa_names.usa_1910_current` a
CROSS JOIN `bigquery-public-data.usa_names.usa_1910_current` b
LIMIT 50;
