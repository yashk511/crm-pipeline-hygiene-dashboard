-- Business question: where is open pipeline aging concentrated?
SELECT
    CASE
        WHEN open_age_days < 30 THEN '0-29 days'
        WHEN open_age_days < 60 THEN '30-59 days'
        WHEN open_age_days < 90 THEN '60-89 days'
        WHEN open_age_days < 180 THEN '90-179 days'
        ELSE '180+ days'
    END AS aging_bucket,
    COUNT(*) AS open_opportunity_count,
    SUM(amount) AS open_pipeline_value
FROM read_csv_auto('clean/fact_opportunities.csv')
WHERE is_closed = FALSE
GROUP BY aging_bucket
ORDER BY CASE aging_bucket
    WHEN '0-29 days' THEN 1
    WHEN '30-59 days' THEN 2
    WHEN '60-89 days' THEN 3
    WHEN '90-179 days' THEN 4
    ELSE 5
END;
