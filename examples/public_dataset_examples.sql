-- Public Dataset Demo Queries
-- Used for testing dry runs, cost estimations, and anti-pattern optimizations

-- 1. BAD QUERY (USA Names - SELECT * scan)
-- Scans all columns across millions of rows
SELECT *
FROM `bigquery-public-data.usa_names.usa_1910_current`;

-- 2. BETTER QUERY (USA Names - Selective projection + Partition/Filter pruning)
SELECT state, gender, year, name, number
FROM `bigquery-public-data.usa_names.usa_1910_current`
WHERE year >= 2000;

-- 3. BAD QUERY (GitHub Timeline - CROSS JOIN / Cartesian Product)
SELECT a.repository_url, b.actor
FROM `bigquery-public-data.samples.github_timeline` a
CROSS JOIN `bigquery-public-data.samples.github_timeline` b
LIMIT 100;

-- 4. BETTER QUERY (GitHub Timeline - Selective JOIN with explicit ON predicate)
SELECT a.repository_url, b.actor
FROM `bigquery-public-data.samples.github_timeline` a
JOIN `bigquery-public-data.samples.github_timeline` b
  ON a.repository_name = b.repository_name
WHERE a.created_at >= '2012-01-01 00:00:00'
LIMIT 100;

-- 5. BAD QUERY (GitHub Nested - UNNEST without column pruning)
SELECT *
FROM `bigquery-public-data.samples.github_nested`,
UNNEST(payload.pages) as page;

-- 6. BETTER QUERY (GitHub Nested - Projected fields only)
SELECT repository.name, page.page_name, page.action
FROM `bigquery-public-data.samples.github_nested`,
UNNEST(payload.pages) as page;
