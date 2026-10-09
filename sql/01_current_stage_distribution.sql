-- Business question: where does the pipeline sit TODAY, by current stage?
-- NOTE: this is a snapshot, not a funnel. Stage counts are not conversion rates;
-- see 06_stage_progression.sql for event-based stage progression.
SELECT
    stage,
    stage_order,
    COUNT(*) AS opportunity_count,
    SUM(amount) AS pipeline_value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_all_opportunities_pct
FROM read_csv_auto('clean/fact_opportunities.csv')
GROUP BY stage, stage_order
ORDER BY stage_order;
