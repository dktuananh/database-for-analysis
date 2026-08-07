-- GLOBAL SUPERSTORE ANALYTICAL SQL WORKBOOK
-- Engine: DuckDB
-- Run from repository root:
--   duckdb
--   .read sql/demo_analysis.sql
--
-- Modeling contract:
--   fact_order      = one row per distinct order header
--   fact_order_line = one row per source order line
-- Hive directories restore order_year without storing it in each Parquet row.

-- ============================================================
-- 0. REGISTER LOGICAL VIEWS
-- ============================================================

CREATE OR REPLACE VIEW dim_date AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_date.parquet');

CREATE OR REPLACE VIEW dim_customer AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_customer.parquet');

CREATE OR REPLACE VIEW dim_product AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_product.parquet');

CREATE OR REPLACE VIEW dim_geography AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_geography.parquet');

CREATE OR REPLACE VIEW dim_ship_mode AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_ship_mode.parquet');

CREATE OR REPLACE VIEW dim_order_priority AS
SELECT * FROM read_parquet('data/global_superstore/dimensions/dim_order_priority.parquet');

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

-- ============================================================
-- 1. MODEL CONTROL TOTALS AND QUALITY ASSERTIONS
-- Expected: 25,754 orders; 51,290 lines; all duplicate/orphan counts = 0.
-- ============================================================

SELECT
  (SELECT COUNT(*) FROM fact_order) AS order_rows,
  (SELECT COUNT(DISTINCT order_key) FROM fact_order) AS unique_orders,
  (SELECT COUNT(*) FROM fact_order_line) AS line_rows,
  (SELECT COUNT(DISTINCT line_item_key) FROM fact_order_line) AS unique_lines,
  (SELECT ROUND(SUM(sales), 2) FROM fact_order_line) AS control_sales,
  (SELECT ROUND(SUM(profit), 2) FROM fact_order_line) AS control_profit;

SELECT 'line_to_order' AS relationship, COUNT(*) AS orphan_rows
FROM fact_order_line AS line
LEFT JOIN fact_order AS ord USING (order_key)
WHERE ord.order_key IS NULL
UNION ALL
SELECT 'line_to_product', COUNT(*)
FROM fact_order_line AS line
LEFT JOIN dim_product AS product USING (product_key)
WHERE product.product_key IS NULL
UNION ALL
SELECT 'order_to_customer', COUNT(*)
FROM fact_order AS ord
LEFT JOIN dim_customer AS customer USING (customer_key)
WHERE customer.customer_key IS NULL
UNION ALL
SELECT 'order_to_geography', COUNT(*)
FROM fact_order AS ord
LEFT JOIN dim_geography AS geography USING (geography_key)
WHERE geography.geography_key IS NULL;

SELECT
  COUNT(*) FILTER (WHERE quantity <= 0) AS invalid_quantity,
  COUNT(*) FILTER (WHERE sales < 0) AS negative_sales,
  COUNT(*) FILTER (WHERE shipping_cost < 0) AS negative_shipping_cost,
  COUNT(*) FILTER (WHERE discount < 0 OR discount > 1) AS invalid_discount,
  COUNT(*) FILTER (
    WHERE sales IS NULL OR quantity IS NULL OR discount IS NULL
       OR profit IS NULL OR shipping_cost IS NULL
  ) AS null_measure_rows
FROM fact_order_line;

SELECT COUNT(*) AS ship_before_order_rows
FROM fact_order
WHERE ship_date_key < order_date_key;

-- ============================================================
-- 2. EXECUTIVE TREND: MONTHLY SALES, PROFIT AND MARGIN
-- Output grain: one row per order month.
-- ============================================================

SELECT
  date.year_month,
  COUNT(DISTINCT ord.order_key) AS orders,
  ROUND(SUM(line.sales), 2) AS sales,
  ROUND(SUM(line.profit), 2) AS profit,
  ROUND(SUM(line.profit) / NULLIF(SUM(line.sales), 0) * 100, 2)
    AS profit_margin_pct
FROM fact_order_line AS line
JOIN fact_order AS ord USING (order_key)
JOIN dim_date AS date
  ON date.date_key = ord.order_date_key
GROUP BY date.year_month
ORDER BY date.year_month;

-- ============================================================
-- 3. YEAR-OVER-YEAR GROWTH AND REVENUE-PROFIT GAP
-- Full calendar years only. Gap > 0 means sales outgrew profit.
-- ============================================================

WITH yearly AS (
  SELECT
    ord.order_year,
    SUM(line.sales) AS sales,
    SUM(line.profit) AS profit
  FROM fact_order_line AS line
  JOIN fact_order AS ord USING (order_key)
  GROUP BY ord.order_year
), compared AS (
  SELECT
    *,
    LAG(sales) OVER (ORDER BY order_year) AS prior_sales,
    LAG(profit) OVER (ORDER BY order_year) AS prior_profit
  FROM yearly
)
SELECT
  order_year,
  ROUND(sales, 2) AS sales,
  ROUND(profit, 2) AS profit,
  ROUND((sales / NULLIF(prior_sales, 0) - 1) * 100, 2)
    AS sales_growth_pct,
  ROUND((profit / NULLIF(prior_profit, 0) - 1) * 100, 2)
    AS profit_growth_pct,
  ROUND(
    ((sales / NULLIF(prior_sales, 0) - 1)
    - (profit / NULLIF(prior_profit, 0) - 1)) * 100,
    2
  ) AS revenue_profit_gap_pct
