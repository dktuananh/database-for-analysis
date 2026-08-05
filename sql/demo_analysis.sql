-- Run with DuckDB from the repository root:
--   duckdb
--   .read sql/demo_analysis.sql
-- Hive partitions add order_year from each directory name.

CREATE OR REPLACE VIEW dim_date AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_date.parquet');

CREATE OR REPLACE VIEW dim_customer AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_customer.parquet');

CREATE OR REPLACE VIEW dim_product AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_product.parquet');

CREATE OR REPLACE VIEW dim_geography AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_geography.parquet');

CREATE OR REPLACE VIEW fact_order AS
SELECT *
FROM read_parquet(
  'data/global_superstore/facts/fact_order/**/*.parquet',
  hive_partitioning = true
);

CREATE OR REPLACE VIEW fact_order_line AS
SELECT *
FROM read_parquet(
  'data/global_superstore/facts/fact_order_line/**/*.parquet',
  hive_partitioning = true
);

-- 1. Monthly sales and profit by product category.
SELECT
  d.year_month,
  p.category,
  ROUND(SUM(line.sales), 2) AS sales,
  ROUND(SUM(line.profit), 2) AS profit,
  ROUND(SUM(line.profit) / NULLIF(SUM(line.sales), 0) * 100, 2) AS profit_margin_pct
FROM fact_order_line AS line
JOIN fact_order AS ord USING (order_key)
JOIN dim_date AS d ON d.date_key = ord.order_date_key
JOIN dim_product AS p USING (product_key)
WHERE ord.order_year = 2014
GROUP BY d.year_month, p.category
ORDER BY d.year_month, sales DESC;

-- 2. Countries with the lowest profit (useful for pricing/discount review).
SELECT
  geo.country,
  ROUND(SUM(line.sales), 2) AS sales,
  ROUND(SUM(line.profit), 2) AS profit,
  ROUND(SUM(line.profit) / NULLIF(SUM(line.sales), 0) * 100, 2) AS profit_margin_pct
FROM fact_order_line AS line
JOIN fact_order AS ord USING (order_key)
JOIN dim_geography AS geo USING (geography_key)
GROUP BY geo.country
ORDER BY profit
LIMIT 15;

-- 3. Shipping service level by mode and customer segment.
SELECT
  ship.ship_mode,
  customer.segment,
  COUNT(*) AS orders,
  ROUND(AVG(ord.ship_days), 2) AS avg_ship_days,
  ROUND(QUANTILE_CONT(ord.ship_days, 0.9), 2) AS p90_ship_days
FROM fact_order AS ord
JOIN dim_customer AS customer USING (customer_key)
JOIN read_parquet('data/global_superstore/dimensions/dim_ship_mode.parquet') AS ship
  USING (ship_mode_key)
GROUP BY ship.ship_mode, customer.segment
ORDER BY avg_ship_days DESC, orders DESC;
