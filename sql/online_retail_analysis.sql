-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/online_retail/prepared/invoice_lines.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

-- All original rows, including corrections and duplicates; signed source values.
SELECT date_trunc('month', invoice_date) AS month,
       count(*) AS lines, count(DISTINCT invoice_no) AS invoices,
       sum(line_amount_gbp) AS signed_amount_gbp,
       count(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_lines
FROM source_data GROUP BY 1 ORDER BY 1;
-- December 2011 is partial. Define cancellation/deduplication policies before RFM.
