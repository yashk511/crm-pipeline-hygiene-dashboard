-- Business question: what share of opportunities reaching each stage later reaches the next stage?
WITH stage_volumes AS (
    -- Step 1: Count the unique number of deals that successfully reached each stage
    SELECT 
        stage_sequence,
        stage,
        COUNT(DISTINCT opp_id) AS deals_reached_stage
    FROM read_csv_auto('clean/opportunity_stage_history.csv')
    WHERE stage NOT IN ('Closed Lost') -- Measure active progression and wins
    GROUP BY 
        stage_sequence, 
        stage
),
progression_rates AS (
    -- Step 2: Use the LAG() window function to pull the previous stage's volume for comparison
    SELECT 
        stage_sequence,
        stage,
        deals_reached_stage,
        LAG(deals_reached_stage) OVER (ORDER BY stage_sequence) AS previous_stage_volume
    FROM stage_volumes
)
-- Step 3: Calculate the stage-to-stage conversion drop-off
SELECT 
    stage_sequence,
    stage,
    deals_reached_stage,
    ROUND((deals_reached_stage * 100.0) / previous_stage_volume, 1) AS transition_rate_pct
FROM progression_rates
ORDER BY stage_sequence;