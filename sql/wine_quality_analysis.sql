-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/wine_quality/prepared/wine_samples.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

SELECT wine_type, quality, count(*) AS samples, avg(alcohol) AS mean_alcohol
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Keep repeated feature vectors in the same split when benchmarking models.
