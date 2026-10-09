-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/student_performance/prepared/subject_results.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

SELECT subject, school, count(*) AS subject_observations,
       avg(g3) AS mean_final_grade, avg(absences) AS mean_absences
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Counts are subject observations, not distinct students.
-- g1/g2 are available only after their grading periods.
