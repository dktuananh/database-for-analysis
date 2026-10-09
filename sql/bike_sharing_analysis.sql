-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/bike_sharing/prepared/hourly_rentals.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

SELECT hour, working_day, count(*) AS observed_hours,
       avg(rental_count) AS mean_rentals
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Forecast target rental_count without casual_count/registered_count.
-- Missing hours are not automatically zero-demand hours.
