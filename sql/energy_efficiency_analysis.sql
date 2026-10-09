-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/energy_efficiency/prepared/building_simulations.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

SELECT orientation, count(*) AS configurations,
       avg(heating_load) AS mean_heating_load, avg(cooling_load) AS mean_cooling_load
FROM source_data GROUP BY 1 ORDER BY 1;
-- These are simulation results. Both load columns are targets in multi-output tasks.
