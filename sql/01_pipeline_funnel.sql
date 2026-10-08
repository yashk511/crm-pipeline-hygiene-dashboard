-- Business question: how many opportunities progress through each stage?
WITH stage_counts AS (
    SELECT
        stage,
        COUNT(*) AS opportunity_count,
        SUM(amount) AS pipeline_value
    FROM read_csv_auto('clean/fact_opportunities.csv')
    GROUP BY stage
),
ordered AS (
    SELECT
        *,
        LAG(opportunity_count) OVER (
            ORDER BY CASE stage
                WHEN 'Prospecting' THEN 1
                WHEN 'Qualification' THEN 2
                WHEN 'Proposal' THEN 3
                WHEN 'Negotiation' THEN 4
                WHEN 'Closed Won' THEN 5
                WHEN 'Closed Lost' THEN 6
            END
        ) AS prior_stage_count
    FROM stage_counts
)
SELECT
    stage,
    opportunity_count,
    pipeline_value,
    ROUND(100.0 * opportunity_count / NULLIF(prior_stage_count, 0), 1) AS stage_to_stage_pct
FROM ordered
ORDER BY CASE stage
    WHEN 'Prospecting' THEN 1
    WHEN 'Qualification' THEN 2
    WHEN 'Proposal' THEN 3
    WHEN 'Negotiation' THEN 4
    WHEN 'Closed Won' THEN 5
    WHEN 'Closed Lost' THEN 6
END;
