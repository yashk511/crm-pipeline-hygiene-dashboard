-- Business question: what share of opportunities reaching each stage later reaches the next stage?
WITH stage_presence AS (
    SELECT DISTINCT opp_id, stage
    FROM read_csv_auto('clean/opportunity_stage_history.csv')
),
stage_counts AS (
    SELECT
        stage,
        COUNT(*) AS opportunities_reaching_stage
    FROM stage_presence
    GROUP BY stage
),
transitions AS (
    SELECT
        current_stage.stage AS from_stage,
        next_stage.stage AS to_stage,
        COUNT(*) AS opportunities_transitioned
    FROM stage_presence current_stage
    JOIN stage_presence next_stage
      ON current_stage.opp_id = next_stage.opp_id
    WHERE CASE current_stage.stage
        WHEN 'Prospecting' THEN 1
        WHEN 'Qualification' THEN 2
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
        WHEN 'Closed Won' THEN 5
        WHEN 'Closed Lost' THEN 5
    END + 1 = CASE next_stage.stage
        WHEN 'Prospecting' THEN 1
        WHEN 'Qualification' THEN 2
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
        WHEN 'Closed Won' THEN 5
        WHEN 'Closed Lost' THEN 5
    END
    GROUP BY current_stage.stage, next_stage.stage
)
SELECT
    transitions.from_stage,
    transitions.to_stage,
    transitions.opportunities_transitioned,
    stage_counts.opportunities_reaching_stage AS opportunities_at_start,
    ROUND(100.0 * transitions.opportunities_transitioned
        / NULLIF(stage_counts.opportunities_reaching_stage, 0), 1) AS transition_rate_pct
FROM transitions
JOIN stage_counts
  ON stage_counts.stage = transitions.from_stage
ORDER BY CASE transitions.from_stage
    WHEN 'Prospecting' THEN 1
    WHEN 'Qualification' THEN 2
    WHEN 'Proposal' THEN 3
    WHEN 'Negotiation' THEN 4
END;
