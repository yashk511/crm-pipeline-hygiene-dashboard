-- Business question: of the opportunities that reached a stage, what share has
-- progressed to the next stage so far?
-- CAVEAT (right-censoring): open deals that have not moved yet count as "not progressed".
-- Rates are therefore "progressed to date", not final conversion rates, and the
-- later stages are understated until their open deals resolve.
WITH stage_presence AS (
    SELECT DISTINCT opp_id, stage, stage_order
    FROM read_csv_auto('clean/opportunity_stage_history.csv')
),
stage_counts AS (
    SELECT stage, stage_order, COUNT(*) AS opportunities_reaching_stage
    FROM stage_presence
    GROUP BY stage, stage_order
),
transitions AS (
    SELECT
        cur.stage AS from_stage,
        cur.stage_order AS from_order,
        nxt.stage AS to_stage,
        nxt.stage_order AS to_order,
        COUNT(*) AS opportunities_progressed
    FROM stage_presence cur
    JOIN stage_presence nxt ON cur.opp_id = nxt.opp_id
    WHERE (cur.stage_order BETWEEN 1 AND 3 AND nxt.stage_order = cur.stage_order + 1)
       OR (cur.stage_order = 4 AND nxt.stage_order IN (5, 6))
    GROUP BY cur.stage, cur.stage_order, nxt.stage, nxt.stage_order
)
SELECT
    t.from_stage,
    t.from_order,
    t.to_stage,
    t.to_order,
    t.opportunities_progressed,
    c.opportunities_reaching_stage AS opportunities_at_start,
    ROUND(100.0 * t.opportunities_progressed / NULLIF(c.opportunities_reaching_stage, 0), 1) AS progressed_to_date_pct
FROM transitions t
JOIN stage_counts c ON c.stage = t.from_stage
ORDER BY t.from_order, t.to_order;
