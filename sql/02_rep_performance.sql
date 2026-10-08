-- Business question: which reps have the strongest pipeline and conversion results?
WITH rep_metrics AS (
    SELECT
        r.rep_name,
        r.region,
        r.team,
        COUNT(*) AS opportunity_count,
        SUM(CASE WHEN o.is_closed = TRUE THEN 1 ELSE 0 END) AS closed_count,
        SUM(CASE WHEN o.is_won = TRUE THEN 1 ELSE 0 END) AS won_count,
        SUM(CASE WHEN o.is_closed = FALSE THEN o.amount ELSE 0 END) AS open_pipeline_value
    FROM read_csv_auto('clean/fact_opportunities.csv') o
    JOIN read_csv_auto('clean/dim_reps.csv') r USING (rep_id)
    GROUP BY r.rep_name, r.region, r.team
)
SELECT
    *,
    ROUND(100.0 * won_count / NULLIF(closed_count, 0), 1) AS win_rate_pct,
    RANK() OVER (ORDER BY open_pipeline_value DESC) AS pipeline_rank
FROM rep_metrics
ORDER BY pipeline_rank;
