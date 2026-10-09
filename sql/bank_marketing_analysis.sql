-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/bank_marketing/prepared/campaign_contacts.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

SELECT contact, poutcome, count(*) AS observations,
       count(*) FILTER (WHERE subscribed = 'yes') AS subscribers,
       avg(CASE WHEN subscribed = 'yes' THEN 1.0 ELSE 0.0 END) AS subscription_rate
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- duration is unavailable before the call: exclude it from pre-call prediction.
