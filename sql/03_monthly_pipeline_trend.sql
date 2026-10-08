-- Business question: how does opportunity creation and open pipeline change by month?
SELECT
    DATE_TRUNC('month', created_date) AS created_month,
    COUNT(*) AS opportunity_count,
    SUM(CASE WHEN is_closed = FALSE THEN amount ELSE 0 END) AS open_pipeline_value,
    SUM(CASE WHEN is_won = TRUE THEN 1 ELSE 0 END) AS won_count
FROM read_csv_auto('clean/fact_opportunities.csv')
GROUP BY created_month
ORDER BY created_month;