FROM compared
ORDER BY order_year;

-- ============================================================
-- 4. CATEGORY PERFORMANCE
-- Never average row-level margins; divide aggregate profit by aggregate sales.
-- ============================================================

SELECT
  product.category,
  COUNT(DISTINCT ord.order_key) AS orders,
  ROUND(SUM(line.sales), 2) AS sales,
  ROUND(SUM(line.profit), 2) AS profit,
  ROUND(SUM(line.profit) / NULLIF(SUM(line.sales), 0) * 100, 2)
    AS profit_margin_pct,
  ROUND(AVG(line.discount) * 100, 2) AS avg_line_discount_pct,
  ROUND(SUM(line.shipping_cost) / NULLIF(SUM(line.sales), 0) * 100, 2)
    AS shipping_cost_ratio_pct
FROM fact_order_line AS line
JOIN fact_order AS ord USING (order_key)
JOIN dim_product AS product USING (product_key)
GROUP BY product.category
ORDER BY sales DESC;

-- ============================================================
-- 5. DISCOUNT RISK BY BAND
-- Descriptive association only; this query does not identify causal effects.
-- ============================================================

WITH banded AS (
  SELECT
    CASE
      WHEN discount = 0 THEN '0%'
      WHEN discount <= 0.10 THEN '0-10%'
      WHEN discount <= 0.20 THEN '10-20%'
      WHEN discount <= 0.30 THEN '20-30%'
      ELSE 'Above 30%'
    END AS discount_band,
    CASE
      WHEN discount = 0 THEN 1
      WHEN discount <= 0.10 THEN 2
      WHEN discount <= 0.20 THEN 3
      WHEN discount <= 0.30 THEN 4
      ELSE 5
    END AS band_order,
    sales,
    profit
  FROM fact_order_line
)
SELECT
  discount_band,
  COUNT(*) AS line_items,
  ROUND(SUM(sales), 2) AS sales,
  ROUND(SUM(profit), 2) AS profit,
  ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2)
    AS profit_margin_pct
FROM banded
GROUP BY discount_band, band_order
ORDER BY band_order;

-- ============================================================
-- 6. CUSTOMER CONCENTRATION
-- NTILE(5) creates customer quintiles within the active filter period.
-- ============================================================

WITH customer_value AS (
  SELECT
    ord.customer_key,
    COUNT(DISTINCT ord.order_key) AS orders,
    SUM(line.sales) AS sales,
    SUM(line.profit) AS profit
  FROM fact_order_line AS line
  JOIN fact_order AS ord USING (order_key)
  GROUP BY ord.customer_key
), ranked AS (
  SELECT
    *,
    NTILE(5) OVER (ORDER BY sales DESC) AS sales_quintile
  FROM customer_value
)
SELECT
  sales_quintile,
  COUNT(*) AS customers,
  ROUND(SUM(sales), 2) AS sales,
  ROUND(SUM(sales) / SUM(SUM(sales)) OVER () * 100, 2)
    AS sales_share_pct,
  ROUND(SUM(profit), 2) AS profit,
  ROUND(SUM(profit) / SUM(SUM(profit)) OVER () * 100, 2)
    AS profit_share_pct
FROM ranked
GROUP BY sales_quintile
ORDER BY sales_quintile;

-- ============================================================
-- 7. MARKET PERFORMANCE WITH A MATERIALITY FLOOR
-- The HAVING clause avoids ranking margins on immaterial sales bases.
-- ============================================================

SELECT
  geography.market,
  COUNT(DISTINCT ord.order_key) AS orders,
  ROUND(SUM(line.sales), 2) AS sales,
  ROUND(SUM(line.profit), 2) AS profit,
  ROUND(SUM(line.profit) / NULLIF(SUM(line.sales), 0) * 100, 2)
    AS profit_margin_pct
FROM fact_order_line AS line
JOIN fact_order AS ord USING (order_key)
JOIN dim_geography AS geography USING (geography_key)
GROUP BY geography.market
HAVING SUM(line.sales) >= 50000
ORDER BY sales DESC;

-- ============================================================
-- 8. SHIPPING SERVICE LEVEL BY MODE AND CUSTOMER SEGMENT
-- Shipping days is an order-header metric, so it must not be averaged on lines.
-- ============================================================

SELECT
  ship.ship_mode,
  customer.segment,
  COUNT(*) AS orders,
  ROUND(AVG(ord.ship_days), 2) AS avg_ship_days,
  ROUND(QUANTILE_CONT(ord.ship_days, 0.9), 2) AS p90_ship_days
FROM fact_order AS ord
JOIN dim_customer AS customer USING (customer_key)
JOIN dim_ship_mode AS ship USING (ship_mode_key)
GROUP BY ship.ship_mode, customer.segment
ORDER BY avg_ship_days DESC, orders DESC;
